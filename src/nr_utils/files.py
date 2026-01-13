import asyncio
import contextlib
import inspect
import logging
import tomllib
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Self


def load_bot_settings(path: str | Path = "bot_settings.toml") -> dict[str, Any]:
    settings_path = Path(path)
    with settings_path.open("rb") as settings:
        return tomllib.load(settings)


class HotReloadingSettings:
    """Monitor bot_settings.toml for changes and publish updates."""

    def __init__(self: Self, path: str | Path = "bot_settings.toml", *, poll_interval: float = 1.0) -> None:
        self._path = Path(path)
        self._poll_interval = poll_interval
        self._settings: dict[str, Any] = load_bot_settings(self._path)
        self._mtime_ns = self._path.stat().st_mtime_ns
        self._listeners: list[Callable[[dict[str, Any]], Awaitable[None] | None]] = []
        self._task: asyncio.Task[None] | None = None
        self._logger = logging.getLogger(__name__)

    def snapshot(self: Self) -> dict[str, Any]:
        """Return the latest cached settings snapshot."""

        return self._settings

    def add_listener(self: Self, listener: Callable[[dict[str, Any]], Awaitable[None] | None]) -> None:
        """Register a callback that is invoked after each successful reload."""

        self._listeners.append(listener)

    def start(self: Self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        """Begin polling for file changes."""

        if self._task is not None:
            return

        if loop is None:
            loop = asyncio.get_running_loop()

        self._task = loop.create_task(self._watch_loop())

    async def stop(self: Self) -> None:
        """Stop polling for file changes."""

        if self._task is None:
            return

        task = self._task
        self._task = None
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    async def _watch_loop(self: Self) -> None:
        try:
            while True:
                await asyncio.sleep(self._poll_interval)
                if self._refresh_from_disk():
                    await self._notify_listeners()
        except asyncio.CancelledError:
            return

    def _refresh_from_disk(self: Self) -> bool:
        try:
            current_mtime = self._path.stat().st_mtime_ns
        except FileNotFoundError:
            self._logger.warning("Settings file '%s' is missing; retaining current configuration.", self._path)
            return False

        if current_mtime == self._mtime_ns:
            return False

        try:
            self._settings = load_bot_settings(self._path)
        except (tomllib.TOMLDecodeError, OSError) as exc:
            self._logger.warning("Failed to reload settings from '%s': %s", self._path, exc)
            return False

        self._mtime_ns = current_mtime
        self._logger.info("Reloaded settings from '%s'", self._path)
        return True

    async def _notify_listeners(self: Self) -> None:
        for listener in self._listeners:
            result = listener(self._settings)
            if inspect.isawaitable(result):
                await result
