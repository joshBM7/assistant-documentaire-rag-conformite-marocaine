"""Extraction du texte (PDF natif, OCR de secours) et nettoyage."""
from __future__ import annotations

import logging
import re
from collections import Counter
from pathlib import Path

from .chunking import ARTICLE_RE

log = logging.getLogger(__name__)
OCR_MIN_CHARS = 40  # en dessous, la page est considérée comme scannée
_OCR_LANGS = {"fr": "fra", "ar": "ara"}


def _ocr_page(page, langue: str) -> str:
    """OCR d'une page PyMuPDF. Renvoie '' si pytesseract/Pillow ne sont pas disponibles."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""
    try:
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return pytesseract.image_to_string(img, lang=_OCR_LANGS.get(langue, "fra+ara"))
    except Exception as exc:  # Tesseract absent ou langue non installée : on n'interrompt pas l'ingestion
        log.warning("OCR indisponible (%s) : page laissée telle quelle", exc)
        return ""


def extract_pages(path: Path, langue: str = "fr") -> list[str]:
    """Retourne le texte de chaque page. .txt = une seule page (utile pour les tests)."""
    path = Path(path)
    if path.suffix.lower() == ".txt":
        return [path.read_text(encoding="utf-8")]
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24.3
    except ImportError:  # pragma: no cover
        import fitz

    pages: list[str] = []
    with fitz.open(path) as pdf:
        for page in pdf:
            text = page.get_text("text") or ""
            if len(text.strip()) < OCR_MIN_CHARS:
                ocr = _ocr_page(page, langue)
                if len(ocr.strip()) > len(text.strip()):
                    text = ocr
            pages.append(text)
    return pages


def clean_pages(pages: list[str]) -> list[str]:
    """Supprime en-têtes/pieds de page répétés et numéros de page, corrige césures et espaces."""
    split = [[ln.rstrip() for ln in p.splitlines()] for p in pages]

    def zone(lines: list[str]) -> list[int]:
        idx = [i for i, ln in enumerate(lines) if ln.strip() and not ARTICLE_RE.match(ln)]
        n = 2 if len(idx) >= 8 else 1  # pages courtes : seulement première et dernière ligne
        return idx[:n] + idx[-n:]

    def key(line: str) -> str:
        return re.sub(r"\d+", "#", line.strip())

    counter: Counter[str] = Counter()
    for lines in split:
        for i in set(zone(lines)):
            if len(lines[i].strip()) <= 100:
                counter[key(lines[i])] += 1

    min_repeat = max(3, len(pages) // 2)
    cleaned: list[str] = []
    for lines in split:
        drop = set()
        for i in set(zone(lines)):
            s = lines[i].strip()
            if re.fullmatch(r"(?:page\s*)?\d{1,4}(?:\s*/\s*\d{1,4})?", s, re.I):
                drop.add(i)
            elif len(pages) >= 4 and len(s) <= 100 and counter[key(s)] >= min_repeat:
                drop.add(i)
        text = "\n".join(ln for i, ln in enumerate(lines) if i not in drop)
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # césures
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        cleaned.append(text.strip())
    return cleaned
