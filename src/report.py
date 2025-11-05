import csv
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from .models import StudentGrade, Submission
from .progress import read_progress_log

logger = logging.getLogger(__name__)


def clean_excel_string(text: str) -> str:
    """
    清理字串中的非法字符,使其可以安全地寫入 Excel

    移除:
    - ANSI 控制字符 (如顏色碼)
    - 其他 Excel 不允許的控制字符

    Args:
        text: 要清理的字串

    Returns:
        清理後的字串
    """
    if not text:
        return text

    # 移除 ANSI escape sequences (例如 \x1b[38;5;16m)
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)

    # 移除其他控制字符 (保留換行符、tab、回車)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    return text


def _apply_jsonl_progress(grade: StudentGrade, progress):
    """
    從 JSONL 進度記錄中復原成績到 StudentGrade

    Args:
        grade: 學生成績物件
        progress: GradingProgress 物件
    """
    # 用於累加子題分數和原因
    problem_scores = defaultdict(int)
    problem_reasons = defaultdict(list)
    extra_scores = defaultdict(int)
    extra_reasons = defaultdict(list)

    for problem_key, result in progress.problems.items():
        # 跳過未批改的題目
        if result.score == -1:
            continue

        # 解析 problem_key (例如 "P1", "P3_a", "P1_ex")
        # 去掉開頭的 P (progress 中的 key 一定是 "P1", "P2" 格式)
        problem_num = problem_key[1:]

        # 判斷是否為額外題
        is_extra = '_ex' in problem_num

        # 取得基礎題號（去除 _ex）
        if is_extra:
            base_problem = problem_num.replace('_ex', '').split('_')[0]
        else:
            base_problem = problem_num.split('_')[0]

        # 累加分數和原因
        if is_extra:
            extra_scores[base_problem] += result.score
            if result.reason:
                extra_reasons[base_problem].append(f'{problem_num}: {result.reason}')
        else:
            problem_scores[base_problem] += result.score
            if result.reason:
                problem_reasons[base_problem].append(f'{problem_num}: {result.reason}')

    # 填入一般題和額外題成績
    _apply_problem_scores(grade, problem_scores, problem_reasons, is_extra=False)
    _apply_problem_scores(grade, extra_scores, extra_reasons, is_extra=True)


def _process_submission_scores(
    submissions: list[Submission],
) -> tuple[dict[str, int], dict[str, list[str]], dict[str, int], dict[str, list[str]]]:
    """
    處理 submissions 並累加分數和原因

    Args:
        submissions: 學生的提交列表

    Returns:
        (problem_scores, problem_reasons, extra_scores, extra_reasons)
    """
    problem_scores = defaultdict(int)
    problem_reasons = defaultdict(list)
    extra_scores = defaultdict(int)
    extra_reasons = defaultdict(list)

    for sub in submissions:
        problem_num = sub.problem_num
        is_extra = sub.is_extra
        score = sub.final_score
        reason = sub.score_reason

        # 取得基礎題號（如 "3_a" -> "3"）
        base_problem = problem_num.split('_')[0]

        if is_extra:
            # 額外題：累加分數和原因
            extra_scores[base_problem] += score
            if reason:
                extra_reasons[base_problem].append(f'{problem_num}: {reason}')
        else:
            # 一般題：累加分數和原因
            problem_scores[base_problem] += score
            if reason:
                problem_reasons[base_problem].append(f'{problem_num}: {reason}')

    return problem_scores, problem_reasons, extra_scores, extra_reasons


def _apply_problem_scores(
    grade: StudentGrade,
    problem_scores: dict[str, int],
    problem_reasons: dict[str, list[str]],
    is_extra: bool = False,
):
    """
    將題目分數和原因應用到 StudentGrade

    Args:
        grade: 學生成績物件
        problem_scores: 基礎題號 -> 總分的字典
        problem_reasons: 基礎題號 -> 原因列表的字典
        is_extra: 是否為額外題
    """
    # 定義題目映射表
    if is_extra:
        score_mapping = {
            '1': 'P1_extra',
            '2': 'P2_extra',
            '3': 'P3_extra',
            '4': 'P4_extra',
        }
        reason_mapping = {
            '1': 'P1_extra_reason',
            '2': 'P2_extra_reason',
            '3': 'P3_extra_reason',
            '4': 'P4_extra_reason',
        }
    else:
        score_mapping = {
            '1': 'P1_score',
            '2': 'P2_score',
            '3': 'P3_score',
            '4': 'P4_score',
        }
        reason_mapping = {
            '1': 'P1_reason',
            '2': 'P2_reason',
            '3': 'P3_reason',
            '4': 'P4_reason',
        }

    # 應用分數和原因
    for base_problem, total_score in problem_scores.items():
        reasons = '; '.join(problem_reasons[base_problem])
        if base_problem in score_mapping:
            setattr(grade, score_mapping[base_problem], total_score)
            setattr(grade, reason_mapping[base_problem], reasons)


def read_existing_grades(csv_path: Path) -> dict[str, StudentGrade]:
    """
    從現有的 CSV 讀取成績

    Args:
        csv_path: CSV 文件路徑

    Returns:
        學號 -> StudentGrade 的字典
    """

    grades_dict = {}

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                student_id = row['學號']
                grade = StudentGrade(student_id=student_id)

                # 讀取分數（空值視為 None）
                def parse_score(value):
                    return int(value) if value.strip() else None

                grade.P1_score = parse_score(row.get('P1', ''))
                grade.P2_score = parse_score(row.get('P2', ''))
                grade.P3_score = parse_score(row.get('P3', ''))
                grade.P4_score = parse_score(row.get('P4', ''))

                grade.P1_extra = parse_score(row.get('P1_extra', ''))
                grade.P2_extra = parse_score(row.get('P2_extra', ''))
                grade.P3_extra = parse_score(row.get('P3_extra', ''))
                grade.P4_extra = parse_score(row.get('P4_extra', ''))

                # 讀取評分原因
                grade.P1_reason = row.get('P1原因', '')
                grade.P2_reason = row.get('P2原因', '')
                grade.P3_reason = row.get('P3原因', '')
                grade.P4_reason = row.get('P4原因', '')

                # 讀取額外題原因
                grade.P1_extra_reason = row.get('P1_extra原因', '')
                grade.P2_extra_reason = row.get('P2_extra原因', '')
                grade.P3_extra_reason = row.get('P3_extra原因', '')
                grade.P4_extra_reason = row.get('P4_extra原因', '')

                grades_dict[student_id] = grade

        logger.info(f'從 {csv_path} 讀取了 {len(grades_dict)} 位學生的成績')
    except Exception as e:
        logger.warning(f'讀取舊成績失敗: {e}')

    return grades_dict


def aggregate_grades(
    submissions: list[Submission],
    existing_csv_path: Path = None,
) -> list[StudentGrade]:
    """
    彙整 submissions 為學生成績並計算總分

    優先從 grading_progress.jsonl 讀取進度，若沒有則從 CSV 讀取

    Args:
        submissions: 批改完成的 submissions 列表
        existing_csv_path: 現有的成績 CSV 路徑

    Returns:
        計算好總分的 StudentGrade 物件列表
    """
    # 1. 優先從 grading_progress.jsonl 讀取進度
    progress_dict = read_progress_log()
    logger.info(f'從 JSONL 讀取了 {len(progress_dict)} 位學生的進度記錄')

    # 2. 從 CSV 讀取舊成績作為 fallback
    csv_grades = {}
    if existing_csv_path and existing_csv_path.exists():
        csv_grades = read_existing_grades(existing_csv_path)
        logger.info(f'從 CSV 讀取了 {len(csv_grades)} 位學生的舊成績')

    # 按學號分組
    student_submissions = defaultdict(list)
    for sub in submissions:
        student_submissions[sub.student_id].append(sub)

    # 收集所有學生（包括 JSONL、CSV 和新的 submissions）
    all_student_ids = (
        set(progress_dict.keys()) | set(csv_grades.keys()) | set(student_submissions.keys())
    )
    grades = []

    for student_id in all_student_ids:
        # 初始化成績（優先順序：CSV -> 空白）
        if student_id in csv_grades:
            grade = csv_grades[student_id]
        else:
            grade = StudentGrade(student_id=student_id)

        # 從 JSONL 復原進度（覆寫 CSV 的資料）
        if student_id in progress_dict:
            _apply_jsonl_progress(grade, progress_dict[student_id])

        # 如果有新批改的 submissions，更新成績（覆寫 JSONL 和 CSV）
        if student_id not in student_submissions:
            # 沒有新批改，直接使用復原的成績
            grade.calculate_total_score()
            grades.append(grade)
            continue

        subs = student_submissions[student_id]

        # 處理新提交的分數和原因
        problem_scores, problem_reasons, extra_scores, extra_reasons = _process_submission_scores(
            subs
        )

        # 填入成績（只更新有新批改的題目）
        _apply_problem_scores(grade, problem_scores, problem_reasons, is_extra=False)
        _apply_problem_scores(grade, extra_scores, extra_reasons, is_extra=True)

        # 計算總分
        grade.calculate_total_score()

        grades.append(grade)

    logger.info(f'彙整了 {len(grades)} 位學生的成績')
    return grades


def generate_csv_report(grades: list[StudentGrade], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        # 寫入標題
        writer.writerow(
            [
                '學號',
                'P1',
                'P1原因',
                'P2',
                'P2原因',
                'P3',
                'P3原因',
                'P4',
                'P4原因',
                'P1_extra',
                'P1_extra原因',
                'P2_extra',
                'P2_extra原因',
                'P3_extra',
                'P3_extra原因',
                'P4_extra',
                'P4_extra原因',
                '總分',
                '異常',
            ]
        )

        # 寫入資料
        for grade in grades:
            issues = '; '.join(grade.issues) if grade.issues else ''

            writer.writerow(
                [
                    grade.student_id,
                    grade.P1_score if grade.P1_score is not None else '',
                    grade.P1_reason,
                    grade.P2_score if grade.P2_score is not None else '',
                    grade.P2_reason,
                    grade.P3_score if grade.P3_score is not None else '',
                    grade.P3_reason,
                    grade.P4_score,
                    grade.P4_reason,
                    grade.P1_extra if grade.P1_extra is not None else '',
                    grade.P1_extra_reason,
                    grade.P2_extra if grade.P2_extra is not None else '',
                    grade.P2_extra_reason,
                    grade.P3_extra if grade.P3_extra is not None else '',
                    grade.P3_extra_reason,
                    grade.P4_extra if grade.P4_extra is not None else '',
                    grade.P4_extra_reason,
                    grade.total_score,
                    issues,
                ]
            )

    logger.info(f'CSV 報告已生成: {output_path}')


def generate_excel_report(
    grades: list[StudentGrade],
    submissions: list[Submission],
    output_path: Path,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 工作表 1: 總成績表
        grade_data = []
        for grade in grades:
            issues = '; '.join(grade.issues) if grade.issues else ''
            grade_data.append(
                {
                    '學號': grade.student_id,
                    'P1': grade.P1_score if grade.P1_score is not None else '',
                    'P1原因': clean_excel_string(grade.P1_reason),
                    'P2': grade.P2_score if grade.P2_score is not None else '',
                    'P2原因': clean_excel_string(grade.P2_reason),
                    'P3': grade.P3_score if grade.P3_score is not None else '',
                    'P3原因': clean_excel_string(grade.P3_reason),
                    'P4': grade.P4_score,
                    'P4原因': clean_excel_string(grade.P4_reason),
                    'P1_extra': grade.P1_extra if grade.P1_extra is not None else '',
                    'P1_extra原因': clean_excel_string(grade.P1_extra_reason),
                    'P2_extra': grade.P2_extra if grade.P2_extra is not None else '',
                    'P2_extra原因': clean_excel_string(grade.P2_extra_reason),
                    'P3_extra': grade.P3_extra if grade.P3_extra is not None else '',
                    'P3_extra原因': clean_excel_string(grade.P3_extra_reason),
                    'P4_extra': grade.P4_extra if grade.P4_extra is not None else '',
                    'P4_extra原因': clean_excel_string(grade.P4_extra_reason),
                    '總分': grade.total_score,
                    '異常': clean_excel_string(issues),
                }
            )

        df_grades = pd.DataFrame(grade_data)
        df_grades.to_excel(writer, sheet_name='總成績表', index=False)

        # 工作表 2: 詳細測試結果
        test_data = []
        for sub in submissions:
            for result in sub.test_results:
                test_data.append(
                    {
                        '學號': sub.student_id,
                        '題號': f'P{sub.problem_num}' + ('_ex' if sub.is_extra else ''),
                        '測試案例': result.get('test_folder', ''),
                        '通過': '是' if result.get('passed', False) else '否',
                        '執行時間(s)': result.get('execution_time', 0),
                        '錯誤': clean_excel_string(result.get('error', '')),
                    }
                )

        if test_data:
            df_tests = pd.DataFrame(test_data)
            df_tests.to_excel(writer, sheet_name='詳細測試結果', index=False)

    logger.info(f'Excel 報告已生成: {output_path}')


def generate_detailed_logs(submissions: list[Submission], output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    # 按學號分組
    student_submissions = defaultdict(list)
    for sub in submissions:
        student_submissions[sub.student_id].append(sub)

    # 為每個學生生成日誌
    for student_id, subs in student_submissions.items():
        log_file = output_dir / f'{student_id}.txt'

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('=' * 60 + '\n')
            f.write(f'學生: {student_id}\n')
            if subs[0].graded_at:
                f.write(f'批改時間: {subs[0].graded_at.strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('=' * 60 + '\n\n')

            # 按題號排序
            subs.sort(key=lambda x: (x.problem_num, x.is_extra))

            for sub in subs:
                problem_label = f'P{sub.problem_num}' + ('_ex' if sub.is_extra else '')
                f.write(f'【{problem_label}】 {sub.file_name}\n')
                f.write('-' * 60 + '\n')

                # 編譯狀態
                if sub.compile_status == 'success':
                    f.write('編譯: ✓ 成功\n')

                    # 測試結果
                    if sub.test_results:
                        f.write('測試結果:\n')
                        for result in sub.test_results:
                            test_folder = result.get('test_folder', '')
                            passed = result.get('passed', False)
                            exec_time = result.get('execution_time', 0)
                            error = result.get('error', '')

                            if passed:
                                f.write(f'  {test_folder}: ✓ 通過 ({exec_time:.3f}s)\n')
                            else:
                                f.write(f'  {test_folder}: ✗ 失敗\n')
                                if error:
                                    f.write(f'    錯誤: {error}\n')
                                else:
                                    expected = result.get('expected', '')
                                    actual = result.get('actual', '')
                                    f.write(f'    預期: {repr(expected)}\n')
                                    f.write(f'    實際: {repr(actual)}\n')

                    f.write(f'最終得分: {sub.final_score}/6\n')
                    f.write(f'評分理由: {sub.score_reason}\n')

                else:
                    f.write('編譯: ✗ 失敗\n')
                    f.write('錯誤訊息:\n')
                    f.write(f'{sub.compile_error}\n')
                    f.write(f'最終得分: {sub.final_score}/6\n')

                f.write('\n')

            # 總分
            total_score = sum(sub.final_score for sub in subs if not sub.is_extra)
            f.write('=' * 60 + '\n')
            f.write(f'總分: {total_score}\n')
            f.write('=' * 60 + '\n')

    logger.info(f'詳細日誌已生成: {output_dir} ({len(student_submissions)} 位學生)')


def generate_summary_report(
    grades: list[StudentGrade],
    submissions: list[Submission],
    output_path: Path,
    start_time: datetime,
    end_time: datetime,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    duration = end_time - start_time
    duration_str = str(duration).split('.')[0]

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('=' * 60 + '\n')
        f.write(' ' * 18 + '作業批改摘要報告\n')
        f.write('=' * 60 + '\n')
        f.write(
            f'批改時間: {start_time.strftime("%Y-%m-%d %H:%M:%S")} - {end_time.strftime("%H:%M:%S")}\n'
        )
        f.write(f'總耗時: {duration_str}\n\n')

        f.write('【統計資訊】\n')
        f.write(f'- 總學生數: {len(grades)}\n')
        f.write(f'- 提交份數: {len(submissions)}\n\n')

        f.write('=' * 60 + '\n')
        f.write('詳細記錄請查看 detailed_logs/ 資料夾\n')
        f.write('=' * 60 + '\n')

    logger.info(f'摘要報告已生成: {output_path}')
