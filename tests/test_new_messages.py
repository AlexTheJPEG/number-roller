import pytest
from src.nr_utils.message import generate_message, MessageRule


@pytest.fixture
def basic_range():
    """Basic test range and default message."""
    return 1, 100, "Default message"


class TestBasicFunctionality:
    """Test basic message generation functionality."""

    def test_empty_rules_returns_default(self, basic_range):
        lowest, highest, default = basic_range
        result = generate_message(50, lowest, highest, default, [])
        assert result == default

    def test_empty_default_and_rules_returns_empty(self, basic_range):
        lowest, highest, _ = basic_range
        result = generate_message(50, lowest, highest, "", [])
        assert result == ""


class TestComparisons:
    """Test comparison conditions (=, !=, >, >=, <, <=)."""

    def test_exact_match_comparison(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="=50", message="Exact match")]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Exact match"

    def test_not_equal_comparison(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="!=50", message="Not fifty")]
        result = generate_message(25, lowest, highest, default, rules)
        assert result == "Default message Not fifty"

    def test_greater_than_comparison(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition=">50", message="Greater than fifty")]
        result = generate_message(75, lowest, highest, default, rules)
        assert result == "Default message Greater than fifty"

    def test_greater_than_or_equal_comparison(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition=">=50", message="At least fifty")]

        # Test equal case
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message At least fifty"

        # Test greater case
        result = generate_message(75, lowest, highest, default, rules)
        assert result == "Default message At least fifty"

    def test_less_than_comparison(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="<50", message="Less than fifty")]
        result = generate_message(25, lowest, highest, default, rules)
        assert result == "Default message Less than fifty"

    def test_less_than_or_equal_comparison(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="<=50", message="At most fifty")]

        # Test equal case
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message At most fifty"

        # Test less case
        result = generate_message(25, lowest, highest, default, rules)
        assert result == "Default message At most fifty"

    def test_comparison_out_of_bounds_ignored(self, basic_range):
        lowest, highest, default = basic_range
        # This should be ignored due to being out of bounds
        rules = [MessageRule(condition="=200", message="Should be ignored")]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == default


class TestRanges:
    """Test range conditions (e.g., 1-100)."""

    def test_number_in_range(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="25-75", message="In middle range")]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message In middle range"

    def test_number_at_range_boundaries(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="25-75", message="In range")]

        # Test lower boundary
        result = generate_message(25, lowest, highest, default, rules)
        assert result == "Default message In range"

        # Test upper boundary
        result = generate_message(75, lowest, highest, default, rules)
        assert result == "Default message In range"

    def test_number_outside_range(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="25-75", message="In range")]
        result = generate_message(10, lowest, highest, default, rules)
        assert result == default

    def test_range_out_of_bounds_ignored(self, basic_range):
        lowest, highest, default = basic_range
        # This should be ignored due to being out of bounds
        rules = [MessageRule(condition="50-200", message="Should be ignored")]
        result = generate_message(75, lowest, highest, default, rules)
        assert result == default


class TestKeywords:
    """Test highest and lowest keywords."""

    def test_highest_keyword(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="highest", message="Maximum value")]
        result = generate_message(highest, lowest, highest, default, rules)
        assert result == "Default message Maximum value"

    def test_lowest_keyword(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="lowest", message="Minimum value")]
        result = generate_message(lowest, lowest, highest, default, rules)
        assert result == "Default message Minimum value"

    def test_highest_keyword_case_insensitive(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="HIGHEST", message="Maximum value")]
        result = generate_message(highest, lowest, highest, default, rules)
        assert result == "Default message Maximum value"


class TestMessageModes:
    """Test different message modes."""

    def test_add_mode(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", mode="add"),
            MessageRule(condition=">=50", message="Second", mode="add")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First Second"

    def test_replace_last_mode(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", mode="add"),
            MessageRule(condition=">49", message="Second", mode="add"),
            MessageRule(condition=">=50", message="Third", mode="replace_last")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First Third"

    def test_replace_except_default_mode(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", mode="add"),
            MessageRule(condition=">49", message="Second", mode="add"),
            MessageRule(condition=">=50", message="Third", mode="replace_except_default")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Third"

    def test_replace_all_mode(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", mode="add"),
            MessageRule(condition=">49", message="Second", mode="add"),
            MessageRule(condition=">=50", message="Third", mode="replace_all")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Third"

    def test_replace_last_on_empty_queue(self, basic_range):
        lowest, highest, _ = basic_range
        rules = [MessageRule(condition="=50", message="Only message", mode="replace_last")]
        result = generate_message(50, lowest, highest, "", rules)
        assert result == "Only message"


class TestStopOnTrigger:
    """Test stop_on_trigger functionality."""

    def test_stop_on_trigger_halts_processing(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", stop_on_trigger=True),
            MessageRule(condition="=50", message="Should not appear")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First"

    def test_stop_on_trigger_only_affects_matching_rules(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=40", message="First"),
            MessageRule(condition="=50", message="Second", stop_on_trigger=True),
            MessageRule(condition="=50", message="Should not appear")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Second"


class TestJumpToRule:
    """Test jump_to_rule functionality."""

    def test_jump_to_rule_skips_intermediate_rules(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", jump_to_rule=2),
            MessageRule(condition="=50", message="Should be skipped"),
            MessageRule(condition="=50", message="Third")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First Third"

    def test_jump_to_rule_invalid_index_ignored(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", jump_to_rule=10),
            MessageRule(condition="=50", message="Second")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First"

    def test_jump_backwards_ignored(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First"),
            MessageRule(condition="=50", message="Second", jump_to_rule=0)
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First Second"


class TestMutualExclusion:
    """Test mutually_exclusive functionality."""

    def test_mutually_exclusive_rules_skipped(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", mutually_exclusive=[1, 2]),
            MessageRule(condition="=50", message="Should be excluded"),
            MessageRule(condition="=50", message="Also excluded"),
            MessageRule(condition="=50", message="Fourth")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First Fourth"

    def test_mutually_exclusive_invalid_indices_ignored(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", mutually_exclusive=[10, 20]),
            MessageRule(condition="=50", message="Second")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First Second"

    def test_mutually_exclusive_backwards_indices_ignored(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=40", message="First"),
            MessageRule(condition="=50", message="Second", mutually_exclusive=[0])
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Second"


class TestComplexScenarios:
    """Test complex scenarios combining multiple features."""

    def test_complex_rule_interaction(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition=">=40", message="At least 40"),
            MessageRule(condition="=50", message="Exactly 50", mutually_exclusive=[3]),
            MessageRule(condition="<=60", message="At most 60"),
            MessageRule(condition="50-55", message="In special range"),  # This gets excluded
            MessageRule(condition=">45", message="Greater than 45", stop_on_trigger=True)
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message At least 40 Exactly 50 At most 60 Greater than 45"

    def test_jump_with_mutual_exclusion(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="First", jump_to_rule=3, mutually_exclusive=[1, 2]),
            MessageRule(condition="=50", message="Should be excluded"),
            MessageRule(condition="=50", message="Also excluded"),
            MessageRule(condition="=50", message="Jumped to")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message First Jumped to"

    def test_multiple_message_modes(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition=">=40", message="First", mode="add"),
            MessageRule(condition=">=50", message="Second", mode="replace_last"),
            MessageRule(condition=">=50", message="Third", mode="add")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Second Third"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_number_out_of_bounds_raises_error(self, basic_range):
        lowest, highest, default = basic_range
        rules = []

        with pytest.raises(ValueError, match="outside bounds"):
            generate_message(0, lowest, highest, default, rules)

        with pytest.raises(ValueError, match="outside bounds"):
            generate_message(101, lowest, highest, default, rules)

    def test_invalid_condition_format_ignored(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="invalid", message="Should be ignored"),
            MessageRule(condition="=50", message="Valid rule")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Valid rule"

    def test_empty_message_in_rule(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="=50", message="")]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == default  # Empty messages get filtered out

    def test_whitespace_only_messages_handled(self, basic_range):
        lowest, highest, default = basic_range
        rules = [MessageRule(condition="=50", message="   ")]
        result = generate_message(50, lowest, highest, default, rules)
        # Should be filtered out, leaving only default
        assert result == default

    def test_zero_and_negative_numbers(self):
        lowest, highest, default = -10, 10, "Default"
        rules = [
            MessageRule(condition="=0", message="Zero"),
            MessageRule(condition="=-5", message="Negative five"),
            MessageRule(condition=">0", message="Positive")
        ]

        result = generate_message(0, lowest, highest, default, rules)
        assert result == "Default Zero"

        result = generate_message(-5, lowest, highest, default, rules)
        assert result == "Default Negative five"

        result = generate_message(5, lowest, highest, default, rules)
        assert result == "Default Positive"


class TestBoundaryValidation:
    """Test boundary validation for conditions."""

    def test_comparison_boundary_validation(self):
        lowest, highest, default = 10, 90, "Default"

        # Valid conditions
        rules = [MessageRule(condition="=50", message="Valid")]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default Valid"

        # Invalid conditions should be silently ignored
        rules = [
            MessageRule(condition="=5", message="Too low"),  # Below lowest
            MessageRule(condition="=95", message="Too high")  # Above highest
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == default

    def test_range_boundary_validation(self):
        lowest, highest, default = 10, 90, "Default"

        # Valid range
        rules = [MessageRule(condition="20-80", message="Valid range")]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default Valid range"

        # Invalid ranges should be silently ignored
        rules = [
            MessageRule(condition="5-15", message="Range too low"),  # Min below lowest
            MessageRule(condition="85-95", message="Range too high")  # Max above highest
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == default


class TestRuleIndexing:
    """Test rule indexing for jumps and mutual exclusion."""

    def test_rule_indices_are_zero_based(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="Rule 0", jump_to_rule=2),
            MessageRule(condition="=50", message="Rule 1 - skipped"),
            MessageRule(condition="=50", message="Rule 2")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Rule 0 Rule 2"

    def test_mutual_exclusion_indices_are_zero_based(self, basic_range):
        lowest, highest, default = basic_range
        rules = [
            MessageRule(condition="=50", message="Rule 0", mutually_exclusive=[1]),
            MessageRule(condition="=50", message="Rule 1 - excluded"),
            MessageRule(condition="=50", message="Rule 2")
        ]
        result = generate_message(50, lowest, highest, default, rules)
        assert result == "Default message Rule 0 Rule 2"