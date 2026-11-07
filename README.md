# MuseLM / HitMaker AI 🎵

An LLM Agent designed for generating and refining song lyrics using RAG techniques, a custom MCP server, and SLM fine-tuning.

## Development Team Setup

All team members must use a virtual environment (venv) to avoid package conflicts. Follow the steps below:

### 1. Clone the repository
```bash
git clone https://github.com/Senior-Projects-2026/LMusic.git
cd LMusic
```

### 2. Create and activate the virtual environment (venv)
**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**On Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
*(When the venv is activated, you will see `(venv)` at the beginning of the command line).*

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Use the linter/formatter (Ruff)
To maintain clean code before committing, run these two commands in your terminal:
```bash
# Automatically format the code
ruff format .

# Check and fix syntax errors or unused imports
ruff check . --fix
```

## Stanza ingestion prototype (Issue #5)

This prototype reads one UTF-8 TXT file per song, removes standalone bracketed
section labels (such as `[Verse 1]` and `[Chorus]`) and HTML tags, normalizes
whitespace, and splits lyrics at blank lines or section labels. It preserves
line breaks within each stanza and Romanian diacritics.

Run from the repository root (Python 3.10+, no additional dependencies):

```powershell
python src/ingest_data.py data/examples/demo_lyrics.txt --song-id demo-1 --genre pop --output data/processed/demo_stanzas.json
```

The sample contains original demonstration lyrics created for this repository;
it is not a commercial song or a verified rhyme/syllable reference. It produces
three records containing `text` and `metadata` (`song_id`, `genre`, zero-based
`stanza_index`, and `source`). Genre is caller-supplied mock metadata, not an
automatically inferred annotation. Pass another input path and song ID to ingest
a new song without changing the code. The output file is replaced on each run.

Scope: this is a cleaning/chunking prototype. CSV/JSON input, embeddings, vector
database insertion, license validation, and deduplication are not implemented
yet. It does not modify `data/golden_dataset.json`.
