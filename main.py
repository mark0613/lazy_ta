import logging
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from src import config
from src.compiler import check_compiler_availability
from src.file_scanner import (
    filter_by_student_ids,
    filter_submissions_by_progress,
    scan_source_codes,
)
from src.grader import compile_all_submissions, grade_submission
from src.models import Submission
from src.report import (
    aggregate_grades,
    generate_csv_report,
    generate_detailed_logs,
    generate_excel_report,
    generate_summary_report,
)
from src.test_runner import TestCaseManager
from src.utils.log import setup_logging

logger = logging.getLogger(__name__)

app = typer.Typer(
    help='Lazy TA - 自動批改系統',
    no_args_is_help=False,  # 允許無參數時執行預設指令
)


def grade_all_submissions_with_progress(
    submissions: list[Submission],
    workers: int = 1,
) -> list[Submission]:
    """
    批改所有 submissions 並顯示進度條和統計資訊

    Args:
        submissions: 要批改的 submissions 列表
        workers: 平行處理的 worker 數量

    Returns:
        批改完成的 submissions 列表
    """
    total = len(submissions)
    graded_submissions = []

    # 統計變數
    success_count = 0
    failed_count = 0
    in_progress_count = 0

    # 建立進度條
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn('•'),
        TimeElapsedColumn(),
        TextColumn('•'),
        TextColumn('[green]✓ {task.fields[success]}'),
        TextColumn('[red]✗ {task.fields[failed]}'),
        TextColumn('[cyan]🔄 {task.fields[in_progress]}'),
    ) as progress:
        task = progress.add_task(
            '[cyan]批改中...',
            total=total,
            success=success_count,
            failed=failed_count,
            in_progress=in_progress_count,
        )

        if workers > 1:
            # 多執行緒模式
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(grade_submission, sub): sub for sub in submissions}
                in_progress_count = len(futures)
                progress.update(task, in_progress=in_progress_count)

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        graded_submissions.append(result)

                        # 更新統計
                        in_progress_count -= 1
                        if result.compile_status == 'failed' or result.final_score == 0:
                            failed_count += 1
                        else:
                            success_count += 1

                    except Exception as e:
                        # 批改過程發生錯誤，記錄並跳過
                        sub = futures[future]
                        logger.error(f'批改失敗: {sub.identifier} - {e}', exc_info=True)
                        in_progress_count -= 1
                        failed_count += 1

                    # 更新進度條
                    progress.update(
                        task,
                        advance=1,
                        success=success_count,
                        failed=failed_count,
                        in_progress=in_progress_count,
                    )
        else:
            # 單執行緒模式
            for sub in submissions:
                in_progress_count = 1
                progress.update(task, in_progress=in_progress_count)

                try:
                    result = grade_submission(sub)
                    graded_submissions.append(result)

                    # 更新統計
                    in_progress_count = 0
                    if result.compile_status == 'failed' or result.final_score == 0:
                        failed_count += 1
                    else:
                        success_count += 1

                except Exception as e:
                    # 批改過程發生錯誤，記錄並跳過
                    logger.error(f'批改失敗: {sub.identifier} - {e}', exc_info=True)
                    in_progress_count = 0
                    failed_count += 1

                # 更新進度條
                progress.update(
                    task,
                    advance=1,
                    success=success_count,
                    failed=failed_count,
                    in_progress=in_progress_count,
                )

    return graded_submissions


def validate_config(require_test_cases: bool = True):
    """
    驗證所有配置

    Args:
        require_test_cases: 是否需要測試案例（grade/build 需要，report 不需要）
    """
    if not config.GOOGLE_API_KEY:
        logger.error('錯誤: 未設定 GOOGLE_API_KEY 環境變數')
        raise typer.Exit(code=1)

    if not Path('source_codes').exists():
        logger.error('錯誤: source_codes/ 資料夾不存在')
        raise typer.Exit(code=1)

    if require_test_cases:
        if not config.TEST_CASES_DIR.exists():
            logger.error(f'錯誤: 測試案例目錄不存在: {config.TEST_CASES_DIR}')
            raise typer.Exit(code=1)

        if not any(config.TEST_CASES_DIR.iterdir()):
            logger.error(f'錯誤: 測試案例目錄為空: {config.TEST_CASES_DIR}')
            raise typer.Exit(code=1)

    # 檢查 compiler
    gcc_path = config.GCC_PATH
    gpp_path = config.GPP_PATH
    logger.info(f'GCC: {gcc_path}')
    logger.info(f'G++: {gpp_path}')
    if not check_compiler_availability():
        raise typer.Exit(code=1)


@app.command()
def grade(
    workers: int = typer.Option(1, '--workers', '-w', help='平行處理的 worker 數量'),
    student: Optional[str] = typer.Option(
        None,
        '--student',
        '-s',
        help='指定批改的學號（逗號分隔）',
    ),
):
    """
    執行完整批改流程（編譯、測試、評分、生成報告）

    範例:
        uv run main.py grade                    # 批改所有未處理的學生
        uv run main.py grade --workers 4        # 使用 4 個 worker 平行處理
        uv run main.py grade --student 110550099  # 只批改特定學號
    """
    # 設定日誌
    setup_logging('INFO')

    logger.info('=' * 60)
    logger.info('Lazy TA - 自動批改')
    logger.info('=' * 60)

    start_time = datetime.now()
    logger.info(f'開始時間: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

    # 驗證所有配置
    try:
        validate_config()
    except typer.Exit:
        return

    # 準備 test cases
    TestCaseManager.get_instance()

    logger.info('階段 1: 掃描提交檔案')
    all_submissions = scan_source_codes(Path('source_codes'))

    if not all_submissions:
        logger.warning('沒有找到任何提交檔案')
        raise typer.Exit(code=0)

    logger.info(f'找到 {len(all_submissions)} 份提交')

    # 過濾提交
    submissions = all_submissions

    # 指定學生模式
    if student:
        student_ids = [s.strip() for s in student.split(',')]
        logger.info(f'指定批改學生: {", ".join(student_ids)}')
        submissions = filter_by_student_ids(submissions, student_ids)

        if not submissions:
            logger.warning('指定的學生沒有提交檔案')
            raise typer.Exit(code=0)

    # 繼續批改模式（預設行為）
    else:
        logger.info('階段 2: 檢查批改進度')
        submissions, _ = filter_submissions_by_progress(all_submissions)

        if not submissions:
            logger.info('所有學生都已批改完成')
            raise typer.Exit(code=0)

    # 統計要批改的學生
    unique_students = set(sub.student_id for sub in submissions)
    logger.info(f'本次批改: {len(unique_students)} 位學生，{len(submissions)} 份提交')

    # 階段 3: 批改
    logger.info(f'階段 3: 編譯、測試與評分（workers={workers}）')
    graded_submissions = grade_all_submissions_with_progress(
        submissions,
        workers=workers,
    )

    # 階段 4: 彙整成績
    logger.info('階段 4: 彙整成績')
    csv_path = Path('results/grades.csv')
    grades = aggregate_grades(graded_submissions, existing_csv_path=csv_path)

    # 階段 5: 生成報告
    logger.info('階段 5: 生成報告')

    # CSV 報告
    generate_csv_report(grades, csv_path)

    # Excel 報告
    excel_path = Path('results/grades.xlsx')
    generate_excel_report(grades, graded_submissions, excel_path)

    # 詳細日誌
    logs_dir = Path('results/detailed_logs')
    generate_detailed_logs(graded_submissions, logs_dir)

    # 摘要報告
    end_time = datetime.now()
    summary_path = Path('results/summary.txt')
    generate_summary_report(grades, graded_submissions, summary_path, start_time, end_time)

    # 完成
    duration = end_time - start_time
    logger.info('=' * 60)
    logger.info('批改完成！')
    logger.info(f'結束時間: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f'總耗時: {str(duration).split(".")[0]}')
    logger.info('=' * 60)
    logger.info('報告檔案：')
    logger.info(f'  - CSV:  {csv_path}')
    logger.info(f'  - Excel: {excel_path}')
    logger.info(f'  - 摘要:  {summary_path}')
    logger.info(f'  - 詳細日誌: {logs_dir}/')
    logger.info('')


@app.command()
def build(
    workers: int = typer.Option(1, '--workers', '-w', help='平行處理的 worker 數量'),
    student: Optional[str] = typer.Option(
        None,
        '--student',
        '-s',
        help='指定編譯的學號（逗號分隔）',
    ),
):
    """
    只編譯學生程式碼（不執行測試和評分）

    範例:
        uv run main.py build                    # 編譯所有未處理的學生
        uv run main.py build --workers 4        # 使用 4 個 worker 平行處理
        uv run main.py build --student 110550099  # 只編譯特定學號
    """
    # 設定日誌
    setup_logging('INFO')

    logger.info('=' * 60)
    logger.info('Lazy TA - 只編譯')
    logger.info('=' * 60)

    start_time = datetime.now()
    logger.info(f'開始時間: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

    # 驗證所有配置
    try:
        validate_config()
    except typer.Exit:
        return

    logger.info('階段 1: 掃描提交檔案')
    all_submissions = scan_source_codes(Path('source_codes'))

    if not all_submissions:
        logger.warning('沒有找到任何提交檔案')
        raise typer.Exit(code=0)

    logger.info(f'找到 {len(all_submissions)} 份提交')

    # 過濾提交
    submissions = all_submissions

    # 指定學生模式
    if student:
        student_ids = [s.strip() for s in student.split(',')]
        logger.info(f'指定編譯學生: {", ".join(student_ids)}')
        submissions = filter_by_student_ids(submissions, student_ids)

        if not submissions:
            logger.warning('指定的學生沒有提交檔案')
            raise typer.Exit(code=0)

    # 繼續編譯模式（預設行為）
    else:
        logger.info('階段 2: 檢查編譯進度')
        submissions, _ = filter_submissions_by_progress(all_submissions)

        if not submissions:
            logger.info('所有學生都已編譯完成')
            raise typer.Exit(code=0)

    # 統計要編譯的學生
    unique_students = set(sub.student_id for sub in submissions)
    logger.info(f'本次編譯: {len(unique_students)} 位學生，{len(submissions)} 份提交')

    # 階段 3: 編譯
    logger.info(f'階段 3: 編譯（workers={workers}）')
    compiled_submissions = compile_all_submissions(
        submissions,
        workers=workers,
    )

    # 生成編譯結果報告
    end_time = datetime.now()
    duration = end_time - start_time

    # 統計編譯結果
    success_count = sum(1 for sub in compiled_submissions if sub.compile_status == 'success')
    failed_count = sum(1 for sub in compiled_submissions if sub.compile_status == 'failed')

    logger.info('=' * 60)
    logger.info('編譯完成！')
    logger.info(f'結束時間: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f'總耗時: {str(duration).split(".")[0]}')
    logger.info('=' * 60)
    logger.info(f'\n編譯結果：')
    logger.info(f'  - 成功: {success_count} 份')
    logger.info(f'  - 失敗: {failed_count} 份')

    if failed_count > 0:
        logger.info('\n編譯失敗的提交：')
        for sub in compiled_submissions:
            if sub.compile_status == 'failed':
                logger.info(f'  - {sub.identifier}: {sub.compile_error}')

    logger.info('')


@app.command()
def clear():
    """
    清除 results 和 tmp 目錄

    範例:
        uv run main.py clear  # 清除所有暫存和結果檔案
    """
    # 設定日誌
    setup_logging('INFO')

    logger.info('=' * 60)
    logger.info('Lazy TA - 清除暫存和結果 (results, tmp)')
    logger.info('=' * 60)

    # 清除 tmp 目錄（整個刪除）
    tmp_path = Path('tmp')
    if tmp_path.exists():
        try:
            shutil.rmtree(tmp_path)
            logger.info(f'✓ 已清除: {tmp_path}/')
        except Exception as e:
            logger.error(f'✗ 清除失敗 {tmp_path}/: {e}')
    else:
        logger.info(f'○ 目錄不存在，跳過: {tmp_path}/')

    # 清除 results 目錄中的非 .log 檔案
    results_path = Path('results')
    if results_path.exists():
        deleted_count = 0
        skipped_count = 0
        error_count = 0

        for item in results_path.rglob('*'):
            if item.is_file():
                # 跳過 .log 檔案
                if item.suffix == '.log':
                    skipped_count += 1
                    continue

                try:
                    item.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f'✗ 刪除失敗 {item}: {e}')
                    error_count += 1

        # 刪除空目錄（由下而上）
        for item in sorted(results_path.rglob('*'), reverse=True):
            if item.is_dir() and not any(item.iterdir()):
                try:
                    item.rmdir()
                except Exception:
                    pass

        logger.info(
            f'✓ 已清除 results/: 刪除 {deleted_count} 個檔案, 跳過 {skipped_count} 個 .log 檔'
        )
        if error_count > 0:
            logger.warning(f'  有 {error_count} 個檔案刪除失敗')
    else:
        logger.info(f'○ 目錄不存在，跳過: {results_path}/')

    logger.info('=' * 60)
    logger.info('清除完成！')
    logger.info('')


@app.command()
def report():
    """
    從 JSONL 進度檔生成報告（不執行編譯、測試、評分）

    範例:
        uv run main.py report  # 從現有進度生成報告
    """
    # 設定日誌
    setup_logging('INFO')

    logger.info('=' * 60)
    logger.info('Lazy TA - 只生成報告')
    logger.info('=' * 60)

    start_time = datetime.now()
    logger.info(f'開始時間: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

    # 檢查進度檔是否存在
    progress_file = config.RESULTS_DIR / 'grading_progress.jsonl'
    if not progress_file.exists():
        logger.error('錯誤: grading_progress.jsonl 不存在，請先執行 grade')
        raise typer.Exit(code=1)

    logger.info('階段 1: 從進度檔讀取資料')
    csv_path = Path('results/grades.csv')

    # 使用空的 graded_submissions，因為我們只從 JSONL 讀取
    grades = aggregate_grades([], existing_csv_path=csv_path)

    logger.info(f'讀取了 {len(grades)} 位學生的成績')

    # 階段 2: 生成報告
    logger.info('階段 2: 生成報告')

    # CSV 報告
    generate_csv_report(grades, csv_path)

    # Excel 報告
    excel_path = Path('results/grades.xlsx')
    generate_excel_report(grades, [], excel_path)

    # 摘要報告
    end_time = datetime.now()
    summary_path = Path('results/summary.txt')
    generate_summary_report(grades, [], summary_path, start_time, end_time)

    # 完成
    duration = end_time - start_time
    logger.info('=' * 60)
    logger.info('報告生成完成！')
    logger.info(f'結束時間: {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info(f'總耗時: {str(duration).split(".")[0]}')
    logger.info('=' * 60)
    logger.info('報告檔案：')
    logger.info(f'  - CSV:  {csv_path}')
    logger.info(f'  - Excel: {excel_path}')
    logger.info(f'  - 摘要:  {summary_path}')
    logger.info('')


if __name__ == '__main__':
    import sys

    # 如果沒有指定 sub-command，預設執行 grade
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1].startswith('-')):
        sys.argv.insert(1, 'grade')

    app()
