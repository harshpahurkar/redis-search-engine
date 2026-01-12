from __future__ import annotations

__version__ = "1.1.0"

import json
import math
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import redis

NON_WORDS = re.compile(r"[^a-z0-9' ]")
STOP_WORDS = {
    "a","able","about","across","after","all","almost","also","am","among","an","and","any",
    "are","as","at","be","because","been","but","by","can","cannot","could","dear","did",
    "do","does","either","else","ever","every","for","from","get","got","had","has","have",
    "he","her","hers","him","his","how","however","i","if","in","into","is","it","its",
    "just","least","let","like","likely","may","me","might","most","must","my","neither",
    "no","nor","not","of","off","often","on","only","or","other","our","own","rather","said",
    "say","says","she","should","since","so","some","than","that","the","their","them","then",
    "there","these","they","this","tis","to","too","twas","us","wants","was","we","were",
    "what","when","where","which","while","who","whom","why","will","with","would","yet","you",
    "your",
}


@dataclass
class SearchHit:
    doc_id: str
    score: float
    title: str | None = None


class SearchEngine:
    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "se") -> None:
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix

    def _key(self, *parts: str) -> str:
        return ":".join([self.prefix, *parts])

    def tokenize(self, text: str) -> List[str]:
        cleaned = NON_WORDS.sub(" ", text.lower())
        tokens = [t for t in cleaned.split() if t and t not in STOP_WORDS]
        return tokens

    def index_document(self, doc_id: str, text: str, title: str | None = None) -> None:
        tokens = self.tokenize(text)
        if not tokens:
            return

        counts = Counter(tokens)
        pipe = self.redis.pipeline()

        terms_key = self._key("doc_terms", doc_id)
        pipe.delete(terms_key)
        for term, freq in counts.items():
            term_key = self._key("term", term)
            pipe.zadd(term_key, {doc_id: float(freq)})
            pipe.sadd(terms_key, term)

        pipe.sadd(self._key("docs"), doc_id)
        doc_key = self._key("doc", doc_id)
        pipe.hset(doc_key, "text", text)
        if title:
            pipe.hset(doc_key, "title", title)
        pipe.execute()

    def remove_document(self, doc_id: str) -> None:
        terms_key = self._key("doc_terms", doc_id)
        terms = self.redis.smembers(terms_key)
        pipe = self.redis.pipeline()
        for term in terms:
            pipe.zrem(self._key("term", term), doc_id)
        pipe.delete(terms_key)
        pipe.delete(self._key("doc", doc_id))
        pipe.srem(self._key("docs"), doc_id)
        pipe.execute()

    def _idf(self, doc_count: int, doc_freq: int) -> float:
        return math.log((doc_count + 1.0) / (doc_freq + 1.0)) + 1.0

    def search(self, query: str, offset: int = 0, limit: int = 10) -> List[SearchHit]:
        tokens = self.tokenize(query)
        if not tokens:
            return []

        positives: List[str] = []
        negatives: List[str] = []
        for raw in query.split():
            if raw.startswith("-") and len(raw) > 1:
                negatives.extend(self.tokenize(raw[1:]))
            else:
                positives.extend(self.tokenize(raw))

        if not positives:
            positives = tokens

        doc_count = self.redis.scard(self._key("docs"))
        if doc_count == 0:
            return []

        temp_key = self._key("tmp", str(os.getpid()), str(int(time.time() * 1000)))
        weights: Dict[str, float] = {}
        for term in positives:
            df = self.redis.zcard(self._key("term", term))
            if df == 0:
                continue
            weights[self._key("term", term)] = self._idf(doc_count, df)

        if not weights:
            return []

        self.redis.zunionstore(temp_key, weights)

        if negatives:
            for term in negatives:
                term_key = self._key("term", term)
                neg_ids = self.redis.zrange(term_key, 0, -1)
                if neg_ids:
                    self.redis.zrem(temp_key, *neg_ids)

        results = self.redis.zrevrange(temp_key, offset, offset + limit - 1, withscores=True)
        self.redis.delete(temp_key)

        hits: List[SearchHit] = []
        for doc_id, score in results:
            title = self.redis.hget(self._key("doc", doc_id), "title")
            hits.append(SearchHit(doc_id=doc_id, score=float(score), title=title))
        return hits

    def load_json(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        for doc in docs:
            self.index_document(doc["id"], doc.get("text", ""), title=doc.get("title"))

    def clear(self) -> None:
        keys = list(self.redis.scan_iter(match=f"{self.prefix}:*"))
        if keys:
            self.redis.delete(*keys)
