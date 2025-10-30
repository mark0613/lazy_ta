from .p1 import P1_EX_PROMPT, P1_PROMPT
from .p2 import P2_EX_PROMPT, P2_PROMPT
from .p3 import P3_A_PROMPT, P3_B_PROMPT, P3_EX_PROMPT
from .p4 import P4_EX_PROMPT, P4_PROMPT

problem_prompt_map = {
    '1': P1_PROMPT,
    '1_ex': P1_EX_PROMPT,
    '2': P2_PROMPT,
    '2_ex': P2_EX_PROMPT,
    '3_a': P3_A_PROMPT,
    '3_b': P3_B_PROMPT,
    '3_ex': P3_EX_PROMPT,
    '4': P4_PROMPT,
    '4_ex': P4_EX_PROMPT,
}


def get_prompt(problem_num: str):
    prompts = problem_prompt_map.get(problem_num)
    if not prompts:
        raise ValueError(f'未知的題目編號: {problem_num}')
    return prompts


def format_failed_tests(test_results: list[dict]) -> str:
    failed_tests = [t for t in test_results if not t.get('passed', False)]

    if not failed_tests:
        return '無失敗案例'

    details = []
    for test in failed_tests:
        test_folder = test.get('test_folder', 'unknown')
        expected = test.get('expected', '')
        actual = test.get('actual', '')
        error = test.get('error', '')

        detail = f'\n測試案例: {test_folder}'

        if error:
            detail += f'\n  錯誤: {error}'
        else:
            # 限制輸出長度避免 token 過多
            expected_preview = expected[:200] + '...' if len(expected) > 200 else expected
            actual_preview = actual[:200] + '...' if len(actual) > 200 else actual

            detail += f'\n  預期輸出:\n{expected_preview}'
            detail += f'\n  實際輸出:\n{actual_preview}'

        details.append(detail)

    return '\n'.join(details)


__all__ = [
    'P1_PROMPT',
    'P1_EX_PROMPT',
    'P2_PROMPT',
    'P2_EX_PROMPT',
    'P3_A_PROMPT',
    'P3_B_PROMPT',
    'P3_EX_PROMPT',
    'P4_PROMPT',
    'P4_EX_PROMPT',
]
