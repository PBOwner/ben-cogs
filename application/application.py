import discord
import asyncio
from discord.ext import commands
from discord.ui import Button, ButtonStyle, View

class Application(commands.Cog):
    """Cog for handling applications."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "application_channel": None,
            "questions": {},
            "applications": {}
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.command()
    async def apply(self, ctx, *, role_name: str):
        """Apply for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        questions = await self.config.guild(ctx.guild).questions()
        role_questions = questions.get(str(role.id))
        if not role_questions:
            return await ctx.send("No questions set for this role.")

        responses = {}
        for question in role_questions:
            await ctx.author.send(f"Question: {question}\nPlease respond in this DM.")
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and m.channel.type == discord.ChannelType.private,
                    timeout=300
                )
                responses[question] = response.content
            except asyncio.TimeoutError:
                await ctx.author.send("Time's up. Please try again later.")
                return

        async with self.config.guild(ctx.guild).applications() as applications:
            applications.setdefault(str(role.id), {})[str(ctx.author.id)] = responses

        application_channel_id = await self.config.guild(ctx.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)

        if application_channel:
            embed = discord.Embed(title=f"Application for {role.name}", color=discord.Color.blue())
            for question, response in responses.items():
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)

            accept_button = Button(style=ButtonStyle.green, label="Accept")
            decline_button = Button(style=ButtonStyle.red, label="Decline")

            view = View()
            view.add_item(accept_button)
            view.add_item(decline_button)

            message = await application_channel.send(embed=embed, view=view)

            def check(button_ctx):
                return button_ctx.author.id == ctx.author.id and button_ctx.message.id == message.id

            try:
                button_ctx = await self.bot.wait_for("button_click", check=check, timeout=60)
                if button_ctx.component.label == "Accept":
                    await button_ctx.respond(type=6)
                    await button_ctx.author.add_roles(role)
                    await button_ctx.author.send(f"Congratulations! You have been hired! The '{role.name}' role was automatically applied.")
                elif button_ctx.component.label == "Decline":
                    await button_ctx.respond(type=6, content="Your application has been declined.")
            except asyncio.TimeoutError:
                await message.edit(view=None)
        else:
            await ctx.send("Application channel not set. Please set an application channel first.")

def setup(bot):
    bot.add_cog(Application(bot))
