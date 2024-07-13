# Number Roller
A Discord bot that generates random numbers on a schedule for users in a server.
Written using [Pycord](https://github.com/Pycord-Development/pycord).

## 🛠 Setup
To get started, [create a Discord application](https://discord.com/developers/applications) and add a bot user for it.

After you've made your application, clone this repo somewhere on your machine, then create the bot settings file `bot_settings.toml`. An example file has been included in the repo detailing every required setting.

As for dependencies, they are all handled by [Poetry](https://github.com/python-poetry/poetry). Install Poetry on your machine if you haven't already, then simply run `poetry install` in the project directory.

To run the bot, activate the virtual environment created by Poetry using `poetry shell` and run `python -m number_roller` in the project directory.

### 🐋 Docker
You can also run this bot as a Docker container. Simply run the following Docker commands in the root directory:
```
docker build . -t number-roller
docker run number-roller
```

## 💬 Notes
An alternative way to run your bot without explicitly activating the virtual environment is by running `poetry run python -m number_roller`. If you're running the bot on VSCode or a Python IDE, the virtual environment may be activated automatically.
