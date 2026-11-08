"""Convert a UTF-8 lyrics file into stanza records with mock metadata."""

import argparse
import json
import re
from pathlib import Path


def split_stanzas(text: str) -> list[str]:
    """Keep line boundaries; blank lines and section markers end a stanza."""
    stanzas = []
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        # Standalone section labels are boundaries, not lyric content.
        if not line or re.fullmatch(r"\[[^\[\]]+\]", line):
            if lines:
                stanzas.append("\n".join(lines))
                lines = []
            continue
        # Strip HTML markup while retaining the words it surrounds.
        line = re.sub(r"<[^>]+>", "", line)
        line = " ".join(line.split())
        if line:
            lines.append(line)
    if lines:
        stanzas.append("\n".join(lines))
    return stanzas


def ingest_file(input_path: Path, song_id: str, genre: str) -> list[dict]:
    """Read one song and attach caller-supplied metadata to each stanza."""
    text = input_path.read_text(encoding="utf-8-sig")
    stanzas = split_stanzas(text)
    if not stanzas:
        raise ValueError("The input contains no lyric stanzas.")
    return [
        {
            "text": stanza,
            "metadata": {
                "song_id": song_id,
                "genre": genre,
                "stanza_index": index,
                "source": input_path.name,
            },
        }
        for index, stanza in enumerate(stanzas)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 TXT file containing one song")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON file")
    parser.add_argument("--song-id", required=True, help="Identifier for this song")
    parser.add_argument("--genre", default="unknown", help="Mock genre metadata")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must be different files.")
    try:
        records = ingest_file(args.input, args.song_id, args.genre)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"Ingestion failed: {error}\n")
    print(f"Saved {len(records)} stanzas to {args.output}")


if __name__ == "__main__":
    main()
