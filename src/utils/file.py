import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def validate_student_id(student_id: str) -> bool:
    """
    驗證學號格式

    合法格式:
    - 9 碼純數字 (例如: 110550099)
    - 1 碼英文 + 6 碼數字 (例如: a123456)
    """
    # 9 碼純數字
    if re.match(r'^\d{9}$', student_id):
        return True

    # 1 碼英文 + 6 碼數字
    if re.match(r'^[a-zA-Z]\d{6}$', student_id):
        return True

    return False


def parse_filename(filename: str, folder_student_id: str) -> Optional[dict]:
    """
    解析檔案名稱

    Args:
        filename: 檔案名稱 (例如: "110550099_P1.c", "110550099_P3_a.c", "110550099_P1_ex.c")
        folder_student_id: 資料夾名稱 (學號)

    Returns:
        解析結果 dict 或 None
        {
            "student_id": str,
            "problem_num": str,  # "1", "3_a", "1_ex", "3_a_ex" etc.
            "extension": str,    # "c" 或 "cpp"
        }
    """
    # 正規化：替換 - 為 _，轉大寫 P
    normalized = filename.replace('-', '_')
    normalized = re.sub(r'_p(\d)', r'_P\1', normalized, flags=re.IGNORECASE)

    # 正則匹配: (學號)_P(完整題號).(c|cpp)
    # 完整題號包含: 基礎題號 + 可選子題 + 可選 _ex
    # 支援: P1, P3_a, P3_b, P1_ex, P3_a_ex, P3_ex 等格式
    pattern = r'^(\w+)_P(\d+(?:_[a-zA-Z])?(?:_ex)?)\.(c|cpp)$'
    match = re.match(pattern, normalized)

    if not match:
        logger.warning(f'檔名格式不符: {filename}')
        return None

    file_student_id = match.group(1)
    problem_num = match.group(2)  # "1", "3_a", "1_ex", "3_a_ex", "3_ex" etc.
    extension = match.group(3)

    # 驗證學號格式
    if not validate_student_id(file_student_id):
        logger.warning(f'無效的學號格式: {file_student_id}')
        return None

    # 驗證題號範圍（基礎題號應該是 1-4）
    # 從 problem_num 中提取基礎題號（去除 _a, _b, _ex 等後綴）
    base_problem = problem_num.split('_')[0]
    if base_problem not in ['1', '2', '3', '4']:
        logger.warning(f'無效的題號: {problem_num}')
        return None

    # P3 的合法格式：3_a, 3_b, 3_a_ex, 3_b_ex, 3_ex
    # 拒絕單獨的 "3"（沒有子題也沒有 _ex）
    if base_problem == '3' and problem_num == '3':
        logger.warning(
            f'P3 必須指定子題 (P3_a 或 P3_b) 或為額外題 (P3_ex): {folder_student_id}/{problem_num}'
        )
        return None

    # 檢查學號是否與資料夾一致
    if file_student_id != folder_student_id:
        logger.warning(
            f'學號不一致：檔名 {file_student_id} vs 資料夾 {folder_student_id}，以資料夾為準'
        )
        file_student_id = folder_student_id

    return {
        'student_id': file_student_id,
        'problem_num': problem_num,
        'extension': extension,
    }


def read_source_code(file_path: str | Path) -> str:
    """
    讀取學生程式碼，先以 big5 讀取，如果不行改用 utf-8 讀取，都不行則判定檔案毀損
    """

    try:
        with open(file_path, 'r', encoding='big5') as f:
            return f.read()
    except UnicodeDecodeError:
        pass

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        pass

    raise ValueError('檔案編碼無法辨識')


def get_executable_path(output_path: Path) -> Path:
    # windows
    if os.name == 'nt':
        return output_path.with_suffix('.exe')

    # unix-like
    return output_path
