import random

from pytest import fixture

from src.nr_utils.message import generate_message
from src.nr_utils.migrate import migrate_legacy_rules


@fixture
def basic_settings() -> tuple:
    return (1, 10, "Cool!")


def legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages):
    """Helper function to test legacy format through migration."""
    rules = migrate_legacy_rules(cond_messages)
    return generate_message(number, lowest_number, highest_number, default_message, rules)


def test_random_number_prints_default(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = random.randint(lowest_number, highest_number)
    assert legacy_generate_message(number, highest_number, lowest_number, default_message, []) == default_message


def test_lowest_number_prints_default(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = lowest_number
    assert legacy_generate_message(number, highest_number, lowest_number, default_message, []) == default_message


def test_highest_number_prints_default(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = highest_number
    assert legacy_generate_message(number, highest_number, lowest_number, default_message, []) == default_message


def test_exact_number_match_replaces_message(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 7
    cond_messages = [(7, "Lucky seven!", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Lucky seven!"


def test_exact_number_match_appends_message(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 7
    cond_messages = [(7, "Lucky seven!", False, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! Lucky seven!"


def test_highest_keyword_replaces_message(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = highest_number
    cond_messages = [("highest", "Maximum reached!", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Maximum reached!"


def test_lowest_keyword_replaces_message(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = lowest_number
    cond_messages = [("lowest", "Minimum value!", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Minimum value!"


def test_multiple_exact_matches_with_break(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 5
    cond_messages = [
        (5, "First match", False, True),  # Break after this
        (5, "Second match", False, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! First match"


def test_multiple_exact_matches_without_break(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 5
    cond_messages = [
        (5, "First match", False, False),
        (5, "Second match", False, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! First match Second match"


def test_no_matches_returns_default(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 5
    cond_messages = [
        (3, "Three", True, False),
        (7, "Seven", True, False),
        ("highest", "Max", True, False),
        ("lowest", "Min", True, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == default_message


def test_zero_as_exact_match() -> None:
    # Use range that includes 0
    lowest_number, highest_number, default_message = -5, 10, "Cool!"
    number = 0
    cond_messages = [(0, "Zero!", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Zero!"


def test_negative_exact_match() -> None:
    # Use range that includes -5
    lowest_number, highest_number, default_message = -10, 10, "Cool!"
    number = -5
    cond_messages = [(-5, "Negative five!", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Negative five!"


def test_empty_conditional_messages_list(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 5
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, [])
    assert result == default_message


def test_complex_mixed_conditions(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 8
    cond_messages = [
        (3, "Three", False, False),
        ((5, 9), "Five to nine", False, False),
        (8, "Eight exactly", False, False),
        ("highest", "Maximum", False, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! Five to nine Eight exactly"


def test_number_in_range_replaces_message(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 5
    cond_messages = [((1, 10), "In range!", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "In range!"


def test_number_in_range_appends_message(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 7
    cond_messages = [((1, 10), "In range!", False, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! In range!"


def test_number_outside_range_uses_default() -> None:
    # Use wider range to accommodate test number
    lowest_number, highest_number, default_message = 1, 20, "Cool!"
    number = 15
    cond_messages = [((1, 10), "In range!", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == default_message


def test_range_boundary_conditions(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    cond_messages = [((5, 8), "Boundary test", True, False)]

    # Test lower boundary
    result = legacy_generate_message(5, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Boundary test"

    # Test upper boundary
    result = legacy_generate_message(8, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Boundary test"

    # Test just outside boundaries
    result = legacy_generate_message(4, highest_number, lowest_number, default_message, cond_messages)
    assert result == default_message

    result = legacy_generate_message(9, highest_number, lowest_number, default_message, cond_messages)
    assert result == default_message


def test_multiple_ranges_first_match_wins(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 6
    cond_messages = [
        ((1, 10), "First range", True, False),
        ((5, 8), "Second range", True, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    # In the legacy implementation, when multiple replace conditions match, the last one wins
    assert result == "Second range"


def test_range_with_break_flag(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 6
    cond_messages = [
        ((1, 10), "First range", False, True),  # Break after this
        ((5, 8), "Second range", False, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! First range"


def test_single_number_range(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 5
    cond_messages = [((5, 5), "Exact match via range", True, False)]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Exact match via range"


def test_mixed_conditions_range_and_exact(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = 7
    cond_messages = [
        (7, "Exact match", False, False),
        ((5, 9), "Range match", False, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! Exact match Range match"


def test_range_with_highest_lowest_keywords(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    cond_messages = [
        ((1, 5), "Low range", False, False),
        ("highest", "It's the max!", False, False),
        ("lowest", "It's the min!", False, False)
    ]

    # Test highest
    result = legacy_generate_message(highest_number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! It's the max!"

    # Test lowest
    result = legacy_generate_message(lowest_number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Cool! Low range It's the min!"


def test_negative_number_ranges() -> None:
    # Use range that includes negative numbers
    lowest_number, highest_number, default_message = -10, 10, "Cool!"
    number = -5
    cond_messages = [
        ((-10, -1), "Negative range", True, False),
        ((0, 10), "Positive range", True, False)
    ]
    result = legacy_generate_message(number, highest_number, lowest_number, default_message, cond_messages)
    assert result == "Negative range"


def test_invalid_range_tuple_ignored() -> None:
    # Test that malformed tuples don't crash the function
    number = 5
    cond_messages = [
        ((1,), "Invalid tuple", True, False),  # Wrong tuple length
        ((1, 10), "Valid range", True, False)
    ]
    result = legacy_generate_message(number, 10, 1, "Default", cond_messages)
    assert result == "Valid range"
