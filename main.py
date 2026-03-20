import os
import discord
from discord import app_commands
from deep_translator import GoogleTranslator
from dotenv import load_dotenv  # Добавляем эту строку

load_dotenv()


class TranslatorBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    # Функция для создания контекстного меню (внутри класса!)
    # Мы выносим её отдельно, чтобы потом добавить в дерево команд
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
        # Создаем объект контекстного меню
        menu = app_commands.ContextMenu(
            name="Translate to RU",
            callback=self.context_translate_func,  # указываем на функцию выше
        )
        self.tree.add_command(menu)
        await self.tree.sync()
        print("Команды синхронизированы!")

    async def on_ready(self):
        print(f"Бот {self.user} готов переводить!")


client = TranslatorBot()


# Обычная слэш-команда /tr (можно оставить вне класса или перенести внутрь)
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
