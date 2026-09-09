"""
medjar.retrieval — hybrid dense + sparse retrieval with reciprocal-rank fusion.

Implements, with no third-party dependencies:
  * Okapi BM25 lexical scoring
  * a hashed bag-of-words vector space with cosine similarity, standing in for a
    learned embedding model (the fusion mechanics are identical either way)
  * reciprocal-rank fusion (RRF)
  * a lightweight cross-encoder surrogate for re-ranking
  * per-specialty scope filtering / boosting

Substituting a real embedding model and cross-encoder means replacing
`DenseIndex.embed` and `Reranker.score`; nothing else changes.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple

from .schemas import Passage, RetrievalHit

_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "in", "is", "it",
    "its", "of", "on", "or", "that", "the", "this", "to", "was", "were", "with", "may",
    "can", "not", "but", "which", "than", "into", "over", "both", "such", "when", "if",
}

_SYNONYMS = {
    "dyspnoea": "dyspnea", "haemodynamic": "hemodynamic", "oedema": "edema",
    "tumour": "tumor", "aetiology": "etiology", "anaemia": "anemia",
    "carcinoma": "cancer", "malignancy": "cancer", "malignant": "cancer",
    "neoplasm": "cancer", "infarction": "infarct", "pulmonary": "lung",
}


def tokenize(text: str) -> List[str]:
    """Lowercase, split, drop stopwords, normalize spelling/synonyms, light stem."""
    raw = re.findall(r"[a-z0-9]+", text.lower())
    out: List[str] = []
    for t in raw:
        if t in _STOP or len(t) < 3:
            continue
        t = _SYNONYMS.get(t, t)
        if len(t) > 4:
            for suf in ("ies", "es", "s"):
                if t.endswith(suf) and len(t) - len(suf) >= 4:
                    t = t[: -len(suf)]
                    break
        out.append(t)
    return out


class BM25Index:
    """Okapi BM25 sparse index."""

    def __init__(self, passages: Sequence[Passage], k1: float = 1.5, b: float = 0.75):
        self.passages = list(passages)
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(p.section + " " + p.text)) for p in self.passages]
        self.doc_len = [sum(d.values()) for d in self.docs]
        self.avgdl = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 0.0
        self.df: Counter = Counter()
        for d in self.docs:
            self.df.update(d.keys())
        self.N = len(self.passages)

    def _idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1.0 + (self.N - df + 0.5) / (df + 0.5))

    def scores(self, query: str) -> List[float]:
        q = tokenize(query)
        out = [0.0] * self.N
        for i, doc in enumerate(self.docs):
            dl = self.doc_len[i] or 1
            s = 0.0
            for term in q:
                tf = doc.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (1.0 - self.b + self.b * dl / (self.avgdl or 1.0))
                s += self._idf(term) * (tf * (self.k1 + 1.0)) / denom
            out[i] = s
        return out


class DenseIndex:
    """Hashed bag-of-words vector space with cosine similarity.

    Stand-in for a learned medical embedding model: deterministic, dependency
    free, and sufficient to exercise the fusion and scoping logic.
    """

    def __init__(self, passages: Sequence[Passage], dim: int = 384):
        self.passages = list(passages)
        self.dim = dim
        self.vecs = [self.embed(p.section + " " + p.text) for p in self.passages]

    def embed(self, text: str) -> List[float]:
        v = [0.0] * self.dim
        toks = tokenize(text)
        tf = Counter(toks)
        for term, n in tf.items():
            h = self._hash(term)
            idx = h % self.dim
            sign = 1.0 if (h >> 16) & 1 else -1.0
            # sublinear term weighting
            v[idx] += sign * (1.0 + math.log(n))
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    @staticmethod
    def _hash(term: str) -> int:
        h = 2166136261
        for ch in term:                      # FNV-1a, stable across runs
            h ^= ord(ch)
            h = (h * 16777619) & 0xFFFFFFFF
        return h

    def scores(self, query: str) -> List[float]:
        q = self.embed(query)
        return [sum(a * b for a, b in zip(q, v)) for v in self.vecs]


class Reranker:
    """Cross-encoder surrogate: term-overlap precision against the exact query."""

    @staticmethod
    def score(query: str, p: Passage) -> float:
        q = set(tokenize(query))
        d = set(tokenize(p.section + " " + p.text))
        if not q:
            return 0.0
        inter = len(q & d)
        # precision-weighted overlap, mildly favouring focused passages
        return (inter / len(q)) * (1.0 + 0.25 * (inter / (len(d) or 1)) ** 0.5)


class HybridRetriever:
    """Dense + sparse retrieval, RRF fusion, re-ranking, specialty scoping."""

    def __init__(self, passages: Sequence[Passage], rrf_k: int = 60):
        self.passages = list(passages)
        self.bm25 = BM25Index(self.passages)
        self.dense = DenseIndex(self.passages)
        self.rrf_k = rrf_k
        self.calls = 0

    @staticmethod
    def _ranks(scores: Sequence[float]) -> Dict[int, int]:
        order = sorted(range(len(scores)), key=lambda i: -scores[i])
        return {idx: r + 1 for r, idx in enumerate(order)}

    def retrieve(
        self,
        query: str,
        scope: Sequence[str] = (),
        top_k: int = 4,
        scope_boost: float = 0.35,
    ) -> List[RetrievalHit]:
        """Return the top-k fused, re-ranked hits for a query under a scope."""
        self.calls += 1
        dense_s = self.dense.scores(query)
        sparse_s = self.bm25.scores(query)
        dr, sr = self._ranks(dense_s), self._ranks(sparse_s)

        fused: List[Tuple[int, float]] = []
        for i, p in enumerate(self.passages):
            rrf = 1.0 / (self.rrf_k + dr[i]) + 1.0 / (self.rrf_k + sr[i])
            if scope and any(t in scope for t in p.specialty_tags):
                rrf *= (1.0 + scope_boost)          # scope boost, not a hard filter
            rrf *= 0.85 + 0.15 * p.recency_weight()  # mild recency preference
            fused.append((i, rrf))

        fused.sort(key=lambda t: -t[1])
        shortlist = fused[: max(top_k * 3, 8)]

        hits: List[RetrievalHit] = []
        for i, rrf in shortlist:
            p = self.passages[i]
            hits.append(RetrievalHit(passage=p, dense=dense_s[i], sparse=sparse_s[i],
                                     rrf=rrf, rerank=Reranker.score(query, p)))
        hits.sort(key=lambda h: -(0.55 * h.rerank + 0.45 * h.rrf * 40.0))
        return hits[:top_k]
