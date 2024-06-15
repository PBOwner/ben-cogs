import discord
from redbot.core import commands

class Application(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.questions = {}
        self.app_channel = None
        self.roles = []

    @commands.command()
    async def addq(self, ctx, role_name: str, *questions):
        """Add questions for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        self.questions[role.id] = questions
        await ctx.send(f"Questions added for role: {role_name}")

    @commands.command()
    async def remq(self, ctx, role_name: str):
        """Remove questions for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        if role.id in self.questions:
            del self.questions[role.id]
            await ctx.send(f"Questions removed for role: {role_name}")
        else:
            await ctx.send("No questions found for this role.")

    @commands.command()
    async def setappchannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for submitting applications."""
        self.app_channel = channel
        await ctx.send(f"Application channel set to: {channel.mention}")

    @commands.command()
    async def apply(self, ctx, role_name: str):
        """Submit an application for a role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")

        if role.id not in self.questions:
            return await ctx.send("No questions found for this role. Please add questions first.")

        questions = self.questions[role.id]
        responses = {}

        for question in questions:
            await ctx.author.send(f"Question: {question}\nPlease respond in this DM.")
            try:
                response = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=300)
                responses[question] = response.content
            except asyncio.TimeoutError:
                await ctx.author.send("Response timed out. Please try again later.")
                return

        application_channel = self.app_channel
        if not application_channel:
            return await ctx.send("Application channel not set. Please set an application channel first.")

        embed = discord.Embed(title=f"Application for {role.name}", color=discord.Color.blue())
        for question, response in responses.items():
            embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)

        await application_channel.send(embed=embed)
        await ctx.send("Your application has been submitted.")

    @commands.command()
    async def listroles(self, ctx):
        """List all roles available for application."""
        role_list = "\n".join([role.name for role in ctx.guild.roles if role.name in self.questions])
        await ctx.send(f"Roles available for application:\n{role_list}")

def setup(bot):
    bot.add_cog(Application(bot))
