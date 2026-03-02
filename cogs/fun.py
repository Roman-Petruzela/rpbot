"""
Zábavné příkazy - dostupné pro všechny uživatele
"""
import random
import discord
from discord.ext import commands
import asyncio

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.content = getattr(bot, "content", {})
        self.guild_volumes = {}

    @commands.command()
    async def gragas_jumpscare(self, ctx, member: discord.Member):
        """Easter egg - přehraje Gragas zvuk uživateli ve voice channelu"""
        if not member.voice:
            return await ctx.send(f"**{member.display_name}** is not in a voice channel.")

        channel = member.voice.channel
        
        vc = await channel.connect()
        await asyncio.sleep(1)  # Krátká pauza, aby se bot správně připojil
        
        # Guild volumes sdílíme s Music cogem
        from cogs.music import Music
        music_cog = self.bot.get_cog('Music')
        volume = 1.0
        if music_cog:
            volume = music_cog.guild_volumes.get(ctx.guild.id, 1.0)
        
        gragas_audio_path = self.content.get("gragas_audio_path", "sources/audio/gragas.ogg")
        source = discord.FFmpegPCMAudio(executable="ffmpeg", source=gragas_audio_path)
        source = discord.PCMVolumeTransformer(source, volume=volume)
        
        vc.play(source)
        while vc.is_playing():
            await asyncio.sleep(1)
        
        await vc.disconnect()
        
    @commands.command()
    async def pero(self, ctx):
        """Fun command"""
        await ctx.send(f"Your size is {random.randint(1, 30)} cm")
        
    @commands.command()
    async def mince(self, ctx):
        vysledek = random.choice(["Orel", "Panna"])
        await ctx.send(f"**{vysledek}**")


async def setup(bot):
    await bot.add_cog(Fun(bot))
