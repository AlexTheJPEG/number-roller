# Number Roller
A Discord bot that generates random numbers on a schedule for users in a server.
Written using [hikari](https://github.com/hikari-py/hikari).

## 🛠 Setup
To get started, [create a Discord application](https://discord.com/developers/applications) and add a bot user for it.

After you've made your application, clone this repo somewhere on your machine, then create the bot settings file `bot_settings.toml`. An example file has been included in the repo detailing every required setting.

As for dependencies, they are all handled by [uv](https://github.com/astral-sh/uv). Install uv on your machine if you haven't already, then simply run `uv sync` in the project directory.

To run the bot, simply run `uv run python -m src.number_roller`.

### 🐋 Docker
You can also run this bot as a Docker container. Simply run the following Docker commands in the root directory:

```
docker build . -t number-roller
docker run number-roller
```

## 🧩 Message rules

Messages are customized with `[[message.rules]]` tables inside `bot_settings.toml`. Each
rule is evaluated in order, sharing the following fields:

- `condition`: comparison expressions like `=50`, `>=90`, `!=13`; ranges written as
  `10-20`; or the keywords `highest` / `lowest`.
- `message`: the text to add or use when the condition matches. Empty strings are ignored.
- `mode` (default `add`):
  - `add` appends to the current message queue.
  - `replace_last` overwrites the most recent non-empty entry.
  - `replace_except_default` clears everything except the original default message before
    appending the new text.
  - `replace_all` clears the entire queue (including the default message) before adding.
- `stop_on_trigger` (default `false`): stop processing additional rules once this one
  matches.
- `jump_to_rule` (optional): skip directly to another rule index (zero-based) after this
  one runs, allowing you to build lightweight state machines.
- `mutually_exclusive` (optional list of indices): marks later rules that should be skipped
  if this rule fires.

Example configuration snippet:

```
[[message.rules]]
condition = "=1"
message = "Unlucky!"
mode = "replace_all"
stop_on_trigger = true

[[message.rules]]
condition = ">=90"
message = "High roll!"
mode = "add"

[[message.rules]]
condition = "highest"
message = "You have the highest number."
stop_on_trigger = true
```

Example run (users Alice, Bob, and Charlie; `number_message = "Your number is {number}."`; `default_message = "Cool!"`):

| User    | Roll | Explanation                                                                 | Bot output                                            |
|---------|-----:|------------------------------------------------------------------------------|-------------------------------------------------------|
| Alice   |    1 | Matches the first rule, so it replaces everything with "Unlucky!".          | `Your number is 1. Unlucky!`                          |
| Bob     |   94 | Triggers the `>=90` rule and is also the highest roll, so both messages add. | `Your number is 94. Cool! High roll! You have the highest number.` |
| Charlie |   57 | Matches no rules, so only the default message is appended.                   | `Your number is 57. Cool!`                            |
