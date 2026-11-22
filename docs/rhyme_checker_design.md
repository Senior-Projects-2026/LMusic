# Romanian rhyme checker

## Setup (once per computer)

1. Download the [official RoLEX archive](https://www.racai.ro/p/reterom/rapoarte/lexicon_reterom_final.zip).
2. Extract the original file to `data/raw/rolex/lexicon_reterom_final.txt`.
   Keep its six-column UTF-8 format unchanged. This directory is ignored by Git;
   each developer must download the resource separately.
3. Activate the project's virtual environment and run commands from the repository root.

For a different location, set this variable before starting Python or MCP:

```powershell
$env:LMUSIC_ROLEX_PATH = "C:\path\to\lexicon_reterom_final.txt"
```

The lexicon is cached in memory. Restart Python/the MCP server after replacing it.
No network access is needed during rhyme checks.

## Usage and results

```powershell
python -c "from src.tools.rhymes import check_rhyme; print(check_rhyme(['mare', 'cărare'], 'AA'))"
```

The existing MCP tool `tool_check_rhyme(lines, scheme)` uses the same function.
For each final word, the checker aligns the annotated stressed syllable with the
phonetic vowels, then compares sounds from the stressed vowel to the word's end.
It normalizes case and Romanian Unicode variants and preserves voicing differences.

| Result field | Meaning |
|---|---|
| `passed` | All endings are resolved and same-label rhyme checks pass |
| `scheme` | Requested scheme, trimmed and uppercased |
| `endings` | Phonetic tails as SAMPA tokens; the example returns `a r e` twice |
| `failed_pairs` | Unsatisfied same-label comparisons, with zero-based line indices |
| `error` | Present for a lexicon setup error or a line-count mismatch |

Unknown words, ambiguous rhyme tails, or inconsistent annotations return an empty
ending and prevent a pass. This means **not verified**, not necessarily **not
rhyming**. For example, `casă` has noun and verb readings with different stress;
this checker does not disambiguate meaning from context. Different scheme labels
are not required to have different sounds. This is a strict, lexicon-based checker,
not an all-words pronunciation model or an approximate-rhyme detector.

## Tests

Unit tests use temporary, team-authored fixtures, without downloading RoLEX:

```powershell
python -m pytest tests/test_rhymes.py -v
```

Integration tests also require the complete local lexicon and the project's MCP
1.x dependency (`mcp[cli]>=1.2.0,<2.0.0`):

```powershell
python -m pytest tests/test_rhymes.py tests/test_mcp_server.py -v
```

Validated for this change: **38 rhyme tests + 5 MCP tests passed**. Tests cover
stress alignment, rhyme schemes, Unicode, ambiguity, and setup errors; passing
these cases does not establish general linguistic accuracy.

## Resource attribution

[RACAI's resource page](https://www.racai.ro/p/llod/index_en.html) lists RoLEX
under **CC BY-NC-ND 4.0**. Follow the source terms and retain attribution; do not
commit the downloaded lexicon or a transformed dictionary to this repository.

Beáta Lőrincz, Elena Irimia, Adriana Stan, Verginica Barbu Mititelu,
*RoLEX: The development of an extended Romanian lexical dataset and its evaluation
at predicting concurrent lexical information*. See the
[authors' description and citation](https://github.com/adrianastan/rolex).
