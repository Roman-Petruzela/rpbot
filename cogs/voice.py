import discord
from discord.ext import commands

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def deny(self, ctx, member: discord.Member):
        if not ctx.author.voice:
            return await ctx.send("Pro použití tohoto příkazu musíš být ve voice kanálu.")
        
        channel = ctx.author.voice.channel
        
        author_permissions = channel.permissions_for(ctx.author)
        if not author_permissions.manage_channels:
            return await ctx.send("Tento kanál není pod tvou správou.")
        
        if member == ctx.author:
            return await ctx.send("Sám sobě nemůžeš zablokovat přístup do voice kanálu.")
        if member == ctx.guild.me:
            return await ctx.send("Botovi nemůžeš zablokovat přístup do voice kanálu.")
        if member.top_role >= ctx.author.top_role:
            return await ctx.send("Nemůžeš zablokovat přístup členovi se stejnou nebo vyšší rolí.")
        
        permissions = channel.permissions_for(member)
        try:
            if permissions.connect:
                await channel.set_permissions(member, connect=False)
                await ctx.send(f"{member} má nyní zakázaný přístup do voice kanálu.")
            else:
                await channel.set_permissions(member, connect=True)
                await ctx.send(f"{member} má nyní povolený přístup do voice kanálu.")
        except (discord.Forbidden, discord.HTTPException):
            await ctx.send("Nepodařilo se upravit oprávnění kanálu.")

async def setup(bot):
    await bot.add_cog(Voice(bot))