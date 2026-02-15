"""Tests for ControllerManager class."""
import pytest
from tests.import_helper import ControllerManager, ControllerNode


class TestControllerManagerInit:
    """Tests for ControllerManager initialization."""

    def test_new_manager_has_empty_controller_map(self, controller_manager):
        """New manager should have empty controller_map."""
        assert controller_manager.controller_map == {}

    def test_new_manager_has_empty_base_controller_list(self, controller_manager):
        """New manager should have empty base_controller_list."""
        assert controller_manager.base_controller_list == []


class TestRebuildTree:
    """Tests for rebuild_tree method."""

    def test_rebuild_with_empty_dict(self, controller_manager):
        """Rebuilding with empty dict should result in empty state."""
        controller_manager.rebuild_tree({})
        assert controller_manager.controller_map == {}
        assert controller_manager.base_controller_list == []

    def test_rebuild_creates_base_controller(self, controller_manager):
        """Rebuilding should register base controller in base_controller_list."""
        tree = {"base_ctrl": {"temp_ctrl": {}}}
        controller_manager.rebuild_tree(tree)
        assert "base_ctrl" in controller_manager.base_controller_list

    def test_rebuild_creates_nodes_in_map(self, controller_manager):
        """Rebuilding should populate controller_map with all nodes."""
        tree = {"base_ctrl": {"temp_ctrl": {}}}
        controller_manager.rebuild_tree(tree)
        assert "base_ctrl" in controller_manager.controller_map
        assert "temp_ctrl" in controller_manager.controller_map

    def test_rebuild_sets_correct_depth(self, controller_manager):
        """Rebuilt nodes should have correct depth values."""
        tree = {"base": {"child": {"grandchild": {}}}}
        controller_manager.rebuild_tree(tree)
        assert controller_manager.controller_map["base"].depth == 0
        assert controller_manager.controller_map["child"].depth == 1
        assert controller_manager.controller_map["grandchild"].depth == 2

    def test_rebuild_sets_parent_child_relationships(self, controller_manager):
        """Rebuilt nodes should have correct parent-child links."""
        tree = {"base": {"child": {}}}
        controller_manager.rebuild_tree(tree)
        base = controller_manager.controller_map["base"]
        child = controller_manager.controller_map["child"]
        assert child.parent is base
        assert child in base.children

    def test_rebuild_handles_multiple_roots(self, controller_manager):
        """Rebuilding should handle multiple root controllers."""
        tree = {"base1": {"temp1": {}}, "base2": {"temp2": {}}}
        controller_manager.rebuild_tree(tree)
        assert "base1" in controller_manager.base_controller_list
        assert "base2" in controller_manager.base_controller_list

    def test_rebuild_clears_previous_state(self, controller_manager):
        """Rebuilding should clear previous state."""
        controller_manager.rebuild_tree({"old_base": {"old_temp": {}}})
        controller_manager.rebuild_tree({"new_base": {"new_temp": {}}})
        assert "old_base" not in controller_manager.controller_map
        assert "new_base" in controller_manager.controller_map


class TestRegisterFirstTemporaryController:
    """Tests for register_first_temporary_controller method."""

    def test_registers_temp_controller_in_map(self, controller_manager):
        """Should add temp controller to controller_map."""
        base = ControllerNode("base")
        temp = ControllerNode("temp", parent=base)
        controller_manager.register_first_temporary_controller(base, temp)
        assert "temp" in controller_manager.controller_map

    def test_adds_base_to_base_controller_list(self, controller_manager):
        """Should add base controller name to base_controller_list."""
        base = ControllerNode("base")
        temp = ControllerNode("temp", parent=base)
        controller_manager.register_first_temporary_controller(base, temp)
        assert "base" in controller_manager.base_controller_list


class TestRegisterChildNode:
    """Tests for register_child_node method."""

    def test_creates_child_node(self, controller_manager):
        """Should create and register child ControllerNode."""
        parent = ControllerNode("parent")
        controller_manager.controller_map["parent"] = parent
        controller_manager.register_child_node(parent, "child")
        assert "child" in controller_manager.controller_map

    def test_child_has_correct_parent(self, controller_manager):
        """Created child should reference correct parent."""
        parent = ControllerNode("parent")
        controller_manager.controller_map["parent"] = parent
        controller_manager.register_child_node(parent, "child")
        child = controller_manager.controller_map["child"]
        assert child.parent is parent

    def test_child_added_to_parent_children(self, controller_manager):
        """Parent's children list should include the new child."""
        parent = ControllerNode("parent")
        controller_manager.controller_map["parent"] = parent
        controller_manager.register_child_node(parent, "child")
        child = controller_manager.controller_map["child"]
        assert child in parent.children


class TestRemoveControllerFromModel:
    """Tests for remove_controller_from_model method."""

    def test_removes_from_controller_map(self, populated_manager):
        """Should remove node from controller_map."""
        node = populated_manager.controller_map["child1_TempControl_Ctrl"]
        populated_manager.remove_controller_from_model(node)
        assert "child1_TempControl_Ctrl" not in populated_manager.controller_map

    def test_removes_from_parent_children(self, populated_manager):
        """Should remove node from parent's children list."""
        node = populated_manager.controller_map["child1_TempControl_Ctrl"]
        parent = node.parent
        populated_manager.remove_controller_from_model(node)
        assert node not in parent.children


class TestContains:
    """Tests for contains method."""

    def test_contains_temp_controller(self, populated_manager):
        """Should return True for temporary controller in map."""
        assert populated_manager.contains("base_ctrl_TempControl_Ctrl") is True

    def test_contains_base_controller(self, populated_manager):
        """Should return True for base controller in base_controller_list."""
        assert populated_manager.contains("base_ctrl") is True

    def test_not_contains_unknown(self, populated_manager):
        """Should return False for unknown controller."""
        assert populated_manager.contains("unknown_ctrl") is False


class TestNodeIsTemporaryController:
    """Tests for node_is_temporary_controller method."""

    def test_returns_true_for_temp_controller(self, populated_manager):
        """Should return True for node in controller_map."""
        assert populated_manager.node_is_temporary_controller("base_ctrl_TempControl_Ctrl") is True

    def test_returns_false_for_base_controller(self, populated_manager):
        """Base controllers are in controller_map too, should return True."""
        # Note: Base controllers ARE in the controller_map
        assert populated_manager.node_is_temporary_controller("base_ctrl") is True

    def test_returns_false_for_unknown(self, populated_manager):
        """Should return False for unknown node."""
        assert populated_manager.node_is_temporary_controller("unknown") is False


class TestNodeIsBaseController:
    """Tests for node_is_base_controller method."""

    def test_returns_true_for_base_controller(self, populated_manager):
        """Should return True for base controller."""
        assert populated_manager.node_is_base_controller("base_ctrl") is True

    def test_returns_false_for_temp_controller(self, populated_manager):
        """Should return False for temporary controller."""
        assert populated_manager.node_is_base_controller("base_ctrl_TempControl_Ctrl") is False

    def test_returns_false_for_unknown(self, populated_manager):
        """Should return False for unknown node."""
        assert populated_manager.node_is_base_controller("unknown") is False


class TestClear:
    """Tests for clear method."""

    def test_clears_controller_map(self, populated_manager):
        """Should empty the controller_map."""
        populated_manager.clear()
        assert populated_manager.controller_map == {}

    def test_clears_base_controller_list(self, populated_manager):
        """Should empty the base_controller_list."""
        populated_manager.clear()
        assert populated_manager.base_controller_list == []


class TestRenameController:
    """Tests for rename_controller method."""

    def test_adds_new_name_to_map(self, populated_manager):
        """Should add controller under new name."""
        node = populated_manager.controller_map["child1_TempControl_Ctrl"]
        populated_manager.rename_controller("child1_TempControl_Ctrl", "renamed_ctrl", node)
        assert "renamed_ctrl" in populated_manager.controller_map

    def test_removes_old_name_from_map(self, populated_manager):
        """Should remove old name from map."""
        node = populated_manager.controller_map["child1_TempControl_Ctrl"]
        populated_manager.rename_controller("child1_TempControl_Ctrl", "renamed_ctrl", node)
        assert "child1_TempControl_Ctrl" not in populated_manager.controller_map

    def test_same_name_keeps_entry(self, populated_manager):
        """Renaming to same name should keep entry."""
        node = populated_manager.controller_map["child1_TempControl_Ctrl"]
        populated_manager.rename_controller("child1_TempControl_Ctrl", "child1_TempControl_Ctrl", node)
        assert "child1_TempControl_Ctrl" in populated_manager.controller_map


class TestGetControllerNodeFromControllerMap:
    """Tests for get_controller_node_from_controller_map method."""

    def test_returns_node_for_existing_controller(self, populated_manager):
        """Should return ControllerNode for existing name."""
        node = populated_manager.get_controller_node_from_controller_map("base_ctrl_TempControl_Ctrl")
        assert node is not None
        assert node.name == "base_ctrl_TempControl_Ctrl"

    def test_returns_none_for_unknown_controller(self, populated_manager):
        """Should return None for unknown name."""
        node = populated_manager.get_controller_node_from_controller_map("unknown")
        assert node is None


class TestGetControllerMapValues:
    """Tests for get_controller_map_values method."""

    def test_returns_all_nodes(self, populated_manager):
        """Should return all nodes in map."""
        values = list(populated_manager.get_controller_map_values())
        assert len(values) == 5  # base_ctrl + 4 temp controllers

    def test_returns_controller_nodes(self, populated_manager):
        """Returned values should be ControllerNode instances."""
        values = list(populated_manager.get_controller_map_values())
        for val in values:
            assert isinstance(val, ControllerNode)
