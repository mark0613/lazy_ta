import logging
from pathlib import Path

from .prompts.rewrite import COMMENT_PROMPT
from .utils.code import count_lines, remove_markdown_wrapping
from .utils.file import read_source_code
from .utils.llm import StatelessTextLLM

logger = logging.getLogger(__name__)

model = StatelessTextLLM(
    prompt=COMMENT_PROMPT,
    input_vars=['source_code'],
)


def rewrite_code_with_retry(original_file: Path, max_retries: int = 3) -> tuple[Path, bool]:
    try:
        original_code = read_source_code(original_file)
    except Exception as e:
        logger.error(f'Failed to read file: {e}')
        return original_file, False

    original_lines = count_lines(original_code)

    for attempt in range(max_retries):
        try:
            response: str = model.invoke({'source_code': original_code})
        except Exception as e:
            logger.debug(f'LLM processing failed (attempt {attempt + 1}): {e}')
            continue

        modified_code = response.strip()
        modified_code = remove_markdown_wrapping(modified_code)
        modified_lines = count_lines(modified_code)

        if modified_lines == original_lines:
            rewritten_file = (
                original_file.parent / f'{original_file.stem}_rewrite{original_file.suffix}'
            )

            with open(rewritten_file, 'w', encoding='utf-8') as f:
                f.write(modified_code)

            logger.debug(
                f'Code rewritten successfully: {rewritten_file.name} (attempt {attempt + 1})'
            )
            return rewritten_file, True
        else:
            logger.debug(
                f'Line count mismatch (attempt {attempt + 1}): '
                f'original={original_lines}, modified={modified_lines}. Retrying...'
            )

    logger.debug(f'Failed to rewrite code after {max_retries} attempts, using original file')
    return original_file, False
