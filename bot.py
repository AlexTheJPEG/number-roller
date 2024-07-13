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
    lowest_number = min(numbers)
    highest_number = max(numbers)

    cond_messages = settings["message"]["cond_messages"]

    for index in range(len(users)):
        number = numbers[index]

        number_message = settings["message"]["number_message"].replace(r"{number}", str(number))

        additional_message = settings["message"]["default_message"]
        for cm in cond_messages:
            if number == cm[0] or \
                (cm[0] == "highest" and number == highest_number) or \
                    (cm[0] == "lowest" and number == lowest_number):
                additional_message = cm[1] if cm[2] else f"{additional_message} {cm[1]}"
                if cm[3]:
                    break

        await channel.send(f"<@{users[index]}> {number_message} {additional_message}")


bot.run(settings["bot"]["token"])
