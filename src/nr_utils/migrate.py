"""Migration tool for converting old message rules to the new format."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Union, Any

import tomllib
import tomli_w

from .message import MessageRule


def _is_range_condition(value: Any) -> bool:
    return (
        isinstance(value, (tuple, list))
        and len(value) == 2
        and all(isinstance(bound, int) for bound in value)
    )


def migrate_legacy_rules(
    cond_messages: list[tuple[Union[int, str, tuple[int, int]], str, bool, bool]]
) -> list[MessageRule]:
    """
    Convert legacy conditional messages to new MessageRule format.

    Args:
        cond_messages: Legacy format list of tuples:
                      [(condition, message, replace, stop), ...]

    Returns:
        List of MessageRule objects in the new format
    """
    rules = []

    for condition, message, replace, stop in cond_messages:
        # Convert condition - keep tuples as tuples for proper handling
        if _is_range_condition(condition):
            # Keep range tuple/list as-is for proper parsing
            migrated_condition = tuple(condition)
        elif isinstance(condition, int):
            # Integer -> "=integer"
            migrated_condition = f"={condition}"
        elif isinstance(condition, str):
            # String (should be "highest" or "lowest") -> keep as is
            migrated_condition = condition
        else:
            # Skip invalid conditions
            continue

        # Convert replace flag to new mode system
        mode = "replace_all" if replace else "add"

        rules.append(MessageRule(
            condition=migrated_condition,
            message=message,
            mode=mode,
            stop_on_trigger=stop
        ))

    return rules


def migrate_bot_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """
    Migrate bot settings from legacy format to new format.

    Args:
        settings: Dictionary containing bot settings

    Returns:
        Updated settings with migrated message rules
    """
    if "message" not in settings or "cond_messages" not in settings["message"]:
        return settings

    # Extract legacy conditional messages
    legacy_cond_messages = settings["message"]["cond_messages"]

    # Migrate to new format
    new_rules = migrate_legacy_rules(legacy_cond_messages)

    # Update settings
    rules_data = []
    for rule in new_rules:
        rule_dict = {
            "condition": rule.condition,
            "message": rule.message,
            "mode": rule.mode,
            "stop_on_trigger": rule.stop_on_trigger
        }
        if rule.jump_to_rule is not None:
            rule_dict["jump_to_rule"] = rule.jump_to_rule
        if rule.mutually_exclusive is not None:
            rule_dict["mutually_exclusive"] = rule.mutually_exclusive
        rules_data.append(rule_dict)

    settings["message"]["rules"] = rules_data

    # Remove legacy format
    del settings["message"]["cond_messages"]

    return settings


def load_rules_from_settings(settings: dict[str, Any]) -> list[MessageRule]:
    """
    Load message rules from bot settings, supporting both new and legacy formats.

    Args:
        settings: Dictionary containing bot settings

    Returns:
        List of MessageRule objects
    """
    if "message" not in settings:
        return []

    message_settings = settings["message"]

    # Check for new format first
    if "rules" in message_settings:
        rules = []
        for rule_data in message_settings["rules"]:
            rules.append(MessageRule(
                condition=rule_data["condition"],
                message=rule_data["message"],
                mode=rule_data.get("mode", "add"),
                stop_on_trigger=rule_data.get("stop_on_trigger", False),
                jump_to_rule=rule_data.get("jump_to_rule"),
                mutually_exclusive=rule_data.get("mutually_exclusive")
            ))
        return rules

    # Fall back to legacy format
    elif "cond_messages" in message_settings:
        return migrate_legacy_rules(message_settings["cond_messages"])

    return []


def migrate_settings_file(settings_path: Path) -> bool:
    """Load a settings file, migrate legacy rules, and persist the result."""

    with settings_path.open("rb") as settings_file:
        settings = tomllib.load(settings_file)

    message_section = settings.get("message")
    if not message_section or "cond_messages" not in message_section:
        return False

    migrate_bot_settings(settings)

    rendered_settings = tomli_w.dumps(settings)
    settings_path.write_text(rendered_settings, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy bot message rules to the new format.")
    parser.add_argument("settings_file", type=Path, help="Path to the bot settings TOML file to migrate.")

    args = parser.parse_args(argv)
    settings_path: Path = args.settings_file

    if not settings_path.exists():
        parser.exit(1, f"Settings file '{settings_path}' does not exist.\n")
    if not settings_path.is_file():
        parser.exit(1, f"Settings file '{settings_path}' is not a file.\n")

    try:
        migrated = migrate_settings_file(settings_path)
    except tomllib.TOMLDecodeError as exc:
        parser.exit(1, f"Failed to parse '{settings_path}': {exc}\n")
    except OSError as exc:
        parser.exit(1, f"Failed to migrate '{settings_path}': {exc}\n")

    if migrated:
        parser.exit(0, f"Migrated legacy rules in '{settings_path}'.\n")
    else:
        parser.exit(0, "No legacy rules found; no changes were made.\n")


if __name__ == "__main__":  # pragma: no cover - manual CLI invocation
    main()
