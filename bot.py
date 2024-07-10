import aiocron
import discord
import random
import tomllib

from pathlib import Path

bot = discord.Bot()

with Path("bot_settings.toml").open("rb") as file:
    settings = tomllib.load(file)


@bot.event
async def on_ready() -> None:
    print("Bot is ready!")


@aiocron.crontab(settings["bot"]["cron"])
async def roll():
    channel = bot.get_channel(settings["bot"]["channel"])
    users = settings["bot"]["users"]
    
    generated_numbers = [random.randint(1, 1000) for _ in users]
    smallest_number = min(generated_numbers)
    largest_number = max(generated_numbers)

    for index in range(len(users)):
        await channel.send(f"<@{users[index]}> {generated_numbers[index]}")


bot.run(settings["bot"]["token"])