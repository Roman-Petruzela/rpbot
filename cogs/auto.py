import discord
from discord.ext import commands
import json
from pathlib import Path


class Auto(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	def _save_config(self):
		config_path = Path(__file__).resolve().parent.parent / "config.json"
		with open(config_path, "w", encoding="utf-8") as config_file:
			json.dump(self.bot.config, config_file, ensure_ascii=False, indent=2)

	@commands.Cog.listener()
	async def on_member_join(self, member: discord.Member):
		guild = member.guild
		me = guild.me or guild.get_member(self.bot.user.id)
		role_id = int(getattr(self.bot, "config", {}).get("auto_role_id", 0) or 0)

		if me is None or not me.guild_permissions.manage_roles or role_id == 0:
			return

		role = guild.get_role(role_id)
		if role is None:
			return

		if role in member.roles or role >= me.top_role:
			return

		try:
			await member.add_roles(role, reason="Automatic member role assignment")
		except (discord.Forbidden, discord.HTTPException):
			return

	@commands.command(name="set_auto_role")
	@commands.has_permissions(administrator=True)
	@commands.guild_only()
	async def set_auto_role(self, ctx, role: discord.Role = None):
		me = ctx.guild.me
		if me is None:
			return await ctx.send("Fatal error: Bot user not found in guild.")

		if role is None:
			role_id = getattr(self.bot, "config", {}).get("auto_role_id", "")
			if role_id == "":
				return await ctx.send("Auto role is not set.")

			current_role = ctx.guild.get_role(int(role_id))
			if current_role is None:
				return await ctx.send(f"Auto role ID is set to `{role_id}`, but this role was not found on this server.")

			return await ctx.send(f"Current auto role: **{current_role.name}** (`{current_role.id}`).")

		if not me.guild_permissions.manage_roles:
			return await ctx.send("Missing permission: I need the 'Manage Roles' permission to do this.")

		if role >= me.top_role:
			return await ctx.send("I cannot assign that role because it is higher or equal to my highest role.")

		self.bot.config["auto_role_id"] = str(role.id)
		self._save_config()
		await ctx.send(f"Auto role was set to **{role.name}** (`{role.id}`).")
    
	@set_auto_role.error
	async def set_auto_role_error(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			await ctx.send(f"Usage: `{ctx.prefix}set_auto_role @Role`")
		elif isinstance(error, commands.BadArgument):
			await ctx.send("Invalid role.")


async def setup(bot):
    await bot.add_cog(Auto(bot))