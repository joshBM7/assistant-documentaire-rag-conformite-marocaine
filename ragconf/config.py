"""Configuration centralisée (variables d'environnement, valeurs par défaut)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # .env facultatif
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    raw_dir: Path = ROOT / "data" / "raw"
    inventaire: Path = ROOT / "data" / "inventaire.csv"
    index_dir: Path = ROOT / "data" / "index"
    eval_file: Path = ROOT / "data" / "eval" / "questions.jsonl"

    # Modèles
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    reranker_model: str = os.getenv("RERANKER_MODEL", "")  # ex. BAAI/bge-reranker-v2-m3 ; vide = désactivé
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-5-5")

    # Récupération
    top_k: int = int(os.getenv("TOP_K", "5"))
    candidates: int = int(os.getenv("CANDIDATES", "20"))

    # Découpage
    chunk_max_chars: int = int(os.getenv("CHUNK_MAX_CHARS", "1800"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))


settings = Settings()
