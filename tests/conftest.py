import hashlib
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ragconf.models import Chunk  # noqa: E402
from ragconf.retrieve import tokenize  # noqa: E402


class FakeEmbedder:
    """Embedding déterministe par sac de mots hachés (tests sans téléchargement de modèle)."""

    DIM = 128

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * self.DIM
        for tok in tokenize(text):
            v[int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.DIM] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def encode_passages(self, texts):
        return [self._vec(t) for t in texts]

    def encode_queries(self, texts):
        return [self._vec(t) for t in texts]


class FakeLLM:
    """LLM scripté : renvoie les réponses dans l'ordre, ou une fonction de la requête."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        r = self.responses
        if callable(r):
            return r(system, user)
        return r.pop(0) if isinstance(r, list) else r


def make_chunks():
    def c(i, doc, art, text, statut="en vigueur", domaine="donnees_personnelles", page=1):
        return Chunk(f"{doc}::{i}", doc, f"Loi {doc}", text, art, page, domaine, "loi", statut, "fr")

    return [
        c(1, "L1", "1", "Article 1 Le responsable du traitement doit informer la personne concernée de la finalité de la collecte."),
        c(2, "L1", "2", "Article 2 Le délai de conservation des données ne peut excéder la durée nécessaire à la finalité."),
        c(3, "L2", "5", "Article 5 Toute demande d'accès à l'information reçoit une réponse dans un délai de trente jours.", domaine="acces_information"),
        c(4, "L3", "7", "Article 7 Ce texte ancien prévoit un registre papier des déclarations.", statut="abrogé"),
    ]
