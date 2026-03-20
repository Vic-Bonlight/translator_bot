import os
import discord
from aiohttp import web  # ДОБАВЛЕНО: нужно для работы сервера
from discord import app_commands
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()


# --- ДОБАВЛЕНО: Функция для Koyeb Health Check ---
async def handle(request):
    return web.Response(text="Bot is alive")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Koyeb ищет порт 8000 по умолчанию
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    print("Web server started on port 8000")


# -----------------------------------------------


class TranslatorBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def context_translate_func(
        self, interaction: discord.Interaction, message: discord.Message
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            if not message.content:
                await interaction.followup.send("В сообщении нет текста для перевода!")
                return

            translated = GoogleTranslator(source="auto", target="ru").translate(
                message.content
            )
            await interaction.followup.send(
                f"**Оригинал:** {message.content}\n\n**Перевод:**\n{translated}"
            )
        except Exception as e:
            await interaction.followup.send(f"Ошибка перевода: {e}")

    async def setup_hook(self):
        # ДОБАВЛЕНО: Запуск сервера прямо внутри бота
        self.loop.create_task(start_web_server())

        menu = app_commands.ContextMenu(
            name="Translate to RU",
            callback=self.context_translate_func,
        )
        self.tree.add_command(menu)
        await self.tree.sync()
        print("Команды синхронизированы!")

    async def on_ready(self):
        print(f"Бот {self.user} готов переводить!")


client = TranslatorBot()


@client.tree.command(name="tr", description="Перевести текст на русский")
@app_commands.describe(text="Что перевести?")
async def translate_cmd(interaction: discord.Interaction, text: str):
    await interaction.response.defer(ephemeral=True)
    try:
        translated = GoogleTranslator(source="auto", target="ru").translate(text)
        await interaction.followup.send(f"**Перевод:**\n{translated}")
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}")


client.run(os.getenv("BOT_TOKEN"))
