import random

import aiocron
import hikari
import pytz

from ..nr_utils.files import load_bot_settings
from ..nr_utils.message import generate_message

settings = load_bot_settings()
bot = hikari.GatewayBot(token=settings["bot"]["token"])


@bot.listen()
async def on_started(event: hikari.StartedEvent) -> None:
    print("Bot is ready!")


@aiocron.crontab(settings["bot"]["cron"], tz=pytz.timezone(settings["bot"]["timezone"]))
async def roll() -> None:
    channel_id = settings["bot"]["channel"]
    users = settings["bot"]["users"]

    numbers = [random.randint(settings["roll"]["min_number"], settings["roll"]["max_number"]) for _ in users]
    lowest_number = min(numbers)
    highest_number = max(numbers)

    cond_messages = settings["message"]["cond_messages"]

    for index in range(len(users)):
        number = numbers[index]

        number_message = settings["message"]["number_message"].replace(r"{number}", str(number))

        default_message = settings["message"]["default_message"]
        additional_message = generate_message(number, highest_number, lowest_number, default_message, cond_messages)

        await bot.rest.create_message(channel_id, f"<@{users[index]}> {number_message} {additional_message}")


bot.run()
