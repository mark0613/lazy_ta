import logging
import subprocess
import time
from pathlib import Path

from src import config

from .models import Submission, TestCase

logger = logging.getLogger(__name__)


class TestCaseManager:
    """測試案例管理器（單例模式）

    在初始化時一次性載入所有測試案例並快取，之後提供 read-only 存取。
    """

    _instance = None

    def __init__(self):
        self._test_cases_cache: dict[str, list[TestCase]] = {}

        # 掃描並載入所有測試案例
        problem_dirs = self._scan_test_directories()
        for problem_dir in problem_dirs:
            problem_num = problem_dir[1:] if problem_dir.startswith('P') else problem_dir
            test_cases = self._load_test_cases(problem_dir)
            self._test_cases_cache[problem_num] = test_cases

        logger.info(
            f'TestCaseManager 初始化完成，載入了 {len(self._test_cases_cache)} 個題目的測試案例'
        )

    @classmethod
    def get_instance(cls) -> 'TestCaseManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_test_cases(self, problem_num: str) -> list[TestCase]:
        return self._test_cases_cache.get(problem_num, [])

    def _scan_test_directories(self) -> list[str]:
        test_cases_dir = Path('test_cases')

        if not test_cases_dir.exists():
            logger.warning('test_cases 目錄不存在')
            return []

        problem_dirs = []
        for item in test_cases_dir.iterdir():
            if item.is_dir() and item.name.startswith('P'):
                problem_dirs.append(item.name)

        return sorted(problem_dirs)

    def _load_test_cases(self, problem_key: str) -> list[TestCase]:
        """
        載入指定題目的所有測試案例

        Args:
            problem_key: 帶 P 前綴的題號 (例如 "P1", "P3_a")
        """
        test_cases = []
        test_dir = Path('test_cases') / problem_key

        if not test_dir.exists():
            logger.warning(f'測試案例資料夾不存在: {test_dir}')
            return test_cases

        problem_num = problem_key[1:]

        # 掃描所有子資料夾
        for folder in test_dir.iterdir():
            if not folder.is_dir():
                continue

            # 檢查是否有 in.txt 和 out.txt
            in_file = folder / 'in.txt'
            out_file = folder / 'out.txt'

            if not in_file.exists() or not out_file.exists():
                logger.warning(f'測試案例資料夾缺少檔案: {folder}')
                continue

            # 建立 TestCase 物件
            test_case = TestCase(problem_num=problem_num, test_folder=folder.name)

            test_cases.append(test_case)
            logger.debug(f'載入測試案例: {problem_key}/{folder.name}')

        return test_cases


def bytes_to_readable_string(data: bytes) -> str:
    """
    將 bytes 轉換為可讀字串
    - 若為有效 UTF-8，返回正常字串
    - 若包含無法解碼的 byte，轉換為 \\xNN 形式

    Args:
        data: 原始 bytes 資料

    Returns:
        可讀字串
    """
    try:
        # 嘗試 UTF-8 解碼
        return data.decode('utf-8')
    except UnicodeDecodeError:
        # 包含無法解碼的 byte，轉換為 hex 表示
        # 使用 repr() 會自動轉換為 \xNN 格式
        result = repr(data)[2:-1]  # 移除 b' 和 ' 的引號
        return result


def run_test_case(
    executable: Path,
    test_case: TestCase,
    timeout: int,
    output_dir: Path = None,
) -> dict:
    """
    執行單一測試案例

    Args:
        executable: 可執行檔路徑
        test_case: 測試案例
        timeout: 超時時間（秒）

    Returns:
        測試結果 dict
    """
    result = {
        'test_folder': test_case.test_folder,
        'passed': False,
        'expected': '',
        'actual': '',
        'execution_time': 0.0,
        'error': '',
    }

    try:
        # 讀取輸入（文字模式）
        with open(test_case.in_path, 'r', encoding='utf-8') as f:
            test_input = f.read()

        # 讀取預期輸出（bytes 模式，以支援任意內容）
        with open(test_case.out_path, 'rb') as f:
            expected_output_bytes = f.read()

        # 轉換為可讀字串用於顯示
        expected_output = bytes_to_readable_string(expected_output_bytes)
        result['expected'] = expected_output

        # 執行程式（bytes 模式，避免解碼錯誤）
        start_time = time.time()
        process = subprocess.run(
            [str(executable)],
            input=test_input.encode('utf-8'),
            capture_output=True,
            timeout=timeout,
            cwd=executable.parent,
        )
        execution_time = time.time() - start_time
        result['execution_time'] = round(execution_time, 3)

        # 取得實際輸出（bytes）
        actual_output_bytes = process.stdout

        # 轉換為可讀字串用於顯示
        actual_output = bytes_to_readable_string(actual_output_bytes)
        result['actual'] = actual_output

        # 儲存輸出到檔案
        if output_dir:
            output_file = output_dir / f'{test_case.test_folder}_out.txt'
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(actual_output)
            except Exception as e:
                logger.warning(f'儲存輸出失敗: {e}')

        # 比對輸出
        if compare_output(expected_output, actual_output):
            result['passed'] = True
            logger.debug(f'測試通過: {test_case.test_folder} ({execution_time:.3f}s)')
        else:
            logger.debug(f'測試失敗: {test_case.test_folder} (輸出不符)')

    except subprocess.TimeoutExpired:
        result['error'] = f'執行超時（超過 {timeout} 秒）'
        logger.debug(f'測試超時: {test_case.test_folder}')

    except Exception as e:
        result['error'] = f'執行錯誤: {str(e)}'
        logger.debug(f'測試錯誤: {test_case.test_folder}: {e}')

    return result


def compare_output(expected: str, actual: str) -> bool:
    """
    比對輸出是否相符

    規則:
    - 逐行比對
    - 忽略行尾空白
    - 忽略檔案結尾空行

    Args:
        expected: 預期輸出
        actual: 實際輸出

    Returns:
        是否相符
    """
    # 分割成行並去除行尾空白
    expected_lines = [line.rstrip() for line in expected.splitlines()]
    actual_lines = [line.rstrip() for line in actual.splitlines()]

    # 移除結尾的空行
    while expected_lines and not expected_lines[-1]:
        expected_lines.pop()

    while actual_lines and not actual_lines[-1]:
        actual_lines.pop()

    # 逐行比對
    return expected_lines == actual_lines


def run_all_tests(submission: Submission, output_dir: Path = None) -> bool:
    """
    執行所有測試案例

    Args:
        submission: Submission 物件
        output_dir: 測試輸出目錄（用於儲存 out.txt）

    Returns:
        是否通過所有測試
    """

    # 取得環境變數配置
    timeout = config.TEST_TIMEOUT

    # 從 submission 取得可執行檔路徑
    executable = submission.executable_path

    if not executable or not executable.exists():
        logger.error(f'可執行檔不存在: {executable}')
        submission.test_results = []
        submission.total_tests = 0
        submission.passed_tests = 0
        return False

    # 載入測試案例
    test_cases = TestCaseManager.get_instance().get_test_cases(submission.problem_num)

    if not test_cases:
        logger.warning(f'{submission.identifier} 找不到對應 test case (可能是學生檔名錯誤)')
        submission.test_results = []
        submission.total_tests = 0
        submission.passed_tests = 0
        submission.final_score = 0
        submission.score_reason = '找不到對應 test case (可能是學生檔名錯誤)'
        return False

    # 執行所有測試
    results = []
    for test_case in test_cases:
        result = run_test_case(executable, test_case, timeout, output_dir)
        results.append(result)

    # 統計結果
    submission.test_results = results
    submission.total_tests = len(results)
    submission.passed_tests = sum(1 for r in results if r['passed'])

    # 判斷是否全部通過
    all_passed = submission.passed_tests == submission.total_tests

    # extra 滿分 5 分，普通題目 30 分，而且輸出格式完全正確再 +1 分
    max_score = 5 if submission.is_extra else 30 + 1

    if all_passed:
        submission.final_score = max_score
        submission.score_reason = f'完全通過 {submission.total_tests} 個測試案例'
        logger.debug(
            f'{submission.identifier} 全部通過: ({submission.passed_tests}/{submission.total_tests})'
        )
    else:
        logger.debug(
            f'{submission.identifier} 部分通過: ({submission.passed_tests}/{submission.total_tests})'
        )

    return all_passed
