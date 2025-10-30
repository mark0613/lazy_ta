from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class Submission(BaseModel):
    """學生提交記錄"""

    student_id: str
    problem_num: str  # "1", "2", "3_a", "3_b", "1_ex", "3_a_ex" etc.

    # 原始路徑
    file_path: Path
    file_name: str

    # tmp 目錄路徑
    tmp_dir: Optional[Path] = None
    tmp_source_file: Optional[Path] = None
    executable_path: Optional[Path] = None

    # 批改結果
    compile_status: str = ''  # "success" / "failed"
    compile_error: str = ''
    test_results: list[dict] = Field(default_factory=list)
    passed_tests: int = 0
    total_tests: int = 0
    final_score: int = 0  # 0-6
    score_reason: str = ''
    llm_response: Optional[dict] = None

    # 時間戳記
    graded_at: Optional[datetime] = None

    @property
    def is_extra(self) -> bool:
        """判斷是否為額外題（problem_num 包含 _ex）"""
        return '_ex' in self.problem_num

    @property
    def problem_description(self) -> str:
        """問題描述，格式: P1, P3_a(ex), P1_ex 等"""
        return f'P{self.problem_num}'

    @property
    def identifier(self) -> str:
        return f'#{self.student_id} - {self.problem_description}'


class TestCase(BaseModel):
    """測試案例結構"""

    problem_num: str  # "1", "2", "3_a", "3_b", "4" etc.
    test_folder: str  # 資料夾名稱（如 "1", "2", "test_basic" 等，不固定）
    in_file: str = 'in.txt'
    out_file: str = 'out.txt'
    timeout: int = 5

    @property
    def test_dir(self) -> Path:
        return Path(f'test_cases/P{self.problem_num}/{self.test_folder}')

    @property
    def in_path(self) -> Path:
        return self.test_dir / self.in_file

    @property
    def out_path(self) -> Path:
        return self.test_dir / self.out_file


class LLMEvaluation(BaseModel):
    """LLM 評分結果"""

    score: int = Field(description='評估的分數')
    reason: str = Field(
        description='評分理由說明，應保持精簡扼要，100 字為限，不使用任何格式化 markdown 語法'
    )


class ProblemResult(BaseModel):
    """單題批改結果"""

    score: int = -1  # -1 表示未批改
    reason: str = ''


class GradingProgress(BaseModel):
    """
    Grading progress record for a student
    """

    student_id: str = Field(alias='id')
    problems: dict[str, ProblemResult] = Field(default_factory=dict)
    completed: bool = False

    model_config = {'populate_by_name': True}

    def is_problem_graded(self, problem_key: str) -> bool:
        result = self.problems.get(problem_key)
        if result is None:
            return False
        return result.score != -1

    def get_ungraded_problems(self) -> list[str]:
        return [key for key, result in self.problems.items() if result.score == -1]

    def update_problem_score(self, problem_key: str, score: int, reason: str = ''):
        self.problems[problem_key] = ProblemResult(score=score, reason=reason)

        # Check if all problems are graded
        if all(r.score != -1 for r in self.problems.values()):
            self.completed = True


class StudentGrade(BaseModel):
    """最終成績記錄"""

    student_id: str

    # 前三題（選做）
    P1_score: Optional[int] = None
    P1_reason: str = ''
    P2_score: Optional[int] = None
    P2_reason: str = ''
    P3_score: Optional[int] = None
    P3_reason: str = ''

    # P4（必做）
    P4_score: int = 0
    P4_reason: str = ''

    # 額外題
    P1_extra: Optional[int] = None
    P1_extra_reason: str = ''
    P2_extra: Optional[int] = None
    P2_extra_reason: str = ''
    P3_extra: Optional[int] = None
    P3_extra_reason: str = ''
    P4_extra: Optional[int] = None
    P4_extra_reason: str = ''

    # 總分計算：前三題取最高分 + 次高分 + P4
    total_score: int = 0

    has_issues: bool = False
    issues: list[str] = Field(default_factory=list)

    def calculate_total_score(self) -> int:
        """計算總分：(前三題選兩個 + P4) + (額外題總分)

        選擇邏輯：
        - 如果最低分是 0（有題目沒做），取最高的兩個
        - 如果最低分不是 0（三題都做了），取最低的兩個
        """
        optional_scores = [
            self.P1_score if self.P1_score is not None else 0,
            self.P2_score if self.P2_score is not None else 0,
            self.P3_score if self.P3_score is not None else 0,
        ]

        # 排序（升序）
        optional_scores.sort()

        # 檢查最低分
        min_score = optional_scores[0]

        if min_score == 0:
            # 有題目沒做，取最高的兩個（即後兩個）
            selected_two = sum(optional_scores[1:3])
        else:
            # 三題都做了，取最低的兩個（即前兩個）
            selected_two = sum(optional_scores[0:2])

        # 一般題總分 = 選中的兩題 + P4
        regular_total = selected_two + self.P4_score

        # 額外題總分
        extra_total = (
            (self.P1_extra if self.P1_extra is not None else 0)
            + (self.P2_extra if self.P2_extra is not None else 0)
            + (self.P3_extra if self.P3_extra is not None else 0)
            + (self.P4_extra if self.P4_extra is not None else 0)
        )

        total = regular_total + extra_total
        self.total_score = total

        return total
