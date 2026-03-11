import discord
import random
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ===== НАСТРОЙКИ =====
TARGET_GIF_URL = os.getenv("TARGET_GIF_URL")  # ссылка на гифку-триггер

# Папка с локальными картинками
IMAGES_FOLDER = "images"

# Автоматически собираем все файлы из папки images
IMAGE_FILES = []
if os.path.exists(IMAGES_FOLDER):
    for filename in os.listdir(IMAGES_FOLDER):
        full_path = os.path.join(IMAGES_FOLDER, filename)
        if os.path.isfile(full_path):
            IMAGE_FILES.append(full_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настраиваем интенты
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')
    print(f'Загружено {len(IMAGE_FILES)} локальных картинок.')

# Команда !image (можно назвать !картинка)
@bot.command()
async def image(ctx):
    """Отправляет случайную картинку из локальной папки"""
    if not IMAGE_FILES:
        await ctx.send("Нет доступных картинок в папке.")
        return
    random_image_path = random.choice(IMAGE_FILES)
    # Отправляем файл
    await ctx.send(file=discord.File(random_image_path))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Проверяем текст сообщения (если ссылка отправлена как текст)
    if TARGET_GIF_URL in message.content:
        if IMAGE_FILES:
            random_image_path = random.choice(IMAGE_FILES)
            await message.channel.send(file=discord.File(random_image_path))
        else:
            await message.channel.send("Нет доступных картинок.")

    # Отладка: выводим информацию о каждом embed'е (для настройки)
    if message.embeds:
        print(f"Найдено {len(message.embeds)} embed'ов в сообщении от {message.author}:")
        for i, embed in enumerate(message.embeds):
            print(f"Embed #{i}:")
            print(f"  Тип: {embed.type}")
            print(f"  URL: {embed.url}")
            print(f"  Заголовок: {embed.title}")
            print(f"  Описание: {embed.description}")
            if embed.thumbnail:
                print(f"  Thumbnail URL: {embed.thumbnail.url}")
            if embed.image:
                print(f"  Image URL: {embed.image.url}")
            if embed.video:
                print(f"  Video URL: {embed.video.url}")
            if embed.provider:
                print(f"  Provider: {embed.provider.name}")
            print("-" * 30)

    # Проверяем embed'ы на наличие целевой гифки (по ID или провайдеру)
    for embed in message.embeds:
        if embed.url and "25572384" in embed.url:
            if IMAGE_FILES:
                random_image_path = random.choice(IMAGE_FILES)
                await message.channel.send(file=discord.File(random_image_path))
            else:
                await message.channel.send("Нет доступных картинок.")
            break
        if embed.provider and embed.provider.name == "Tenor":
            # Здесь можно добавить дополнительные проверки (например, title)
            if IMAGE_FILES:
                random_image_path = random.choice(IMAGE_FILES)
                await message.channel.send(file=discord.File(random_image_path))
            else:
                await message.channel.send("Нет доступных картинок.")
            break

    await bot.process_commands(message)

bot.run(BOT_TOKEN)