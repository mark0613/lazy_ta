def count_lines(code: str) -> int:
    return len(code.strip().split('\n'))


def remove_markdown_wrapping(content: str) -> str:
    if content.startswith('```') and content.endswith('```'):
        lines = content.split('\n')
        if len(lines) > 2:
            return '\n'.join(lines[1:-1]).strip()
    return content
