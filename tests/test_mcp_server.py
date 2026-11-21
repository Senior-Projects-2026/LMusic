import asyncio
import json

from src.mcp_server import mcp
from src.tools.rhymes import check_rhyme
from src.tools.sentiment import analyze_sentiment
from src.tools.syllables import count_syllables


def test_mcp_tools_registered():
    tools = asyncio.run(mcp.list_tools())
    tool_names = {tool.name for tool in tools}
    assert {
        "tool_count_syllables",
        "tool_check_rhyme",
        "tool_analyze_sentiment",
    }.issubset(tool_names)


def test_syllable_tool_contract():
    lines = ["Pe strada veche plouă iar", "Și vântul bate-n felinar"]
    result = count_syllables(lines=lines, target_syllables=[8, 8])
    assert "passed" in result
    assert "lines" in result
    assert len(result["lines"]) == 2
    assert set(result["lines"][0].keys()) == {
        "line_index",
        "text",
        "actual_syllables",
        "target_syllables",
        "difference",
        "matched",
    }


def test_rhyme_tool_contract():
    lines = [
        "Sub clar de lună stăm tăcuți",
        "De gânduri vechi suntem pierduți",
        "Iar vântul suflă peste mare",
        "Și stinge ultima cărare",
    ]
    result = check_rhyme(lines=lines, scheme="AABB")
    assert result["passed"] is True
    assert result["scheme"] == "AABB"
    assert result["failed_pairs"] == []


def test_rhyme_tool_detects_mismatch():
    lines = [
        "Sub clar de lună stăm tăcuți",
        "Iar vântul suflă peste mare",
    ]
    result = check_rhyme(lines=lines, scheme="AA")
    assert result["passed"] is False
    assert len(result["failed_pairs"]) == 1


def test_mcp_protocol_invocation():
    _, payload = asyncio.run(
        mcp.call_tool(
            "tool_check_rhyme",
            {
                "lines": ["Afară ninge liniștit", "Și visul nostru s-a oprit"],
                "scheme": "AA",
            },
        )
    )
    assert payload["passed"] is True

    _, sentiment_payload = asyncio.run(
        mcp.call_tool(
            "tool_analyze_sentiment",
            {"text": "Ploaie rece în noapte și dor", "target_mood": "melancolic"},
        )
    )
    assert sentiment_payload["advisory"] is True
    assert sentiment_payload["detected_mood"] == "melancolic"