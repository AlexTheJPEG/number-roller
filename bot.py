import random
from pathlib import Path

import aiocron
import discord
import tomllib

bot = discord.Bot()

with Path("bot_settings.toml").open("rb") as file:
    settings = tomllib.load(file)


@bot.event
async def on_ready() -> None:
    print("Bot is ready!")


@aiocron.crontab(settings["bot"]["cron"])
async def roll() -> None:
    channel = bot.get_channel(settings["bot"]["channel"])
    users = settings["bot"]["users"]

    numbers = [random.randint(settings["roll"]["min_number"], settings["roll"]["max_number"]) for _ in users]
    smallest_number = min(numbers)
    largest_number = max(numbers)

    for index in range(len(users)):
        number = numbers[index]
        number_message = settings["message"]["number_message"].replace(r"{number}", str(number))
        default_message = settings["message"]["default_message"]
        await channel.send(f"<@{users[index]}> {number_message} {default_message}")


bot.run(settings["bot"]["token"])
