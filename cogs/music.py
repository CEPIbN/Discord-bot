import discord
import yt_dlp
from discord.ext import commands
import asyncio
from config import YDL_OPTS, FFMPEG_OPTIONS, SKIP_GIF

ytdl = yt_dlp.YoutubeDL(YDL_OPTS)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}      
        self.voice_clients = {}

    def get_audio_url(self, query):
        """Извлекает прямую ссылку на аудио из YouTube/других источников"""
        try:
            info = ytdl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            return info['url']
        except Exception as e:
            print(f"Ошибка получения аудио: {e}")
            return None

    async def play_next(self, guild_id):
        """Воспроизводит следующий трек в очереди"""
        if guild_id in self.queues and self.queues[guild_id]:
            url = self.queues[guild_id].pop(0)
            voice_client = self.voice_clients.get(guild_id)
            if voice_client and voice_client.is_connected():
                source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

                def after_playing(error):
                    if error:
                        print(f"Ошибка воспроизведения: {error}")
                    # Планируем следующий трек в цикле событий бота
                    asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop)

                voice_client.play(source, after=after_playing)
        else:
            # Очередь пуста – отключаемся через 5 минут, если ничего не появилось
            await asyncio.sleep(300)
            voice_client = self.voice_clients.get(guild_id)
            if voice_client and voice_client.is_connected() and not voice_client.is_playing():
                await voice_client.disconnect()
                del self.voice_clients[guild_id]
                if guild_id in self.queues:
                    del self.queues[guild_id]

    @commands.command()
    async def play(self, ctx, *, query):
        """Воспроизводит музыку из YouTube"""
        if not ctx.author.voice:
            await ctx.send("Вы должны находиться в голосовом канале!")
            return

        channel = ctx.author.voice.channel
        guild_id = ctx.guild.id

        # Подключаемся, если ещё не в канале
        if guild_id not in self.voice_clients or not self.voice_clients[guild_id].is_connected():
            self.voice_clients[guild_id] = await channel.connect()

        url = self.get_audio_url(query)
        if not url:
            await ctx.send("Не удалось получить аудио. Проверьте ссылку или запрос.")
            return

        if guild_id not in self.queues:
            self.queues[guild_id] = []
        self.queues[guild_id].append(url)

        voice_client = self.voice_clients[guild_id]
        if not voice_client.is_playing():
            await self.play_next(guild_id)
            await ctx.send(f"Начинаю воспроизведение: {query}")
        else:
            await ctx.send(f"Добавлено в очередь: {query}")

    @commands.command()
    async def stop(self, ctx):
        """Останавливает воспроизведение и очищает очередь"""
        guild_id = ctx.guild.id
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_connected():
            self.voice_clients[guild_id].stop()
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
            if guild_id in self.queues:
                del self.queues[guild_id]
            await ctx.send("Воспроизведение остановлено и очередь очищена.")
        else:
            await ctx.send("Бот не находится в голосовом канале.")

    @commands.command()
    async def skip(self, ctx):
        """Пропускает текущий трек"""
        guild_id = ctx.guild.id
        if guild_id in self.voice_clients and self.voice_clients[guild_id].is_playing():
            self.voice_clients[guild_id].stop()
            await ctx.send("Трек пропущен.")
            await self.play_next(guild_id)
        else:
            await ctx.send(SKIP_GIF)

async def setup(bot):
    await bot.add_cog(Music(bot))