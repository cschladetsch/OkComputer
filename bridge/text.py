from __future__ import annotations

import re

_MARKDOWN = re.compile(r"(\*\*|\*|#|`|_|~|>|\[|\]|\(|\))")


def strip_markdown(text: str) -> str:
    return re.sub(r"\s+", " ", _MARKDOWN.sub("", text)).strip()


def sentence_chunks(text: str, chunk_chars: int) -> list[str]:
    cleaned = strip_markdown(text)
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]
    chunks: list[str] = []
    for part in parts or [cleaned]:
        while len(part) > chunk_chars:
            chunks.append(part[:chunk_chars].strip())
            part = part[chunk_chars:].strip()
        if part:
            chunks.append(part)
    return chunks
