"""Shared fixtures for cr_tempController tests."""
import pytest

# Import from helper to avoid Maya dependencies
from tests.import_helper import ControllerNode, ControllerManager


@pytest.fixture
def controller_node():
    """Create a simple controller node."""
    return ControllerNode("test_controller")


@pytest.fixture
def controller_node_with_parent():
    """Create a controller node with a parent."""
    parent = ControllerNode("parent_controller")
    child = ControllerNode("child_controller", parent=parent)
    return child


@pytest.fixture
def controller_hierarchy():
    """Create a 3-level controller hierarchy."""
    root = ControllerNode("root")
    child1 = ControllerNode("child1", parent=root)
    child2 = ControllerNode("child2", parent=root)
    grandchild = ControllerNode("grandchild", parent=child1)

    root.children = [child1, child2]
    child1.children = [grandchild]

    return {
        "root": root,
        "child1": child1,
        "child2": child2,
        "grandchild": grandchild,
    }


@pytest.fixture
def controller_manager():
    """Create a fresh ControllerManager instance."""
    return ControllerManager()


@pytest.fixture
def sample_tree_dict():
    """Sample tree dictionary structure for rebuild_tree testing."""
    return {
        "base_ctrl": {
            "base_ctrl_TempControl_Ctrl": {
                "child1_TempControl_Ctrl": {},
                "child2_TempControl_Ctrl": {
                    "grandchild_TempControl_Ctrl": {}
                }
            }
        }
    }


@pytest.fixture
def populated_manager(controller_manager, sample_tree_dict):
    """Create a ControllerManager with a pre-populated tree."""
    controller_manager.rebuild_tree(sample_tree_dict)
    return controller_manager
