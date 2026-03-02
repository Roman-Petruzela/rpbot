# rpbot

A lightweight Discord bot written in Python using `discord.py` with a modular Cog-based structure.

## Features
- **Admin commands**: send server rules, bulk-assign roles, manage allowed text channels.
- **Music commands**: play audio from YouTube URLs, stop, skip, and adjust volume.
- **Fun commands**: meme/sound effects and small random commands.

## Project Structure
- `main.py` – bot entry point, config/content loading, event handlers, cog loading.
- `cogs/` – command modules (`admin.py`, `music.py`, `fun.py`, `test.py`).
- `config.json` – bot token, command prefix, allowed channels, yt-dlp/ffmpeg options.
- `content.json` – text content and file paths used by commands.
- `sources/` – static media files (audio and images).

## Requirements
- Python 3.10+
- `discord.py`
- `yt-dlp`
- `ffmpeg` available in system PATH

## Run
1. Install dependencies (for example): `pip install discord.py yt-dlp`
2. Set your Discord bot token in `config.json`
3. Start the bot: `python main.py`
