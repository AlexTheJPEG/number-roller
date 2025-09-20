import random
from typing import Any

import aiocron
import hikari
import pytz

from ..nr_utils.files import load_bot_settings
from ..nr_utils.message import generate_message

settings: dict[str, Any] = load_bot_settings()
bot: hikari.GatewayBot = hikari.GatewayBot(token=settings["bot"]["token"])


@bot.listen()
async def on_started(event: hikari.StartedEvent) -> None:
    print("Bot is ready!")


@aiocron.crontab(settings["bot"]["cron"], tz=pytz.timezone(settings["bot"]["timezone"]))
async def roll() -> None:
    channel_id: int = settings["bot"]["channel"]
    users: list[int] = settings["bot"]["users"]

    numbers: list[int] = [random.randint(settings["roll"]["min_number"], settings["roll"]["max_number"]) for _ in users]
    lowest_number: int = min(numbers)
    highest_number: int = max(numbers)

    cond_messages: list[tuple[int, str, bool, bool]] = settings["message"]["cond_messages"]

    for index in range(len(users)):
        number: int = numbers[index]

        number_message: str = settings["message"]["number_message"].replace(r"{number}", str(number))

        default_message: str = settings["message"]["default_message"]
        additional_message: str = generate_message(number, highest_number, lowest_number, default_message, cond_messages)

        await bot.rest.create_message(channel_id, f"<@{users[index]}> {number_message} {additional_message}")


bot.run()
