from redbot.core import commands
import discord

class ApplicationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.questions = {}  # Dict to store questions for each role
        self.app_channel = None  # Channel for submitting applications
        self.role_list_channel = None  # Channel for displaying roles

    @commands.command()
    async def addq(self, ctx, role_name: str, *questions):
        """Add questions for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send("Role not found.")
        self.questions[str(role.id)] = questions
        await ctx.send(f"Questions added for role {role_name}.")

    @commands.command()
    async def remq(self, ctx, role_name: str):
        """Remove questions for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role or str(role.id) not in self.questions:
            return await ctx.send("Questions not found for this role.")
        del self.questions[str(role.id)]
        await ctx.send(f"Questions removed for role {role_name}.")

    @commands.command()
    async def apply(self, ctx, role_name: str):
        """Apply for a specific role."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role or str(role.id) not in self.questions:
            return await ctx.send("Role or questions not found.")

        questions = self.questions[str(role.id)]
        responses = {}
        for question in questions:
            await ctx.author.send(f"Question: {question}\nPlease respond in this DM.")
            response = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=300)
            responses[question] = response.content

        await ctx.send("Your application has been submitted.")

        application_channel = self.app_channel
        if not application_channel:
            return await ctx.send("Application channel not set. Please set an application channel first.")

        embed = discord.Embed(title=f"Application for {role.name}", color=discord.Color.blue())
        for question, response in responses.items():
            embed.add_field(name=f"Question: {question}", value=f"Response: {response}", inline=False)

        message = await application_channel.send(embed=embed)
        await message.add_reaction("✅")  # Accept reaction
        await message.add_reaction("❌")  # Decline reaction

        def reaction_check(reaction, user):
            return user == ctx.author and reaction.message == message

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", check=reaction_check, timeout=60)
            if str(reaction.emoji) == "✅":
                await ctx.author.add_roles(role)
                await ctx.author.send(f"Congratulations! You have been accepted for the '{role.name}' role.")
            elif str(reaction.emoji) == "❌":
                await ctx.author.send(f"Sorry, you are declined for '{role.name}'. Please try again after 3 days.")
        except asyncio.TimeoutError:
            await message.clear_reactions()
        
    @commands.command()
    async def setappchannel(self, ctx, channel: discord.TextChannel):
        """Set the submission channel for applications."""
        self.app_channel = channel
        await ctx.send(f"Application channel set to {channel.mention}.")

    @commands.command()
    async def rolelist(self, ctx):
        """Display the list of roles with questions."""
        role_list = []
        for role_id, questions in self.questions.items():
            role = discord.utils.get(ctx.guild.roles, id=int(role_id))
            role_list.append(f"{role.name}: {', '.join(questions)}")
        await ctx.send("**Role List:**\n" + "\n".join(role_list))

    @commands.command()
    async def setrolechannel(self, ctx, channel: discord.TextChannel):
        """Set the channel for displaying the role list."""
        self.role_list_channel = channel
        await ctx.send(f"Role list channel set to {channel.mention}.")

def setup(bot):
    bot.add_cog(ApplicationCog(bot))
