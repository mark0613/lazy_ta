from pathlib import Path

import pytest

from src.models import GradingProgress, ProblemResult, Submission
from src.progress import write_progress_entry
from src.report import aggregate_grades


@pytest.fixture
def isolated_progress(tmp_path):
    """隔離 progress 檔案的 fixture"""
    import src.config as config
    import src.progress as progress_module

    original_path = config.PROGRESS_LOG_PATH
    test_jsonl = tmp_path / 'test_progress.jsonl'
    test_jsonl.touch()

    # 更新兩個地方的路徑
    config.PROGRESS_LOG_PATH = test_jsonl
    progress_module.log_path = test_jsonl

    yield test_jsonl

    # 還原
    config.PROGRESS_LOG_PATH = original_path
    progress_module.log_path = original_path


class TestAggregateGrades:
    """測試 aggregate_grades() 函數"""

    def test_empty_input(self, isolated_progress):
        """測試空輸入 - 無任何資料"""
        grades = aggregate_grades(submissions=[], existing_csv_path=None)

        assert grades == []

    def test_only_new_submissions(self, isolated_progress):
        """測試只有新提交，無歷史記錄"""
        submissions = [
            Submission(
                student_id='110550099',
                problem_num='1',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='全部通過',
            ),
            Submission(
                student_id='110550099',
                problem_num='4',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=4,
                total_tests=6,
                final_score=5,
                score_reason='部分通過',
            ),
        ]

        grades = aggregate_grades(submissions=submissions, existing_csv_path=None)

        assert len(grades) == 1
        grade = grades[0]
        assert grade.student_id == '110550099'
        assert grade.P1_score == 6
        assert grade.P1_reason == '1: 全部通過'
        assert grade.P4_score == 5
        assert grade.P4_reason == '4: 部分通過'
        assert grade.P2_score is None
        assert grade.P3_score is None

    def test_sub_problem_aggregation(self, isolated_progress):
        """測試子題加總 - P3_a + P3_b = P3 總分"""
        submissions = [
            Submission(
                student_id='A123456',
                problem_num='3_a',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='P3a 通過',
            ),
            Submission(
                student_id='A123456',
                problem_num='3_b',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=4,
                total_tests=6,
                final_score=5,
                score_reason='P3b 部分通過',
            ),
            Submission(
                student_id='A123456',
                problem_num='4',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='全通過',
            ),
        ]

        grades = aggregate_grades(submissions=submissions)

        grade = grades[0]
        assert grade.P3_score == 11  # 6 + 5
        assert grade.P3_reason == '3_a: P3a 通過; 3_b: P3b 部分通過'
        assert grade.P4_score == 6

    def test_extra_problem_scoring(self, isolated_progress):
        """測試額外題計分"""
        submissions = [
            Submission(
                student_id='TEST001',
                problem_num='1',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='全通過',
            ),
            Submission(
                student_id='TEST001',
                problem_num='1_ex',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=4,
                total_tests=6,
                final_score=5,
                score_reason='額外題部分通過',
            ),
            Submission(
                student_id='TEST001',
                problem_num='4',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='全通過',
            ),
        ]

        grades = aggregate_grades(submissions=submissions)

        grade = grades[0]
        assert grade.P1_score == 6
        assert grade.P1_extra == 5
        assert grade.P1_extra_reason == '1_ex: 額外題部分通過'
        assert grade.P4_score == 6

    def test_multiple_students(self, isolated_progress):
        """測試多位學生"""
        submissions = [
            Submission(
                student_id='STU001',
                problem_num='1',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='全通過',
            ),
            Submission(
                student_id='STU002',
                problem_num='2',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=4,
                total_tests=6,
                final_score=5,
                score_reason='部分通過',
            ),
        ]

        grades = aggregate_grades(submissions=submissions)

        assert len(grades) == 2
        student_ids = {g.student_id for g in grades}
        assert student_ids == {'STU001', 'STU002'}

    def test_jsonl_progress_only(self, isolated_progress):
        """測試只從 JSONL 復原成績（無新提交）"""
        # 寫入進度
        progress = GradingProgress(student_id='JSONL001')
        progress.problems['P1'] = ProblemResult(score=6, reason='全通過')
        progress.problems['P4'] = ProblemResult(score=5, reason='部分通過')
        progress.completed = True
        write_progress_entry(progress)

        # 測試復原
        grades = aggregate_grades(submissions=[], existing_csv_path=None)

        assert len(grades) == 1
        grade = grades[0]
        assert grade.student_id == 'JSONL001'
        assert grade.P1_score == 6
        assert grade.P4_score == 5

    def test_csv_grades_only(self, isolated_progress, tmp_path):
        """測試只從 CSV 讀取成績（無 JSONL，無新提交）"""
        # 準備 CSV
        csv_path = tmp_path / 'test_grades.csv'
        csv_content = """學號,P1,P1原因,P2,P2原因,P3,P3原因,P4,P4原因,P1_extra,P1_extra原因,P2_extra,P2_extra原因,P3_extra,P3_extra原因,P4_extra,P4_extra原因,總分,異常
CSV001,6,,5,,,,6,,,,,,,,,,17,
"""
        csv_path.write_text(csv_content, encoding='utf-8-sig')

        grades = aggregate_grades(submissions=[], existing_csv_path=csv_path)

        assert len(grades) == 1
        grade = grades[0]
        assert grade.student_id == 'CSV001'
        assert grade.P1_score == 6
        assert grade.P2_score == 5
        assert grade.P4_score == 6

    def test_priority_new_over_jsonl(self, isolated_progress):
        """測試優先度：新提交 > JSONL"""
        # JSONL 中有舊成績
        progress = GradingProgress(student_id='PRIORITY001')
        progress.problems['P1'] = ProblemResult(score=3, reason='舊成績')
        progress.completed = False
        write_progress_entry(progress)

        # 新提交有更新的成績
        submissions = [
            Submission(
                student_id='PRIORITY001',
                problem_num='1',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='新成績',
            ),
        ]

        grades = aggregate_grades(submissions=submissions, existing_csv_path=None)

        grade = grades[0]
        # 應該使用新提交的成績，而非 JSONL
        assert grade.P1_score == 6
        assert grade.P1_reason == '1: 新成績'

    def test_priority_jsonl_over_csv(self, isolated_progress, tmp_path):
        """測試優先度：JSONL > CSV"""
        # CSV 中有舊成績
        csv_path = tmp_path / 'test_grades.csv'
        csv_content = """學號,P1,P1原因,P2,P2原因,P3,P3原因,P4,P4原因,P1_extra,P1_extra原因,P2_extra,P2_extra原因,P3_extra,P3_extra原因,P4_extra,P4_extra原因,總分,異常
PRIORITY002,3,CSV舊成績,,,,,0,,,,,,,,,,3,
"""
        csv_path.write_text(csv_content, encoding='utf-8-sig')

        # JSONL 中有新成績
        progress = GradingProgress(student_id='PRIORITY002')
        progress.problems['P1'] = ProblemResult(score=6, reason='JSONL新成績')
        write_progress_entry(progress)

        grades = aggregate_grades(submissions=[], existing_csv_path=csv_path)

        grade = grades[0]
        # 應該使用 JSONL 的成績，而非 CSV
        assert grade.P1_score == 6
        assert '1: JSONL新成績' in grade.P1_reason

    def test_all_three_sources(self, isolated_progress, tmp_path):
        """測試三種資料來源同時存在：CSV + JSONL + 新提交"""
        # 1. CSV 有 P1=3
        csv_path = tmp_path / 'test_grades.csv'
        csv_content = """學號,P1,P1原因,P2,P2原因,P3,P3原因,P4,P4原因,P1_extra,P1_extra原因,P2_extra,P2_extra原因,P3_extra,P3_extra原因,P4_extra,P4_extra原因,總分,異常
ALL001,3,CSV,,,,,0,,,,,,,,,,3,
"""
        csv_path.write_text(csv_content, encoding='utf-8-sig')

        # 2. JSONL 有 P1=4 (應覆寫 CSV)
        progress = GradingProgress(student_id='ALL001')
        progress.problems['P1'] = ProblemResult(score=4, reason='JSONL')
        write_progress_entry(progress)

        # 3. 新提交有 P1=6 (應覆寫 JSONL)
        submissions = [
            Submission(
                student_id='ALL001',
                problem_num='1',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='新提交',
            ),
        ]

        grades = aggregate_grades(submissions=submissions, existing_csv_path=csv_path)

        grade = grades[0]
        # 最終應該使用新提交的成績
        assert grade.P1_score == 6
        assert '1: 新提交' in grade.P1_reason

    def test_partial_update(self, isolated_progress):
        """測試部分更新：JSONL 有 P1，新提交只更新 P2"""
        # JSONL 有 P1 和 P4 的成績
        progress = GradingProgress(student_id='PARTIAL001')
        progress.problems['P1'] = ProblemResult(score=6, reason='P1 舊成績')
        progress.problems['P4'] = ProblemResult(score=5, reason='P4 舊成績')
        write_progress_entry(progress)

        # 新提交只有 P2（不影響 P1 和 P4）
        submissions = [
            Submission(
                student_id='PARTIAL001',
                problem_num='2',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=3,
                total_tests=6,
                final_score=4,
                score_reason='P2 新成績',
            ),
        ]

        grades = aggregate_grades(submissions=submissions, existing_csv_path=None)

        grade = grades[0]
        # P1 和 P4 保持 JSONL 的成績
        assert grade.P1_score == 6
        assert '1: P1 舊成績' in grade.P1_reason
        assert grade.P4_score == 5
        # P2 使用新提交的成績
        assert grade.P2_score == 4
        assert '2: P2 新成績' in grade.P2_reason

    def test_calculate_total_score_called(self, isolated_progress):
        """測試 calculate_total_score() 有被正確呼叫"""
        submissions = [
            Submission(
                student_id='TOTAL001',
                problem_num='1',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='全通過',
            ),
            Submission(
                student_id='TOTAL001',
                problem_num='2',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=4,
                total_tests=6,
                final_score=5,
                score_reason='部分通過',
            ),
            Submission(
                student_id='TOTAL001',
                problem_num='4',
                file_path=Path('test.c'),
                file_name='test.c',
                passed_tests=6,
                total_tests=6,
                final_score=6,
                score_reason='全通過',
            ),
        ]

        grades = aggregate_grades(submissions=submissions)

        grade = grades[0]
        # 三題都做了，取最低兩題 (5+6) + P4(6) = 17
        assert grade.total_score == 17

    def test_skip_ungraded_jsonl_entries(self, isolated_progress):
        """測試跳過 JSONL 中未批改的項目 (score=-1)"""
        progress = GradingProgress(student_id='SKIP001')
        progress.problems['P1'] = ProblemResult(score=6, reason='已批改')
        progress.problems['P2'] = ProblemResult(score=-1, reason='')  # 未批改
        progress.problems['P4'] = ProblemResult(score=5, reason='已批改')
        write_progress_entry(progress)

        grades = aggregate_grades(submissions=[], existing_csv_path=None)

        grade = grades[0]
        assert grade.P1_score == 6
        assert grade.P2_score is None  # 應該被跳過
        assert grade.P4_score == 5
