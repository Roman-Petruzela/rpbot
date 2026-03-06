import discord
from discord.ext import commands
import asyncio
from pathlib import Path
import json
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rpbot")

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


async def send_log(message: str):
    log_channel_id = bot.config.get("log_channel_id")
    if not log_channel_id:
        return

    try:
        channel_id = int(log_channel_id)
    except (TypeError, ValueError):
        logger.warning("Invalid log_channel_id in config: %s", log_channel_id)
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            logger.warning("Unable to fetch log channel: %s", channel_id)
            return

    if isinstance(channel, (discord.TextChannel, discord.Thread)):
        try:
            await channel.send(message)
        except (discord.Forbidden, discord.HTTPException):
            logger.warning("Unable to send message to log channel: %s", channel_id)


bot.send_log = send_log


@bot.event
async def on_ready():
    print(f'Logged in as: {bot.user}')
    print(f'Bot ID: {bot.user.id}')
    print('------')
    await send_log(f"Bot is online as **{bot.user}** (ID: `{bot.user.id}`).")


@bot.event
async def on_command(ctx):
    await send_log(
        f"Command `{ctx.command}` used by **{ctx.author}** in {ctx.channel.mention}."
    )


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ctx = await bot.get_context(message)

    # Admin cog commands are allowed in any text channel.
    if ctx.command and getattr(ctx.command, "cog_name", None) == "Admin":
        await bot.invoke(ctx)
        return

    raw_allowed_channels = bot.config.get("allowed_channels", [])
    if isinstance(raw_allowed_channels, int):
        raw_allowed_channels = [raw_allowed_channels]

    if raw_allowed_channels == []:
        await bot.invoke(ctx)
        return
    
    allowed_channel_ids = {int(channel_id) for channel_id in raw_allowed_channels}
    if message.channel.id not in allowed_channel_ids:
        return

    await bot.invoke(ctx)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("This command is restricted to administrators.")
        await send_log(
            f"Missing permissions: **{ctx.author}** tried `{ctx.command}` in {ctx.channel.mention}."
        )
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("This command cannot be used in private messages.")
        await send_log(f"Blocked DM command `{ctx.command}` by **{ctx.author}**.")
    elif isinstance(error, (commands.ChannelNotFound)):
        await ctx.send("Invalid channel.")
        await send_log(
            f"Invalid channel argument in `{ctx.command}` by **{ctx.author}**."
        )
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await send_log(
            f"Unhandled error in `{ctx.command}` by **{ctx.author}**: `{error}`"
        )
        raise error

async def load_cogs():
    base_dir = Path(__file__).parent / "cogs"

    for file in sorted(base_dir.rglob("*.py")):
        if file.name == "__init__.py" or file.name.startswith("_"):
            continue

        rel = file.relative_to(Path(__file__).parent).with_suffix("")
        module = ".".join(rel.parts)

        try:
            await bot.load_extension(module)
            print(f"Loaded: {module}")
        except Exception as e:
            print(f"Error loading {module}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    global RESTART_REQUESTED
    RESTART_REQUESTED = True
    await ctx.send("Restarting bot...")
    await send_log(f"Restart requested by **{ctx.author}**.")
    await bot.close()
    
@bot.command()
@commands.has_permissions(administrator=True)
async def end(ctx):
    await ctx.send("Closing bot...")
    await send_log(f"Shutdown requested by **{ctx.author}**.")
    await bot.close()


if __name__ == '__main__':
    asyncio.run(main())
    if RESTART_REQUESTED:
        print("Restart requested, restarting bot...")
        os.execv(sys.executable, [sys.executable, *sys.argv])
