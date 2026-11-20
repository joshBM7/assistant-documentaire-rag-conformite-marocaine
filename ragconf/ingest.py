"""Pipeline d'ingestion : inventaire.csv -> extraction -> nettoyage -> découpage."""
from __future__ import annotations

import csv
import logging
from pathlib import Path

from .chunking import chunk_document
from .config import Settings, settings as default_settings
from .extract import clean_pages, extract_pages
from .models import Chunk

log = logging.getLogger(__name__)
REQUIRED_COLUMNS = {"doc_id", "titre", "type", "statut", "langue", "domaine"}


def load_inventaire(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Colonnes manquantes dans {path} : {sorted(missing)}")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader if (row.get("doc_id") or "").strip()]


def find_source_file(raw_dir: Path, doc_id: str) -> Path | None:
    for ext in (".pdf", ".txt"):
        p = raw_dir / f"{doc_id}{ext}"
        if p.exists():
            return p
    return None


def build_chunks(cfg: Settings = default_settings) -> list[Chunk]:
    chunks: list[Chunk] = []
    for row in load_inventaire(cfg.inventaire):
        src = find_source_file(cfg.raw_dir, row["doc_id"])
        if src is None:
            log.warning("Fichier introuvable pour %s (attendu : %s.pdf)", row["doc_id"], row["doc_id"])
            continue
        meta = {**row, "statut": row["statut"].lower()}  # statut normalisé (filtre « abrogé »)
        pages = clean_pages(extract_pages(src, row.get("langue", "fr")))
        doc_chunks = chunk_document(pages, meta, cfg.chunk_max_chars, cfg.chunk_overlap)
        log.info("%s : %d pages -> %d passages", row["doc_id"], len(pages), len(doc_chunks))
        chunks.extend(doc_chunks)
    return chunks
