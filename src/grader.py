import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from src import config

from .compiler import compile_code
from .file_scanner import get_problem_key
from .llm_evaluator import evaluate_with_llm
from .llm_writer import rewrite_code_with_retry
from .models import Submission
from .progress import update_progress_entry
from .test_runner import run_all_tests
from .utils.file import get_executable_path

logger = logging.getLogger(__name__)


def setup_workspace(submission: Submission) -> Submission:
    """
    建立工作目錄、複製檔案
    """
    problem_key = get_problem_key(submission)

    # 建立 tmp 目錄結構: tmp/<學號>/P<題號>/
    temp_dir = Path('tmp') / submission.student_id / f'P{submission.problem_num}'
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 建立測試輸出目錄
    test_output_dir = temp_dir / 'test_results'
    test_output_dir.mkdir(exist_ok=True)

    # 複製原始檔到 tmp
    temp_source_file = temp_dir / submission.file_name
    try:
        shutil.copy2(submission.file_path, temp_source_file)
    except Exception as e:
        logger.error(f'複製檔案失敗: {e}')
        submission.compile_status = 'failed'
        submission.compile_error = f'複製檔案失敗: {str(e)}'
        submission.final_score = 0
        submission.score_reason = '複製檔案失敗'
        submission.graded_at = datetime.now()

        # 更新進度
        update_progress_entry(submission.student_id, problem_key, 0, submission.score_reason)

        return submission

    # 設置 submission 的 tmp 路徑
    submission.tmp_dir = temp_dir
    submission.tmp_source_file = temp_source_file

    # 可執行檔路徑: tmp/<學號>/P<題號>/<檔名去掉副檔名>.exe
    executable = temp_source_file.with_suffix('')
    if os.name == 'nt':
        executable = executable.with_suffix('.exe')
    submission.executable_path = executable

    return submission


def compile_original(submission: Submission) -> Submission:
    """
    編譯原始版本
    """
    # 如果前一階段已經失敗，直接返回
    if submission.compile_status == 'failed':
        return submission

    problem_key = get_problem_key(submission)
    timeout = config.COMPILE_TIMEOUT

    original_success, original_error = compile_code(submission.tmp_source_file, timeout)

    if not original_success:
        submission.compile_status = 'failed'
        submission.compile_error = original_error
        submission.final_score = 0
        submission.score_reason = '編譯失敗'
        submission.graded_at = datetime.now()
        logger.debug(f'原始版本編譯失敗: {submission.student_id} P{submission.problem_num}')

        # 更新進度
        update_progress_entry(submission.student_id, problem_key, 0, submission.score_reason)

        return submission

    submission.compile_status = 'success'
    submission.compile_error = ''

    return submission


def rewrite_with_llm(submission: Submission) -> Submission:
    """
    LLM rewrite 並嘗試編譯
    """
    # 如果編譯失敗，跳過此階段
    if submission.compile_status == 'failed':
        return submission

    timeout = config.COMPILE_TIMEOUT
    rewritten_file, line_match = rewrite_code_with_retry(submission.tmp_source_file, max_retries=3)

    if line_match:
        rewrite_compile_success, rewrite_error = compile_code(rewritten_file, timeout)

        if rewrite_compile_success:
            logger.debug(f'{submission.identifier} Rewrite 版本編譯成功，使用 rewrite 版本測試')
            submission.executable_path = get_executable_path(rewritten_file)
        else:
            logger.debug(
                f'{submission.identifier} Rewrite 版本編譯失敗，使用原始版本測試: {rewrite_error}'
            )
    else:
        logger.debug(f'{submission.identifier} Rewrite 失敗，使用原始版本測試')

    return submission


def run_tests(submission: Submission) -> Submission:
    """
    執行所有 test cases
    """
    # 如果編譯失敗，跳過此階段
    if submission.compile_status == 'failed':
        return submission

    submission.graded_at = datetime.now()

    # 取得測試輸出目錄
    test_output_dir = submission.tmp_dir / 'test_results'

    all_passed = run_all_tests(submission, test_output_dir)

    if all_passed:
        logger.debug(f'{submission.identifier} 全部通過')
        # 全部通過立即更新進度
        problem_key = get_problem_key(submission)
        update_progress_entry(
            submission.student_id,
            problem_key,
            submission.final_score,
            submission.score_reason,
        )

    return submission


def evaluate_with_llm_if_needed(submission: Submission) -> Submission:
    """
    如果測試未全過，用 LLM 評分
    """
    # 如果編譯失敗，跳過此階段
    if submission.compile_status == 'failed':
        return submission

    # 如果全部測試通過，跳過 LLM 評分
    if submission.passed_tests == submission.total_tests:
        return submission

    # 測試未全部通過 - 需要 LLM 評分
    logger.debug(
        f'{submission.identifier} 需要 LLM 評分:  ({submission.passed_tests}/{submission.total_tests})'
    )

    evaluate_with_llm(submission)

    # LLM 評分後更新進度
    problem_key = get_problem_key(submission)
    update_progress_entry(
        submission.student_id,
        problem_key,
        submission.final_score,
        submission.score_reason,
    )

    return submission


def compile_submission_only(submission: Submission) -> Submission:
    """
    只編譯流程：只執行編譯階段，不執行測試和評分
    """
    # 只執行前兩個階段
    sub = setup_workspace(submission)
    sub = compile_original(sub)

    return sub


def grade_submission(submission: Submission) -> Submission:
    """
    完整批改流程：
    1. 建立工作目錄、複製檔案
    2. 編譯原始版本
    3. LLM rewrite 並嘗試編譯
    4. 執行所有 test cases
    5. 如果測試未全過，用 LLM 評分
    """
    # 依序執行各階段
    sub = setup_workspace(submission)
    sub = compile_original(sub)

    # 如果編譯失敗，直接返回
    if sub.compile_status == 'failed':
        return sub

    sub = rewrite_with_llm(sub)
    sub = run_tests(sub)
    sub = evaluate_with_llm_if_needed(sub)

    return sub


def compile_all_submissions(
    submissions: list[Submission],
    workers: int = 1,
) -> list[Submission]:
    """
    平行編譯所有 submissions（不執行測試和評分）

    Args:
        submissions: 要編譯的 submissions 列表
        workers: 平行處理的 worker 數量

    Returns:
        編譯完成的 submissions 列表
    """
    logger.info(f'開始編譯 {len(submissions)} 份 submissions，使用 {workers} 個 workers')

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(compile_submission_only, sub) for sub in submissions]
            compiled_submissions = [f.result() for f in futures]
    else:
        compiled_submissions = [compile_submission_only(sub) for sub in submissions]

    logger.info('所有 submissions 編譯完成')
    return compiled_submissions


def grade_all_submissions(
    submissions: list[Submission],
    workers: int = 1,
) -> list[Submission]:
    """
    平行批改所有 submissions

    Args:
        submissions: 要批改的 submissions 列表
        workers: 平行處理的 worker 數量

    Returns:
        批改完成的 submissions 列表
    """
    logger.info(f'開始批改 {len(submissions)} 份 submissions，使用 {workers} 個 workers')

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(grade_submission, sub) for sub in submissions]
            graded_submissions = [f.result() for f in futures]
    else:
        graded_submissions = [grade_submission(sub) for sub in submissions]

    logger.info('所有 submissions 批改完成')
    return graded_submissions
