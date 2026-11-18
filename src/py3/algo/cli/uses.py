"""Match a plain-English need ("shortest distance between two zip codes") to algorithms.

Used by `algo uses` (alias `u`). Each algorithm is described by phrases from the registry
(its `uses`, identification phrases, name and category) and from the problems it is the primary
pattern for (title, keywords and uses). A query and every phrase are reduced to canonical word
stems (a few synonyms folded together, e.g. zip code / city / address -> location), and words are
weighted by rarity (IDF), so "zip" counts for more than "two". Stdlib only.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

Item = dict[str, Any]


def _words(text: str) -> list[str]:
    """Space-separated word list (keeps the tables below readable)."""
    return text.split()


STOPWORDS = frozenset(
    _words(
        "a an the of to in on for by with and or is are be at from into that this it its as all "
        "each every find get how what which who my me i using use want need some any can do does "
        "across between over under than then so"
    )
)

# Words that mean the same thing for this purpose -> one canonical token.
_GROUPS = {
    "location": "zip zipcode postcode postal address city town location place destination",
    "route": "distance route routing direction path navigation",
    "min": "smallest minimum min lowest least fewest",
    "max": "largest maximum max biggest highest greatest",
    "shortest": "shortest fastest quickest closest nearest",
    "cost": "cheapest cheap cost costs price",
    "number": "integer int number value digit",
    "duplicate": "duplicate repeated repeat dedupe deduplicate",
    "search": "searching search lookup look",
    "schedule": "schedule scheduling calendar meeting",
    "person": "friend people person user",
}
SYNONYMS = {w: canon for canon, words in _GROUPS.items() for w in _words(words)}
SPLIT = {"chessboard": ["chess", "board"], "zipcode": ["zip", "code"]}
MIN_LEN = 2  # tokens shorter than this are dropped
MIN_PLURAL = 4  # only strip a plural "s" from words at least this long
COHERENCE = 1.0  # bonus weight for the single phrase that covers most of the query
CUTOFF = 0.4  # with a query, drop algorithms scoring below this fraction of the best

# Phrase weights by source: an algorithm's own uses count most.
W_USE, W_PRIMARY, W_TAG, W_SECONDARY = 1.0, 0.8, 0.7, 0.4


def _stem(w: str) -> str:
    """Crude English stemmer: enough to match plurals and -ing/-ed forms."""
    for suf, rep, n in (("ies", "y", 4), ("sses", "ss", 5), ("ing", "", 5), ("ed", "", 4)):
        if w.endswith(suf) and len(w) > n:
            return w[: -len(suf)] + rep
    if w.endswith("s") and not w.endswith("ss") and len(w) >= MIN_PLURAL:
        return w[:-1]
    return w


def tokens(text: str) -> set[str]:
    """Canonical stems of the meaningful words in text."""
    out: set[str] = set()
    for raw in re.findall(r"[a-z0-9]+", text.lower()):
        for w in SPLIT.get(raw, [raw]):
            if w in STOPWORDS or len(w) < MIN_LEN:
                continue
            stem = _stem(SYNONYMS.get(w, w))
            s = SYNONYMS.get(stem, stem)
            if s not in STOPWORDS:  # "finding" -> "find"
                out.add(s)
    return out


@dataclass
class Phrase:
    """One descriptive phrase for an algorithm and where it came from."""

    text: str
    weight: float
    toks: set[str]
    problem: int | None = None  # set when the phrase describes a problem


@dataclass
class Match:
    """An algorithm ranked for a query."""

    algo: Item
    score: float
    matched: list[str] = field(default_factory=list)  # the algorithm's own uses that matched
    problems: list[Item] = field(default_factory=list)  # best problems for this algorithm


def _problem_text(p: Item) -> list[str]:
    return [p["title"], *p.get("keywords", []), *p.get("uses", [])]


def phrases_for(algo: Item, problems: list[Item]) -> list[Phrase]:
    """Every phrase that describes algo, weighted by source."""
    out = [Phrase(u, W_USE, tokens(u)) for u in algo.get("uses", [])]
    tags = [algo["id"], algo.get("name", ""), algo.get("category", "")]
    out += [Phrase(t, W_TAG, tokens(t)) for t in tags + algo.get("identification", []) if t]
    for p in problems:
        if algo["id"] not in p["algorithms"]:
            continue
        w = W_PRIMARY if p["algorithms"][0] == algo["id"] else W_SECONDARY
        out += [Phrase(t, w, tokens(t), p["id"]) for t in _problem_text(p)]
    return out


def idf_table(all_phrases: list[list[Phrase]]) -> dict[str, float]:
    """Inverse document frequency of each token across every phrase."""
    df: dict[str, int] = {}
    n = 0
    for group in all_phrases:
        for ph in group:
            n += 1
            for t in ph.toks:
                df[t] = df.get(t, 0) + 1
    return {t: math.log(1 + n / c) for t, c in df.items()}


def _phrase_score(q: set[str], ph: Phrase, idf: dict[str, float]) -> float:
    return ph.weight * sum(idf.get(t, 0.0) for t in q & ph.toks)


def score_algorithm(q: set[str], group: list[Phrase], idf: dict[str, float]) -> float:
    """Each query word counts once (its best phrase), plus the best single phrase again.

    The second term rewards one phrase that says the whole thing ("smallest ... integers") over
    words scattered across unrelated phrases.
    """
    if not q:
        return 0.0
    per_token = sum(
        max((ph.weight * idf.get(t, 0.0) for ph in group if t in ph.toks), default=0.0) for t in q
    )
    best = max((_phrase_score(q, ph, idf) for ph in group), default=0.0)
    return per_token + COHERENCE * best


def rank_problems(
    algo: Item, problems: list[Item], q: set[str], idf: dict[str, float], limit: int
) -> list[Item]:
    """Problems this algorithm is the primary (optimal) pattern for, best match first."""

    def fit(p: Item) -> float:
        return sum(idf.get(t, 0.0) for t in q & tokens(" ".join(_problem_text(p))))

    mine = [p for p in problems if p["algorithms"][:1] == [algo["id"]]]
    if not mine:  # e.g. design: fall back to problems that use it at all
        mine = [p for p in problems if algo["id"] in p["algorithms"]]
    rep = algo.get("leetcode_id")
    mine.sort(key=lambda p: (-fit(p), p["id"] != rep, p.get("list") != "study99", p["id"]))
    return mine[:limit]


def search(
    query: str, registry: list[Item], problems: list[Item], *, top: int = 5, per_algo: int = 3
) -> list[Match]:
    """Algorithms ranked for a free-text need; with an empty query, every algorithm in order."""
    groups = [phrases_for(a, problems) for a in registry]
    idf = idf_table(groups)
    q = tokens(query)
    if not query.strip():
        return [
            Match(a, 0.0, a.get("uses", []), rank_problems(a, problems, q, idf, per_algo))
            for a in registry
        ]
    out = []
    for a, group in zip(registry, groups, strict=True):
        s = score_algorithm(q, group, idf)
        if s <= 0:
            continue
        own = sorted(
            (ph for ph in group if ph.weight == W_USE and q & ph.toks),
            key=lambda ph: -_phrase_score(q, ph, idf),
        )
        out.append(Match(a, s, [ph.text for ph in own[:3]], []))
    out.sort(key=lambda m: -m.score)
    out = [m for m in out if m.score >= CUTOFF * out[0].score][:top] if out else []
    for m in out:
        m.problems = rank_problems(m.algo, problems, q, idf, per_algo)
    return out


__all__ = ["Match", "Phrase", "phrases_for", "rank_problems", "search", "tokens"]
