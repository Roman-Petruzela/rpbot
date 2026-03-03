"""
Hlavní entry point Discord bota - modulární struktura s Cogs
"""
import discord
from discord.ext import commands
import asyncio
from pathlib import Path
import json
import os
import sys


def load_config():
    config_path = Path(__file__).parent / "config.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_content():
    content_path = Path(__file__).parent / "content.json"
    with open(content_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_discord_token():
    token_path = Path(__file__).parent / "token"
    if not token_path.exists():
        raise FileNotFoundError("Token file was not found. Create a file named 'token' in the project root.")

    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("Token file is empty.")

    return token


CONFIG = load_config()
CONTENT = load_content()
DISCORD_TOKEN = load_discord_token()
COMMAND_PREFIX = CONFIG["command_prefix"]
RESTART_REQUESTED = False


# Nastavení intentů
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Vytvoření bot instance
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)
bot.config = CONFIG
bot.content = CONTENT


@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user}')
    print(f'Bot ID: {bot.user.id}')
    print('------')


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    raw_allowed_channels = bot.config.get("allowed_channels", [])
    if isinstance(raw_allowed_channels, int):
        raw_allowed_channels = [raw_allowed_channels]

    if raw_allowed_channels == []:
        await bot.process_commands(message)
        return
    
    allowed_channel_ids = {int(channel_id) for channel_id in raw_allowed_channels}
    if message.channel.id not in allowed_channel_ids:
        return

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    """Globální error handler"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("This command is restricted to administrators.")
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("This command cannot be used in private messages.")
    elif isinstance(error, (commands.ChannelNotFound)):
        await ctx.send("Invalid channel.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignorujeme neexistující příkazy
    else:
        raise error

async def load_cogs():
    """Načte všechny Cogs moduly ze složky cogs (včetně podsložek)."""
    base_dir = Path(__file__).parent / "cogs"

    for file in sorted(base_dir.rglob("*.py")):
        # přeskočí __init__.py a "privátní" soubory
        if file.name == "__init__.py" or file.name.startswith("_"):
            continue

        rel = file.relative_to(Path(__file__).parent).with_suffix("")
        module = ".".join(rel.parts)  # např. cogs.music nebo cogs.admin.moderation

        try:
            await bot.load_extension(module)
            print(f"Loaded: {module}")
        except Exception as e:
            print(f"Error loading {module}: {e}")

async def main():
    """Hlavní asynchronní funkce"""
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    """Restartuje bota"""
    global RESTART_REQUESTED
    RESTART_REQUESTED = True
    await ctx.send("Restarting bot...")
    await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
    if RESTART_REQUESTED:
        print("Restart requested, restarting bot...")
        os.execv(sys.executable, [sys.executable, *sys.argv])
