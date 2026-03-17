import discord
from discord.ext import commands
import ollama

class Chat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def generate_chat_response(self, prompt: str, model: str = "qwen3:1.7b") -> str:
        """Генерирует ответ с помощью локальной Ollama."""
        try:
            response = ollama.chat(model=model, messages=[
                {"role": "user", "content": prompt}
            ])
            return response["message"]["content"].strip()
        except Exception as e:
            print(f"Ошибка при генерации ответа: {e}")
            return "Извините, произошла ошибка при генерации ответа."

    @commands.command(name="чат", aliases=["chat"])
    async def chat(self, ctx, *, message: str):
        """Ведёт диалог с ИИ через Ollama"""
        thinking_msg = await ctx.send("🤔 Думаю...")
        try:
            response = await self.generate_chat_response(message)
            if len(response) > 1990:
                response = response[:1990] + "..."
            await thinking_msg.edit(content=response)
        except Exception as e:
            await thinking_msg.edit(content=f"Ошибка: {e}")

async def setup(bot):
    await bot.add_cog(Chat(bot))