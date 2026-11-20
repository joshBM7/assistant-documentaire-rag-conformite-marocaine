"""Découpage structurel des textes juridiques : un passage par article."""
from __future__ import annotations

import re
from bisect import bisect_right

from .models import Chunk

ARTICLE_RE = re.compile(
    r"^[ \t]*(?:article|art\.)[ \t]+(?P<num>premier|1er|\d+(?:[ \t]*[-–][ \t]*\d+)?"
    r"(?:[ \t]+(?:bis|ter|quater))?)\b"
    r"|^[ \t]*المادة[ \t]+(?P<num_ar>\d+|الأولى)",
    re.IGNORECASE | re.MULTILINE,
)


def normalize_label(raw: str) -> str:
    s = re.sub(r"\s+", " ", raw.strip().lower()).replace("–", "-")
    s = re.sub(r"\s*-\s*", "-", s)
    return "1" if s in ("premier", "1er", "الأولى") else s


def split_articles(text: str) -> list[tuple[str | None, int, int]]:
    """Retourne des (label, début, fin). Les références du type « l'article 5 » en milieu
    de ligne ne déclenchent pas de coupure : seul un début de ligne compte."""
    matches = list(ARTICLE_RE.finditer(text))
    if not matches:
        return [(None, 0, len(text))]
    spans: list[tuple[str | None, int, int]] = []
    if text[: matches[0].start()].strip():
        spans.append((None, 0, matches[0].start()))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        spans.append((normalize_label(m.group("num") or m.group("num_ar")), m.start(), end))
    return spans


def split_long(text: str, max_chars: int, overlap: int) -> list[str]:
    """Découpe un texte long en morceaux <= max_chars (+ chevauchement) aux limites de phrases."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]
    sentences: list[str] = []
    for s in re.split(r"(?<=[.!?;:])\s+|\n{2,}", text):
        while len(s) > max_chars:  # phrase démesurée : coupe dure
            sentences.append(s[:max_chars])
            s = s[max_chars:]
        if s.strip():
            sentences.append(s)
    pieces: list[str] = []
    cur = ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > max_chars:
            pieces.append(cur.strip())
            tail = cur[-overlap:] if overlap else ""
            tail = tail[tail.find(" ") + 1 :] if " " in tail else ""
            cur = f"{tail} {s}".strip()
        else:
            cur = f"{cur} {s}".strip() if cur else s
    if cur.strip():
        pieces.append(cur.strip())
    return pieces


def chunk_document(pages: list[str], meta: dict, max_chars: int = 1800, overlap: int = 200) -> list[Chunk]:
    """Transforme les pages d'un document en passages avec article et page d'origine."""
    text, starts = "", []
    for p in pages:
        starts.append(len(text))
        text += p + "\n"

    chunks: list[Chunk] = []
    for span_idx, (label, start, end) in enumerate(split_articles(text)):
        body = text[start:end].strip()
        if not body:
            continue
        page = bisect_right(starts, start)  # pages numérotées à partir de 1
        for piece_idx, piece in enumerate(split_long(body, max_chars, overlap)):
            chunks.append(
                Chunk(
                    chunk_id=f"{meta['doc_id']}::{span_idx:03d}-{piece_idx}",
                    doc_id=meta["doc_id"],
                    titre=meta.get("titre", ""),
                    text=piece,
                    article=label,
                    page=page,
                    domaine=meta.get("domaine", ""),
                    type=meta.get("type", ""),
                    statut=meta.get("statut", ""),
                    langue=meta.get("langue", ""),
                )
            )
    return chunks


def chunk_plain_text(text: str, max_chars: int = 900) -> list[str]:
    """Découpage par paragraphes pour un document soumis (sans structure d'articles)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out: list[str] = []
    for p in paras:
        out.extend(split_long(p, max_chars, 0))
    return out
