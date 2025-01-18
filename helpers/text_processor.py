import re
from typing import List

def clean_text(text: str) -> str:
    """Remove backspaces and affected characters."""
    stack = []
    for char in text:
        if char != "\x08":
            stack.append(char)
        elif stack:
            stack.pop()
    return "".join(stack)

def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences."""
    return re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)

def clean(text: str) -> str:
    """Remove ANSI codes and backspaces."""
    return clean_text(strip_ansi(text))

def filter_lines(text: str, exclude_patterns: List[str]) -> str:
    """Filter out lines that match any of the exclude patterns."""
    compiled_patterns = [re.compile(pattern) for pattern in exclude_patterns]
    return "\n".join(
        line
        for line in text.splitlines()
        if not any(pattern.search(line) for pattern in compiled_patterns)
    )

def dedent(text: str) -> str:
    """Remove common leading whitespace from each line in the text."""
    return "\n".join(line.lstrip() for line in text.splitlines())
