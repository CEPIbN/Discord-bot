import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_GIF_URL = os.getenv("TARGET_GIF_URL")
SKIP_GIF = os.getenv("SKIP_GIF")
COFFEE_GIF = os.getenv("COFFEE_GIF")
TARGET_USER_ID = os.getenv("TARGET_USER_ID")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
MIN_INTERVAL = int(os.getenv("MIN_INTERVAL"))
MAX_INTERVAL = int(os.getenv("MAX_INTERVAL"))
IMAGES_FOLDER = "images"
IMAGE_FILES = []

if os.path.exists(IMAGES_FOLDER):
    for filename in os.listdir(IMAGES_FOLDER):
        full_path = os.path.join(IMAGES_FOLDER, filename)
        if os.path.isfile(full_path):
            IMAGE_FILES.append(full_path)

# === Реакции для случайного добавления ===
REACTIONS = ['👍', '❤️', '😂', '😮', '😢', '😡', '🎉', '🤔', '👀', '🔥', '🥳', '💯']

# === Настройки YouTube DL для музыки ===
YDL_OPTS = {
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

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}