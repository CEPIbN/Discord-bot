import discord
from discord.ext import commands
import json
import os
from typing import Optional, List

KNOWLEDGE_FILE = "knowledge.json"
DEFAULT_PROMPT = "Ты полезный ассистент, который отвечает на вопросы."

class Knowledge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.knowledge_data = self.load_knowledge()

    def load_knowledge(self) -> dict:
        """Загружает данные из JSON файла."""
        if not os.path.exists(KNOWLEDGE_FILE):
            default_data = {
                "system_prompt": DEFAULT_PROMPT,
                "facts": []
            }
            self.save_knowledge(default_data)
            return default_data
        try:
            with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Если файл повреждён, создаём заново
            default_data = {
                "system_prompt": DEFAULT_PROMPT,
                "facts": []
            }
            self.save_knowledge(default_data)
            return default_data

    def save_knowledge(self, data: Optional[dict] = None):
        """Сохраняет данные в JSON файл."""
        if data is None:
            data = self.knowledge_data
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @commands.group(name="промт", aliases=["prompt"], invoke_without_command=True)
    async def prompt_group(self, ctx):
        """Управление системным промтом."""
        await ctx.send_help(ctx.command)

    @prompt_group.command(name="установить", aliases=["set"])
    async def set_prompt(self, ctx, *, prompt_text: str):
        """Устанавливает новый системный промт."""
        self.knowledge_data["system_prompt"] = prompt_text
        self.save_knowledge()
        await ctx.send(f"✅ Системный промт обновлён:\n```{prompt_text[:500]}```")

    @prompt_group.command(name="показать", aliases=["show"])
    async def show_prompt(self, ctx):
        """Показывает текущий системный промт."""
        prompt = self.knowledge_data.get("system_prompt", DEFAULT_PROMPT)
        await ctx.send(f"📝 Текущий системный промт:\n```{prompt}```")

    @commands.group(name="знание", aliases=["knowledge", "fact"], invoke_without_command=True)
    async def knowledge_group(self, ctx):
        """Управление базой знаний."""
        await ctx.send_help(ctx.command)

    @knowledge_group.command(name="добавить", aliases=["add"])
    async def add_fact(self, ctx, *, fact: str):
        """Добавляет факт в базу знаний."""
        if "facts" not in self.knowledge_data:
            self.knowledge_data["facts"] = []
        self.knowledge_data["facts"].append(fact)
        self.save_knowledge()
        await ctx.send(f"✅ Факт добавлен (всего: {len(self.knowledge_data['facts'])})")

    @knowledge_group.command(name="удалить", aliases=["remove"])
    async def remove_fact(self, ctx, index: int):
        """Удаляет факт по индексу (начиная с 1)."""
        facts = self.knowledge_data.get("facts", [])
        if index < 1 or index > len(facts):
            await ctx.send(f"❌ Неверный индекс. Доступные индексы: 1-{len(facts)}")
            return
        removed = facts.pop(index - 1)
        self.knowledge_data["facts"] = facts
        self.save_knowledge()
        await ctx.send(f"✅ Факт удалён:\n```{removed[:200]}```")

    @knowledge_group.command(name="список", aliases=["list"])
    async def list_facts(self, ctx):
        """Показывает все факты в базе знаний."""
        facts = self.knowledge_data.get("facts", [])
        if not facts:
            await ctx.send("📭 База знаний пуста.")
            return
        lines = [f"{i+1}. {fact[:100]}{'...' if len(fact) > 100 else ''}" for i, fact in enumerate(facts)]
        text = "\n".join(lines)
        if len(text) > 1990:
            text = text[:1990] + "..."
        await ctx.send(f"📚 Факты ({len(facts)}):\n```{text}```")

    @knowledge_group.command(name="очистить", aliases=["clear"])
    async def clear_facts(self, ctx):
        """Очищает всю базу знаний."""
        self.knowledge_data["facts"] = []
        self.save_knowledge()
        await ctx.send("✅ База знаний очищена.")

    @commands.command(name="чатсбазой", aliases=["chatkb"])
    async def chat_with_knowledge(self, ctx, *, message: str):
        """Чат с использованием системного промта и базы знаний."""
        # Загружаем текущий промт
        system_prompt = self.knowledge_data.get("system_prompt", DEFAULT_PROMPT)
        facts = self.knowledge_data.get("facts", [])
        # Формируем контекст
        context = ""
        if facts:
            context = "Контекст (база знаний):\n" + "\n".join(f"- {fact}" for fact in facts[:5])  # ограничим 5 фактами
        full_prompt = f"{system_prompt}\n\n{context}\n\nВопрос: {message}\nОтвет:"
        # Используем существующую генерацию из чат-кога
        chat_cog = self.bot.get_cog("Chat")
        if chat_cog:
            thinking_msg = await ctx.send("🤔 Думаю...")
            try:
                response = await chat_cog.generate_chat_response(full_prompt)
                if len(response) > 1990:
                    response = response[:1990] + "..."
                await thinking_msg.edit(content=response)
            except Exception as e:
                await thinking_msg.edit(content=f"Ошибка: {e}")
        else:
            await ctx.send("❌ Чат-модуль не загружен.")

async def setup(bot):
    await bot.add_cog(Knowledge(bot))