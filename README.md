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