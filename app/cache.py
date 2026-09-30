from __future__ import annotations

import copy
import threading
import time
from collections import defaultdict
from dataclasses import dataclass

from app.retrieval import canonical_query, jaccard, tokenize


@dataclass
class CacheValue:
    canonical: str
    payload: dict
    created_at: float
    last_accessed: float


class SemanticCache:
    """Validated in-memory cache with an inverted-token candidate index.

    Semantic lookup compares only entries sharing query terms instead of scanning
    the complete cache, keeping the fast path practical for large paraphrase sets.
    """

    def __init__(self, threshold: float = 0.72, max_entries: int = 100_000, ttl_seconds: int = 86_400):
        self.threshold = threshold
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, CacheValue] = {}
        self._token_index: dict[str, set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self.hits = 0
        self.misses = 0

    def _remove(self, key: str) -> None:
        entry = self._entries.pop(key, None)
        if not entry:
            return
        for token in set(tokenize(entry.canonical)):
            keys = self._token_index.get(token)
            if keys:
                keys.discard(key)
                if not keys:
                    self._token_index.pop(token, None)

    def _evict_if_needed(self) -> None:
        while len(self._entries) >= self.max_entries:
            oldest = min(self._entries.values(), key=lambda value: value.last_accessed)
            self._remove(oldest.canonical)

    def put(self, query: str, payload: dict) -> None:
        key = canonical_query(query)
        now = time.time()
        with self._lock:
            if key in self._entries:
                self._remove(key)
            self._evict_if_needed()
            self._entries[key] = CacheValue(key, copy.deepcopy(payload), now, now)
            for token in set(tokenize(key)):
                self._token_index[token].add(key)

    def get(self, query: str) -> tuple[dict | None, str | None, float]:
        key = canonical_query(query)
        now = time.time()
        with self._lock:
            exact = self._entries.get(key)
            if exact and now - exact.created_at <= self.ttl_seconds:
                exact.last_accessed = now
                self.hits += 1
                return copy.deepcopy(exact.payload), key, 1.0
            if exact:
                self._remove(key)

            candidates: set[str] = set()
            for token in set(tokenize(key)):
                candidates.update(self._token_index.get(token, ()))
            best_key, best_score = None, 0.0
            for candidate in candidates:
                entry = self._entries.get(candidate)
                if not entry:
                    continue
                if now - entry.created_at > self.ttl_seconds:
                    self._remove(candidate)
                    continue
                score = jaccard(key, candidate)
                if score > best_score:
                    best_key, best_score = candidate, score
            if best_key and best_score >= self.threshold:
                self._entries[best_key].last_accessed = now
                self.hits += 1
                return copy.deepcopy(self._entries[best_key].payload), best_key, best_score
            self.misses += 1
            return None, None, best_score

    def stats(self) -> dict:
        with self._lock:
            total = self.hits + self.misses
            return {
                "entries": len(self._entries),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(self.hits / total, 4) if total else 0.0,
                "threshold": self.threshold,
                "max_entries": self.max_entries,
            }

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
