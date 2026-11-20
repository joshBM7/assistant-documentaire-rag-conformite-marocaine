"""Structures de données communes."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    titre: str
    text: str
    article: str | None = None
    page: int | None = None
    domaine: str = ""
    type: str = ""
    statut: str = ""
    langue: str = ""

    def label(self) -> str:
        """Référence lisible utilisée pour les citations."""
        parts = [self.titre or self.doc_id]
        if self.article:
            parts.append(f"art. {self.article}")
        if self.page:
            parts.append(f"p. {self.page}")
        return ", ".join(parts)

    def contextual_text(self) -> str:
        """Texte envoyé à l'embedding et au reranker : titre + article + contenu."""
        head = self.titre or self.doc_id
        if self.article:
            head += f" — Article {self.article}"
        return f"{head}\n{self.text}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Chunk":
        return cls(**d)
