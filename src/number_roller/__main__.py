import random
from typing import Any

import aiocron
import hikari
import pytz

from ..nr_utils.files import load_bot_settings
from ..nr_utils.message import generate_message
from ..nr_utils.migrate import load_rules_from_settings

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

    # Load message rules (supports both new and legacy formats)
    rules = load_rules_from_settings(settings)

    for index in range(len(users)):
        number: int = numbers[index]

        number_message: str = settings["message"]["number_message"].replace(r"{number}", str(number))

        default_message: str = settings["message"]["default_message"]
        additional_message: str = generate_message(number, lowest_number, highest_number, default_message, rules)

        await bot.rest.create_message(channel_id, f"<@{users[index]}> {number_message} {additional_message}")


bot.run()
