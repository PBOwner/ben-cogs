from .applicationcog import ApplicationCog

def setup(bot):
    cog = ApplicationCog(bot)
    bot.add_cog(cog)
