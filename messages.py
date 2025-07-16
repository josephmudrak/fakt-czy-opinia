# messages.py
# Receive messages from Discord

import discord
import os

from agent import call_agent_async, root_agent
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService


load_dotenv()


BOT_TOKEN: str | None = os.getenv("DISCORD_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Discord bot token not set")

intents: discord.Intents = discord.Intents.default()
intents.message_content = True

client: discord.Client = discord.Client(intents=intents)

app_name: str = "fact_or_opinion"
session_service: InMemorySessionService = InMemorySessionService()

runner: Runner = Runner(
    agent=root_agent, app_name=app_name, session_service=session_service
)

# Sessions already read
_seen_sessions: set[str] = set()


@client.event
async def on_ready():
    """
    Bot has been initialised successfully.
    """
    print(f"Logged on as {client.user}")


@client.event
async def on_message(message) -> str | None:
    """
    Returns the content of each new message in a Discord channel.

    Args:
        message: The message object.

    Returns:
        message.content (str): The content of the message. If the message is
        from the bot itself, it will be `None`.
    """
    if message.author == client.user:
        # Message is from the bot itself - ignore
        return

    user_id: str = str(message.author.id)
    session_id = str(message.channel.id)

    key: str = f"{user_id}::{session_id}"

    if key not in _seen_sessions:
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        _seen_sessions.add(key)

    query: str = message.content

    try:
        agent_json: str | None = await call_agent_async(
            query, runner, user_id, session_id
        )

        if agent_json:
            await message.channel.send(agent_json)
        else:
            await message.channel.send("No response from agent")
    except Exception as e:
        await message.channel.send(f"Agent error: {e}")


client.run(BOT_TOKEN)
