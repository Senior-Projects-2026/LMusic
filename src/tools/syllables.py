import re
from typing import Any


def count_syllables(lines: list[str], target_syllables: list[int] | None = None) -> dict[str, Any]:
    """
    Count syllables per line in Romanian lyrics and compare against optional targets.

    Args:
        lines: List of lyric lines to evaluate.
        target_syllables: Optional list of expected syllable counts per line.
                          If a single-element list is provided, it applies to all lines.

    Returns:
        Dictionary containing total lines, per-line breakdown, and pass/fail status.
    """
    # TODO (Matei): Replace vowel-group heuristic with deterministic Romanian syllabification
    # (handling diphthongs, triphthongs, hiatus, and hyphenated clitics like "mi-am", "s-a").
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
        # Fallback placeholder: count contiguous Romanian vowel clusters
        vowel_groups = re.findall(r"[aeiouăâîAEIOUĂÂÎ]+", line)
        actual_count = len(vowel_groups) if line.strip() else 0
        target = normalized_targets[idx]
        diff = (actual_count - target) if target is not None else 0
        matched = (diff == 0) if target is not None else True

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