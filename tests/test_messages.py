import random

from pytest import fixture

from src.nr_utils.message import generate_message


@fixture
def basic_settings() -> tuple:
    return (1, 10, "Cool!")


def test_random_number_prints_default(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = random.randint(lowest_number, highest_number)
    assert generate_message(number, highest_number, lowest_number, default_message, []) == default_message


def test_lowest_number_prints_default(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = lowest_number
    assert generate_message(number, highest_number, lowest_number, default_message, []) == default_message


def test_highest_number_prints_default(basic_settings: tuple) -> None:
    lowest_number, highest_number, default_message = basic_settings
    number = highest_number
    assert generate_message(number, highest_number, lowest_number, default_message, []) == default_message
