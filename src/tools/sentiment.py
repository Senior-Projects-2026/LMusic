from typing import Any


def analyze_sentiment(text: str, target_mood: str | None = None) -> dict[str, Any]:
    """
    Advisory emotional tone evaluator for generated Romanian lyrics.

    Args:
        text: Full stanza or lyric passage to evaluate.
        target_mood: Optional desired mood/theme (e.g., "melancolic", "energic", "club").

    Returns:
        Advisory tone breakdown (does not block the ReAct loop).
    """
    lowered = text.lower()
    melancholic_cues = ("ploaie", "noapte", "dor", "singur", "lacrimi", "toamnă", "rece")
    energetic_cues = ("dans", "lumină", "foc", "sus", "vară", "ritm", "zbor")

    mel_score = sum(1 for word in melancholic_cues if word in lowered)
    eng_score = sum(1 for word in energetic_cues if word in lowered)

    if mel_score > eng_score:
        detected = "melancolic"
    elif eng_score > mel_score:
        detected = "energic"
    else:
        detected = "neutru"

    return {
        "advisory": True,
        "detected_mood": detected,
        "target_mood": target_mood,
        "aligned": (target_mood.lower() == detected) if target_mood else True,
    }