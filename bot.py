import discord
import random
import os
import asyncio
import yt_dlp
import ollama
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# ===== НАСТРОЙКИ =====
# Ссылки на гифки
TARGET_GIF_URL = os.getenv("TARGET_GIF_URL")
SKIP_GIF = os.getenv("SKIP_GIF")
COFFEE_GIF = os.getenv("COFFEE_GIF")

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

# ===== ФУНКЦИЯ ДЛЯ ЧАТА С ИИ =====
async def generate_chat_response(prompt: str, model: str = "qwen3:1.7b") -> str:
    """Генерирует ответ на промпт с помощью Ollama."""
    try:
        response = ollama.chat(model=model, messages=[
            {"role": "user", "content": prompt}
        ])
        return response["message"]["content"].strip()
    except Exception as e:
        print(f"Ошибка при генерации ответа: {e}")
        return "Извините, произошла ошибка при генерации ответа."

# Настраиваем интенты
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='*', intents=intents)

# ===== НАСТРОЙКИ ДЛЯ СЛУЧАЙНОГО ПИНГА =====
TARGET_USER_ID = os.getenv("TARGET_USER_ID")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
MIN_INTERVAL = int(os.getenv("MIN_INTERVAL"))
MAX_INTERVAL = int(os.getenv("MAX_INTERVAL")) 

ping_task_started = False

async def random_ping_loop():
    """Фоновая задача: ждёт случайное время и пинает пользователя."""
    await bot.wait_until_ready()
    if not TARGET_USER_ID or not TARGET_CHANNEL_ID:
        print("Не заданы TARGET_USER_ID или TARGET_CHANNEL_ID. Фоновый пинг отключён.")
        return
    try:
        target_user_id = int(TARGET_USER_ID)
        target_channel_id = int(TARGET_CHANNEL_ID)
    except ValueError:
        print("Ошибка: TARGET_USER_ID и TARGET_CHANNEL_ID должны быть целыми числами.")
        return

    while not bot.is_closed():
        delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
        print(f"Следующий пинг через {delay} секунд.")
        await asyncio.sleep(delay)

        channel = bot.get_channel(target_channel_id)
        if channel is None:
            print(f"Канал с ID {target_channel_id} не найден. Пинг пропущен.")
            continue

        try:
            msg = await channel.send(f"<@{target_user_id}> https://tenor.com/view/markiplier-markiplier-soyjak-soyjak-wojak-bouncing-gif-27376523")
            print(f"Отправлен пинг пользователю {target_user_id} в канал {target_channel_id}")
            # Ждём 5 секунд
            await asyncio.sleep(1)
            await msg.delete()
        except Exception as e:
            print(f"Ошибка при отправке пинга: {e}")

@bot.event
async def on_ready():
    global ping_task_started
    print(f'Бот {bot.user} успешно запущен!')
    print(f'Загружено {len(IMAGE_FILES)} локальных картинок.')
    if not ping_task_started:
        bot.loop.create_task(random_ping_loop())
        ping_task_started = True

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
    if not ctx.author.voice:
        await ctx.send("Вы должны находиться в голосовом канале!")
        return

    channel = ctx.author.voice.channel
    guild_id = ctx.guild.id

    if guild_id not in voice_clients or not voice_clients[guild_id].is_connected():
        voice_clients[guild_id] = await channel.connect()

    url = get_audio_url(query)
    if not url:
        await ctx.send("Не удалось получить аудио. Проверьте ссылку или запрос.")
        return

    if guild_id not in queues:
        queues[guild_id] = []
    queues[guild_id].append(url)

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
    await ctx.send(file=discord.File(random_image_path))

@bot.command()
async def Кофе(ctx):
    """Готовит кофе"""
    await ctx.send(f"Окей, приготовлю {COFFEE_GIF}")

@bot.command(name="чат", aliases=["chat"])
async def chat(ctx, *, message: str):
    """Ведёт диалог с ИИ через Ollama"""
    # Отправляем сообщение о том, что бот думает
    thinking_msg = await ctx.send("🤔 Думаю...")
    try:
        response = await generate_chat_response(message)
        # Обрезаем ответ если слишком длинный (ограничение Discord 2000 символов)
        if len(response) > 1990:
            response = response[:1990] + "..."
        await thinking_msg.edit(content=response)
    except Exception as e:
        await thinking_msg.edit(content=f"Ошибка: {e}")

# Реакция на гифку
REACTIONS = ['👍', '❤️', '😂', '😮', '😢', '😡', '🎉', '🤔', '👀', '🔥', '🥳', '💯']

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Проверяем текст сообщения
    if TARGET_GIF_URL in message.content:
        if IMAGE_FILES:
            random_image_path = random.choice(IMAGE_FILES)
            await message.channel.send(file=discord.File(random_image_path))
        else:
            await message.channel.send("Нет доступных картинок.")

    # Отладка embed'ов (если нужна)
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

    # Проверяем embed'ы на наличие целевой гифки
    for embed in message.embeds:
        if embed.url and "25572384" in embed.url:
            if IMAGE_FILES:
                random_image_path = random.choice(IMAGE_FILES)
                await message.channel.send(file=discord.File(random_image_path))
            else:
                await message.channel.send("Нет доступных картинок.")
            break
        if embed.provider and embed.provider.url == "https://tenor.com/view/%D1%81%D0%BA%D0%B8%D0%BD%D1%8C-%D0%B6%D0%BE%D0%BF%D1%83-%D1%81%D0%BA%D0%B8%D0%BD%D1%8C%D0%B6%D0%BE%D0%BF%D1%83-gif-25572384":
            if IMAGE_FILES:
                random_image_path = random.choice(IMAGE_FILES)
                await message.channel.send(file=discord.File(random_image_path))
            else:
                await message.channel.send("Нет доступных картинок.")
            break

    # Случайная реакция
    reaction = random.choice(REACTIONS)
    try:
        await message.add_reaction(reaction)
        print(f"Поставил реакцию {reaction} на сообщение от {message.author}")
    except discord.Forbidden:
        print("Нет прав на добавление реакций в этом канале.")
    except discord.HTTPException as e:
        print(f"Ошибка при добавлении реакции: {e}")

    await bot.process_commands(message)

bot.run(BOT_TOKEN)