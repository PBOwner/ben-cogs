from redbot.core import commands
from .application import Application

def setup(bot):
    cog = Application(bot)
    bot.add_cog(cog)
