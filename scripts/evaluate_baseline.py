"""Evaluate Experiment 1 (Zero-Shot Baseline) outputs against deterministic tools."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Ensure repository root is importable when executed directly
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.tools.rhymes import check_rhyme
from src.tools.syllables import count_syllables

INPUT_PATH = REPO_ROOT / "results" / "baseline_outputs.json"
OUTPUT_PATH = REPO_ROOT / "results" / "baseline_evaluation.json"

META_PREFIXES = (
    "bună",
    "iată",
    "sigur",
    "desigur",
    "îmi pare rău",
    "îmi pare rau",
    "pentru a ",
    "această ",
    "acest ",
    "aceste ",
    "sper că",
    "în continuare",
    "cert,",
    "claro",
    "sure,",
    "i'm sorry",
    "feel free",
    "în ceea ce privește",
    "încercând să",
    "îți pot oferi",
    "bineînțeles",
    "bineînțărită",
    "aici este",
    "aici sunt",
    "îmi vine în minte",
    "poemul tău",
    "în acest moment, mă simt",
    "pentru a găsi",
    "în această întrebare",
    "versul de pe",
    "în versul ",
    "aceasta este o frază",
    "un refren pop despre",
    "libertate este un concept",
    "marea este un termen",
    "mare - cuvânt",
    "în concluzie",
    "așadar,",
    "îmi rezum",
    "încăperea mea, învățând",
    "total:",
    "aici se numără",
)


def _is_meta_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.endswith(":"):
        return True
    if re.match(r"^[\(\[].*[\)\]]$", stripped):
        return True
    if re.match(r"^(versul|strofa|primă catr|a doua catr|secundă catr)\b", stripped, re.I):
        return True
    # Prose paragraphs / explanations are much longer than 7-11 syllable lyric lines
    if len(stripped) > 120:
        return True
    lowered = stripped.lower()
    return any(lowered.startswith(prefix) for prefix in META_PREFIXES)


def extract_candidate_lines(raw_output: str, expected_lines: int | None) -> tuple[list[str], bool]:
    """
    Extract candidate lyric lines from raw zero-shot output.

    Returns:
        (candidate_lines, is_clean_format)
        is_clean_format is True only if the model returned pure lyrics with no chatter
        and matched expected_lines (when specified).
    """
    raw_non_empty = [ln.strip() for ln in raw_output.splitlines() if ln.strip()]
    cleaned_lyrics: list[str] = []

    for ln in raw_non_empty:
        if _is_meta_line(ln):
            continue
        # Remove leading list numbers ("1. ", "2) ") and wrapping quotes/markdown bold
        text = re.sub(r"^\d+[\.\)]\s*", "", ln)
        text = text.strip('"*„”«» ')
        if text and not _is_meta_line(text):
            cleaned_lyrics.append(text)

    no_chatter = len(raw_non_empty) > 0 and len(raw_non_empty) == len(cleaned_lyrics)
    if expected_lines is not None:
        is_clean_format = no_chatter and len(cleaned_lyrics) == expected_lines
        candidate = cleaned_lyrics[:expected_lines]
    else:
        is_clean_format = no_chatter and len(cleaned_lyrics) > 0
        candidate = cleaned_lyrics[:4]

    return candidate, is_clean_format


def evaluate_record(record: dict[str, Any]) -> dict[str, Any]:
    constraints = record.get("expected_constraints", {})
    exp_lines: int | None = constraints.get("lines")
    exp_syllables: int | None = constraints.get("syllables_per_line")
    exp_scheme: str | None = constraints.get("rhyme_scheme")

    eval_target_len = exp_lines or (len(exp_scheme) if exp_scheme else None)
    candidate_lines, is_clean_format = extract_candidate_lines(
        record["output"], eval_target_len
    )

    # 1. Line count adherence (on extracted stanza)
    line_count_ok: bool | None = None
    if exp_lines is not None:
        line_count_ok = len(candidate_lines) == exp_lines

    # 2. Syllable adherence (exact and +/- 1 tolerance)
    syllable_stanza_exact: bool | None = None
    syllable_stanza_tol1: bool | None = None
    syllable_line_exact_hits = 0
    syllable_line_tol1_hits = 0
    syllable_line_total = 0

    if exp_syllables is not None:
        if candidate_lines:
            exact_res = count_syllables(
                candidate_lines, target_syllables=[exp_syllables], tolerance=0
            )
            tol1_res = count_syllables(
                candidate_lines, target_syllables=[exp_syllables], tolerance=1
            )
            syllable_stanza_exact = exact_res["passed"] and (
                exp_lines is None or len(candidate_lines) == exp_lines
            )
            syllable_stanza_tol1 = tol1_res["passed"] and (
                exp_lines is None or len(candidate_lines) == exp_lines
            )
            syllable_line_exact_hits = sum(
                1 for item in exact_res["lines"] if item["matched"]
            )
            syllable_line_tol1_hits = sum(
                1 for item in tol1_res["lines"] if item["matched"]
            )
            syllable_line_total = len(candidate_lines)
        else:
            syllable_stanza_exact = False
            syllable_stanza_tol1 = False

    # 3. Rhyme adherence
    rhyme_ok: bool | None = None
    unresolved_endings = 0
    total_endings = 0
    rhyme_error: str | None = None

    if exp_scheme is not None:
        if len(candidate_lines) == len(exp_scheme):
            rhyme_res = check_rhyme(candidate_lines, exp_scheme)
            if "error" in rhyme_res:
                raise RuntimeError(rhyme_res["error"])
            rhyme_ok = rhyme_res["passed"]
            endings = rhyme_res["endings"]
            total_endings = len(endings)
            unresolved_endings = sum(1 for e in endings if not e)
        else:
            rhyme_ok = False
            rhyme_error = f"Extracted {len(candidate_lines)} lines for scheme {exp_scheme}"

    # 4. Joint pass (all specified constraints satisfied simultaneously)
    checks = [c for c in (line_count_ok, syllable_stanza_exact, rhyme_ok) if c is not None]
    joint_pass = all(checks) if checks else is_clean_format

    return {
        "id": record["id"],
        "model": record["model"],
        "theme": record["theme"],
        "expected_constraints": constraints,
        "extracted_lines": candidate_lines,
        "clean_format": is_clean_format,
        "line_count_passed": line_count_ok,
        "syllable_stanza_exact": syllable_stanza_exact,
        "syllable_stanza_tol1": syllable_stanza_tol1,
        "syllable_line_exact_hits": syllable_line_exact_hits,
        "syllable_line_tol1_hits": syllable_line_tol1_hits,
        "syllable_line_total": syllable_line_total,
        "rhyme_passed": rhyme_ok,
        "unresolved_endings": unresolved_endings,
        "total_endings": total_endings,
        "rhyme_error": rhyme_error,
        "joint_pass": joint_pass,
    }


def summarize_by_model(evaluations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    models = list(dict.fromkeys(ev["model"] for ev in evaluations))
    summary: dict[str, dict[str, Any]] = {}

    for model in models:
        rows = [ev for ev in evaluations if ev["model"] == model]
        n = len(rows)

        clean_fmt = sum(1 for r in rows if r["clean_format"])

        line_rows = [r for r in rows if r["line_count_passed"] is not None]
        line_ok = sum(1 for r in line_rows if r["line_count_passed"])

        syl_rows = [r for r in rows if r["syllable_stanza_exact"] is not None]
        syl_exact_ok = sum(1 for r in syl_rows if r["syllable_stanza_exact"])
        syl_tol1_ok = sum(1 for r in syl_rows if r["syllable_stanza_tol1"])
        tot_syl_lines = sum(r["syllable_line_total"] for r in syl_rows)
        hit_syl_lines_exact = sum(r["syllable_line_exact_hits"] for r in syl_rows)
        hit_syl_lines_tol1 = sum(r["syllable_line_tol1_hits"] for r in syl_rows)

        rhyme_rows = [r for r in rows if r["rhyme_passed"] is not None]
        rhyme_ok = sum(1 for r in rhyme_rows if r["rhyme_passed"])
        tot_endings = sum(r["total_endings"] for r in rhyme_rows)
        unres_endings = sum(r["unresolved_endings"] for r in rhyme_rows)

        joint_ok = sum(1 for r in rows if r["joint_pass"])

        summary[model] = {
            "total_prompts": n,
            "clean_format_pct": round(100 * clean_fmt / n, 1),
            "line_count_pct": round(100 * line_ok / len(line_rows), 1),
            "syllable_stanza_exact_pct": round(100 * syl_exact_ok / len(syl_rows), 1),
            "syllable_stanza_tol1_pct": round(100 * syl_tol1_ok / len(syl_rows), 1),
            "syllable_line_exact_pct": round(
                100 * hit_syl_lines_exact / tot_syl_lines, 1
            )
            if tot_syl_lines
            else 0.0,
            "syllable_line_tol1_pct": round(
                100 * hit_syl_lines_tol1 / tot_syl_lines, 1
            )
            if tot_syl_lines
            else 0.0,
            "rhyme_stanza_pct": round(100 * rhyme_ok / len(rhyme_rows), 1),
            "unresolved_rhyme_words_pct": round(
                100 * unres_endings / tot_endings, 1
            )
            if tot_endings
            else 0.0,
            "joint_all_constraints_pct": round(100 * joint_ok / n, 1),
        }

    return summary


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing baseline outputs: {INPUT_PATH}")

    raw_data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    outputs = raw_data["outputs"]

    evaluations = [evaluate_record(rec) for rec in outputs]
    summary = summarize_by_model(evaluations)

    report = {
        "metadata": raw_data.get("metadata", {}),
        "summary": summary,
        "evaluations": evaluations,
    }
    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    headers = [
        "Model",
        "Clean Format",
        "Line Count",
        "Syllables (Stanza Exact / ±1)",
        "Syllables (Line Exact / ±1)",
        "Rhyme Scheme",
        "Unresolved Words",
        "Joint Pass",
    ]
    rows = [
        [
            f"`{model}`",
            f"{s['clean_format_pct']}%",
            f"{s['line_count_pct']}%",
            f"{s['syllable_stanza_exact_pct']}% / {s['syllable_stanza_tol1_pct']}%",
            f"{s['syllable_line_exact_pct']}% / {s['syllable_line_tol1_pct']}%",
            f"{s['rhyme_stanza_pct']}%",
            f"{s['unresolved_rhyme_words_pct']}%",
            f"{s['joint_all_constraints_pct']}%",
        ]
        for model, s in summary.items()
    ]

    widths = [max(len(r[i]) for r in [headers, *rows]) for i in range(len(headers))]

    def fmt_row(cells: list[str]) -> str:
        padded = [
            cells[0].ljust(widths[0]),
            *(cells[i].rjust(widths[i]) for i in range(1, len(cells))),
        ]
        return "| " + " | ".join(padded) + " |"

    sep = "|-" + "-|-".join(
        ":" + "-" * (widths[0] - 1) if i == 0 else "-" * (widths[i] - 1) + ":"
        for i in range(len(widths))
    ) + "-|"

    print("\n### Experiment 1: Zero-Shot Baseline Results\n")
    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row))
    print(f"\nSaved detailed evaluation to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()