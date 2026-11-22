# Romanian rhyme checker: implementation plan

## Existing contract

Keep `check_rhyme(lines: list[str], scheme: str)` and the MCP wrapper unchanged.
Preserve the existing response keys (`passed`, `scheme`, `endings`,
`failed_pairs`, and `error` for invalid line counts), including zero-based pair
indices. The current extractor removes word boundaries and compares only the
last two letters; it does not determine pronunciation or stress.

## Resource findings

No pronunciation or stress lexicon is currently included in this repository.
[RoLEX](https://github.com/adrianastan/rolex) provides 330,866 entries according
to its authors. Although that GitHub README does not state a license,
[RACAI's RoLLOD resource page](https://www.racai.ro/p/llod/index_en.html)
explicitly lists its RoLEX resource under CC BY-NC-ND 4.0. Use the official
RACAI distribution locally, retain its attribution and terms, and do not commit
a transformed dataset or assume the same terms automatically apply to a
different mirror. The implementation will read the original local file and
compute results in memory for the noncommercial course project.

The GitHub tabular sample was inspected on 22 November 2026: UTF-8 with a BOM,
tab-separated columns for word form, lemma, MSD tag, syllabification, stress-marked
spelling, and space-separated phonetic tokens. An apostrophe precedes the stressed
vowel in inspected multisyllabic entries; monosyllables may have no marker.
Phonetic tokens include multicharacter symbols, so character indexing is unsafe.
The official archive must be inspected as well before fixing the parser format.
Stress must be aligned from the spelling/syllabification fields to the phonetic
vowel nucleus, with explicit treatment of glides and nonsyllabic final `i`.

Alternative: [MaRePhoR](https://speech.utcluj.ro/marephor/) has 72,375 entries
and an explicit CC BY-NC 3.0 license, with attribution and citation requirements.
It is smaller; its stress information must be inspected before treating it as a
replacement. A [published Romanian G2P implementation](https://github.com/speech-utcluj/romanian-phonetic-transcription)
is also available under GPL-3.0, but is not a validated drop-in stress predictor.
No trained fallback model is selected or claimed to work at this stage.

Romanian does not have a general rule making final voiced and voiceless
consonants interchangeable. See the authors' study of
[Romanian devoicing](https://pure.mpg.de/rest/items/item_527002_2/component/file_527001/content).
Consequently, blindly merging `t/d`, `p/b`, or `s/z` would introduce false
positives. Such substitutions would be an optional approximate-rhyme policy,
not part of the initial strict checker.

## Selected approach for the first implementation

1. Extract the final word rather than concatenating all letters in the line.
   Normalize Unicode, case, and legacy Romanian cedilla characters (`ş/ţ`),
   while preserving meaningful distinctions such as `s/ș` and `t/ț`.
2. Load the full, externally supplied RoLEX lexicon from a configurable local
   path and cache its index. Keep data acquisition separate from tool calls:
   no per-word network requests or silent downloads. Deduplicate identical
   pronunciations while retaining genuinely different stress/pronunciation
   variants. Use small team-authored entries only as parser/test fixtures,
   not as the production vocabulary. Report a missing lexicon as a setup error,
   rather than silently substituting a tiny dictionary.
3. Compare normalized phonetic tails, including all sounds following the stressed
   vowel. Normalize genuine alternate spellings of the same sound (such as
   Romanian `â/î` in a phonetic representation); preserve voiced/unvoiced pairs.
   Multiple attested pronunciations must not be silently resolved arbitrarily.
4. For an unknown or ambiguous final word, return an empty tail. A required
   same-label pair containing an empty tail fails conservatively. Under the
   unchanged contract, this means "not verified", not proof of a non-rhyme.
   Document this distinction for callers; richer per-line uncertainty reporting
   would require a separately agreed contract extension.
5. Preserve the current same-label grouping behavior. Enforcing that different
   scheme labels must have different sounds is outside this change.

The selected design is a large-lexicon checker with a conservative unknown-word
fallback, not an all-words pronunciation engine. Names, slang, missing inflected
forms, and context-dependent stress can remain unresolved. A learned fallback
would require a separate held-out evaluation of both stress and rhyme tails
before enabling it; phoneme prediction alone is insufficient. Measure lexical
coverage on final words in the Golden Dataset and available baseline outputs,
reporting known, unknown, ambiguous, and alignment-failure counts separately.

## Validation in the following stages

- Preserve the existing MCP examples: `tăcuți/pierduți`, `mare/cărare`, and
  `liniștit/oprit`.
- Check positive pairs (`casă/masă`, `iubire/fericire`) and a negative pair with
  the same last two letters (`casă/frumoasă`).
- Check punctuation, capitalization, Unicode variants, blank lines, unknown
  words, ambiguous pronunciations, and invalid line counts.
- Exercise AABB and ABAB grouping and preserve the dictionary contract.
- Check that voiced/unvoiced differences are not collapsed in strict comparison.

Stage 1 only records the design. Stage 2 inspects the official archive and implements
local lexicon loading, stress-to-phoneme alignment, and extraction; Stage 3 adds
dedicated tests and a coverage measurement; Stage 4 documents actual usage and runs
the final integration checks. No model, syllable-counter, or MCP-server changes
are needed for Stage 1.

## Stage 2: local setup and observed behavior

The official [RACAI archive](https://www.racai.ro/p/reterom/rapoarte/lexicon_reterom_final.zip)
was inspected: `lexicon_reterom_final.txt` has 330,866 six-column rows. The code
reads this original file without creating a redistributed derivative lexicon.
Attribution: Beáta Lőrincz, Elena Irimia, Adriana Stan, Verginica Barbu Mititelu,
*RoLEX: The development of an extended Romanian lexical dataset and its evaluation
at predicting concurrent lexical information*. See the resource links above for
the authors' citation and applicable CC BY-NC-ND 4.0 terms.

Download and unzip the archive locally. Default file location:
`data/raw/rolex/lexicon_reterom_final.txt` (`data/raw/` is ignored by Git).
For a different location, set the environment variable before starting Python
or the MCP server:

```powershell
$env:LMUSIC_ROLEX_PATH = "C:\path\to\lexicon_reterom_final.txt"
```

No extra Python dependencies are required. The lexicon is indexed once per path
and cached; restart the process after replacing the file. A missing, empty, or
structurally malformed file returns a setup error through the existing error
response shape. Unknown, ambiguous, or unalignable words have empty endings and
cannot pass verification, including when their scheme label occurs only once.

Alignment uses the stressed spelling to locate the syllable, then selects the
corresponding SAMPA vowel nucleus. It checks matching vowel identity and equal
syllable/nucleus counts. Unsupported phones or inconsistent annotations remain
unresolved. This is a guarded alignment procedure, not a claim that all source
annotations or resulting tails are correct.

Important validation refinement: RoLEX includes both noun and verb readings of
`casă` and `masă`, with different stressed tails. Without part-of-speech/context
disambiguation, these words intentionally remain unresolved. Use their noun
readings as isolated parser fixtures later, not as unambiguous full-lexicon
positive cases. `casă/frumoasă` is therefore not a reliable negative-only example
either: the verb reading can have the same tail. This illustrates why last-two-
letter matching and silent pronunciation selection are inadequate.
