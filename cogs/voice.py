import discord
from discord.ext import commands

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = set()
    
    @commands.Cog.listener()
    async def on_voice_state_update(self,member, before, after):
        if before.channel == after.channel:
            return
        
        trigger_id = int(self.bot.config.get("voice_trigger_id", 0) or 0)
        if trigger_id == 0:
            return
        
        if before.channel and before.channel.id in self.temp_channels:
            if len(before.channel.members) == 0:
                channel_name_log = before.channel.name
                try:
                    await before.channel.delete()
                    self.temp_channels.remove(before.channel.id)
                    send_log = getattr(self.bot, "send_log", None)
                    if callable(send_log):
                        await send_log(f"Dočasný voice kanál **{channel_name_log}** byl smazán (prázdný).")
                except (discord.Forbidden, discord.HTTPException) as e:
                    send_log = getattr(self.bot, "send_log", None)
                    if callable(send_log):
                        await send_log(f"Chyba při mazání dočasného kanálu **{channel_name_log}**: `{e}`")

        if member.bot:
            return

        if after.channel is None:
            return

        if after.channel.id == trigger_id:
            guild = member.guild
            channel_name = self.bot.config.get("voice_default_name", "{member.display_name} roomka")
            channel_name = channel_name.format(member=member)
            category = after.channel.category
            try:
                new_channel = await guild.create_voice_channel(name=channel_name, category=category)
                self.temp_channels.add(new_channel.id)
                await member.move_to(new_channel)
                send_log = getattr(self.bot, "send_log", None)
                if callable(send_log):
                    await send_log(f"Dočasný voice kanál **{channel_name}** byl vytvořen pro **{member}**.")
                permissions = new_channel.permissions_for(member)
                try:
                    if not permissions.manage_channels:
                        await new_channel.set_permissions(member, manage_channels=True)
                        send_log = getattr(self.bot, "send_log", None)
                        if callable(send_log):
                            await send_log(f"{member} je správce kanálu **{channel_name}**.")
                except (discord.Forbidden, discord.HTTPException):
                    send_log = getattr(self.bot, "send_log", None)
                    if callable(send_log):
                        await send_log("Nepodařilo se upravit oprávnění kanálu.")
            except (discord.Forbidden, discord.HTTPException) as e:
                send_log = getattr(self.bot, "send_log", None)
                if callable(send_log):
                    await send_log(f"Chyba při vytváření dočasného kanálu pro **{member}**: `{e}`")


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