"""Tests for naming utilities."""
import pytest
from tests.import_helper import build_temp_control_data_name, constants


class TestBuildTempControlDataName:
    """Tests for build_temp_control_data_name function."""

    def test_appends_correct_suffix(self):
        """Should append _TempControl_Data suffix."""
        result = build_temp_control_data_name("my_controller")
        assert result == "my_controller_TempControl_Data"

    def test_uses_constant_suffix(self):
        """Should use suffix from constants."""
        result = build_temp_control_data_name("ctrl")
        expected = f"ctrl{constants.SUFFIXE_TEMP_CONTROL_DATA}"
        assert result == expected

    def test_empty_string_input(self):
        """Should handle empty string input."""
        result = build_temp_control_data_name("")
        assert result == "_TempControl_Data"

    def test_special_characters(self):
        """Should handle controller names with special characters."""
        result = build_temp_control_data_name("ctrl_L_arm|joint_01")
        assert result == "ctrl_L_arm|joint_01_TempControl_Data"

    def test_preserves_underscores(self):
        """Should preserve underscores in controller name."""
        result = build_temp_control_data_name("left_arm_ctrl")
        assert result == "left_arm_ctrl_TempControl_Data"

    def test_preserves_namespaces(self):
        """Should preserve Maya-style namespaces in controller name."""
        result = build_temp_control_data_name("character:arm_ctrl")
        assert result == "character:arm_ctrl_TempControl_Data"


class TestConstantsSuffixes:
    """Tests that naming constants are correctly defined."""

    def test_temp_control_data_suffix_defined(self):
        """SUFFIXE_TEMP_CONTROL_DATA should be defined."""
        assert hasattr(constants, 'SUFFIXE_TEMP_CONTROL_DATA')
        assert constants.SUFFIXE_TEMP_CONTROL_DATA == "_TempControl_Data"

    def test_temp_control_ctrl_suffix_defined(self):
        """SUFFIXE_TEMP_CONTROL_CTRLLER should be defined."""
        assert hasattr(constants, 'SUFFIXE_TEMP_CONTROL_CTRLLER')
        assert constants.SUFFIXE_TEMP_CONTROL_CTRLLER == "_TempControl_Ctrl"

    def test_temp_pivot_suffix_defined(self):
        """SUFFIXE_TEMP_PIVOT should be defined."""
        assert hasattr(constants, 'SUFFIXE_TEMP_PIVOT')
        assert constants.SUFFIXE_TEMP_PIVOT == "_TMP_PIVOT"
