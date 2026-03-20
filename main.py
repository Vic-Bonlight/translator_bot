import os
import discord
from aiohttp import web
from discord import app_commands
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()


# --- Веб-сервер для Koyeb ---
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
# ВАЖНО: В LANG_MENU только 5 языков (лимит Discord)
LANG_MENU = {
    "RU": {"name": "Русский", "code": "ru"},
    "EN": {"name": "English", "code": "en"},
    "DE": {"name": "Deutsch", "code": "de"},
    "FR": {"name": "Français", "code": "fr"},
    "ES": {"name": "Español", "code": "es"},
}

# Все языки для команды /tr
ALL_LANGS = LANG_MENU.copy()
ALL_LANGS["ZH"] = {"name": "Chinese", "code": "zh-CN"}


class TranslatorBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.loop.create_task(start_web_server())

        # Создаем контекстные меню (ровно 5 штук)
        for lang_id in LANG_MENU.keys():
            self.create_context_menu(lang_id)

        await self.tree.sync()
        print("Команды синхронизированы!")

    def create_context_menu(self, lang_id):
        async def context_menu_callback(
            interaction: discord.Interaction, message: discord.Message
        ):
            await interaction.response.defer(ephemeral=True)
            try:
                if not message.content:
                    await interaction.followup.send("Текст не найден!")
                    return

                target_code = LANG_MENU[lang_id]["code"]
                translated = GoogleTranslator(
                    source="auto", target=target_code
                ).translate(message.content)
                lang_name = LANG_MENU[lang_id]["name"]
                await interaction.followup.send(
                    f"**Перевод на {lang_name}:**\n{translated}"
                )
            except Exception as e:
                await interaction.followup.send(f"Ошибка: {e}")

        menu = app_commands.ContextMenu(
            name=f"Translate to {lang_id}", callback=context_menu_callback
        )
        # --- ДОБАВЬТЕ ЭТИ СТРОКИ НИЖЕ ---
        # Разрешаем использовать в личке и на серверах
        menu.allowed_contexts = discord.AppCommandContext(
            guild=True, dm_channel=True, private_channel=True
        )
        # Разрешаем установку и на сервер, и пользователю в профиль
        menu.allowed_installs = discord.AppInstallationType(guild=True, user=True)
        # -------------------------------
        self.tree.add_command(menu)

    async def on_ready(self):
        print(f"Бот {self.user} готов!")


client = TranslatorBot()


@client.tree.command(name="tr", description="Перевести текст")
@app_commands.describe(text="Текст", language="Язык")
# Добавляем контексты здесь тоже:
@app_commands.allowed_contexts(guild=True, dm_channel=True, private_channel=True)
@app_commands.allowed_installs(guild=True, user=True)
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
        target_code = ALL_LANGS[language.value]["code"]
        translated = GoogleTranslator(source="auto", target=target_code).translate(text)
        await interaction.followup.send(f"**Перевод ({language.name}):**\n{translated}")
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}")


client.run(os.getenv("BOT_TOKEN"))
