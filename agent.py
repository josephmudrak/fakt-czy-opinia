import json
import os

from dotenv import load_dotenv
from google.adk.agents import Agent, LlmAgent
from google.adk.runners import Runner
from google.genai import Client
from google.genai.types import Content, Part

from text import normalise


load_dotenv()

google_api_key: str | None = os.getenv("GOOGLE_API_KEY")

if not google_api_key:
    raise ValueError("Environment variable GOOGLE_API_KEY not set")

client: Client = Client(api_key=google_api_key)

MODEL_GEMINI_2_0_FLASH: str = "gemini-2.0-flash"


async def call_agent_async(
    query: str, runner: Runner, user_id: str, session_id: str
) -> str | None:
    """
    Calls the agent asynchronously with the provided query and session details.

    Args:
        query (str): The input query to send to the agent.
        runner (Runner): The runner instance for executing the agent.
        user_id (str): The user ID for the session.
        session_id (str): The session ID for the session.
    """

    content: Content = Content(role="user", parts=[Part(text=query)])
    final_text: str | None = "No response from agent"  # Default

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text
            elif event.actions and event.actions.escalate:
                final_text = (
                    "Agent escalated: "
                    f"{event.error_message or 'No message provided'}"
                )
            break

    if not final_text:
        raise ValueError("No final response from agent")
    else:
        return final_text


def evaluate(text: str) -> dict | None:
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

    if not response.text:
        raise ValueError("No response text from Gemini")
    else:
        return json.loads(normalise(response.text))


fact_or_opinion: LlmAgent = LlmAgent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="fact_or_opinion",
    description="Extracts objective facts and subjective opinions from text.",
    instruction="""
        You are an agent that distinguishes between objective facts and
        subjective opinions in text. Use the 'evaluate' tool to parse the
        input text. Then, use the 'normalise' tool to remove any artifacts from
        Gemini, such as Markdown commands, and ensure the output is coherent.
        Once completed, return a JSON object with your findings in the following
        format:
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
        DO NOT use Markdown formatting in your response. Instead, use the
        'normalise' tool to clean up the output.""",
    tools=[evaluate, normalise],
)

if fact_or_opinion:
    root_model: str = MODEL_GEMINI_2_0_FLASH

    fact_or_opinion_team: Agent = Agent(
        name="fact_or_opinion_root",
        model=root_model,
        description="Main coordinator agent.",
        instruction=(
            "You are the primary coordinator agent that the user will interact "
            "with. Your ONLY role is to manage the 'fact_or_opinion' agent."
            "Delegate the task of evaluating an input string to the "
            "'fact_or_opinion' agent, and return the results in JSON format. "
            "In any other case, respond appropriately or state that you cannot "
            "handle the request, or that it is somehow invalid."
        ),
        sub_agents=[fact_or_opinion],
    )
else:
    raise ValueError("Failed to create root agent")

root_agent: Agent = fact_or_opinion_team
