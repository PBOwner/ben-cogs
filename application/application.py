import discord
from redbot.core import commands, Config

class Application(commands.Cog):
    """Cog for handling Mental Health Buddy applications."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "application_channel": None,
            "questions": [],
            "applications": {},
            "button_message": "Click the button below to apply for a Mental Health Buddy."
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.command()
    async def addmhbq(self, ctx, *, question: str):
        """Add a question for the Mental Health Buddy application."""
        async with self.config.guild(ctx.guild).questions() as questions:
            questions.append(question)
        await ctx.send("Question added.")

    @commands.guild_only()
    @commands.command()
    async def setmhbreq(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    async def setbuttonmessage(self, ctx, *, message: str):
        """Set the message to be displayed with the application button."""
        await self.config.guild(ctx.guild).button_message.set(message)
        await ctx.send("Button message set.")

    @commands.guild_only()
    @commands.command()
    async def listquestions(self, ctx):
        """List questions for the Mental Health Buddy application."""
        questions = await self.config.guild(ctx.guild).questions()
        if questions:
            questions_list = '\n'.join(f"{idx+1}. {q}" for idx, q in enumerate(questions))
            await ctx.send(f"Questions:\n{questions_list}")
        else:
            await ctx.send("No questions set for the application.")

    @commands.guild_only()
    @commands.command()
    async def removeq(self, ctx, index: int):
        """Remove a question by its index."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if 0 < index <= len(questions):
                removed_question = questions.pop(index - 1)
                await ctx.send(f"Removed question: {removed_question}")
            else:
                await ctx.send("Invalid question index.")

    @commands.guild_only()
    @commands.command()
    async def clearq(self, ctx):
        """Clear all questions for the Mental Health Buddy application."""
        await self.config.guild(ctx.guild).questions.set([])
        await ctx.send("All questions cleared.")

    @commands.guild_only()
    @commands.command()
    async def applymhb(self, ctx):
        """Apply for a Mental Health Buddy."""
        questions = await self.config.guild(ctx.guild).questions()
        if not questions:
            await ctx.send("No questions set for the application.")
            return

        await ctx.author.send("Starting your application for a Mental Health Buddy. Please answer the following questions:")

        responses = {}
        for question in questions:
            await ctx.author.send(f"Question: {question}")
            try:
                response = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author == ctx.author and isinstance(m.channel, discord.DMChannel),
                    timeout=300
                )
                responses[question] = response.content
            except asyncio.TimeoutError:
                await ctx.author.send("You took too long to respond. Please try again later.")
                return

        async with self.config.guild(ctx.guild).applications() as applications:
            applications[str(ctx.author.id)] = responses

        application_channel_id = await self.config.guild(ctx.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)

        if application_channel:
            embed = discord.Embed(title=f"New Application - {ctx.author.display_name}", color=discord.Color.blue())
            for question, response in responses.items():
                embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)
            await application_channel.send(embed=embed)
            await ctx.author.send("Application submitted. Thank you!")
        else:
            await ctx.author.send("Application channel not set. Please contact an admin.")
