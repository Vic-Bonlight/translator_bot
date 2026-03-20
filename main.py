import os
import discord
from aiohttp import web
from discord import app_commands
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()


# --- Веб-сервер для Koyeb Health Check ---
async def handle(request):
    return web.Response(text="Bot is alive")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()


# --- Словарь настроек языков ---
LANGS = {
    "RU": {"name": "Русский", "code": "ru"},
    "EN": {"name": "English", "code": "en"},
    "DE": {"name": "Deutsch", "code": "de"},
    "FR": {"name": "Français", "code": "fr"},
    "ES": {"name": "Español", "code": "es"},
    "ZH": {"name": "Chinese", "code": "zh-CN"},
}


class TranslatorBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    # Универсальная функция перевода для контекстного меню
    async def universal_context_translate(
        self,
        interaction: discord.Interaction,
        message: discord.Message,
        target_lang: str,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            if not message.content:
                await interaction.followup.send("Нет текста для перевода!")
                return

            translated = GoogleTranslator(
                source="auto", target=LANGS[target_lang]["code"]
            ).translate(message.content)
            lang_name = LANGS[target_lang]["name"]
            await interaction.followup.send(
                f"**Перевод на {lang_name}:**\n{translated}"
            )
        except Exception as e:
            await interaction.followup.send(f"Ошибка: {e}")

    async def setup_hook(self):
        # Запускаем сервер для Koyeb
        self.loop.create_task(start_web_server())

        # Создаем контекстные меню для каждого языка из списка
        for lang_id, info in LANGS.items():
            # Используем default value в lambda, чтобы зафиксировать lang_id
            ctx_menu = app_commands.ContextMenu(
                name=f"Translate to {lang_id}",
                callback=lambda i, m, l=lang_id: self.universal_context_translate(
                    i, m, l
                ),
            )
            self.tree.add_command(ctx_menu)

        await self.tree.sync()
        print("Команды синхронизированы!")

    async def on_ready(self):
        print(f"Бот {self.user} готов к работе на 6 языках!")


client = TranslatorBot()


# Слэш-команда /tr с выбором языка
@client.tree.command(name="tr", description="Перевести текст на выбранный язык")
@app_commands.describe(text="Текст для перевода", language="Выберите язык")
@app_commands.choices(
    language=[
        app_commands.Choice(name="Русский", value="RU"),
        app_commands.Choice(name="English", value="EN"),
        app_commands.Choice(name="Deutsch", value="DE"),
        app_commands.Choice(name="Français", value="FR"),
        app_commands.Choice(name="Español", value="ES"),
        app_commands.Choice(name="Chinese", value="ZH"),
    ]
)
async def translate_cmd(
    interaction: discord.Interaction, text: str, language: app_commands.Choice[str]
):
    await interaction.response.defer(ephemeral=True)
    try:
        target_code = LANGS[language.value]["code"]
        translated = GoogleTranslator(source="auto", target=target_code).translate(text)
        await interaction.followup.send(f"**Перевод ({language.name}):**\n{translated}")
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}")


client.run(os.getenv("BOT_TOKEN"))
