# messages.py
# Receive messages from Discord

import discord
import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN: str | None = os.getenv("DISCORD_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Discord bot token not set")

intents: discord.Intents = discord.Intents.default()
intents.message_content = True

client: discord.Client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged on as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    return message.content


client.run(BOT_TOKEN)
