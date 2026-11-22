import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

_DEFAULT_LEXICON = (
    Path(__file__).resolve().parents[2] / "data/raw/rolex/lexicon_reterom_final.txt"
)
_VOWELS = {"a", "e", "i", "o", "u", "@", "1"}
_PHONEMES = _VOWELS | {
    "r",
    "t",
    "n",
    "l",
    "s",
    "k",
    "m",
    "p",
    "d",
    "j",
    "ts",
    "i_0",
    "z",
    "b",
    "f",
    "tS",
    "v",
    "S",
    "g",
    "e_X",
    "gZ",
    "Z",
    "h",
    "o_X",
    "k_j",
    "ks",
    "w",
    "g_j",
    "gz",
}
_VOWEL_SOUND = dict(zip("aeiouăâî", ("a", "e", "i", "o", "u", "@", "1", "1")))


def _normalize(text: str) -> str:
    return (
        unicodedata.normalize("NFC", text).lower().translate(str.maketrans("şţ", "șț"))
    )


def _tail_from_entry(syllables: str, stressed: str, phonetic: str) -> str:
    """Align a RoLEX stressed syllable with its SAMPA vowel nucleus.

    Glides (j/w/e_X/o_X) and final nonsyllabic i_0 are not nuclei.
    Reject inconsistent annotations instead of guessing their alignment.
    """
    syllables, stressed = _normalize(syllables), _normalize(stressed)
    parts = syllables.split(".")
    spelling = "".join(parts)
    if not all(parts) or stressed.replace("'", "") != spelling:
        return ""
    phones = phonetic.split()
    if not phones or any(phone not in _PHONEMES for phone in phones):
        return ""
    nuclei = [i for i, phone in enumerate(phones) if phone in _VOWELS]
    if len(nuclei) != len(parts):
        return ""
    if "'" not in stressed:
        return " ".join(phones[nuclei[0] :]) if len(parts) == 1 else ""
    if stressed.count("'") != 1:
        return ""
    position = stressed.index("'")
    if position + 1 >= len(stressed):
        return ""
    vowel = _VOWEL_SOUND.get(stressed[position + 1])
    offset = 0
    for index, part in enumerate(parts):
        if offset <= position < offset + len(part):
            nucleus = nuclei[index]
            if phones[nucleus] != vowel:
                return ""
            return " ".join(phones[nucleus:])
        offset += len(part)
    return ""


@lru_cache(maxsize=2)
def _load_lexicon(path: str) -> dict[str, frozenset[str]]:
    """Load original six-column RoLEX TSV; cache until process restart.

    Empty tails remain in variant sets: an unaligned pronunciation must not
    silently disappear and make an ambiguous word look verified.
    """
    entries: dict[str, set[str]] = {}
    with Path(path).open(encoding="utf-8-sig") as source:
        for number, row in enumerate(source, 1):
            if not row.strip():
                continue
            columns = row.rstrip("\r\n").split("\t")
            if len(columns) != 6:
                raise ValueError(f"Invalid RoLEX row {number}: expected six columns")
            word, _, _, syllables, stressed, phonetic = columns
            tail = _tail_from_entry(syllables, stressed, phonetic)
            entries.setdefault(_normalize(word), set()).add(tail)
    if not entries:
        raise ValueError("RoLEX lexicon is empty")
    return {word: frozenset(tails) for word, tails in entries.items()}


def _extract_rhyme_tail(line: str) -> str:
    """Return a unique attested phonetic tail, or empty for unresolved words."""
    words = re.findall(r"[^\W\d_]+(?:[-’'][^\W\d_]+)*", _normalize(line))
    if not words:
        return ""
    path = str(Path(os.environ.get("LMUSIC_ROLEX_PATH", _DEFAULT_LEXICON)).resolve())
    variants = _load_lexicon(path).get(words[-1], frozenset())
    return next(iter(variants)) if len(variants) == 1 else ""


def check_rhyme(lines: list[str], scheme: str) -> dict[str, Any]:
    """
    Verify same-label rhyme pairs using unique RoLEX phonetic tails.

    Empty endings mean unresolved words, not proven non-rhymes. Different
    labels are not required to have different sounds. No network calls occur.

    Args:
        lines: List of lyric lines in the stanza.
        scheme: Expected rhyme pattern (e.g., "AABB", "ABAB", "AABBCC").

    Returns:
        Pass status, SAMPA endings, and failed pairs; error for setup failures.
    """
    clean_scheme = scheme.strip().upper()
    if len(lines) != len(clean_scheme):
        return {
            "passed": False,
            "scheme": clean_scheme,
            "error": (
                f"Line count ({len(lines)}) does not match "
                f"scheme length ({len(clean_scheme)})."
            ),
            "endings": [],
            "failed_pairs": [],
        }

    try:
        endings = [_extract_rhyme_tail(line) for line in lines]
    except (OSError, UnicodeError, ValueError) as error:
        return {
            "passed": False,
            "scheme": clean_scheme,
            "error": (
                "RoLEX setup error: configure LMUSIC_ROLEX_PATH to the original "
                f"six-column UTF-8 lexicon. {error}"
            ),
            "endings": [],
            "failed_pairs": [],
        }
    groups: dict[str, list[int]] = {}
    for idx, label in enumerate(clean_scheme):
        groups.setdefault(label, []).append(idx)

    failed_pairs = []
    for label, indices in groups.items():
        if len(indices) < 2:
            continue
        anchor_idx = indices[0]
        anchor_tail = endings[anchor_idx]
        for compare_idx in indices[1:]:
            if endings[compare_idx] != anchor_tail or not anchor_tail:
                failed_pairs.append(
                    {
                        "label": label,
                        "expected_line": anchor_idx,
                        "actual_line": compare_idx,
                        "expected_ending": anchor_tail,
                        "actual_ending": endings[compare_idx],
                    }
                )

    return {
        "passed": bool(endings) and all(endings) and len(failed_pairs) == 0,
        "scheme": clean_scheme,
        "endings": endings,
        "failed_pairs": failed_pairs,
    }
