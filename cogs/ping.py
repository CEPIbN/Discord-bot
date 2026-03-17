import discord
import datetime
import random
import asyncio
from discord.ext import commands
from config import (
    TARGET_GIF_URL, IMAGE_FILES, REACTIONS,
    TARGET_USER_ID, TARGET_CHANNEL_ID, MIN_INTERVAL, MAX_INTERVAL
)

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ping_task_started = False
        self.ping_task = None

    async def random_ping_loop(self):
        """Фоновая задача: ждёт случайное время и пинает пользователя."""
        await self.bot.wait_until_ready()
        if not TARGET_USER_ID or not TARGET_CHANNEL_ID:
            print("Не заданы TARGET_USER_ID или TARGET_CHANNEL_ID. Фоновый пинг отключён.")
            return
        try:
            target_user_id = int(TARGET_USER_ID)
            target_channel_id = int(TARGET_CHANNEL_ID)
        except ValueError:
            print("Ошибка: TARGET_USER_ID и TARGET_CHANNEL_ID должны быть целыми числами.")
            return

        while not self.bot.is_closed():
            delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
            print(f"Следующий пинг через {delay} секунд.")
            await asyncio.sleep(delay)

            channel = self.bot.get_channel(target_channel_id)
            if channel is None:
                print(f"Канал с ID {target_channel_id} не найден. Пинг пропущен.")
                continue

            try:
                msg = await channel.send(f"<@{target_user_id}> https://tenor.com/view/markiplier-markiplier-soyjak-soyjak-wojak-bouncing-gif-27376523")
                print(f"Отправлен пинг пользователю {target_user_id} в канал {target_channel_id}")
                await asyncio.sleep(1)
                await msg.delete()
            except Exception as e:
                print(f"Ошибка при отправке пинга: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        global ping_task_started
        print(f"[{datetime.datetime.now()}] on_message (ping) вызван: автор={message.author}, контент={message.content[:50]}")
        if not ping_task_started:
            await self.random_ping_loop()
        ping_task_started = True
        if message.author == self.bot.user:
            return

        # Случайная реакция
        reaction = random.choice(REACTIONS)
        try:
            await message.add_reaction(reaction)
            print(f"Поставил реакцию {reaction} на сообщение от {message.author}")
        except discord.Forbidden:
            print("Нет прав на добавление реакций в этом канале.")
        except discord.HTTPException as e:
            print(f"Ошибка при добавлении реакции: {e}")
async def setup(bot):
    await bot.add_cog(Ping(bot))