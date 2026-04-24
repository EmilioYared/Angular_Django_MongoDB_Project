from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts).strip()

    return path.read_text(encoding="utf-8", errors="ignore").strip()


def normalize_text(text: str) -> str:
    return " ".join(text.split())


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(cleaned)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length:
            split_at = cleaned.rfind(" ", start + max(chunk_size // 2, 1), end)
            if split_at > start:
                end = split_at

        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(end - overlap, start + 1)

    return chunks
