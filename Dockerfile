# Используем официальный образ Python
FROM python:3.13-slim

# Устанавливаем системные зависимости для ffmpeg и других библиотек
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libnacl-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем проект
COPY . .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Запускаем бота
CMD ["python", "bot.py"]