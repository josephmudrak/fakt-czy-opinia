import os

from dotenv import load_dotenv
from google import genai
from google.adk.agents import LlmAgent


load_dotenv()

google_api_key: str | None = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise ValueError("Environment variable GOOGLE_API_KEY not set")

client: genai.Client = genai.Client(api_key=google_api_key)

MODEL_GEMINI_2_0_FLASH: str = "gemini-2.0-flash"


def evaluate(text: str) -> None:
    """
    Evaluates the input text to determine if it contains objective facts or
    subjective opinions.

    Args:
        text (str): The input text to evaluate.
    Returns:
        dict: A dictionary containing the evaluation results with confidence
        scores.
    """

    response = client.models.generate_content(
        model=MODEL_GEMINI_2_0_FLASH,
        contents=(
            "Evaluate the following text to determine if it contains objective "
            "facts or subjective opinions. \n\n"
            f"{text}\n\n"
            "Provide a JSON response with confidence scores for each "
            "identified fact and opinion, in the following format:\n"
            "{"
            '  "facts": ['
            "    {"
            '      "text": "The sky is blue.",'
            '      "confidence": 0.95'
            "    }"
            "    {"
            '      "text": "2 plus 2 equals 4.",'
            '      "confidence": 0.98'
            "    }"
            "  ],"
            '  "opinions": ['
            "    {"
            '      "text": "I think the sky is beautiful.",'
            '      "confidence": 0.90'
            "    },"
            "    {"
            '      "text": "In my opinion, chocolate is the best flavor.",'
            '      "confidence": 0.85'
            "    }"
            "  ]"
            "}"
        ),
    )

    print(response.text)


fact_or_opinion_agent: LlmAgent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="fact_or_opinion_agent",
    description="Extracts objective facts and subjective opinions from text.",
    instruction="""
        You are an agent that distinguishes between objective facts and
        subjective opinions in text. Use the 'evaluate' tool to parse the
        input text. Once completed, return a JSON object with your findings in
        the following format:
        {
            "facts": [
                {
                    "text": "The sky is blue.",
                    "confidence": 0.95
                }
                {
                    "text": "2 plus 2 equals 4.",
                    "confidence": 0.98
                }
            ],
            "opinions": [
                {
                    "text": "I think the sky is beautiful.",
                    "confidence": 0.90
                },
                {
                    "text": "In my opinion, chocolate is the best flavor.",
                    "confidence": 0.85
                }
            ]
        }
        """,
    tools=[evaluate],
)
