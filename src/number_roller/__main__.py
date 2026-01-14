from __future__ import annotations

import logging
import random
from typing import Any

import aiocron
import hikari
import pytz

from ..nr_utils.files import HotReloadingSettings
from ..nr_utils.message import generate_message, load_rules_from_settings

logger = logging.getLogger(__name__)

settings_reloader = HotReloadingSettings()
initial_settings = settings_reloader.snapshot()
bot: hikari.GatewayBot = hikari.GatewayBot(token=initial_settings["bot"]["token"])

_current_schedule: tuple[str, str] = (
    initial_settings["bot"]["cron"],
    initial_settings["bot"]["timezone"],
)
_roll_job: aiocron.Cron | None = None


async def roll() -> None:
    """Roll numbers for each configured user and send the rendered message.

    Returns:
        None.
    """

    settings = settings_reloader.snapshot()

    channel_id: int = settings["bot"]["channel"]
    users: list[int] = settings["bot"]["users"]

    min_number = settings["roll"]["min_number"]
    max_number = settings["roll"]["max_number"]

    numbers: list[int] = [random.randint(min_number, max_number) for _ in users]
    lowest_number: int = min(numbers)
    highest_number: int = max(numbers)

    rules = load_rules_from_settings(settings)

    for index, user_id in enumerate(users):
        number: int = numbers[index]

        number_message: str = settings["message"]["number_message"].replace(r"{number}", str(number))

        default_message: str = settings["message"]["default_message"]
        additional_message: str = generate_message(
            number,
            min_number,
            max_number,
            default_message,
            rules,
            roll_lowest=lowest_number,
            roll_highest=highest_number,
        )

        await bot.rest.create_message(channel_id, f"<@{user_id}> {number_message} {additional_message}")


def _schedule_roll_job(cron_expr: str, timezone_name: str) -> aiocron.Cron:
    """Create and schedule the background cron job that triggers ``roll``.

    Args:
        cron_expr: POSIX cron expression describing when to run the job.
        timezone_name: IANA timezone name used to interpret the cron expression.

    Returns:
        The scheduled ``aiocron`` job handle.
    """

    tz = pytz.timezone(timezone_name)
    logger.info("Scheduling roll job with cron '%s' in timezone '%s'", cron_expr, timezone_name)
    return aiocron.crontab(cron_expr, func=roll, tz=tz)


def _handle_settings_reload(updated_settings: dict[str, Any]) -> None:
    """React to a hot settings update by reconfiguring the cron schedule if needed.

    Args:
        updated_settings: Fresh settings emitted by :class:`HotReloadingSettings`.

    Returns:
        None.
    """

    global _roll_job, _current_schedule

    new_schedule = (
        updated_settings["bot"]["cron"],
        updated_settings["bot"]["timezone"],
    )

    if new_schedule != _current_schedule:
        logger.info("Detected schedule change; reloading cron job")
        if _roll_job is not None:
            _roll_job.stop()
        _roll_job = _schedule_roll_job(*new_schedule)
        _current_schedule = new_schedule


settings_reloader.add_listener(_handle_settings_reload)
_roll_job = _schedule_roll_job(*_current_schedule)


@bot.listen()
async def on_started(_event: hikari.StartedEvent) -> None:
    """Bootstrap the hot-reload watcher once the bot gateway is ready.

    Args:
        _event: The hikari ``StartedEvent`` dispatched by the gateway.

    Returns:
        None.
    """

    logger.info("Bot is ready! Hot reload watcher running.")
    settings_reloader.start()


bot.run()
