import discord
import random
from discord.ext import commands
from config import IMAGE_FILES, COFFEE_GIF

class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def image(self, ctx):
        """Отправляет случайную картинку из локальной папки"""
        if not IMAGE_FILES:
            await ctx.send("Нет доступных картинок в папке.")
            return
        random_image_path = random.choice(IMAGE_FILES)
        await ctx.send(file=discord.File(random_image_path))

async def setup(bot):
    await bot.add_cog(Images(bot))