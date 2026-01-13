import tomllib

import pytest
from src.nr_utils.migrate import (
    migrate_bot_settings,
    migrate_legacy_rules,
    migrate_settings_file,
    load_rules_from_settings,
)
from src.nr_utils.message import MessageRule


class TestLegacyRuleMigration:
    """Test migration of legacy conditional messages to new format."""

    def test_migrate_integer_condition(self):
        legacy_rules = [(7, "Lucky seven!", True, False)]
        migrated = migrate_legacy_rules(legacy_rules)

        assert len(migrated) == 1
        assert migrated[0].condition == "=7"
        assert migrated[0].message == "Lucky seven!"
        assert migrated[0].mode == "replace_all"
        assert migrated[0].stop_on_trigger is False

    def test_migrate_range_condition(self):
        legacy_rules = [((1, 10), "Low range", False, True)]
        migrated = migrate_legacy_rules(legacy_rules)

        assert len(migrated) == 1
        assert migrated[0].condition == (1, 10)
        assert migrated[0].message == "Low range"
        assert migrated[0].mode == "add"
        assert migrated[0].stop_on_trigger is True

    def test_migrate_keyword_conditions(self):
        legacy_rules = [
            ("highest", "Maximum!", True, False),
            ("lowest", "Minimum!", False, True)
        ]
        migrated = migrate_legacy_rules(legacy_rules)

        assert len(migrated) == 2
        assert migrated[0].condition == "highest"
        assert migrated[0].mode == "replace_all"
        assert migrated[1].condition == "lowest"
        assert migrated[1].mode == "add"

    def test_migrate_mixed_conditions(self):
        legacy_rules = [
            (69, "Nice", False, False),
            ((1, 100), "In range", True, False),
            ("highest", "Winner!", False, True)
        ]
        migrated = migrate_legacy_rules(legacy_rules)

        assert len(migrated) == 3
        assert migrated[0].condition == "=69"
        assert migrated[0].mode == "add"
        assert migrated[1].condition == (1, 100)
        assert migrated[1].mode == "replace_all"
        assert migrated[2].condition == "highest"
        assert migrated[2].stop_on_trigger is True

    def test_migrate_list_range_condition(self):
        legacy_rules = [([5, 15], "List range", False, False)]
        migrated = migrate_legacy_rules(legacy_rules)

        assert len(migrated) == 1
        assert migrated[0].condition == (5, 15)
        assert migrated[0].message == "List range"

    def test_migrate_invalid_conditions_skipped(self):
        legacy_rules = [
            (7, "Valid", False, False),
            ("invalid", "Should be skipped", False, False),
            (None, "Also invalid", False, False),
            (42, "Valid again", True, True)
        ]
        migrated = migrate_legacy_rules(legacy_rules)

        # Should only have 3 valid rules (invalid ones skipped)
        assert len(migrated) == 3
        assert migrated[0].condition == "=7"
        assert migrated[1].condition == "invalid"  # String conditions are kept as-is
        assert migrated[2].condition == "=42"

    def test_migrate_empty_list(self):
        migrated = migrate_legacy_rules([])
        assert migrated == []


class TestBotSettingsMigration:
    """Test migration of complete bot settings."""

    def test_migrate_settings_with_cond_messages(self):
        settings = {
            "bot": {"token": "abc123"},
            "message": {
                "default_message": "Cool!",
                "cond_messages": [
                    [1, "Unlucky!", True, True],
                    [69, "Nice.", False, False]
                ]
            }
        }

        migrated = migrate_bot_settings(settings)

        assert "cond_messages" not in migrated["message"]
        assert "rules" in migrated["message"]
        assert len(migrated["message"]["rules"]) == 2

        rule1 = migrated["message"]["rules"][0]
        assert rule1["condition"] == "=1"
        assert rule1["message"] == "Unlucky!"
        assert rule1["mode"] == "replace_all"
        assert rule1["stop_on_trigger"] is True

    def test_migrate_settings_without_message_section(self):
        settings = {"bot": {"token": "abc123"}}
        migrated = migrate_bot_settings(settings)
        assert migrated == settings

    def test_migrate_settings_without_cond_messages(self):
        settings = {
            "bot": {"token": "abc123"},
            "message": {"default_message": "Cool!"}
        }
        migrated = migrate_bot_settings(settings)
        assert migrated == settings


class TestRuleLoading:
    """Test loading rules from settings with both formats."""

    def test_load_new_format_rules(self):
        settings = {
            "message": {
                "rules": [
                    {
                        "condition": "=50",
                        "message": "Half way",
                        "mode": "add",
                        "stop_on_trigger": False
                    },
                    {
                        "condition": ">=90",
                        "message": "High roll",
                        "mode": "replace_all",
                        "stop_on_trigger": True,
                        "jump_to_rule": 3,
                        "mutually_exclusive": [2]
                    }
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

    def test_load_legacy_format_rules(self):
        settings = {
            "message": {
                "cond_messages": [
                    [7, "Lucky!", True, False],
                    [(50, 75), "Mid range", False, True]
                ]
            }
        }

        rules = load_rules_from_settings(settings)

        assert len(rules) == 2
        assert rules[0].condition == "=7"
        assert rules[0].mode == "replace_all"
        assert rules[1].condition == (50, 75)
        assert rules[1].stop_on_trigger is True

    def test_load_rules_no_message_section(self):
        settings = {"bot": {"token": "abc123"}}
        rules = load_rules_from_settings(settings)
        assert rules == []

    def test_load_rules_empty_message_section(self):
        settings = {"message": {}}
        rules = load_rules_from_settings(settings)
        assert rules == []

    def test_new_format_takes_precedence(self):
        """Test that new format is used when both formats are present."""
        settings = {
            "message": {
                "rules": [
                    {"condition": "=99", "message": "New format"}
                ],
                "cond_messages": [
                    [77, "Legacy format", False, False]
                ]
            }
        }

        rules = load_rules_from_settings(settings)

        assert len(rules) == 1
        assert rules[0].condition == "=99"
        assert rules[0].message == "New format"


class TestMigrationIntegration:
    """Test end-to-end migration workflow."""

    def test_complete_workflow(self):
        """Test complete migration from legacy to new format."""
        from src.nr_utils.message import generate_message

        # Original legacy format
        legacy_cond_messages = [
            [1, "Minimum!", True, True],
            [(10, 20), "Teen range", False, False],
            ["highest", "Maximum!", False, True]
        ]

        # Test with legacy workflow simulation
        rules = migrate_legacy_rules(legacy_cond_messages)

        # Test various numbers
        result1 = generate_message(1, 1, 100, "Default", rules)
        assert result1 == "Minimum!"  # Should replace and stop

        result2 = generate_message(15, 1, 100, "Default", rules)
        assert result2 == "Default Teen range"  # Should add to default

        result3 = generate_message(100, 1, 100, "Default", rules)
        assert result3 == "Default Maximum!"  # Should add and stop

        result4 = generate_message(50, 1, 100, "Default", rules)
        assert result4 == "Default"  # No matches, just default


class TestMigrationCli:
    def test_migrate_settings_file_updates_file(self, tmp_path):
        settings_path = tmp_path / "bot_settings.toml"
        settings_path.write_text(
            """
[message]
cond_messages = [
    [1, "Minimum!", true, true],
    [[5, 10], "Range", false, false]
]
""".strip()
        , encoding="utf-8")

        migrated = migrate_settings_file(settings_path)
        assert migrated is True

        updated_settings = tomllib.loads(settings_path.read_text(encoding="utf-8"))
        assert "cond_messages" not in updated_settings["message"]
        assert len(updated_settings["message"]["rules"]) == 2
        assert updated_settings["message"]["rules"][0]["condition"] == "=1"

    def test_migrate_settings_file_skips_when_no_legacy(self, tmp_path):
        settings_path = tmp_path / "bot_settings.toml"
        settings_path.write_text(
            """
[message]
number_message = "Your number is {number}."
""".strip()
        , encoding="utf-8")

        migrated = migrate_settings_file(settings_path)
        assert migrated is False

        settings_after = tomllib.loads(settings_path.read_text(encoding="utf-8"))
        assert "cond_messages" not in settings_after["message"]
        assert "rules" not in settings_after["message"]
