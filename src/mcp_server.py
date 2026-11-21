from typing import Any

from mcp.server.fastmcp import FastMCP

from src.tools.rhymes import check_rhyme
from src.tools.sentiment import analyze_sentiment
from src.tools.syllables import count_syllables

mcp = FastMCP("LMusic-Tools")


@mcp.tool()
def tool_count_syllables(
    lines: list[str], target_syllables: list[int] | None = None
) -> dict[str, Any]:
    """Count syllables per line in Romanian lyrics and report deviations from target counts."""
    return count_syllables(lines=lines, target_syllables=target_syllables)


@mcp.tool()
def tool_check_rhyme(lines: list[str], scheme: str) -> dict[str, Any]:
    """Verify whether a stanza matches a target rhyme scheme (e.g., AABB, ABAB) and return failed pairs."""
    return check_rhyme(lines=lines, scheme=scheme)


@mcp.tool()
def tool_analyze_sentiment(text: str, target_mood: str | None = None) -> dict[str, Any]:
    """Advisory check for the emotional tone of generated Romanian lyrics."""
    return analyze_sentiment(text=text, target_mood=target_mood)


if __name__ == "__main__":
    mcp.run()