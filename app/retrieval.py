from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


TOKEN_RE = re.compile(r"[a-z0-9]+")

ALIASES = {
    "dies": "drain",
    "dying": "drain",
    "flat": "drain",
    "laggy": "slow",
    "sluggish": "slow",
    "blurry": "blur",
    "flickers": "flicker",
    "hot": "overheat",
    "heating": "overheat",
    "disconnecting": "disconnect",
    "drops": "disconnect",
    "swipes": "swipe",
    "gestures": "gesture",
    "pictures": "photo",
    "photos": "photo",
    "alerts": "notification",
}

STOP = {
    "a", "an", "and", "are", "after", "before", "for", "from", "i", "is",
    "it", "me", "my", "of", "on", "phone", "the", "to", "with", "won", "t",
}


def tokenize(text: str) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall(text.lower()):
        token = ALIASES.get(token, token)
        if token not in STOP and len(token) > 1:
            tokens.append(token)
    return tokens


def canonical_query(text: str) -> str:
    tokens = tokenize(text)
    return " ".join(sorted(dict.fromkeys(tokens))) or text.strip().lower()


def jaccard(left: str, right: str) -> float:
    a, b = set(tokenize(left)), set(tokenize(right))
    return len(a & b) / len(a | b) if a and b else 0.0


@dataclass(frozen=True)
class RankedRecord:
    record: dict
    score: float
    lexical_score: float
    semantic_score: float


class HybridRetriever:
    """Small, dependency-light BM25 plus concept-overlap retriever.

    The interface is intentionally replaceable by a dense embedding index when the
    official 10k+ corpus is available. RRF-inspired score fusion keeps the current
    baseline deterministic and inspectable.
    """

    def __init__(self, records: list[dict]):
        self.records = records
        self.docs = [tokenize(self._document(record)) for record in records]
        self.avgdl = sum(map(len, self.docs)) / max(1, len(self.docs))
        self.df = Counter()
        for doc in self.docs:
            self.df.update(set(doc))

    @staticmethod
    def _document(record: dict) -> str:
        return " ".join(
            [record.get("title", ""), record.get("domain", ""), *record.get("symptoms", []),
             *record.get("paraphrases", []), record.get("reference_text", "")]
        )

    def _bm25(self, query: list[str], doc: list[str]) -> float:
        if not query or not doc:
            return 0.0
        tf = Counter(doc)
        k1, b = 1.5, 0.75
        score = 0.0
        for term in query:
            n = self.df.get(term, 0)
            idf = math.log(1 + (len(self.docs) - n + 0.5) / (n + 0.5))
            freq = tf.get(term, 0)
            denom = freq + k1 * (1 - b + b * len(doc) / max(self.avgdl, 1))
            score += idf * (freq * (k1 + 1) / denom if denom else 0)
        return score

    def search(self, query: str, top_k: int = 3) -> list[RankedRecord]:
        q_tokens = tokenize(query)
        raw_lex = [self._bm25(q_tokens, doc) for doc in self.docs]
        ranked = []
        for record, doc, lex in zip(self.records, self.docs, raw_lex):
            semantic = len(set(q_tokens) & set(doc)) / max(1, len(set(q_tokens)))
            # Saturating absolute BM25 confidence avoids turning an unrelated
            # top result into a high-confidence match merely because it ranked first.
            lexical = lex / (lex + 3.0) if lex > 0 else 0.0
            score = 0.54 * lexical + 0.46 * semantic
            ranked.append(RankedRecord(record, min(score, 1.0), lexical, semantic))
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]


def best_semantic_match(query: str, candidates: Iterable[str]) -> tuple[str | None, float]:
    best, score = None, 0.0
    for candidate in candidates:
        value = jaccard(query, candidate)
        if value > score:
            best, score = candidate, value
    return best, score
