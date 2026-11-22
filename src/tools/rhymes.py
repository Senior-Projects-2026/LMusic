import re
from typing import Any


def _extract_rhyme_tail(line: str) -> str:
    """Placeholder phonetic tail extractor (last 2 alphabetic characters)."""
    cleaned = re.sub(r"[^a-zA-ZăâîșțĂÂÎȘȚ]", "", line.lower())
    return cleaned[-2:] if len(cleaned) >= 2 else cleaned


def check_rhyme(lines: list[str], scheme: str) -> dict[str, Any]:
    """
    Verify whether a stanza's lines follow the requested rhyme scheme (e.g., AABB, ABAB).

    Args:
        lines: List of lyric lines in the stanza.
        scheme: Expected rhyme pattern string (e.g., "AABB", "ABAB", "AABBCC").

    Returns:
        Dictionary with overall pass status, extracted rhyme endings, and failed line pairs.
    """
    # TODO (Dado): Implement Romanian phonetic suffix extraction from the last stressed vowel
    # and phonetic equivalence rules (e.g., voiced/unvoiced consonant pairs).
    clean_scheme = scheme.strip().upper()
    if len(lines) != len(clean_scheme):
        return {
            "passed": False,
            "scheme": clean_scheme,
            "error": f"Line count ({len(lines)}) does not match scheme length ({len(clean_scheme)}).",
            "endings": [],
            "failed_pairs": [],
        }

    endings = [_extract_rhyme_tail(line) for line in lines]
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
        "passed": len(failed_pairs) == 0,
        "scheme": clean_scheme,
        "endings": endings,
        "failed_pairs": failed_pairs,
    }