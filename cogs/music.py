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
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel.")

        channel = ctx.author.voice.channel
        me = ctx.guild.me
        permissions = channel.permissions_for(me)
        if not permissions.connect:
            return await ctx.send("I don't have permission to connect to your voice channel.")
        if not permissions.speak:
            return await ctx.send("I don't have permission to speak in your voice channel.")

        ydl_options = self.config.get("ydl_options", {})
        ffmpeg_options = self.config.get("ffmpeg_options", {})

        try:
            if ctx.voice_client is None:
                vc = await channel.connect(timeout=15.0, reconnect=False)
            else:
                vc = ctx.voice_client
                if vc.channel != channel:
                    await vc.move_to(channel)
        except discord.ClientException as e:
            print(f"[play] Voice client error: {e}")
            return await ctx.send("Couldn't connect to voice channel. Check if I'm already connected or restart me.")
        except RuntimeError as e:
            print(f"[play] Runtime voice error: {e}")
            return await ctx.send("Voice dependencies are missing on host (install PyNaCl).")
        except asyncio.TimeoutError:
            return await ctx.send("Connecting to voice channel timed out.")
        except Exception as e:
            print(f"[play] Unexpected voice connect error: {e}")
            return await ctx.send("Failed to connect to your voice channel.")

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
        try:
            source = discord.FFmpegPCMAudio(source=url2, **ffmpeg_options)
            source = discord.PCMVolumeTransformer(source, volume=guild_volume)
            vc.play(source)
        except FileNotFoundError:
            if vc.is_connected():
                await vc.disconnect(force=True)
            return await ctx.send("FFmpeg was not found on host. Install FFmpeg and add it to PATH.")
        except Exception as e:
            print(f"[play] Failed to start playback: {e}")
            if vc.is_connected() and not vc.is_playing():
                await vc.disconnect(force=True)
            return await ctx.send("Failed to start playback.")

        await ctx.send(f"Now playing: **{title}**")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Disconnected.")
        else:
            await ctx.send("I'm not connected to a voice channel.")

    @commands.command()
    async def volume(self, ctx, procenta: int):
        if procenta < 0 or procenta > 100:
            return await ctx.send("Enter volume between 0 and 100.")

        nova_hlasitost = procenta / 100
        self.guild_volumes[ctx.guild.id] = nova_hlasitost

        if ctx.voice_client and ctx.voice_client.source and isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
            ctx.voice_client.source.volume = nova_hlasitost

        await ctx.send(f"Volume set to {procenta}%")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing.")


async def setup(bot):
    await bot.add_cog(Music(bot))
