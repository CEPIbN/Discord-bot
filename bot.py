import discord
from discord.ext import commands
from config import BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='*', intents=intents)

# Загружаем все коги из папки cogs
async def load_extensions():
    await bot.load_extension("cogs.music")
    await bot.load_extension("cogs.chat")
    await bot.load_extension("cogs.images")
    await bot.load_extension("cogs.events")
    await bot.load_extension("cogs.coffee")
    #await bot.load_extension("cogs.ping")

@bot.event
async def setup_hook():
    await load_extensions()
    print("Все коги загружены.")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)