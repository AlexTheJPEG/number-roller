import asyncio
from pathlib import Path
from textwrap import dedent
from typing import Any

from src.nr_utils.files import HotReloadingSettings, load_bot_settings


def _render_settings(channel: int = 123, cron: str = "0 9 * * *") -> str:
    return dedent(
        f"""
        [bot]
        token = "abc123"
        channel = {channel}
        users = [1, 2, 3]
        cron = "{cron}"
        timezone = "UTC"

        [roll]
        min_number = 1
        max_number = 10

        [message]
        default_message = "Default"
        number_message = "Number {{number}}"
        """
    ).strip()


def test_load_bot_settings_accepts_custom_path(tmp_path: Path) -> None:
    settings_path = tmp_path / "custom_settings.toml"
    settings_path.write_text(_render_settings(channel=999), encoding="utf-8")

    loaded = load_bot_settings(settings_path)

    assert loaded["bot"]["channel"] == 999


def test_hot_reloading_settings_notifies_on_change(tmp_path: Path) -> None:
    settings_path = tmp_path / "bot_settings.toml"
    settings_path.write_text(_render_settings(channel=1), encoding="utf-8")

    async def _runner() -> None:
        reloader = HotReloadingSettings(path=settings_path, poll_interval=0.01)
        notifications: list[int] = []
        change_event = asyncio.Event()

        def _listener(data: dict[str, Any]) -> None:
            notifications.append(data["bot"]["channel"])
            change_event.set()

        reloader.add_listener(_listener)
        reloader.start(asyncio.get_running_loop())

        settings_path.write_text(_render_settings(channel=777), encoding="utf-8")

        await asyncio.wait_for(change_event.wait(), timeout=1)

        assert notifications[-1] == 777
        assert reloader.snapshot()["bot"]["channel"] == 777

        await reloader.stop()

    asyncio.run(_runner())
