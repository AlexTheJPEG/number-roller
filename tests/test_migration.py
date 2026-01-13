from typing import Self

import pytest

from src.nr_utils.message import MessageRule, load_rules_from_settings


class TestLoadRulesFromSettings:
    def test_loads_new_format_rules(self: Self) -> None:
        settings = {
            "message": {
                "rules": [
                    {
                        "condition": "=50",
                        "message": "Half way",
                        "mode": "add",
                        "stop_on_trigger": False,
                    },
                    {
                        "condition": ">=90",
                        "message": "High roll",
                        "mode": "replace_all",
                        "stop_on_trigger": True,
                        "jump_to_rule": 3,
                        "mutually_exclusive": [2],
                    },
                ]
            }
        }

        rules = load_rules_from_settings(settings)

        assert len(rules) == 2
        assert rules[0].condition == "=50"
        assert rules[0].mode == "add"
        assert rules[0].jump_to_rule is None
        assert rules[1].condition == ">=90"
        assert rules[1].jump_to_rule == 3
        assert rules[1].mutually_exclusive == [2]

    def test_returns_empty_without_message_section(self: Self) -> None:
        settings = {"bot": {"token": "abc123"}}
        rules = load_rules_from_settings(settings)
        assert rules == []

    def test_returns_empty_when_rules_missing(self: Self) -> None:
        settings = {"message": {}}
        rules = load_rules_from_settings(settings)
        assert rules == []

    def test_list_conditions_become_tuples(self: Self) -> None:
        settings = {
            "message": {
                "rules": [
                    {
                        "condition": [1, 5],
                        "message": "Between one and five",
                        "mode": "replace_all",
                    }
                ]
            }
        }

        rules = load_rules_from_settings(settings)

        assert len(rules) == 1
        assert isinstance(rules[0], MessageRule)
        assert rules[0].condition == (1, 5)
        assert rules[0].mode == "replace_all"

    def test_invalid_rule_entries_are_skipped(self: Self) -> None:
        settings = {
            "message": {
                "rules": [
                    {"condition": "=10"},  # missing message
                    "totally invalid",
                    {
                        "condition": "=20",
                        "message": "Valid",
                    },
                ]
            }
        }

        rules = load_rules_from_settings(settings)

        assert len(rules) == 1
        assert rules[0].message == "Valid"

    def test_cond_messages_key_raises(self: Self) -> None:
        settings = {
            "message": {
                "cond_messages": [
                    [1, "Legacy", True, True],
                ]
            }
        }

        with pytest.raises(ValueError, match="Legacy message rules"):
            load_rules_from_settings(settings)
