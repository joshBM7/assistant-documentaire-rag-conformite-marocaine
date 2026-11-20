"""Chaîne de requête : récupération -> génération avec citations -> garde-fous."""
from __future__ import annotations

from dataclasses import dataclass, field

from .config import Settings, settings as default_settings
from .guardrails import REFUSAL_MESSAGE, REFUSAL_TOKEN, check_answer
from .retrieve import Hit, HybridRetriever

SYSTEM_PROMPT = f"""Tu es un assistant d'aide à la conformité réglementaire. Tu réponds UNIQUEMENT à partir \
des extraits numérotés [S1], [S2]… fournis par l'utilisateur.

Règles :
- Chaque affirmation doit être suivie du ou des extraits qui la justifient, au format [S1] ou [S1][S3].
- N'utilise aucune connaissance extérieure et n'invente jamais un article, une loi ou une date.
- Ne cite un numéro d'article que s'il figure dans les extraits.
- Si les extraits ne permettent pas de répondre avec certitude, réponds exactement : {REFUSAL_TOKEN}
- Réponds dans la langue de la question, de façon concise et précise.
- Tu fournis une aide à la décision, pas un avis juridique."""


def build_user_prompt(question: str, hits: list[Hit]) -> str:
    blocks = [f"[S{i}] ({h.chunk.label()})\n{h.chunk.text}" for i, h in enumerate(hits, start=1)]
    return "Extraits :\n\n" + "\n\n".join(blocks) + f"\n\nQuestion : {question}"


@dataclass
class Answer:
    question: str
    answer: str
    refused: bool
    reason: str = ""
    sources: list[Hit] = field(default_factory=list)
    cited: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "refused": self.refused,
            "reason": self.reason,
            "cited": self.cited,
            "sources": [
                {
                    "ref": f"S{i}",
                    "label": h.chunk.label(),
                    "doc_id": h.chunk.doc_id,
                    "article": h.chunk.article,
                    "page": h.chunk.page,
                    "text": h.chunk.text,
                    "score": round(h.score, 5),
                }
                for i, h in enumerate(self.sources, start=1)
            ],
        }


class RAGPipeline:
    def __init__(self, retriever: HybridRetriever, llm, top_k: int = 5, candidates: int = 20):
        self.retriever, self.llm, self.top_k, self.candidates = retriever, llm, top_k, candidates

    def ask(self, question: str, filters: dict | None = None, top_k: int | None = None) -> Answer:
        hits = self.retriever.search(question, top_k or self.top_k, self.candidates, filters)
        if not hits:
            return Answer(question, REFUSAL_MESSAGE, True, "aucun passage trouvé")
        raw = self.llm.complete(SYSTEM_PROMPT, build_user_prompt(question, hits))
        guard = check_answer(raw, hits)
        if guard.refused:
            return Answer(question, REFUSAL_MESSAGE, True, guard.reason, hits)
        return Answer(question, raw, False, "", hits, guard.cited)


def load_pipeline(cfg: Settings = default_settings) -> RAGPipeline:
    """Assemble la chaîne complète à partir de l'index construit par « ingest »."""
    from .index import ChromaDense, Embedder, load_chunks
    from .llm import LLM
    from .retrieve import CrossEncoderReranker

    chunks = load_chunks(cfg.index_dir)
    dense = ChromaDense(cfg.index_dir, Embedder(cfg.embedding_model))
    reranker = CrossEncoderReranker(cfg.reranker_model) if cfg.reranker_model else None
    retriever = HybridRetriever(chunks, dense, reranker)
    return RAGPipeline(retriever, LLM(cfg.llm_model), cfg.top_k, cfg.candidates)
