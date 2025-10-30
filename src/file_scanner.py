import logging
from collections import defaultdict
from pathlib import Path

from .models import Submission
from .progress import (
    GradingProgress,
    get_student_status,
    initialize_student_progress,
    read_progress_log,
)
from .utils.file import parse_filename, validate_student_id

logger = logging.getLogger(__name__)


def scan_source_codes(source_dir: Path) -> list[Submission]:
    """
    Scan source_codes/ directory and parse all student submissions

    Args:
        source_dir: Path to source_codes/ directory

    Returns:
        List of all Submission objects
    """
    submissions = []

    if not source_dir.exists():
        logger.error(f'source_codes/ directory does not exist: {source_dir}')
        return submissions

    # Iterate through all student folders
    for student_folder in source_dir.iterdir():
        if not student_folder.is_dir():
            continue

        student_id = student_folder.name

        # Validate folder name (student ID)
        if not validate_student_id(student_id):
            logger.warning(f'Invalid student ID folder: {student_id}')
            continue

        # Scan all source files for this student
        for file_path in student_folder.glob('*.[c]*'):
            if file_path.suffix not in ['.c', '.cpp']:
                continue

            # Parse filename
            parse_result = parse_filename(file_path.name, student_id)
            if parse_result is None:
                continue

            # Create Submission object
            submission = Submission(
                student_id=parse_result['student_id'],
                problem_num=parse_result['problem_num'],
                file_path=file_path,
                file_name=file_path.name,
            )

            submissions.append(submission)
            logger.debug(f'Found submission: {submission.identifier}')

    logger.info(f'總共 Submissions: {len(submissions)}')
    return submissions


def get_problem_key(submission: Submission) -> str:
    """
    Generate problem key from submission (e.g., "P1", "P1_ex", "P3_a", "P3_a_ex")

    Args:
        submission: Submission object

    Returns:
        Problem key string
    """
    return f'P{submission.problem_num}'


def filter_submissions_by_progress(
    submissions: list[Submission],
) -> tuple[list[Submission], dict[str, GradingProgress]]:
    """
    根據批改進度篩選提交的檔案

    優先順序：
    1. 跳過已完成的學生
    2. 優先處理有部分進度的學生（先批改未完成的題目）
    3. 處理新學生（初始化進度並批改所有題目）

    Args:
        submissions: 所有提交檔案的列表

    Returns:
        (filtered_submissions, progress_dict)
    """
    # Read progress log
    progress_dict = read_progress_log()

    # Group submissions by student
    student_submissions = defaultdict(list)
    for sub in submissions:
        student_submissions[sub.student_id].append(sub)

    # Categorize students
    completed_students = []
    partial_students = []
    new_students = []

    for student_id, subs in student_submissions.items():
        is_completed, progress = get_student_status(progress_dict, student_id)

        if is_completed:
            completed_students.append(student_id)
        elif progress is not None:
            # Has partial progress
            partial_students.append(student_id)
        else:
            # New student - initialize progress
            new_students.append(student_id)
            problem_keys = [get_problem_key(sub) for sub in subs]
            progress = initialize_student_progress(student_id, problem_keys)
            progress_dict[student_id] = progress

    logger.info(
        f'學生狀態: {len(completed_students)} 完成, '
        f'{len(partial_students)} 部分, {len(new_students)} 新增'
    )

    # Filter submissions to grade
    filtered_submissions = []

    # Priority 1: Partial students (only ungraded problems)
    for student_id in partial_students:
        progress = progress_dict[student_id]
        ungraded_keys = progress.get_ungraded_problems()

        for sub in student_submissions[student_id]:
            problem_key = get_problem_key(sub)
            if problem_key in ungraded_keys:
                filtered_submissions.append(sub)

    # Priority 2: New students (all problems)
    for student_id in new_students:
        filtered_submissions.extend(student_submissions[student_id])

    logger.info(f'待批改的提交數量: {len(filtered_submissions)}')

    return filtered_submissions, progress_dict


def filter_by_student_ids(
    submissions: list[Submission],
    student_ids: list[str],
) -> list[Submission]:
    filtered = [sub for sub in submissions if sub.student_id in student_ids]
    logger.info(f'篩選到 {len(filtered)} 個指定學生的提交')
    return filtered
