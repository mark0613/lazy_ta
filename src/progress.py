import json
import logging
import threading
from typing import Optional

from src import config

from .models import GradingProgress, ProblemResult

logger = logging.getLogger(__name__)

_file_lock = threading.Lock()

log_path = config.PROGRESS_LOG_PATH


def read_progress_log() -> dict[str, GradingProgress]:
    """
    Read grading progress from JSONL file

    Returns:
        Dictionary mapping student_id -> GradingProgress
    """
    progress_dict = {}

    with _file_lock:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        progress = GradingProgress.model_validate(data)
                        progress_dict[progress.student_id] = progress
                    except (json.JSONDecodeError, Exception) as e:
                        logger.debug(f'Failed to parse JSONL line {line_num}: {e}')
                        continue

            logger.info(f'載入 {len(progress_dict)} 位學生的進度記錄')
        except Exception as e:
            logger.error(f'Failed to read progress log: {e}')

    return progress_dict


def write_progress_entry(progress: GradingProgress):
    """
    Append a new progress entry to JSONL file

    Args:
        log_path: Path to JSONL file
        progress: Progress record to write
    """
    with _file_lock:
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                json_line = progress.model_dump_json(by_alias=True)
                f.write(json_line + '\n')

            logger.debug(f'Added progress entry: {progress.student_id}')
        except Exception as e:
            logger.error(f'Failed to write progress entry: {e}')


def update_progress_entry(student_id: str, problem_key: str, score: int, reason: str = ''):
    """
    更新學生的評分進度記錄

    Args:
        student_id: 學號
        problem_key: 題目 key (e.g., "P1", "P3_a")
        score: 分數
        reason: 評分原因
    """
    with _file_lock:
        try:
            # Read all records
            progress_dict = {}

            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        progress = GradingProgress.model_validate(data)
                        progress_dict[progress.student_id] = progress
                    except Exception:
                        continue

            # Update target student's record
            if student_id in progress_dict:
                progress = progress_dict[student_id]
                progress.update_problem_score(problem_key, score, reason)

                # Rewrite entire file
                with open(log_path, 'w', encoding='utf-8') as f:
                    for sid, prog in progress_dict.items():
                        json_line = prog.model_dump_json(by_alias=True)
                        f.write(json_line + '\n')

                logger.debug(
                    f'Updated progress: {student_id} {problem_key}={score} '
                    f'(completed={progress.completed})'
                )
            else:
                logger.debug(f'Student record not found: {student_id}')

        except Exception as e:
            logger.error(f'Failed to update progress entry: {e}')


def initialize_student_progress(
    student_id: str,
    problem_keys: list[str],
) -> GradingProgress:
    """
    初始化學生的評分進度記錄
    """
    progress = GradingProgress(student_id=student_id)

    for key in problem_keys:
        progress.problems[key] = ProblemResult(score=-1, reason='')

    write_progress_entry(progress)

    logger.debug(f'Initialized progress: {student_id} ({len(problem_keys)} problems)')
    return progress


def get_student_status(
    progress_dict: dict[str, GradingProgress],
    student_id: str,
) -> tuple[bool, Optional[GradingProgress]]:
    """
    獲取學生的評分完成狀態
    """
    if student_id not in progress_dict:
        return False, None

    progress = progress_dict[student_id]
    return progress.completed, progress
