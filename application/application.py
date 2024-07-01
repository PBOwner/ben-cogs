import discord
from discord.ext import commands
from redbot.core import Config

class Application(commands.Cog):
    """Cog for handling Mental Health Buddy applications."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "application_channel": None,
            "questions": [],
            "applications": {}
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.command()
    async def addq(self, ctx, *, question: str):
        """Add a question for the Mental Health Buddy application."""
        async with self.config.guild(ctx.guild).questions() as questions:
            questions.append(question)
        await ctx.send("Question added.")

    @commands.guild_only()
    @commands.command()
    async def setappchannel(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    async def listqs(self, ctx):
        """List questions for the Mental Health Buddy application."""
        questions = await self.config.guild(ctx.guild).questions()
        if questions:
            questions_list = '\n'.join(f"{idx+1}. {q}" for idx, q in enumerate(questions))
            await ctx.send(f"Questions:\n{questions_list}")
        else:
            await ctx.send("No questions set for the application.")

    @commands.guild_only()
    @commands.command()
    async def remq(self, ctx, index: int):
        """Remove a question by its index."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if 0 < index <= len(questions):
                removed_question = questions.pop(index - 1)
                await ctx.send(f"Removed question: {removed_question}")
            else:
                await ctx.send("Invalid question index.")

    @commands.guild_only()
    @commands.command()
    async def clearqs(self, ctx):
        """Clear all questions for the Mental Health Buddy application."""
        await self.config.guild(ctx.guild).questions.set([])
        await ctx.send("All questions cleared.")

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            application_channel_id = await self.config.guild(guild).application_channel()
            if application_channel_id:
                channel = self.bot.get_channel(application_channel_id)
                if channel:
                    await channel.send(
                        "Click the button below to apply for a Mental Health Buddy.",
                        view=ApplyButton(self.bot, self.config)
                    )

class ApplyButton(discord.ui.View):
    def __init__(self, bot, config):
        super().__init__(timeout=None)
        self.bot = bot
        self.config = config

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.primary)
    async def apply_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        questions = await self.config.guild(interaction.guild).questions()
        if not questions:
            await interaction.response.send_message("No questions set for the application.", ephemeral=True)
            return

        modal = ApplicationModal(self.bot, self.config, questions)
        await interaction.response.send_modal(modal)

class ApplicationModal(discord.ui.Modal):
    def __init__(self, bot, config, questions):
        self.bot = bot
        self.config = config
        self.questions = questions
        components = [discord.ui.InputText(label=q, style=discord.InputTextStyle.long) for q in questions]
        super().__init__(title="Mental Health Buddy Application", components=components)

    async def callback(self, interaction: discord.Interaction):
        responses = {self.questions[i]: component.value for i, component in enumerate(self.children)}
        async with self.config.guild(interaction.guild).applications() as applications:
            applications[str(interaction.user.id)] = responses

        application_channel_id = await self.config.guild(interaction.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)

        if application_channel:
            embed = discord.Embed(title=f"New Application - {interaction.user.display_name}", color=discord.Color.blue())
            for question, response in responses.items():
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            await application_channel.send(embed=embed)
            await interaction.response.send_message("Application submitted. Thank you!", ephemeral=True)
        else:
            await interaction.response.send_message("Application channel not set. Please contact an admin.", ephemeral=True)
