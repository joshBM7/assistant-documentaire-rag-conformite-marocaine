"""Embeddings, index vectoriel (ChromaDB) et stockage des passages."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

from .models import Chunk

log = logging.getLogger(__name__)
COLLECTION = "reglementation"
CHUNKS_FILE = "chunks.jsonl"


class EmbedderLike(Protocol):
    def encode_passages(self, texts: list[str]) -> list[list[float]]: ...
    def encode_queries(self, texts: list[str]) -> list[list[float]]: ...


class Embedder:
    """Modèle multilingue sentence-transformers (e5 / bge-m3). Chargement paresseux."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None
        self._e5 = "e5" in model_name.lower()  # les modèles e5 exigent des préfixes

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _encode(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False).tolist()

    def encode_passages(self, texts: list[str]) -> list[list[float]]:
        return self._encode([f"passage: {t}" for t in texts] if self._e5 else texts)

    def encode_queries(self, texts: list[str]) -> list[list[float]]:
        return self._encode([f"query: {t}" for t in texts] if self._e5 else texts)


def save_chunks(chunks: list[Chunk], index_dir: Path) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    with open(index_dir / CHUNKS_FILE, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")


def load_chunks(index_dir: Path) -> list[Chunk]:
    path = Path(index_dir) / CHUNKS_FILE
    if not path.exists():
        raise FileNotFoundError(f"{path} introuvable : lancez d'abord « python -m ragconf.cli ingest ».")
    with open(path, encoding="utf-8") as f:
        return [Chunk.from_dict(json.loads(line)) for line in f if line.strip()]


def _client(index_dir: Path):
    import chromadb

    return chromadb.PersistentClient(path=str(Path(index_dir) / "chroma"))


def build_index(chunks: list[Chunk], embedder: EmbedderLike, index_dir: Path, batch: int = 64) -> None:
    """(Re)construit l'index vectoriel et le fichier de passages."""
    save_chunks(chunks, index_dir)
    client = _client(index_dir)
    try:
        client.delete_collection(COLLECTION)
    except Exception:  # collection inexistante
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    for i in range(0, len(chunks), batch):
        part = chunks[i : i + batch]
        col.add(
            ids=[c.chunk_id for c in part],
            documents=[c.text for c in part],
            embeddings=embedder.encode_passages([c.contextual_text() for c in part]),
            metadatas=[
                {
                    "doc_id": c.doc_id,
                    "article": c.article or "",
                    "page": c.page or 0,
                    "domaine": c.domaine,
                    "type": c.type,
                    "statut": c.statut,
                    "langue": c.langue,
                }
                for c in part
            ],
        )
    log.info("Index construit : %d passages", len(chunks))


class ChromaDense:
    """Recherche sémantique (similarité cosinus) dans ChromaDB."""

    def __init__(self, index_dir: Path, embedder: EmbedderLike):
        self.embedder = embedder
        self.collection = _client(index_dir).get_collection(COLLECTION)

    def search(self, query: str, n: int, where: dict | None = None) -> list[tuple[str, float]]:
        total = self.collection.count()
        if total == 0:
            return []
        qv = self.embedder.encode_queries([query])[0]
        res = self.collection.query(query_embeddings=[qv], n_results=min(n, total), where=where)
        return [(i, 1.0 - d) for i, d in zip(res["ids"][0], res["distances"][0])]
