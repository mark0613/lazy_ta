from src.models import StudentGrade


class TestStudentGradeCalculateTotalScore:
    """測試 StudentGrade.calculate_total_score() 方法"""

    def test_all_zero(self):
        """測試三題都沒做 (0, 0, 0) + P4"""
        grade = StudentGrade(
            student_id='TEST001',
            P1_score=0,
            P2_score=0,
            P3_score=0,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 三題都是 0，取最高兩題 (0+0) + P4(6) = 6
        assert total == 6
        assert grade.total_score == 6

    def test_one_done_two_zero(self):
        """測試只做一題 (6, 0, 0) + P4 - 應取最高兩題"""
        grade = StudentGrade(
            student_id='TEST002',
            P1_score=6,
            P2_score=0,
            P3_score=0,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 有 0 存在，取最高兩題: P1(6) + 0 + P4(6) = 12
        assert total == 12
        assert grade.total_score == 12

    def test_two_done_one_zero(self):
        """測試做兩題 (6, 5, 0) + P4 - 應取最高兩題"""
        grade = StudentGrade(
            student_id='TEST003',
            P1_score=6,
            P2_score=5,
            P3_score=0,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 有 0 存在，取最高兩題: P1(6) + P2(5) + P4(6) = 17
        assert total == 17
        assert grade.total_score == 17

    def test_all_done_penalty(self):
        """測試三題都做 (6, 5, 4) + P4 - 應取最低兩題（懲罰）"""
        grade = StudentGrade(
            student_id='TEST004',
            P1_score=6,
            P2_score=5,
            P3_score=4,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 沒有 0，取最低兩題（懲罰）: P3(4) + P2(5) + P4(6) = 15
        assert total == 15
        assert grade.total_score == 15

    def test_all_done_penalty_different_order(self):
        """測試三題都做，不同順序 (4, 6, 5) + P4 - 應取最低兩題"""
        grade = StudentGrade(
            student_id='TEST005',
            P1_score=4,
            P2_score=6,
            P3_score=5,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 沒有 0，取最低兩題: P1(4) + P3(5) + P4(6) = 15
        assert total == 15

    def test_all_perfect_penalty(self):
        """測試三題都滿分 (6, 6, 6) + P4 - 仍應取最低兩題"""
        grade = StudentGrade(
            student_id='TEST006',
            P1_score=6,
            P2_score=6,
            P3_score=6,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 沒有 0，取最低兩題: 6 + 6 + 6 = 18
        assert total == 18

    def test_with_extra_problems(self):
        """測試有額外題的情況"""
        grade = StudentGrade(
            student_id='TEST007',
            P1_score=6,
            P2_score=5,
            P3_score=0,
            P4_score=6,
            P1_extra=5,
            P3_extra=4,
        )

        total = grade.calculate_total_score()

        # 一般題: (6+5) + 6 = 17
        # 額外題: 5 + 4 = 9
        # 總分: 17 + 9 = 26
        assert total == 26

    def test_only_p4_done(self):
        """測試只做 P4（必做題）"""
        grade = StudentGrade(
            student_id='TEST008',
            P1_score=0,
            P2_score=0,
            P3_score=0,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 取最高兩題 (0+0) + P4(6) = 6
        assert total == 6

    def test_p4_is_zero(self):
        """測試 P4 為 0 的情況"""
        grade = StudentGrade(
            student_id='TEST009',
            P1_score=6,
            P2_score=5,
            P3_score=4,
            P4_score=0,
        )

        total = grade.calculate_total_score()

        # 沒有 0（P4 不算在前三題）→ 取最低兩題: 4 + 5 + 0 = 9
        assert total == 9

    def test_none_values_treated_as_zero(self):
        """測試 None 值被當作 0 處理"""
        grade = StudentGrade(
            student_id='TEST010',
            P1_score=6,
            P2_score=None,  # 未做，應被當作 0
            P3_score=None,  # 未做，應被當作 0
            P4_score=5,
        )

        total = grade.calculate_total_score()

        # None 被當作 0，有 0 存在 → 取最高兩題: 6 + 0 + 5 = 11
        assert total == 11

    def test_all_none_except_p4(self):
        """測試除了 P4 外都是 None"""
        grade = StudentGrade(
            student_id='TEST011',
            P1_score=None,
            P2_score=None,
            P3_score=None,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # None 被當作 0: (0+0) + 6 = 6
        assert total == 6

    def test_extra_only(self):
        """測試只有額外題，沒有一般題"""
        grade = StudentGrade(
            student_id='TEST012',
            P1_score=0,
            P2_score=0,
            P3_score=0,
            P4_score=0,
            P1_extra=5,
            P2_extra=6,
        )

        total = grade.calculate_total_score()

        # 一般題: 0, 額外題: 5 + 6 = 11
        assert total == 11

    def test_boundary_min_score(self):
        """測試邊界情況：最低分"""
        grade = StudentGrade(
            student_id='TEST013',
            P1_score=1,
            P2_score=1,
            P3_score=1,
            P4_score=1,
        )

        total = grade.calculate_total_score()

        # 沒有 0，取最低兩題: 1 + 1 + 1 = 3
        assert total == 3

    def test_boundary_one_zero_rest_full(self):
        """測試邊界情況：一題 0，其他滿分"""
        grade = StudentGrade(
            student_id='TEST014',
            P1_score=6,
            P2_score=6,
            P3_score=0,
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 有 0 存在，取最高兩題: 6 + 6 + 6 = 18
        assert total == 18

    def test_mixed_scores_no_zero(self):
        """測試混合分數，無 0"""
        grade = StudentGrade(
            student_id='TEST015',
            P1_score=3,
            P2_score=5,
            P3_score=2,
            P4_score=4,
        )

        total = grade.calculate_total_score()

        # 沒有 0，取最低兩題: 2 + 3 + 4 = 9
        assert total == 9

    def test_sub_problem_sum(self):
        """測試子題分數已加總的情況（如 P3_a + P3_b = P3_score）"""
        grade = StudentGrade(
            student_id='TEST016',
            P1_score=6,
            P2_score=5,
            P3_score=11,  # P3_a(6) + P3_b(5) 的總和
            P4_score=6,
        )

        total = grade.calculate_total_score()

        # 沒有 0，取最低兩題: 5 + 6 + 6 = 17
        # （P3 的 11 分最高，不被選）
        assert total == 17

    def test_all_extra_problems(self):
        """測試所有題目都有額外題"""
        grade = StudentGrade(
            student_id='TEST017',
            P1_score=6,
            P2_score=5,
            P3_score=0,
            P4_score=6,
            P1_extra=5,
            P2_extra=4,
            P3_extra=3,
            P4_extra=6,
        )

        total = grade.calculate_total_score()

        # 一般題: (6+5) + 6 = 17
        # 額外題: 5+4+3+6 = 18
        # 總分: 35
        assert total == 35
