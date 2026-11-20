"""Client LLM (API Anthropic). Remplaçable : il suffit de fournir une méthode complete()."""
from __future__ import annotations

import os

from .config import settings


class LLM:
    def __init__(self, model: str | None = None, api_key: str | None = None):
        self.model = model or settings.llm_model
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
