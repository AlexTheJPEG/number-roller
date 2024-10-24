import tomllib
from pathlib import Path


def load_bot_settings() -> dict:
    with Path("bot_settings.toml").open("rb") as settings:
        return tomllib.load(settings)
