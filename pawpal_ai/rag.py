from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9']+")


@dataclass
class KnowledgeChunk:
    chunk_id: str
    title: str
    content: str


@dataclass
class RetrievalHit:
    chunk: KnowledgeChunk
    score: int


class KnowledgeBaseRetriever:
    def __init__(self, knowledge_path: str) -> None:
        path = Path(knowledge_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.chunks: List[KnowledgeChunk] = [
            KnowledgeChunk(
                chunk_id=str(item["chunk_id"]),
                title=str(item["title"]),
                content=str(item["content"]),
            )
            for item in payload["chunks"]
        ]

    def _tokenize(self, text: str) -> List[str]:
        return [match.group(0).lower() for match in _TOKEN_PATTERN.finditer(text)]

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievalHit]:
        query_terms = set(self._tokenize(query))
        hits: List[RetrievalHit] = []
        for chunk in self.chunks:
            chunk_terms = set(self._tokenize(chunk.title + " " + chunk.content))
            overlap = query_terms.intersection(chunk_terms)
            score = len(overlap)
            if score > 0:
                hits.append(RetrievalHit(chunk=chunk, score=score))

        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]

    def format_context(self, hits: List[RetrievalHit]) -> str:
        if not hits:
            return "No external knowledge found."
        lines: List[str] = []
        for index, hit in enumerate(hits, start=1):
            lines.append(
                f"[{index}] {hit.chunk.title}: {hit.chunk.content}"
            )
        return "\n".join(lines)
