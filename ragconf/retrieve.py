"""Recherche hybride (dense + BM25) fusionnée par RRF, avec reranking optionnel."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .models import Chunk

FILTER_KEYS = ("doc_id", "domaine", "type", "statut", "langue")


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class BM25Index:
    def __init__(self, ids: list[str], texts: list[str]):
        from rank_bm25 import BM25Plus  # idf toujours positif, fiable sur de petits corpus

        self.ids = ids
        docs = [tokenize(t) or ["_"] for t in texts]
        self.vocab = [set(d) for d in docs]  # BM25Plus note aussi les documents sans aucun mot de la requête
        self.bm25 = BM25Plus(docs) if ids else None

    def search(self, query: str, n: int, allowed: set[str] | None = None) -> list[tuple[str, float]]:
        if self.bm25 is None:
            return []
        q = tokenize(query)
        qset = set(q)
        scores = self.bm25.get_scores(q)
        ranked = sorted(zip(self.ids, scores, self.vocab), key=lambda x: x[1], reverse=True)
        return [
            (i, float(s)) for i, s, v in ranked if s > 0 and (v & qset) and (allowed is None or i in allowed)
        ][:n]


def rrf(rank_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    """Reciprocal Rank Fusion : score(d) = somme 1 / (k + rang)."""
    fused: dict[str, float] = {}
    for ranking in rank_lists:
        for rank, doc_id in enumerate(ranking, start=1):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank)
    return fused


class DenseLike(Protocol):
    def search(self, query: str, n: int, where: dict | None = None) -> list[tuple[str, float]]: ...


@dataclass
class Hit:
    chunk: Chunk
    score: float
    dense: float | None = None
    bm25: float | None = None


class CrossEncoderReranker:
    """Reclasse les candidats avec un cross-encoder (ex. BAAI/bge-reranker-v2-m3)."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]:
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        scores = self._model.predict([(query, h.chunk.contextual_text()) for h in hits])
        for h, s in zip(hits, scores):
            h.score = float(s)
        return sorted(hits, key=lambda h: h.score, reverse=True)[:top_k]


class HybridRetriever:
    def __init__(self, chunks: list[Chunk], dense: DenseLike, reranker=None, rrf_k: int = 60):
        self.chunks = {c.chunk_id: c for c in chunks}
        self.dense = dense
        self.reranker = reranker
        self.rrf_k = rrf_k
        self.bm25 = BM25Index([c.chunk_id for c in chunks], [c.contextual_text() for c in chunks])

    def _filters(self, filters: dict | None) -> tuple[set[str], dict | None]:
        f = {k: v for k, v in (filters or {}).items() if v and k in FILTER_KEYS}
        exclude_abrogated = "statut" not in f  # par défaut, on ignore les textes abrogés
        allowed = {
            c.chunk_id
            for c in self.chunks.values()
            if all(getattr(c, k) == v for k, v in f.items())
            and not (exclude_abrogated and c.statut.strip().lower() == "abrogé")
        }
        clauses = [{k: v} for k, v in f.items()]
        if exclude_abrogated:
            clauses.append({"statut": {"$ne": "abrogé"}})
        where = None if not clauses else clauses[0] if len(clauses) == 1 else {"$and": clauses}
        return allowed, where

    def search(self, query: str, top_k: int = 5, candidates: int = 20, filters: dict | None = None) -> list[Hit]:
        allowed, where = self._filters(filters)
        if not allowed:
            return []
        dense = [(i, s) for i, s in self.dense.search(query, candidates, where) if i in allowed]
        lexical = self.bm25.search(query, candidates, allowed)
        fused = rrf([[i for i, _ in dense], [i for i, _ in lexical]], self.rrf_k)
        dmap, bmap = dict(dense), dict(lexical)
        ordered = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)[:candidates]
        hits = [Hit(self.chunks[i], score, dmap.get(i), bmap.get(i)) for i, score in ordered]
        if self.reranker and hits:
            hits = self.reranker.rerank(query, hits, top_k)
        return hits[:top_k]
