"""Tests for the deterministic Romanian syllable counter (src/tools/syllables.py)."""

import pytest

from src.tools.syllables import (
    LEXICON_ENV,
    _load_lexicon,
    count_line_syllables,
    count_syllables,
    count_word_syllables,
)

# Hand-labelled syllable counts covering the rules (diphthongs, triphthongs,
# spelling-only e/i, short final -i, hiatus).
GOLD_WORDS = {
    "iubire": 3,
    "inimă": 3,
    "ochii": 2,
    "ochi": 1,
    "aer": 2,
    "poezie": 4,
    "luceafărul": 4,
    "știu": 1,
    "creioane": 3,
    "a": 1,
    "ea": 1,
    "idee": 3,
    "copiii": 3,
    "copii": 2,
    "gheorghe": 2,
    "chiar": 1,
    "lupi": 1,
    "familie": 4,
    "ceas": 1,
    "frumoasă": 3,
    "noapte": 2,
    "stele": 2,
    "viața": 2,
    "luna": 2,
    "iarbă": 2,
    "ploaia": 2,
    "cântec": 2,
    "inimioară": 5,
    "dor": 1,
    "mare": 2,
    "soare": 2,
    "lumină": 3,
    "munți": 1,
    "pomii": 2,
    "maria": 3,
    "ziua": 2,
    "baie": 2,
    "voie": 2,
    "geografie": 5,
    "eu": 1,
    "mea": 1,
    "tău": 1,
    "noi": 1,
    "vreau": 1,
    "iarăși": 2,
    "cântare": 3,
    "îngeri": 2,
    "gânduri": 2,
    "albastru": 3,
    "speranță": 3,
    "plouă": 2,
    "vioară": 3,
}

# Held-out words, labelled before the rules were run on them and never used to
# tune the rules. The remaining errors are hiatus words that need a lexicon.
HELD_OUT = {
    "casă": 2,
    "câine": 2,
    "pâine": 2,
    "mâine": 2,
    "fereastră": 3,
    "ușă": 2,
    "dragoste": 3,
    "dragostea": 3,
    "zâmbet": 2,
    "lacrimă": 3,
    "lacrimi": 2,
    "visuri": 2,
    "vise": 2,
    "inimii": 3,
    "sufletul": 3,
    "suflete": 3,
    "oameni": 2,
    "femeie": 3,
    "ploaie": 2,
    "aiurea": 3,
    "seară": 2,
    "dimineață": 4,
    "vioară": 3,
    "cheie": 2,
    "ghiocel": 2,
    "ceață": 2,
    "geamul": 2,
    "chemare": 3,
    "vecie": 3,
    "continuare": 5,
    "ruină": 3,
    "real": 2,
    "teatru": 3,
    "poet": 2,
    "zeul": 2,
    "muzeu": 2,
    "ideal": 3,
    "alee": 3,
    "aici": 2,
    "oricine": 4,
    "nimeni": 2,
    "primăvară": 4,
    "toamnă": 2,
    "iarnă": 2,
    "vară": 2,
    "foc": 1,
    "joc": 1,
    "liniștea": 3,
    "cuvinte": 3,
    "cuvântul": 3,
    "nouă": 2,
    "două": 2,
}


@pytest.mark.parametrize("word,expected", sorted(GOLD_WORDS.items()))
def test_word_syllables(word, expected):
    assert count_word_syllables(word) == expected


def test_held_out_accuracy_beats_vowel_groups():
    correct = sum(count_word_syllables(w) == n for w, n in HELD_OUT.items())
    assert correct / len(HELD_OUT) >= 0.85


@pytest.mark.parametrize(
    "line,expected",
    [
        ("Pe strada veche plouă iar", 8),
        ("Și vântul bate-n felinar", 8),
        ("mi-am", 1),
        ("s-a dus", 2),
        ("dă-mi", 1),
        ("într-o zi", 3),
        ("Și-ncerca", 3),
        ("Sub clar de lună stăm tăcuți", 8),
        ("", 0),
        ("   ", 0),
        ("2026!!!", 0),
    ],
)
def test_line_syllables(line, expected):
    assert count_line_syllables(line) == expected


def test_cedilla_and_comma_diacritics_count_the_same():
    assert count_line_syllables("Şi ţara") == count_line_syllables("Și țara") == 3


def test_contract_and_targets():
    lines = ["Pe strada veche plouă iar", "Și vântul bate-n felinar"]
    result = count_syllables(lines=lines, target_syllables=[8])
    assert result["passed"] is True
    assert result["line_count"] == 2
    assert [ln["target_syllables"] for ln in result["lines"]] == [8, 8]
    assert set(result["lines"][0]) == {
        "line_index",
        "text",
        "actual_syllables",
        "target_syllables",
        "difference",
        "matched",
    }


def test_difference_sign_and_failure():
    result = count_syllables(["Pe strada veche plouă iar"], target_syllables=[7])
    line = result["lines"][0]
    assert result["passed"] is False
    assert line["difference"] == 1 and line["matched"] is False


def test_tolerance():
    result = count_syllables(
        ["Pe strada veche plouă iar"], target_syllables=[7], tolerance=1
    )
    assert result["passed"] is True


def test_no_targets_always_pass():
    result = count_syllables(["o linie oarecare"])
    assert result["passed"] is True
    assert result["lines"][0]["target_syllables"] is None
    assert result["lines"][0]["difference"] == 0


def test_lexicon_overrides_rules(tmp_path, monkeypatch):
    lexicon = tmp_path / "lex.tsv"
    lexicon.write_text("# word\tsyllables\nreal\tre-al\naici\t2\n", encoding="utf-8")
    monkeypatch.setenv(LEXICON_ENV, str(lexicon))
    _load_lexicon.cache_clear()
    try:
        assert count_word_syllables("real") == 2
        assert count_word_syllables("aici") == 2
        assert count_word_syllables("mare") == 2  # not in lexicon -> rules
    finally:
        monkeypatch.delenv(LEXICON_ENV)
        _load_lexicon.cache_clear()
