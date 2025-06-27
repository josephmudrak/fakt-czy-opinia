# text.py
# Text processing tasks
import re


def normalise(text: str) -> str:
    """
    Normalises the input text by removing unnecessary whitespace and artifacts
    from Gemini.
    Args:
        text (str): The input text to normalise.
    Returns:
        str: The normalised text.
    """

    return re.sub(r"^```(?:json)?\n|\n```$", "", text.strip())
