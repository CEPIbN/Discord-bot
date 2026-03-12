import discord
import random
import os
import asyncio
import yt_dlp
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ===== НАСТРОЙКИ =====
#Ссылки на гифки
TARGET_GIF_URL = os.getenv("TARGET_GIF_URL")
SKIP_GIF = os.getenv("SKIP_GIF")
# Папка с локальными картинками
IMAGES_FOLDER = "images"

# Автоматически собираем все файлы из папки images
IMAGE_FILES = []
if os.path.exists(IMAGES_FOLDER):
    for filename in os.listdir(IMAGES_FOLDER):
        full_path = os.path.join(IMAGES_FOLDER, filename)
        if os.path.isfile(full_path):
            IMAGE_FILES.append(full_path)

# Музыкальные очереди и состояния
queues = {}
voice_clients = {}
ytdl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
ytdl = yt_dlp.YoutubeDL(ytdl_opts)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настраиваем интенты
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')
    print(f'Загружено {len(IMAGE_FILES)} локальных картинок.')

# Вспомогательные функции для музыки
def get_audio_url(query):
    """Извлекает URL аудио из YouTube/других источников"""
    try:
        info = ytdl.extract_info(query, download=False)
        if 'entries' in info:
            info = info['entries'][0]
        return info['url']
    except Exception as e:
        print(f"Ошибка при получении аудио: {e}")
        return None

async def play_next(guild_id):
    """Воспроизводит следующий трек в очереди"""
    if guild_id in queues and queues[guild_id]:
        url = queues[guild_id].pop(0)
        voice_client = voice_clients.get(guild_id)
        if voice_client and voice_client.is_connected():
            source = discord.FFmpegPCMAudio(url, **ffmpeg_options)
            def after_playing(error):
                if error:
                    print(f"Ошибка воспроизведения: {error}")
                bot.loop.create_task(play_next(guild_id))
            voice_client.play(source, after=after_playing)
    else:
        # Если очередь пуста, отключаемся через некоторое время
        await asyncio.sleep(300)  # 5 минут
        voice_client = voice_clients.get(guild_id)
        if voice_client and voice_client.is_connected() and not voice_client.is_playing():
            await voice_client.disconnect()
            del voice_clients[guild_id]
            if guild_id in queues:
                del queues[guild_id]

# Команда !play
@bot.command()
async def play(ctx, *, query):
    """Воспроизводит музыку из YouTube"""
    # Проверяем, находится ли пользователь в голосовом канале
    if not ctx.author.voice:
        await ctx.send("Вы должны находиться в голосовом канале!")
        return

    channel = ctx.author.voice.channel
    guild_id = ctx.guild.id

    # Подключаемся к каналу, если ещё не подключены
    if guild_id not in voice_clients or not voice_clients[guild_id].is_connected():
        voice_clients[guild_id] = await channel.connect()

    # Получаем URL аудио
    url = get_audio_url(query)
    if not url:
        await ctx.send("Не удалось получить аудио. Проверьте ссылку или запрос.")
        return

    # Добавляем в очередь
    if guild_id not in queues:
        queues[guild_id] = []
    queues[guild_id].append(url)

    # Если ничего не играет, начинаем воспроизведение
    voice_client = voice_clients[guild_id]
    if not voice_client.is_playing():
        await play_next(guild_id)
        await ctx.send(f"Начинаю воспроизведение: {query}")
    else:
        await ctx.send(f"Добавлено в очередь: {query}")

# Команда !stop
@bot.command()
async def stop(ctx):
    """Останавливает воспроизведение и очищает очередь"""
    guild_id = ctx.guild.id
    if guild_id in voice_clients and voice_clients[guild_id].is_connected():
        voice_clients[guild_id].stop()
        await voice_clients[guild_id].disconnect()
        del voice_clients[guild_id]
        if guild_id in queues:
            del queues[guild_id]
        await ctx.send("Воспроизведение остановлено и очередь очищена.")
    else:
        await ctx.send("Бот не находится в голосовом канале.")

# Команда !skip
@bot.command()
async def skip(ctx):
    """Пропускает текущий трек"""
    guild_id = ctx.guild.id
    if guild_id in voice_clients and voice_clients[guild_id].is_playing():
        voice_clients[guild_id].stop()
        await ctx.send("Трек пропущен.")
        await play_next(guild_id)
    else:
        await ctx.send(f"{SKIP_GIF}")

# Команда !image
@bot.command()
async def image(ctx):
    """Отправляет случайную картинку из локальной папки"""
    if not IMAGE_FILES:
        await ctx.send("Нет доступных картинок в папке.")
        return
    random_image_path = random.choice(IMAGE_FILES)
    # Отправляем файл
    await ctx.send(file=discord.File(random_image_path))

# Реакция на гифку
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