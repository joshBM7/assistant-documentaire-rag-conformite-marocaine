"""Garde-fous : citations obligatoires, articles inventés, refus argumenté."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .chunking import normalize_label
from .retrieve import Hit

REFUSAL_TOKEN = "INSUFFISANT"
REFUSAL_MESSAGE = (
    "Je ne peux pas répondre de façon fiable : les documents du corpus ne contiennent pas "
    "d'éléments suffisants pour justifier une réponse."
)
CITE_RE = re.compile(r"\[S(\d+)\]")
ARTICLE_MENTION_RE = re.compile(r"\bart(?:icles?|\.)\s*(\d+(?:\s*(?:bis|ter|quater))?)", re.IGNORECASE)


@dataclass
class GuardResult:
    refused: bool
    reason: str = ""
    cited: list[int] = field(default_factory=list)  # numéros S# valides cités


def _mentioned_articles(text: str) -> set[str]:
    return {normalize_label(m) for m in ARTICLE_MENTION_RE.findall(text)}


def check_answer(raw: str, hits: list[Hit]) -> GuardResult:
    """Valide la réponse du LLM. Toute réponse non vérifiable est transformée en refus."""
    text = raw.strip()
    if not text or text.upper().startswith(REFUSAL_TOKEN):
        return GuardResult(True, "le modèle juge les extraits insuffisants")

    cited = sorted({int(n) for n in CITE_RE.findall(text)})
    if not cited:
        return GuardResult(True, "aucune citation dans la réponse")
    if any(n < 1 or n > len(hits) for n in cited):
        return GuardResult(True, "citation vers un extrait inexistant")

    # Un numéro d'article cité dans la réponse doit apparaître dans le contexte fourni.
    allowed = {normalize_label(h.chunk.article) for h in hits if h.chunk.article}
    for h in hits:
        allowed |= _mentioned_articles(h.chunk.text)
    unknown = _mentioned_articles(text) - allowed
    if unknown:
        return GuardResult(True, f"article(s) absent(s) du contexte : {', '.join(sorted(unknown))}")
    return GuardResult(False, "", cited)
