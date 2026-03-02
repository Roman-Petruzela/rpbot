"""
Admin příkazy - jen pro uživatele s Administrator oprávněním
"""
import discord
from discord.ext import commands
import asyncio
import json
from pathlib import Path


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.content = getattr(bot, "content", {})

    def _save_config(self):
        config_path = Path(__file__).resolve().parent.parent / "config.json"
        with open(config_path, "w", encoding="utf-8") as config_file:
            json.dump(self.bot.config, config_file, ensure_ascii=False, indent=2)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pravidla(self, ctx):
        """Odešle pravidla serveru s invite linkem"""
        rules_gif_path = self.content.get("rules_gif_path", "")
        rules_text = self.content.get("rules_text", "")
        invite_url = self.content.get("invite_url", "")
        embed_color = self.content.get("embed_color", "")

        await ctx.send(file=discord.File(rules_gif_path))
        await ctx.send(rules_text)
        embed = discord.Embed(
            title="Invite your friends!",
            description=f"```{invite_url}```",
            color=discord.Color.from_str(embed_color)
        )
        view = discord.ui.View()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="roleall")
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def roleall(self, ctx, role: discord.Role):
        """Hromadně přiřadí roli všem členům serveru"""
        guild = ctx.guild
        me = guild.me

        if me is None:
            return await ctx.send("Fatal error: Bot user not found in guild.")

        if not guild.me.guild_permissions.manage_roles:
            return await ctx.send("Missing permission: I need the 'Manage Roles' permission to do this.")

        if role >= me.top_role:
            return await ctx.send("I cannot assign that role because it is higher or equal to my highest role.")

        await ctx.send(f"Starting to assign the role **{role.name}** to all members. This may take a while...")

        added = 0
        skipped = 0
        failed = 0

        for member in guild.members:
            if member.bot:
                continue

            if role in member.roles:
                skipped += 1
                await ctx.send(f"**{member.display_name}** already has the role, skipping.")
                continue

            if member.top_role >= me.top_role:
                failed += 1
                await ctx.send(f"**{member.display_name}** cannot be assigned the role because it is higher or equal to my highest role.")
                continue

            try:
                await member.add_roles(role, reason=f"Bulk role assignment by {ctx.author}")
                added += 1
                await ctx.send(f"Role **{role.name}** was assigned to **{member.display_name}**")
                await asyncio.sleep(0.2)
            except (discord.Forbidden, discord.HTTPException):
                failed += 1

        await ctx.send(
            f"Done. Added: **{added}**, already had: **{skipped}**, failed: **{failed}**."
        )

    @roleall.error
    async def roleall_error(self, ctx, error):
        """Error handler pro roleall"""
        if isinstance(error, commands.BadArgument):
            await ctx.send("Usage: `!roleall @Role`")
    
    @commands.command()        
    @commands.has_permissions(administrator=True)
    async def add_channel(self, ctx, channel: discord.TextChannel):
        """Přidá textový kanál do seznamu povolených kanálů pro příkazy"""
        raw_allowed_channels = self.bot.config.get("allowed_channels", [])
        if isinstance(raw_allowed_channels, int):
            raw_allowed_channels = [raw_allowed_channels]

        allowed_channel_ids = [int(channel_id) for channel_id in raw_allowed_channels]

        if channel.id in allowed_channel_ids:
            await ctx.send("This channel is already in the allowed channels list.")
            return

        allowed_channel_ids.append(channel.id)
        self.bot.config["allowed_channels"] = allowed_channel_ids
        self._save_config()

        await ctx.send(f"Channel **{channel.name}** has been added to the allowed channels list.")

    @add_channel.error
    async def add_channel_error(self, ctx, error):
        """Error handler for add_channel"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{ctx.prefix}add_channel #channel`")
        elif isinstance(error, (commands.BadArgument, commands.ChannelNotFound)):
            await ctx.send("Invalid channel.")
            
    @commands.command()        
    @commands.has_permissions(administrator=True)
    async def rem_channel(self, ctx, channel: discord.TextChannel):
        """Odebere textový kanál ze seznamu povolených kanálů pro příkazy"""
        raw_allowed_channels = self.bot.config.get("allowed_channels", [])
        if isinstance(raw_allowed_channels, int):
            raw_allowed_channels = [raw_allowed_channels]

        allowed_channel_ids = [int(channel_id) for channel_id in raw_allowed_channels]

        if channel.id not in allowed_channel_ids:
            await ctx.send("This channel is not in the allowed channels list.")
            return

        allowed_channel_ids.remove(channel.id)
        self.bot.config["allowed_channels"] = allowed_channel_ids
        self._save_config()

        await ctx.send(f"Channel **{channel.name}** has been removed from the allowed channels list.")

    @rem_channel.error
    async def rem_channel_error(self, ctx, error):
        """Error handler for rem_channel"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Usage: `{ctx.prefix}rem_channel #channel`")
        elif isinstance(error, (commands.BadArgument, commands.ChannelNotFound)):
            await ctx.send("Invalid channel.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
