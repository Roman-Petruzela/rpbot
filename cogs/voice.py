import discord
from discord.ext import commands

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def deny(self, ctx, member: discord.Member):
        if not ctx.author.voice:
            return await ctx.send("You must be in a voice channel to use this command.")
        
        channel = ctx.author.voice.channel
        
        author_permissions = channel.permissions_for(ctx.author)
        if not author_permissions.manage_channels:
            return await ctx.send("This channel is not under your control.")
        
        if member == ctx.author:
            return await ctx.send("You cannot deny yourself access to the voice channel.")
        if member == ctx.guild.me:
            return await ctx.send("You cannot deny the bot access to the voice channel.")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("You cannot deny access to a member with an equal or higher role.")
        
        permissions = channel.permissions_for(member)
        try:
            if permissions.connect:
                await channel.set_permissions(member, connect=False)
                await ctx.send(f"{member} has been denied access to the voice channel.")
            else:
                await channel.set_permissions(member, connect=True)
                await ctx.send(f"{member} has been allowed access to the voice channel.")
        except (discord.Forbidden, discord.HTTPException):
            await ctx.send("I could not update channel permissions.")

async def setup(bot):
    await bot.add_cog(Voice(bot))