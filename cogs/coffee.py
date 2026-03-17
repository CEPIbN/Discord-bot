from discord.ext import commands
from config import COFFEE_GIF
import datetime

class Coffee(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def кофе(self, ctx):
        """Готовит кофе"""
        print(f"[{datetime.datetime.now()}] Команда 'кофе' вызвана пользователем {ctx.author} в канале {ctx.channel}")
        await ctx.send(f"Окей, приготовлю {COFFEE_GIF}")

async def setup(bot):
    await bot.add_cog(Coffee(bot))