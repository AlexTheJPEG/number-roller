import re
from dataclasses import dataclass
from typing import Any, Optional, Union


@dataclass
class MessageRule:
    """Represents a single message generation rule."""

    # Condition: comparison string (e.g. "=99", ">=7", "<30"), range tuple, or keywords
    condition: Union[str, tuple[int, int]]

    # The message to apply
    message: str

    # Message mode: "add", "replace_last", "replace_except_default", "replace_all"
    mode: str = "add"

    # Stop processing more rules if this rule triggers
    stop_on_trigger: bool = False

    # Jump to specific rule index if this rule triggers
    jump_to_rule: Optional[int] = None

    # List of mutually exclusive rule indices
    mutually_exclusive: Optional[list[int]] = None


def _parse_condition(condition_str: str, lowest_number: int, highest_number: int) -> Union[str, tuple[int, int]]:
    """Parse a condition string into a usable condition."""
    # Handle keywords
    if condition_str.lower() in ["highest", "lowest"]:
        return condition_str.lower()

    # Handle ranges (e.g., "1-100")
    range_match = re.match(r"^(\d+)-(\d+)$", condition_str)
    if range_match:
        min_val, max_val = int(range_match.group(1)), int(range_match.group(2))

        # Validate range is within bounds
        if min_val < lowest_number or max_val > highest_number:
            raise ValueError(f"Range {min_val}-{max_val} is outside bounds {lowest_number}-{highest_number}")

        return (min_val, max_val)

    # Handle comparisons (e.g., "=99", ">=7", "<30")
    comp_match = re.match(r"^([><=!]+)(-?\d+)$", condition_str)
    if comp_match:
        value_str = comp_match.group(2)
        value = int(value_str)

        # Validate value is within bounds
        if value < lowest_number or value > highest_number:
            raise ValueError(f"Comparison value {value} is outside bounds {lowest_number}-{highest_number}")

        return condition_str

    raise ValueError(f"Invalid condition: {condition_str}")


def _evaluate_condition(condition: Union[str, tuple[int, int]], number: int, lowest_number: int, highest_number: int) -> bool:
    """Evaluate whether a condition is met for the given number."""
    if isinstance(condition, tuple):
        # Range condition
        min_val, max_val = condition
        return min_val <= number <= max_val

    if isinstance(condition, str):
        # Handle keywords
        if condition == "highest":
            return number == highest_number
        elif condition == "lowest":
            return number == lowest_number

        # Handle comparisons
        comp_match = re.match(r"^([><=!]+)(-?\d+)$", condition)
        if comp_match:
            operator, value_str = comp_match.groups()
            value = int(value_str)

            operations = {
                "=": lambda n, v: n == v,
                "!=": lambda n, v: n != v,
                ">": lambda n, v: n > v,
                ">=": lambda n, v: n >= v,
                "<": lambda n, v: n < v,
                "<=": lambda n, v: n <= v,
            }
            return operations.get(operator, lambda n, v: False)(number, value)

    return False


def generate_message(
    number: int, lowest_number: int, highest_number: int, default_message: str, rules: list[MessageRule]
) -> str:
    """
    Generate a message based on the given number and rules.

    Args:
        number: The number to generate a message for
        lowest_number: The lowest possible number
        highest_number: The highest possible number
        default_message: The default message
        rules: List of MessageRule objects to process

    Returns:
        The generated message string
    """
    # Validate input number is within bounds
    if not (lowest_number <= number <= highest_number):
        raise ValueError(f"Number {number} is outside bounds {lowest_number}-{highest_number}")

    # Track which rules have been excluded due to mutual exclusion
    excluded_rules = set()

    # Start with default message in the queue
    message_queue = [default_message] if default_message else []

    # Process rules sequentially
    rule_index = 0
    while rule_index < len(rules):
        # Skip if this rule is excluded
        if rule_index in excluded_rules:
            rule_index += 1
            continue

        rule = rules[rule_index]

        try:
            # Parse and evaluate the condition
            parsed_condition = (
                _parse_condition(rule.condition, lowest_number, highest_number)
                if isinstance(rule.condition, str)
                else rule.condition
            )
            condition_met = _evaluate_condition(parsed_condition, number, lowest_number, highest_number)
        except ValueError:
            # Skip invalid conditions
            rule_index += 1
            continue

        if condition_met:
            # Apply the rule based on its mode
            if rule.mode == "add":
                message_queue.append(rule.message)
            elif rule.mode == "replace_last":
                if message_queue:
                    message_queue[-1] = rule.message
                else:
                    message_queue.append(rule.message)
            elif rule.mode == "replace_except_default":
                # Keep default message, replace everything else
                message_queue = [default_message, rule.message] if default_message else [rule.message]
            elif rule.mode == "replace_all":
                # Replace everything including default
                message_queue = [rule.message]

            # Handle mutual exclusion
            if rule.mutually_exclusive:
                for excluded_index in rule.mutually_exclusive:
                    if excluded_index > rule_index and excluded_index < len(rules):
                        excluded_rules.add(excluded_index)

            # Handle stop condition
            if rule.stop_on_trigger:
                break

            # Handle jump condition
            if rule.jump_to_rule is not None:
                if rule.jump_to_rule > rule_index and rule.jump_to_rule < len(rules):
                    rule_index = rule.jump_to_rule
                    continue
                else:
                    # Invalid jump index, stop processing
                    break

        rule_index += 1

    # Join all messages with spaces, filtering out empty strings
    return " ".join(msg for msg in message_queue if msg).strip()


def load_rules_from_settings(settings: dict[str, Any]) -> list[MessageRule]:
    """Load the supported MessageRule objects from the provided settings dict."""

    message_settings = settings.get("message")
    if not isinstance(message_settings, dict):
        return []

    if "cond_messages" in message_settings:
        raise ValueError(
            "Legacy message rules ('cond_messages') are no longer supported."
            " Please migrate to [[message.rules]] entries."
        )

    rules_config = message_settings.get("rules")
    if not isinstance(rules_config, list):
        return []

    rules: list[MessageRule] = []
    for rule_dict in rules_config:
        if not isinstance(rule_dict, dict):
            continue

        condition = rule_dict.get("condition")
        message = rule_dict.get("message")
        if condition is None or message is None:
            continue

        normalized_condition: Union[str, tuple[int, int]]
        if isinstance(condition, list):
            if len(condition) != 2:
                continue
            normalized_condition = (int(condition[0]), int(condition[1]))
        elif isinstance(condition, tuple):
            if len(condition) != 2:
                continue
            normalized_condition = (int(condition[0]), int(condition[1]))
        else:
            normalized_condition = str(condition)

        rules.append(
            MessageRule(
                condition=normalized_condition,
                message=str(message),
                mode=rule_dict.get("mode", "add"),
                stop_on_trigger=rule_dict.get("stop_on_trigger", False),
                jump_to_rule=rule_dict.get("jump_to_rule"),
                mutually_exclusive=rule_dict.get("mutually_exclusive"),
            )
        )

    return rules

