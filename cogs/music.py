"""
Hudební příkazy - přehrávání z YouTube ve voice channelech
"""
import discord
from discord.ext import commands
import yt_dlp
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = getattr(bot, "config", {})
        self.guild_volumes = {}

    @commands.command()
    async def play(self, ctx, url):
        """Přehraje hudbu z YouTube URL"""
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel.")

        channel = ctx.author.voice.channel
        ydl_options = self.config.get("ydl_options","")
        ffmpeg_options = self.config.get("ffmpeg_options","")

        if ctx.voice_client is None:
            vc = await channel.connect()
        else:
            vc = ctx.voice_client

        await ctx.send("Searching and preparing audio...")
        
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                title = info.get('title', 'Unknown title')
            except Exception as e:
                print(f"[play] Error while loading video: {e}")
                await ctx.send("Failed to load the video.")
                return

        guild_volume = self.guild_volumes.get(ctx.guild.id, 1.0)
        source = discord.FFmpegPCMAudio(source=url2, **ffmpeg_options)
        source = discord.PCMVolumeTransformer(source, volume=guild_volume)
        vc.play(source)
        await ctx.send(f"Now playing: **{title}**")

    @commands.command()
    async def stop(self, ctx):
        """Odpojí bota z voice channelu"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not connected to a voice channel.")

    @commands.command()
    async def volume(self, ctx, procenta: int):
        """Nastaví hlasitost v procentech (0-100)"""
        if procenta < 0 or procenta > 100:
            return await ctx.send("Enter volume between 0 and 100.")

        nova_hlasitost = procenta / 100
        self.guild_volumes[ctx.guild.id] = nova_hlasitost

        if ctx.voice_client and ctx.voice_client.source and isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
            ctx.voice_client.source.volume = nova_hlasitost

        await ctx.send(f"Volume set to {procenta}%")

    @commands.command()
    async def skip(self, ctx):
        """Přeskočí aktuální skladbu"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")


async def setup(bot):
    await bot.add_cog(Music(bot))
