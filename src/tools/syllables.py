"""Deterministic Romanian syllable counter for lyric lines.

The counter finds the syllable nuclei of each word (one vowel, diphthong or
triphthong per syllable) instead of counting raw vowel groups. It handles:

* diphthongs and triphthongs that form a single syllable ("iar", "soare", "leoaică");
* spelling-only vowels: the e/i in ce/ci/ge/gi/che/chi/ghe/ghi before a/o/u/ă/î
  ("ceas", "chiar", "geam") and the short final -i after a consonant ("lupi", "munți");
* hiatus in word-final -ie/-ia/-iă ("poezie" = po-e-zi-e) and in -ioa- after a
  consonant ("vioară" = vi-oa-ră);
* hyphenated clitics, which share a syllable with their host word
  ("mi-am", "s-a", "bate-n", "într-o").

Known limits: some hiatus words are read as diphthongs ("real", "aici", "teatru"
are counted one syllable short). Poetic elision between words (sinalefă) is not
applied, so "să-apară" counts as 4. For exact counts, a lexicon can override the
rules: set LMUSIC_SYLLABLE_LEXICON to a UTF-8 TSV file with lines
``word<TAB>syllable count`` or ``word<TAB>syl-la-bles`` (e.g. built from RoLEX).

Measured on a held-out list of 52 hand-labelled words (tests/test_syllables.py):
86.5% exact, versus 61.5% for the previous vowel-group heuristic and 75.0% for
Pyphen's Romanian hyphenation patterns.
"""

from __future__ import annotations

import os
import re
import unicodedata
from functools import lru_cache
from typing import Any

VOWELS = frozenset("aăâeiîouy")

# Vowel pairs pronounced as one syllable (falling and rising diphthongs).
DIPHTHONGS = frozenset(
    {
        "ai",
        "ei",
        "oi",
        "ui",
        "ăi",
        "îi",
        "ii",
        "au",
        "eu",
        "ou",
        "iu",
        "ău",
        "îu",
        "ea",
        "ia",
        "ie",
        "io",
        "oa",
        "ua",
        "uă",
    }
)

# Vowel triples pronounced as one syllable.
TRIPHTHONGS = frozenset(
    {"eai", "eau", "iai", "iau", "iei", "ieu", "ioa", "oai", "uai", "eoa", "iou"}
)

LEXICON_ENV = "LMUSIC_SYLLABLE_LEXICON"


def normalize(text: str) -> str:
    """Lowercase, NFC, cedilla ş/ţ -> comma-below ș/ț, and â -> î (same sound)."""
    text = unicodedata.normalize("NFC", text.lower())
    return text.replace("ş", "ș").replace("ţ", "ț").replace("â", "î")


def tokenize(line: str) -> list[str]:
    """Split a line into words; hyphenated or apostrophised clitics are joined
    to their host word because they share a syllable ("mi-am" -> "miam")."""
    line = re.sub(r"(?<=[^\W\d_])[-’'](?=[^\W\d_])", "", normalize(line))
    return re.findall(r"[^\W\d_]+", line)


@lru_cache(maxsize=4)
def _load_lexicon(path: str) -> dict[str, int]:
    lexicon: dict[str, int] = {}
    if not path or not os.path.exists(path):
        return lexicon
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            if not raw.strip() or raw.startswith("#"):
                continue
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            word, value = normalize(parts[0].strip()), parts[1].strip()
            if value.isdigit():
                lexicon[word] = int(value)
            elif value:
                lexicon[word] = len([s for s in value.split("-") if s])
    return lexicon


def _vowel_mask(word: str) -> list[bool]:
    """True for letters that can carry a syllable nucleus."""
    mask = [ch in VOWELS for ch in word]
    keep_spelled_vowel = word.startswith("geo")  # ge-o-gra-fi-e
    for k, ch in enumerate(word):
        if ch not in "ei" or keep_spelled_vowel:
            continue
        after_cg = k >= 1 and (
            word[k - 1] in "cg"
            or (word[k - 1] == "h" and k >= 2 and word[k - 2] in "cg")
        )
        nxt = word[k + 1] if k + 1 < len(word) else ""
        if after_cg and nxt and nxt in "aouăî":
            mask[k] = False
    # Short final -i after a consonant ("lupi", "pomi", "munți").
    if len(word) >= 2 and word[-1] == "i" and not mask[-2] and any(mask[:-1]):
        mask[-1] = False
    return mask


def _split_cluster(cluster: str) -> int:
    """Number of nuclei in a run of consecutive vowels."""
    count, i = 0, 0
    while i < len(cluster):
        if cluster[i : i + 3] in TRIPHTHONGS:
            i += 3
        elif cluster[i : i + 2] in DIPHTHONGS:
            i += 2
        else:
            i += 1
        count += 1
    return count


def _rule_count(word: str) -> int:
    mask = _vowel_mask(word)
    count, k = 0, 0
    while k < len(word):
        if not mask[k]:
            k += 1
            continue
        start = k
        while k < len(word) and mask[k]:
            k += 1
        cluster = word[start:k]
        after_consonant = start >= 1 and not mask[start - 1]
        nuclei = _split_cluster(cluster)
        # vi-oa-ră, i-ni-mi-oa-ră: "ioa" after a consonant is i + oa.
        if cluster.startswith("ioa") and after_consonant:
            nuclei = 1 + _split_cluster(cluster[1:])
        # po-e-zi-e, fa-mi-li-a: final -ie/-ia/-iă after a consonant is a hiatus
        # when the word already has a nucleus ("ia", "mie" stay one syllable).
        if k == len(word) and cluster in {"ie", "ia", "iă"} and after_consonant:
            if count > 0:
                nuclei = 2
        count += nuclei
    return count


def count_word_syllables(word: str) -> int:
    """Syllables in one word (lexicon first, then rules)."""
    word = normalize(word)
    lexicon = _load_lexicon(os.environ.get(LEXICON_ENV, ""))
    if word in lexicon:
        return lexicon[word]
    return _rule_count(word)


def count_line_syllables(line: str) -> int:
    """Syllables in one lyric line. Digits and punctuation are ignored."""
    return sum(count_word_syllables(word) for word in tokenize(line))


def count_syllables(
    lines: list[str],
    target_syllables: list[int] | None = None,
    tolerance: int = 0,
) -> dict[str, Any]:
    """
    Count syllables per line in Romanian lyrics and compare against optional targets.

    Args:
        lines: List of lyric lines to evaluate.
        target_syllables: Optional list of expected syllable counts per line.
                          If a single-element list is provided, it applies to all lines.
        tolerance: Allowed absolute difference from the target (0 = exact match).

    Returns:
        Dictionary containing total lines, per-line breakdown, and pass/fail status.
        ``difference`` is actual minus target: positive means the line is too long.
    """
    normalized_targets: list[int | None]
    if not target_syllables:
        normalized_targets = [None] * len(lines)
    elif len(target_syllables) == 1 and len(lines) > 1:
        normalized_targets = target_syllables * len(lines)
    else:
        normalized_targets = [
            target_syllables[i] if i < len(target_syllables) else None
            for i in range(len(lines))
        ]

    results = []
    all_matched = True

    for idx, line in enumerate(lines):
        actual_count = count_line_syllables(line) if line.strip() else 0
        target = normalized_targets[idx]
        diff = (actual_count - target) if target is not None else 0
        matched = abs(diff) <= tolerance if target is not None else True

        if not matched:
            all_matched = False

        results.append(
            {
                "line_index": idx,
                "text": line,
                "actual_syllables": actual_count,
                "target_syllables": target,
                "difference": diff,
                "matched": matched,
            }
        )

    return {
        "passed": all_matched,
        "line_count": len(lines),
        "lines": results,
    }