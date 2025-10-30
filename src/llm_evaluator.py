import logging

from .models import LLMEvaluation, Submission
from .prompts.problem import format_failed_tests, get_prompt
from .utils.file import read_source_code
from .utils.llm import StatelessJsonLLM

logger = logging.getLogger(__name__)


def get_llm(problem_num: str):
    return StatelessJsonLLM(
        prompt=get_prompt(problem_num),
        response_model=LLMEvaluation,
        response_model_placeholder='format_instructions',
        input_vars=[
            'identifier',
            'source_code',
            'passed_tests',
            'total_tests',
            'failed_test_details',
        ],
    )


def evaluate_with_llm(submission: Submission) -> LLMEvaluation:
    try:
        source_code = read_source_code(submission.file_path)
    except Exception as e:
        logger.error(f'#{submission.student_id} 讀取程式碼失敗: {e}')
        return LLMEvaluation(
            score=-1,
            reason=f'{submission.identifier} 讀取程式碼失敗: {str(e)}',
        )

    model = get_llm(submission.problem_num)

    try:
        response: LLMEvaluation = model.invoke(
            {
                'identifier': submission.identifier,
                'source_code': source_code,
                'passed_tests': submission.passed_tests,
                'total_tests': submission.total_tests,
                'failed_test_details': format_failed_tests(submission.test_results),
            }
        )
    except Exception as e:
        logger.warning(f'{submission.identifier} LLM 評分失敗: {e}')
        return LLMEvaluation(
            score=-1,
            reason=f'{submission.identifier} LLM 評分失敗: {str(e)}',
        )

    submission.llm_response = response.model_dump()
    submission.final_score = response.score
    submission.score_reason = response.reason

    logger.debug(f'{submission.identifier} LLM 評分完成，得分 {response.score}/6')
    return response
