"""Vérification de conformité : exigences du référentiel -> verdict sur un document soumis."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .chunking import chunk_plain_text
from .models import Chunk
from .retrieve import BM25Index

VERDICTS = ("conforme", "non_conforme", "non_determine")

EXTRACT_SYSTEM = """Tu aides à préparer un contrôle de conformité. À partir des extraits numérotés d'un texte \
réglementaire, extrais les exigences VÉRIFIABLES sur un document (obligations, interdictions, délais, mentions \
obligatoires, procédures). Formule chacune en une phrase simple et testable. N'invente rien et reste fidèle au texte.
Réponds uniquement avec du JSON : [{"exigence": "...", "source": "S1"}]. Si rien n'est vérifiable, réponds []."""

CHECK_SYSTEM = """Tu es un contrôleur de conformité. On te donne une exigence réglementaire et des extraits \
numérotés (D1, D2…) d'un document soumis. Détermine si le document respecte l'exigence, en te fondant UNIQUEMENT \
sur ces extraits.
- "conforme" : un extrait démontre explicitement le respect de l'exigence ;
- "non_conforme" : un extrait contredit l'exigence ou omet un élément qu'elle impose ;
- "non_determine" : les extraits ne permettent pas de conclure.
Réponds uniquement avec du JSON : {"verdict": "...", "justification": "une ou deux phrases", "preuves": ["D1"]}"""


@dataclass
class Requirement:
    id: str
    texte: str
    source_label: str
    source_chunk_id: str


@dataclass
class Finding:
    requirement: Requirement
    verdict: str
    justification: str
    preuves: list[str] = field(default_factory=list)  # extraits du document soumis


def extract_json(text: str):
    """Extrait le premier objet/tableau JSON d'une réponse de LLM (avec ou sans bloc ```)."""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    candidate = m.group(1) if m else text
    positions = sorted((candidate.find(o), o, c) for o, c in (("[", "]"), ("{", "}")) if candidate.find(o) != -1)
    for start, _, closer in positions:
        end = candidate.rfind(closer)
        if end > start:
            try:
                return json.loads(candidate[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("JSON introuvable ou invalide dans la réponse du modèle")


def extract_requirements(chunks: list[Chunk], llm, max_requirements: int = 30, batch_chars: int = 6000) -> list[Requirement]:
    batches: list[list[Chunk]] = []
    cur: list[Chunk] = []
    size = 0
    for c in chunks:
        if cur and size + len(c.text) > batch_chars:
            batches.append(cur)
            cur, size = [], 0
        cur.append(c)
        size += len(c.text)
    if cur:
        batches.append(cur)

    reqs: list[Requirement] = []
    seen: set[str] = set()
    for batch in batches:
        user = "\n\n".join(f"[S{i}] ({c.label()})\n{c.text}" for i, c in enumerate(batch, start=1))
        try:
            data = extract_json(llm.complete(EXTRACT_SYSTEM, user, max_tokens=2000))
        except ValueError:
            continue
        for item in data if isinstance(data, list) else []:
            texte = str(item.get("exigence", "")).strip()
            m = re.fullmatch(r"S(\d+)", str(item.get("source", "")).strip())
            if not texte or not m or not 1 <= int(m.group(1)) <= len(batch) or texte.lower() in seen:
                continue
            src = batch[int(m.group(1)) - 1]
            seen.add(texte.lower())
            reqs.append(Requirement(f"E{len(reqs) + 1}", texte, src.label(), src.chunk_id))
            if len(reqs) >= max_requirements:
                return reqs
    return reqs


def check_document(doc_text: str, requirements: list[Requirement], llm, top_excerpts: int = 4) -> list[Finding]:
    excerpts = chunk_plain_text(doc_text)
    ids = [f"D{i}" for i in range(1, len(excerpts) + 1)]
    ex_map = dict(zip(ids, excerpts))
    index = BM25Index(ids, excerpts)

    findings: list[Finding] = []
    for req in requirements:
        found = [i for i, _ in index.search(req.texte, top_excerpts)]
        if not found:
            findings.append(Finding(req, "non_determine", "Aucun passage du document ne semble traiter cette exigence."))
            continue
        user = f"Exigence : {req.texte}\n\nExtraits du document :\n\n" + "\n\n".join(f"[{i}] {ex_map[i]}" for i in found)
        try:
            data = extract_json(llm.complete(CHECK_SYSTEM, user, max_tokens=600))
            verdict = data.get("verdict") if data.get("verdict") in VERDICTS else "non_determine"
            justification = str(data.get("justification", "")).strip()
            preuves = [p for p in data.get("preuves", []) if p in ex_map]
        except (ValueError, AttributeError):
            findings.append(Finding(req, "non_determine", "Réponse du modèle illisible."))
            continue
        if verdict == "conforme" and not preuves:  # pas de conformité sans preuve
            verdict, justification = "non_determine", f"{justification} (aucune preuve citée)".strip()
        findings.append(Finding(req, verdict, justification, [ex_map[p] for p in preuves]))
    return findings


def findings_to_markdown(findings: list[Finding], reference: str = "") -> str:
    counts = {v: sum(f.verdict == v for f in findings) for v in VERDICTS}
    lines = ["# Rapport de conformité", ""]
    if reference:
        lines += [f"Référentiel : {reference}", ""]
    lines += [
        f"Exigences analysées : {len(findings)} — conformes : {counts['conforme']}, "
        f"non conformes : {counts['non_conforme']}, non déterminées : {counts['non_determine']}",
        "",
        "> Aide à la décision : ce rapport ne remplace pas un avis juridique.",
        "",
    ]
    icon = {"conforme": "✅", "non_conforme": "❌", "non_determine": "❔"}
    for f in findings:
        lines += [
            f"## {f.requirement.id} {icon[f.verdict]} {f.verdict.replace('_', ' ')}",
            f"**Exigence :** {f.requirement.texte}",
            f"**Source :** {f.requirement.source_label}",
            f"**Justification :** {f.justification}",
        ]
        lines += [f"> {p}" for p in f.preuves]
        lines.append("")
    return "\n".join(lines)
