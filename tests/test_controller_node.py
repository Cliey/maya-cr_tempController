"""Tests for ControllerNode class."""
import pytest
from tests.import_helper import ControllerNode


class TestControllerNodeCreation:
    """Tests for ControllerNode initialization."""

    def test_create_node_with_name(self):
        """Node should store the provided name."""
        node = ControllerNode("my_controller")
        assert node.name == "my_controller"

    def test_create_node_without_parent(self):
        """Node without parent should have None parent."""
        node = ControllerNode("my_controller")
        assert node.parent is None

    def test_create_node_with_parent(self):
        """Node should store provided parent reference."""
        parent = ControllerNode("parent")
        child = ControllerNode("child", parent=parent)
        assert child.parent is parent

    def test_new_node_has_empty_children(self):
        """New node should have empty children list."""
        node = ControllerNode("my_controller")
        assert node.children == []


class TestControllerNodeDepth:
    """Tests for depth calculation."""

    def test_root_node_has_depth_zero(self):
        """Node without parent should have depth 0."""
        node = ControllerNode("root")
        assert node.depth == 0

    def test_child_node_has_depth_one(self):
        """Direct child should have depth 1."""
        parent = ControllerNode("parent")
        child = ControllerNode("child", parent=parent)
        assert child.depth == 1

    def test_grandchild_has_depth_two(self):
        """Grandchild should have depth 2."""
        root = ControllerNode("root")
        child = ControllerNode("child", parent=root)
        grandchild = ControllerNode("grandchild", parent=child)
        assert grandchild.depth == 2

    def test_deep_hierarchy_depth(self):
        """Depth should increment for each level."""
        current = ControllerNode("level_0")
        for i in range(1, 5):
            current = ControllerNode(f"level_{i}", parent=current)
        assert current.depth == 4


class TestControllerNodeAddChild:
    """Tests for add_child method."""

    def test_add_child_appends_to_children(self):
        """add_child should append child to children list."""
        parent = ControllerNode("parent")
        child = ControllerNode("child")
        parent.add_child(child)
        assert child in parent.children

    def test_add_child_sets_parent(self):
        """add_child should update child's parent reference."""
        parent = ControllerNode("parent")
        child = ControllerNode("child")
        parent.add_child(child)
        assert child.parent is parent

    def test_add_child_rejects_non_controller_node(self):
        """add_child should raise TypeError for non-ControllerNode."""
        parent = ControllerNode("parent")
        with pytest.raises(TypeError):
            parent.add_child("not_a_node")

    def test_add_child_rejects_dict(self):
        """add_child should raise TypeError for dict."""
        parent = ControllerNode("parent")
        with pytest.raises(TypeError):
            parent.add_child({"name": "fake"})

    def test_add_multiple_children(self):
        """Parent should support multiple children."""
        parent = ControllerNode("parent")
        child1 = ControllerNode("child1")
        child2 = ControllerNode("child2")
        parent.add_child(child1)
        parent.add_child(child2)
        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children


class TestControllerNodeStringRepresentation:
    """Tests for __str__ and __repr__."""

    def test_str_contains_name(self):
        """String representation should contain node name."""
        node = ControllerNode("my_controller")
        assert "my_controller" in str(node)

    def test_repr_contains_name(self):
        """Repr should contain node name."""
        node = ControllerNode("my_controller")
        assert "my_controller" in repr(node)
