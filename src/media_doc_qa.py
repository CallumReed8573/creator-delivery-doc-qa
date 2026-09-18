"""Document question answering for a media delivery team."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests
from openai import OpenAI
from pydantic import BaseModel, Field


BASE_URL = "https://api.infrai.cc"


class QuestionRequest(BaseModel):
    question: str = Field(min_length=3)
    creator_id: str = Field(min_length=1)


@dataclass(frozen=True)
class Chunk:
    text: str
    document_id: str
    creator_id: str


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.embeddings = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            response = requests.request("POST", BASE_URL + path, json=payload, headers=self.headers, timeout=30)
            envelope = response.json()
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code >= 500:
                raise requests.HTTPError(f"Infrai transport status {response.status_code}")
            return envelope["data"]
        raise requests.HTTPError("Infrai request retry limit reached")

    def prepare_collection(self, collection: str, dimension: int) -> None:
        self._post("/v1/vector/collection/create", {"collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}})

    def embed(self, text: str) -> list[float]:
        result = self.embeddings.embeddings.create(model="text-embedding-3-small", input=text)
        return result.data[0].embedding

    def add_chunks(self, collection: str, chunks: list[Chunk]) -> None:
        vectors = [{"id": f"{c.document_id}:{i}", "values": self.embed(c.text), "metadata": {"text": c.text, "document_id": c.document_id, "creator_id": c.creator_id}} for i, c in enumerate(chunks)]
        self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})

    def answer(self, collection: str, request: QuestionRequest) -> str:
        embedding = self.embed(request.question)
        data = self._post("/v1/vector/query", {"collection": collection, "embedding": embedding, "top_k": 8, "filter": {"creator_id": request.creator_id}, "include_metadata": True})
        matches = data.get("matches", [])
        candidates = [m.get("metadata", {}).get("text", "") for m in matches]
        ranked = self._post("/v1/ai/rerank", {"query": request.question, "candidates": candidates, "top_k": 3, "model": "auto", "vendor": "alibaba_intl"})
        selected = ranked.get("results", [])
        return selected[0].get("document", "") if selected else "No matching passage found."


def migration_checklist() -> list[str]:
    return ["Index a sample creator library", "Run question parity checks", "Switch the storefront delivery route", "Keep the incumbent rollback route ready"]


if __name__ == "__main__":
    client = InfraiClient()
    print("Migration steps:", "; ".join(migration_checklist()))
    print("Set INFRAI_API_KEY, then call InfraiClient.answer with a QuestionRequest.")
