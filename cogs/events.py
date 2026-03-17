import discord
import random
import asyncio
from discord.ext import commands
from config import (
    TARGET_GIF_URL, IMAGE_FILES, REACTIONS,
    TARGET_USER_ID, TARGET_CHANNEL_ID, MIN_INTERVAL, MAX_INTERVAL
)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ping_task_started = False
        self.ping_task = None

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Бот {self.bot.user} успешно запущен!')
        print(f'Загружено {len(IMAGE_FILES)} локальных картинок.')
        
    @commands.Cog.listener()
    async def on_message(self, message):
        import datetime
        print(f"[{datetime.datetime.now()}] on_message (events) вызван: автор={message.author}, контент={message.content[:50]}")
        if message.author == self.bot.user:
            return

        # Проверка на целевую гифку в тексте
        if TARGET_GIF_URL and TARGET_GIF_URL in message.content:
            if IMAGE_FILES:
                random_image_path = random.choice(IMAGE_FILES)
                await message.channel.send(file=discord.File(random_image_path))
            else:
                await message.channel.send("Нет доступных картинок.")

        # Отладка embed'ов (опционально)
        if message.embeds:
            print(f"Найдено {len(message.embeds)} embed'ов в сообщении от {message.author}:")
            for i, embed in enumerate(message.embeds):
                print(f"Embed #{i}: тип={embed.type}, url={embed.url}, title={embed.title}")
                # можно добавить больше деталей при необходимости

        # Проверка embed'ов на целевую гифку по определённым признакам
        for embed in message.embeds:
            # Проверка по URL, содержащему идентификатор гифки
            if embed.url and "25572384" in embed.url:
                if IMAGE_FILES:
                    random_image_path = random.choice(IMAGE_FILES)
                    await message.channel.send(file=discord.File(random_image_path))
                else:
                    await message.channel.send("Нет доступных картинок.")
                break
            # Проверка по провайдеру (Tenor)
            if embed.provider and embed.provider.url == "https://tenor.com/view/%D1%81%D0%BA%D0%B8%D0%BD%D1%8C-%D0%B6%D0%BE%D0%BF%D1%83-%D1%81%D0%BA%D0%B8%D0%BD%D1%8C%D0%B6%D0%BE%D0%BF%D1%83-gif-25572384":
                if IMAGE_FILES:
                    random_image_path = random.choice(IMAGE_FILES)
                    await message.channel.send(file=discord.File(random_image_path))
                else:
                    await message.channel.send("Нет доступных картинок.")
                break

        # Не вызываем process_commands, чтобы избежать дублирования

async def setup(bot):
    await bot.add_cog(Events(bot))