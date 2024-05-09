from redbot.core.bot import Red

from .invoice import Invoice

async def setup(bot: Red):
    await bot.add_cog(Invoice(bot))