"""API FastAPI : /ask, /compliance, /health.   Lancement : uvicorn ragconf.api:app"""
from __future__ import annotations

import os
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(title="Assistant RAG – conformité des documents publics", version="0.1.0")
MAX_UPLOAD_MB = 15


@lru_cache(maxsize=1)
def get_pipeline():
    from .pipeline import load_pipeline

    return load_pipeline()


class AskRequest(BaseModel):
    question: str
    domaine: str | None = None
    doc_id: str | None = None
    top_k: int | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents")
def documents():
    """Liste des documents indexés (pour alimenter les filtres de l'interface)."""
    chunks = get_pipeline().retriever.chunks.values()
    docs = {c.doc_id: {"doc_id": c.doc_id, "titre": c.titre, "domaine": c.domaine, "statut": c.statut} for c in chunks}
    return sorted(docs.values(), key=lambda d: d["doc_id"])


@app.post("/ask")
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(400, "Question vide")
    ans = get_pipeline().ask(req.question, {"domaine": req.domaine, "doc_id": req.doc_id}, req.top_k)
    return ans.to_dict()


@app.post("/compliance")
async def compliance(file: UploadFile = File(...), ref: str = Form(...), max_requirements: int = Form(15)):
    from .compliance import check_document, extract_requirements, findings_to_markdown
    from .extract import clean_pages, extract_pages

    pipe = get_pipeline()
    ref_chunks = [c for c in pipe.retriever.chunks.values() if c.doc_id == ref]
    if not ref_chunks:
        raise HTTPException(404, f"Texte de référence inconnu : {ref}")

    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Fichier trop volumineux (max {MAX_UPLOAD_MB} Mo)")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".pdf", ".txt"):
        raise HTTPException(415, "Formats acceptés : PDF, TXT")

    # Le document soumis n'est écrit que le temps du traitement, puis supprimé.
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(data)
        tmp.close()
        text = "\n\n".join(clean_pages(extract_pages(Path(tmp.name))))
    finally:
        os.unlink(tmp.name)

    reqs = extract_requirements(ref_chunks, pipe.llm, max_requirements)
    findings = check_document(text, reqs, pipe.llm)
    return {
        "reference": ref_chunks[0].titre,
        "findings": [
            {
                "id": f.requirement.id,
                "exigence": f.requirement.texte,
                "source": f.requirement.source_label,
                "verdict": f.verdict,
                "justification": f.justification,
                "preuves": f.preuves,
            }
            for f in findings
        ],
        "markdown": findings_to_markdown(findings, ref_chunks[0].titre),
    }
