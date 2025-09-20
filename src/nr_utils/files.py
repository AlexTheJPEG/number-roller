import tomllib
from pathlib import Path
from typing import Any


def load_bot_settings() -> dict[str, Any]:
    with Path("bot_settings.toml").open("rb") as settings:
        return tomllib.load(settings)
