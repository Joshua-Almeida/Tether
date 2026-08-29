from __future__ import annotations

import math
import re

from langchain_core.documents import Document

TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return TOKEN.findall((text or "").lower())


def rrf_fuse(*rankings: list[str], k: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            if not doc_id:
                continue
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda item: scores[item], reverse=True)


class BM25Index:
    def __init__(self, documents: list[Document], k1: float = 1.5, b: float = 0.75) -> None:
        self.documents = documents
        self.k1 = k1
        self.b = b
        self.tokenized = [tokenize(doc.page_content) for doc in documents]
        self.doc_len = [len(tokens) or 1 for tokens in self.tokenized]
        self.avgdl = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 1.0
        df: dict[str, int] = {}
        for tokens in self.tokenized:
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        n = len(documents) or 1
        self.idf = {term: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}

    def rank(self, query: str, k: int) -> list[Document]:
        if not self.documents:
            return []
        terms = tokenize(query)
        scored: list[tuple[float, int]] = []
        for index, tokens in enumerate(self.tokenized):
            tf: dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            score = 0.0
            length = self.doc_len[index]
            for term in terms:
                freq = tf.get(term)
                if not freq:
                    continue
                idf = self.idf.get(term, 0.0)
                denom = freq + self.k1 * (1.0 - self.b + self.b * length / self.avgdl)
                score += idf * (freq * (self.k1 + 1.0)) / denom
            scored.append((score, index))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [self.documents[index] for _score, index in scored[:k]]
