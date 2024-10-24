# Number Roller
A Discord bot that generates random numbers on a schedule for users in a server.
Written using [Pycord](https://github.com/Pycord-Development/pycord).

## 🛠 Setup
To get started, [create a Discord application](https://discord.com/developers/applications) and add a bot user for it.

After you've made your application, clone this repo somewhere on your machine, then create the bot settings file `bot_settings.toml`. An example file has been included in the repo detailing every required setting.

As for dependencies, they are all handled by [uv](https://github.com/astral-sh/uv). Install uv on your machine if you haven't already, then simply run `uv sync` in the project directory.

To run the bot, simply run `uv run python -m src.number_roller`.

### 🐋 Docker
(UNDER CONSTRUCTION)
