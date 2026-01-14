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


def _parse_condition(condition_str: str, allowed_lowest: int, allowed_highest: int) -> Union[str, tuple[int, int]]:
    """Normalize a textual condition into a comparable value.

    Args:
        condition_str: The raw condition expression provided in the settings.
        lowest_number: The minimum allowed number in the rolling range.
        highest_number: The maximum allowed number in the rolling range.

    Returns:
        Either a validated comparison string (e.g., ``"=50"``) or a tuple representing an inclusive range.

    Raises:
        ValueError: If the condition cannot be parsed or falls outside the allowed bounds.
    """
    # Handle keywords
    if condition_str.lower() in ["highest", "lowest"]:
        return condition_str.lower()

    # Handle ranges (e.g., "1-100")
    range_match = re.match(r"^(\d+)-(\d+)$", condition_str)
    if range_match:
        min_val, max_val = int(range_match.group(1)), int(range_match.group(2))

        # Validate range is within bounds
        if min_val < allowed_lowest or max_val > allowed_highest:
            raise ValueError(f"Range {min_val}-{max_val} is outside bounds {allowed_lowest}-{allowed_highest}")

        return (min_val, max_val)

    # Handle comparisons (e.g., "=99", ">=7", "<30")
    comp_match = re.match(r"^([><=!]+)(-?\d+)$", condition_str)
    if comp_match:
        value_str = comp_match.group(2)
        value = int(value_str)

        # Validate value is within bounds
        if value < allowed_lowest or value > allowed_highest:
            raise ValueError(f"Comparison value {value} is outside bounds {allowed_lowest}-{allowed_highest}")

        return condition_str

    raise ValueError(f"Invalid condition: {condition_str}")


def _evaluate_condition(condition: Union[str, tuple[int, int]], number: int, lowest_number: int, highest_number: int) -> bool:
    """Determine whether a number satisfies a parsed condition.

    Args:
        condition: A comparison string or tuple produced by :func:`_parse_condition`.
        number: The value produced for a particular user.
        lowest_number: The minimum allowable roll.
        highest_number: The maximum allowable roll.

    Returns:
        ``True`` if the supplied number matches the condition, ``False`` otherwise.
    """
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
    number: int,
    allowed_lowest: int,
    allowed_highest: int,
    default_message: str,
    rules: list[MessageRule],
    *,
    roll_lowest: Optional[int] = None,
    roll_highest: Optional[int] = None,
) -> str:
    """
    Generate a message based on the given number and rules.

    Args:
        number: The number to generate a message for
        allowed_lowest: The lowest possible configured number
        allowed_highest: The highest possible configured number
        default_message: The default message
        rules: List of MessageRule objects to process
        roll_lowest: Optional lowest actual roll in the batch (used for "lowest" keyword)
        roll_highest: Optional highest actual roll in the batch (used for "highest" keyword)

    Returns:
        The generated message string
    """
    # Validate input number is within bounds
    if not (allowed_lowest <= number <= allowed_highest):
        raise ValueError(f"Number {number} is outside bounds {allowed_lowest}-{allowed_highest}")

    effective_lowest = roll_lowest if roll_lowest is not None else allowed_lowest
    effective_highest = roll_highest if roll_highest is not None else allowed_highest
    effective_lowest = max(allowed_lowest, effective_lowest)
    effective_highest = min(allowed_highest, effective_highest)

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
                _parse_condition(rule.condition, allowed_lowest, allowed_highest)
                if isinstance(rule.condition, str)
                else rule.condition
            )
            condition_met = _evaluate_condition(parsed_condition, number, effective_lowest, effective_highest)
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
    """Build rule objects from a settings dictionary.

    Args:
        settings: The fully parsed TOML configuration loaded from disk.

    Returns:
        A list of :class:`MessageRule` instances that can be supplied to :func:`generate_message`.

    Raises:
        ValueError: If legacy ``cond_messages`` entries are present.
    """

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
        if isinstance(condition, (list, tuple)):
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
