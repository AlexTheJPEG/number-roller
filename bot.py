import discord
import tomllib

from pathlib import Path

bot = discord.Bot()

with Path("bot_settings.toml").open("rb") as file:
    settings = tomllib.load(file)


@bot.event
async def on_ready() -> None:
    print("Bot is ready!")


bot.run(settings["bot"]["token"])