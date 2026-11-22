"""Controlled, team-authored fixtures; no external RoLEX download required.

These annotations exercise specific readings, not a comprehensive dictionary.
In particular, casa/masa noun readings here are intentionally unambiguous.
"""

import unicodedata

import pytest

from src.tools.rhymes import (
    _extract_rhyme_tail,
    _load_lexicon,
    _tail_from_entry,
    check_rhyme,
)


@pytest.fixture(autouse=True)
def lexicon(tmp_path, monkeypatch):
    entries = [
        ("casă", "ca.să", "c'asă", "k a s @"),
        ("masă", "ma.să", "m'asă", "m a s @"),
        ("frumoasă", "fru.moa.să", "frumo'asă", "f r u m o_X a s @"),
        ("mare", "ma.re", "m'are", "m a r e"),
        ("cărare", "că.ra.re", "căr'are", "k @ r a r e"),
        ("iubire", "iu.bi.re", "iub'ire", "j u b i r e"),
        ("fericire", "fe.ri.ci.re", "feric'ire", "f e r i tS i r e"),
        ("tăcuți", "tă.cuți", "tăc'uți", "t @ k u ts i_0"),
        ("pierduți", "pier.duți", "pierd'uți", "p j e r d u ts i_0"),
        ("liniștit", "li.niș.tit", "linișt'it", "l i n i S t i t"),
        ("oprit", "o.prit", "opr'it", "o p r i t"),
        ("lac", "lac", "lac", "l a k"),
        ("suflă", "su.flă", "s'uflă", "s u f l @"),
        ("suflă", "su.flă", "sufl'ă", "s u f l @"),
    ]
    path = tmp_path / "controlled.tsv"
    path.write_text(
        "\n".join(
            f"{word}\t=\tTEST\t{syllables}\t{stress}\t{phones}"
            for word, syllables, stress, phones in entries
        ),
        encoding="utf-8-sig",
    )
    monkeypatch.setenv("LMUSIC_ROLEX_PATH", str(path))
    _load_lexicon.cache_clear()
    yield path
    _load_lexicon.cache_clear()


@pytest.mark.parametrize(
    "word,tail",
    [
        ("casă", "a s @"),
        ("frumoasă", "a s @"),
        ("iubire", "i r e"),
        ("pierduți", "u ts i_0"),
        ("lac", "a k"),
    ],
)
def test_stressed_tail(word, tail):
    assert _extract_rhyme_tail(word) == tail


@pytest.mark.parametrize(
    "lines,scheme",
    [
        (["casă", "masă"], "AA"),
        (["iubire", "fericire"], "AA"),
        (["tăcuți", "pierduți", "mare", "cărare"], "AABB"),
        (["mare", "oprit", "cărare", "liniștit"], "ABAB"),
    ],
)
def test_matching_schemes(lines, scheme):
    result = check_rhyme(lines, scheme)
    assert result["passed"] is True
    assert result["failed_pairs"] == []
    assert set(result) == {"passed", "scheme", "endings", "failed_pairs"}


def test_same_last_letters_do_not_prove_rhyme():
    result = check_rhyme(["mare", "fericire"], "AA")
    assert result["passed"] is False
    assert result["endings"] == ["a r e", "i r e"]
    assert result["failed_pairs"] == [
        {
            "label": "A",
            "expected_line": 0,
            "actual_line": 1,
            "expected_ending": "a r e",
            "actual_ending": "i r e",
        }
    ]


def test_noun_readings_casa_and_frumoasa_do_rhyme():
    # The stressed nucleus is /a/; the preceding /o_X/ glide is outside the tail.
    assert check_rhyme(["casă", "frumoasă"], "AA")["passed"] is True


@pytest.mark.parametrize("word", ["LiniŞTIT!!!", "Un vers liniștit…", "liniștit"])
def test_normalization_and_final_word(word):
    assert _extract_rhyme_tail(word) == "i t"


def test_decomposed_unicode():
    assert _extract_rhyme_tail(unicodedata.normalize("NFD", "tăcuți")) == "u ts i_0"


@pytest.mark.parametrize("word", ["", "...", "123", "necunoscutxyz", "suflă"])
def test_unresolved_words_cannot_pass(word):
    result = check_rhyme([word, word], "AA")
    assert result["passed"] is False
    assert result["endings"] == ["", ""]
    assert not check_rhyme([word], "A")["passed"]


@pytest.mark.parametrize(
    "syllables,stress,phones",
    [
        ("ma.re", "mare", "m a r e"),  # Missing multisyllabic stress.
        ("ma.re", "m'are", "m a r"),  # Wrong nucleus count.
        ("ma.re", "m'are", "m o r e"),  # Wrong stressed vowel identity.
        ("ma.re", "m'ar'e", "m a r e"),
        ("ma.re", "m'are", "m a UNKNOWN e"),
        ("ma.re", "m'ase", "m a s e"),
    ],
)
def test_inconsistent_annotations_remain_unresolved(syllables, stress, phones):
    assert _tail_from_entry(syllables, stress, phones) == ""


@pytest.mark.parametrize("first,second", [("t", "d"), ("p", "b"), ("s", "z")])
def test_voicing_is_not_collapsed(first, second):
    assert _tail_from_entry("at", "'at", f"a {first}") != _tail_from_entry(
        "at", "'at", f"a {second}"
    )


def test_duplicate_readings_do_not_create_ambiguity(lexicon):
    with lexicon.open("a", encoding="utf-8") as output:
        output.write("\nmare\t=\tTEST\tma.re\tm'are\tm a r e\n")
    assert _extract_rhyme_tail("mare") == "a r e"


def test_failed_alignment_does_not_disappear_from_variants(lexicon):
    with lexicon.open("a", encoding="utf-8") as output:
        output.write("\nmare\t=\tTEST\tma.re\tmare\tm a r e\n")
    assert _extract_rhyme_tail("mare") == ""


@pytest.mark.parametrize("content", ["", "only\ttwo", b"\xff"])
def test_invalid_lexicon_returns_setup_error(lexicon, content):
    if isinstance(content, bytes):
        lexicon.write_bytes(content)
    else:
        lexicon.write_text(content, encoding="utf-8")
    result = check_rhyme(["mare", "cărare"], "AA")
    assert result["passed"] is False
    assert "RoLEX setup error" in result["error"]
    assert result["endings"] == result["failed_pairs"] == []


def test_missing_lexicon_returns_setup_error(lexicon):
    lexicon.unlink()
    assert "RoLEX setup error" in check_rhyme(["mare"], "A")["error"]


def test_invalid_line_count_does_not_require_lexicon(lexicon):
    lexicon.unlink()
    result = check_rhyme(["mare"], "AA")
    assert result["passed"] is False
    assert "Line count" in result["error"]


def test_empty_stanza_does_not_pass():
    assert check_rhyme([], "")["passed"] is False


def test_scheme_normalization_and_distinct_label_policy():
    assert check_rhyme(["mare", "cărare"], " aa ")["scheme"] == "AA"
    # Preserve the existing policy: different labels may share a tail.
    assert check_rhyme(["mare", "cărare"], "AB")["passed"] is True
