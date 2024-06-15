import discord
import asyncio
from redbot.core import commands, Config

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
    async def addq(self, ctx, role: discord.Role, *, question: str):
        """Add a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            questions.setdefault(str(role.id), []).append(question)
        await ctx.send(f"Question added for {role.name}.")

    @commands.guild_only()
    @commands.command()
    async def setappchannel(self, ctx, channel: discord.TextChannel):
        """Set the application channel."""
        await self.config.guild(ctx.guild).application_channel.set(channel.id)
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.guild_only()
    @commands.command()
    async def listroles(self, ctx):
        """List roles available for application."""
        questions = await self.config.guild(ctx.guild).questions()
        roles = [ctx.guild.get_role(int(role_id)).name for role_id in questions if ctx.guild.get_role(int(role_id))]
        if roles:
            roles_list = '\n'.join(roles)
            await ctx.send("Roles available for application:\n{}\n\nUse `apply <role_name>` to apply for a role.".format(roles_list))
        else:
            await ctx.send("No roles set for applications.")

    @commands.command()
    async def apply(self, ctx, role_name: str):
        """Submit an application for a role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        questions = await self.config.guild(ctx.guild).questions()
        role_questions = questions.get(str(role.id))
        if not role_questions:
            return await ctx.send("No questions found for this role. Please add questions first.")

        responses = {}

        for question in role_questions:
            await ctx.author.send(f"Question: {question}\nPlease respond in this DM.")
            try:
                response = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=300)
                responses[question] = response.content
            except asyncio.TimeoutError:
                await ctx.author.send("Response timed out. Please try again later.")
                return

        application_channel_id = await self.config.guild(ctx.guild).application_channel()
        application_channel = self.bot.get_channel(application_channel_id)

        if not application_channel:
            return await ctx.send("Application channel not set. Please set an application channel first.")

        embed = discord.Embed(title=f"Application for {role.name}", color=discord.Color.blue())
        for question, response in responses.items():
            embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)

        message = await application_channel.send(embed=embed, components=[
            Button(style=ButtonStyle.green, label="Accept", custom_id="accept"),
            Button(style=ButtonStyle.red, label="Deny", custom_id="deny")
        ])

        def check(res):
            return ctx.author == res.user and res.channel == message.channel

        try:
            res = await self.bot.wait_for("button_click", check=check, timeout=300)
            if res.component.custom_id == "Accept":
                await ctx.author.add_roles(role)
                await ctx.author.send(f"Your application for {role.name} has been accepted.")
            elif res.component.custom_id == "Deny":
                await ctx.author.send(f"Your application for {role.name} has been denied.")
        except asyncio.TimeoutError:
            await ctx.author.send("Response timed out. Please try again later.")

        await ctx.send("Your application has been submitted.")

    @commands.guild_only()
    @commands.command()
    async def remq(self, ctx, role: discord.Role, *, question: str):
        """Remove a question for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if question in questions.get(str(role.id), []):
                questions[str(role.id)].remove(question)
                await ctx.send(f"Question removed for {role.name}.")
            else:
                await ctx.send("Question not found for this role.")

    @commands.guild_only()
    @commands.command()
    async def clearqs(self, ctx, role: discord.Role):
        """Clear all questions for a specific role."""
        async with self.config.guild(ctx.guild).questions() as questions:
            if str(role.id) in questions:
                del questions[str(role.id)]
                await ctx.send(f"Questions cleared for {role.name}.")
            else:
                await ctx.send("No questions set for this role.")
