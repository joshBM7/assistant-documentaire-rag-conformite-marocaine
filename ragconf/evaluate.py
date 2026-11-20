"""Évaluation : récupération, exactitude des citations, refus appropriés.

Le fichier de résultats contient aussi les colonnes question / answer / contexts / ground_truth,
directement exploitables avec RAGAS pour les métriques de fidélité et de pertinence.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .chunking import normalize_label
from .models import Chunk


def load_questions(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip() and not line.lstrip().startswith("//")]


def matches(chunk: Chunk, expected: dict) -> bool:
    if chunk.doc_id != expected["doc_id"]:
        return False
    art = expected.get("article")
    return art is None or chunk.article == normalize_label(str(art))


def evaluate(pipeline, questions: list[dict], out_path: Path | None = None) -> dict:
    rows = []
    for q in questions:
        ans = pipeline.ask(q["question"])
        expected = q.get("sources", [])
        cited_chunks = [ans.sources[i - 1].chunk for i in ans.cited if 0 < i <= len(ans.sources)]
        if expected:
            retrieval_hit = any(matches(h.chunk, e) for h in ans.sources for e in expected)
            citation_ok = (not ans.refused) and any(matches(c, e) for c in cited_chunks for e in expected)
        else:
            retrieval_hit = citation_ok = None
        row = {
            "id": q.get("id"),
            "categorie": q.get("categorie", "factuelle"),
            "refused": ans.refused,
            "retrieval_hit": retrieval_hit,
            "citation_ok": citation_ok,
            # colonnes compatibles RAGAS
            "question": q["question"],
            "answer": ans.answer,
            "contexts": [h.chunk.text for h in ans.sources],
            "ground_truth": q.get("reference_answer", ""),
        }
        rows.append(row)

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return summarize(rows)


def _rate(values: list[bool]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def summarize(rows: list[dict]) -> dict:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cat[r["categorie"]].append(r)
    report: dict = {"n": len(rows), "categories": {}}
    for cat, rs in by_cat.items():
        if cat == "sans_reponse":
            report["categories"][cat] = {"n": len(rs), "refus_correct": _rate([r["refused"] for r in rs])}
        else:
            report["categories"][cat] = {
                "n": len(rs),
                "retrieval_hit": _rate([bool(r["retrieval_hit"]) for r in rs]),
                "citation_ok": _rate([bool(r["citation_ok"]) for r in rs]),
                "faux_refus": _rate([r["refused"] for r in rs]),
            }
    answerable = [r for r in rows if r["categorie"] != "sans_reponse"]
    unanswerable = [r for r in rows if r["categorie"] == "sans_reponse"]
    report["global"] = {
        "retrieval_hit": _rate([bool(r["retrieval_hit"]) for r in answerable]),
        "citation_ok": _rate([bool(r["citation_ok"]) for r in answerable]),
        "refus_correct": _rate([r["refused"] for r in unanswerable]),
    }
    return report
