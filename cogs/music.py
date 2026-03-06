import discord
from discord.ext import commands
import yt_dlp
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = getattr(bot, "config", {})
        self.guild_volumes = {}
        self.guild_queues = {}
        self.guild_now_playing = {}

    def _get_guild_queue(self, guild_id: int):
        return self.guild_queues.setdefault(guild_id, [])

    async def _start_track(self, channel: discord.abc.Messageable, vc: discord.VoiceClient, guild_id: int, track: dict):
        ffmpeg_options = self.config.get("ffmpeg_options", {})
        guild_volume = self.guild_volumes.get(guild_id, 1.0)

        try:
            source = discord.FFmpegPCMAudio(source=track["stream_url"], **ffmpeg_options)
            source = discord.PCMVolumeTransformer(source, volume=guild_volume)

            def _after_playback(error):
                if error:
                    print(f"[play] Playback error: {error}")
                self.bot.loop.call_soon_threadsafe(
                    asyncio.create_task,
                    self._play_next(guild_id=guild_id, channel=channel, vc=vc),
                )

            vc.play(source, after=_after_playback)
            self.guild_now_playing[guild_id] = track
            await channel.send(f"Právě hraje: **{track['title']}**")
        except FileNotFoundError:
            if vc.is_connected():
                await vc.disconnect(force=True)
            await channel.send("FFmpeg nebyl na hostiteli nalezen. Nainstaluj FFmpeg a přidej ho do PATH.")
        except Exception as e:
            print(f"[play] Failed to start playback: {e}")
            if vc.is_connected() and not vc.is_playing():
                await vc.disconnect(force=True)
            await channel.send("Nepodařilo se spustit přehrávání.")

    async def _play_next(self, guild_id: int, channel: discord.abc.Messageable, vc: discord.VoiceClient):
        queue = self._get_guild_queue(guild_id)
        if not queue:
            self.guild_now_playing.pop(guild_id, None)
            return

        next_track = queue.pop(0)
        await self._start_track(channel=channel, vc=vc, guild_id=guild_id, track=next_track)

    @commands.command()
    async def play(self, ctx, url):
        if not ctx.author.voice:
            return await ctx.send("Musíš být ve voice kanálu.")

        channel = ctx.author.voice.channel
        me = ctx.guild.me
        permissions = channel.permissions_for(me)
        if not permissions.connect:
            return await ctx.send("Nemám oprávnění připojit se do tvého voice kanálu.")
        if not permissions.speak:
            return await ctx.send("Nemám oprávnění mluvit ve tvém voice kanálu.")

        ydl_options = self.config.get("ydl_options", {})

        try:
            if ctx.voice_client is None:
                vc = await channel.connect(timeout=15.0, reconnect=False)
            else:
                vc = ctx.voice_client
                if vc.channel != channel:
                    await vc.move_to(channel)
        except discord.ClientException as e:
            print(f"[play] Voice client error: {e}")
            return await ctx.send("Nepodařilo se připojit do voice kanálu. Zkontroluj, jestli už nejsem připojený, nebo mě restartuj.")
        except RuntimeError as e:
            print(f"[play] Runtime voice error: {e}")
            return await ctx.send("Na hostiteli chybí voice závislosti (nainstaluj PyNaCl).")
        except asyncio.TimeoutError:
            return await ctx.send("Připojení do voice kanálu vypršelo.")
        except Exception as e:
            print(f"[play] Unexpected voice connect error: {e}")
            return await ctx.send("Nepodařilo se připojit do tvého voice kanálu.")

        await ctx.send("Vyhledávám a připravuji audio...")
        
        with yt_dlp.YoutubeDL(ydl_options) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                url2 = info["url"]
                title = info.get('title', 'Neznámý název')
            except Exception as e:
                print(f"[play] Error while loading video: {e}")
                await ctx.send("Nepodařilo se načíst video.")
                return

        track = {
            "title": title,
            "stream_url": url2,
            "requested_by": str(ctx.author),
        }

        if vc.is_playing() or vc.is_paused():
            queue = self._get_guild_queue(ctx.guild.id)
            queue.append(track)
            return await ctx.send(f"Přidáno do fronty na pozici **{len(queue)}**: **{title}**")

        await self._start_track(channel=ctx.channel, vc=vc, guild_id=ctx.guild.id, track=track)

    @commands.command()
    async def queue(self, ctx):
        now_playing = self.guild_now_playing.get(ctx.guild.id)
        queue = self._get_guild_queue(ctx.guild.id)

        if not now_playing and not queue:
            return await ctx.send("Fronta je prázdná.")

        lines = []
        if now_playing:
            lines.append(f"Teď hraje: **{now_playing['title']}**")

        if queue:
            lines.append("Další ve frontě:")
            for index, track in enumerate(queue, start=1):
                lines.append(f"{index}. {track['title']}")

        await ctx.send("\n".join(lines))

    @commands.command()
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc is None or not vc.is_connected():
            return await ctx.send("Nejsem připojený ve voice kanálu.")

        if vc.is_paused():
            return await ctx.send("Přehrávání už je pozastavené.")

        if not vc.is_playing():
            return await ctx.send("Momentálně nic nehraje.")

        vc.pause()
        await ctx.send("Přehrávání pozastaveno.")

    @commands.command()
    async def stop(self, ctx):
        if ctx.voice_client:
            self._get_guild_queue(ctx.guild.id).clear()
            self.guild_now_playing.pop(ctx.guild.id, None)
            await ctx.voice_client.disconnect()
            await ctx.send("Odpojeno.")
        else:
            await ctx.send("Nejsem připojený ve voice kanálu.")

    @commands.command()
    async def volume(self, ctx, procenta: int):
        if procenta < 0 or procenta > 100:
            return await ctx.send("Zadej hlasitost mezi 0 a 100.")

        nova_hlasitost = procenta / 100
        self.guild_volumes[ctx.guild.id] = nova_hlasitost

        if ctx.voice_client and ctx.voice_client.source and isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer):
            ctx.voice_client.source.volume = nova_hlasitost

        await ctx.send(f"Hlasitost nastavena na {procenta}%")

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("Přeskočeno.")
        else:
            await ctx.send("Momentálně nic nehraje.")


async def setup(bot):
    await bot.add_cog(Music(bot))
