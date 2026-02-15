"""Tests for ControllerCreationMode enum and label mappings."""
import pytest
from tests.import_helper import (
    ControllerCreationMode,
    MODE_LABEL_TO_ENUM,
    MODE_ENUM_TO_LABEL,
)


class TestControllerCreationModeEnum:
    """Tests for the ControllerCreationMode enum values."""

    def test_world_space_exists(self):
        """WORLD_SPACE should be a valid enum value."""
        assert ControllerCreationMode.WORLD_SPACE is not None
        assert ControllerCreationMode.WORLD_SPACE.value == 1

    def test_object_space_exists(self):
        """OBJECT_SPACE should be a valid enum value."""
        assert ControllerCreationMode.OBJECT_SPACE is not None
        assert ControllerCreationMode.OBJECT_SPACE.value == 2

    def test_relative_space_exists(self):
        """RELATIVE_SPACE should be a valid enum value."""
        assert ControllerCreationMode.RELATIVE_SPACE is not None
        assert ControllerCreationMode.RELATIVE_SPACE.value == 3

    def test_camera_space_exists(self):
        """CAMERA_SPACE should be a valid enum value."""
        assert ControllerCreationMode.CAMERA_SPACE is not None
        assert ControllerCreationMode.CAMERA_SPACE.value == 4

    def test_enum_has_four_members(self):
        """Enum should have exactly 4 members."""
        assert len(ControllerCreationMode) == 4


class TestModeLabelToEnumMapping:
    """Tests for MODE_LABEL_TO_ENUM dictionary."""

    def test_world_space_label_maps_correctly(self):
        """'World Space' should map to WORLD_SPACE enum."""
        assert MODE_LABEL_TO_ENUM["World Space"] == ControllerCreationMode.WORLD_SPACE

    def test_object_space_label_maps_correctly(self):
        """'Object Space' should map to OBJECT_SPACE enum."""
        assert MODE_LABEL_TO_ENUM["Object Space"] == ControllerCreationMode.OBJECT_SPACE

    def test_relative_space_label_maps_correctly(self):
        """'Relative Space' should map to RELATIVE_SPACE enum."""
        assert MODE_LABEL_TO_ENUM["Relative Space"] == ControllerCreationMode.RELATIVE_SPACE

    def test_camera_space_label_maps_correctly(self):
        """'Camera Space' should map to CAMERA_SPACE enum."""
        assert MODE_LABEL_TO_ENUM["Camera Space"] == ControllerCreationMode.CAMERA_SPACE

    def test_label_to_enum_has_all_modes(self):
        """MODE_LABEL_TO_ENUM should have entries for all enum values."""
        assert len(MODE_LABEL_TO_ENUM) == len(ControllerCreationMode)


class TestModeEnumToLabelMapping:
    """Tests for MODE_ENUM_TO_LABEL dictionary."""

    def test_world_space_enum_maps_correctly(self):
        """WORLD_SPACE should map to 'World Space' label."""
        assert MODE_ENUM_TO_LABEL[ControllerCreationMode.WORLD_SPACE] == "World Space"

    def test_object_space_enum_maps_correctly(self):
        """OBJECT_SPACE should map to 'Object Space' label."""
        assert MODE_ENUM_TO_LABEL[ControllerCreationMode.OBJECT_SPACE] == "Object Space"

    def test_relative_space_enum_maps_correctly(self):
        """RELATIVE_SPACE should map to 'Relative Space' label."""
        assert MODE_ENUM_TO_LABEL[ControllerCreationMode.RELATIVE_SPACE] == "Relative Space"

    def test_camera_space_enum_maps_correctly(self):
        """CAMERA_SPACE should map to 'Camera Space' label."""
        assert MODE_ENUM_TO_LABEL[ControllerCreationMode.CAMERA_SPACE] == "Camera Space"

    def test_enum_to_label_has_all_modes(self):
        """MODE_ENUM_TO_LABEL should have entries for all enum values."""
        assert len(MODE_ENUM_TO_LABEL) == len(ControllerCreationMode)


class TestBidirectionalConsistency:
    """Tests for bidirectional mapping consistency."""

    def test_roundtrip_label_to_enum_to_label(self):
        """Converting label->enum->label should return original label."""
        for label, enum_val in MODE_LABEL_TO_ENUM.items():
            assert MODE_ENUM_TO_LABEL[enum_val] == label

    def test_roundtrip_enum_to_label_to_enum(self):
        """Converting enum->label->enum should return original enum."""
        for enum_val, label in MODE_ENUM_TO_LABEL.items():
            assert MODE_LABEL_TO_ENUM[label] == enum_val

    def test_all_enum_values_have_labels(self):
        """Every enum value should have a corresponding label."""
        for mode in ControllerCreationMode:
            assert mode in MODE_ENUM_TO_LABEL

    def test_all_labels_have_enum_values(self):
        """Every label should map to a valid enum value."""
        for label in MODE_LABEL_TO_ENUM:
            assert MODE_LABEL_TO_ENUM[label] in ControllerCreationMode
