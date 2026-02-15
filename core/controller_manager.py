import cr_tempController.core.controller_node as ctrl_node
import logging

LOGGER = logging.getLogger(__name__)
ControllerNodeMap = dict[str, ctrl_node.ControllerNode]


class ControllerManager:
    def __init__(self):
        self.controller_map: ControllerNodeMap = {}  # string → ControllerNode
        # list of top-level controller (the one from which we want to create a temporary controller)
        self.base_controller_list: list[str] = []

    def rebuild_tree(self, controller_tree: dict = {}):
        """
        Rebuild the entire controller tree from stored data.
        Safe to call on Undo and Redo.
        """
        LOGGER.info("Rebuilding controller tree")

        root_nodes = self.__build_nodes(
            parent_node=None,
            children_dict=controller_tree
        )

        self.__install_tree(root_nodes)

    def __build_nodes(
            self,
            parent_node: ctrl_node.ControllerNode | None,
            children_dict: dict) -> list[ctrl_node.ControllerNode]:
        """
        Build the **ControllerNode** objects from the provided **children_dict**
        **Children_dict** is a dictionnary with the following structure:
        {
            "Base_controller_Name": {
                "Temporary_controller_name": {
                    "Child1_name": {}
                }
            }
        }
        :param parent_node: The parent node where the child will be added
        :param children_dict: The dictionnary of all children
        """
        nodes = []

        for name, children in children_dict.items():
            node = ctrl_node.ControllerNode(name, parent=parent_node)
            nodes.append(node)

            if isinstance(children, dict) and children:
                node.children = self.__build_nodes(node, children)

        return nodes

    def __install_tree(self, root_nodes: list[ctrl_node.ControllerNode]) -> None:
        """
        Install a freshly built controller tree into internal state.
        """
        self.base_controller_list = []
        self.controller_map.clear()

        def register(node: ctrl_node.ControllerNode):
            self.controller_map[node.name] = node
            for child in node.children:
                register(child)

        for node in root_nodes:
            self.base_controller_list.append(node.name)
            register(node)

    def register_first_temporary_controller(self, base_controller: ctrl_node.ControllerNode, temp_controller: ctrl_node.ControllerNode):
        self.controller_map[temp_controller.name] = temp_controller
        self.base_controller_list.append(base_controller.name)

    def register_child_node(self, parent_node: ctrl_node.ControllerNode, child_controller: str):
        """
        Create ControllerNode instance and register it internally.

        :param parent_node: The Parent Node
        :type parent_node: ctrl_node.ControllerNode
        :param child_controller: The children controller to register
        :type child_controller: str
        """

        child_node = ctrl_node.ControllerNode(
            name=child_controller,
            parent=parent_node
        )

        parent_node.add_child(child_node)
        self.controller_map[child_node.name] = child_node

    def remove_controller_from_model(self, node: ctrl_node.ControllerNode):
        """
        Remove the node from the controller_map

        :param self: Description
        :param node: Description
        :type node: ctrl_node.ControllerNode
        """
        self.controller_map.pop(node.name)
        node.parent.children.remove(node)

    def delete_root_node(self, node: ctrl_node.ControllerNode):
        try:
            node_parent_name = node.parent.name

            # Remove node and all its child
            self._remove_node_tree_from_map(node)

            # Remove parent (Base controller) from controller_map AND root_nodes list
            self.controller_map.pop(node_parent_name)
            self.base_controller_list.remove(node_parent_name)
        except Exception:
            LOGGER.warning("Error occured when deleting root node.")
            raise Exception("Error occured when deleting root node.")

        return True

    def _remove_node_tree_from_map(self, node: ctrl_node.ControllerNode):
        """
        Recursively remove node and all children from controller_map

        :param node: Node we want to delete from the controller_map
        :type node: ctrl_node.ControllerNode
        """

        for child in node.children:
            self._remove_node_tree_from_map(child)

        self.controller_map.pop(node.name)

    def contains(self, node: str) -> bool:
        """
        Check if the Tree View contains the specified item

        :param node: Controller to test
        :type node: str
        :return: Description
        :rtype: bool
        """
        return self.node_is_temporary_controller(node) or self.node_is_base_controller(node)

    def node_is_temporary_controller(self, node_name: str):
        return node_name in self.controller_map

    def node_is_base_controller(self, node_name: str):
        return node_name in self.base_controller_list

    def clear(self):
        self.controller_map.clear()
        self.base_controller_list.clear()

    def get_controller_node_from_controller_map(self, controller_name: str) -> ctrl_node.ControllerNode:
        """
        Retrieve the Controller Node for the specified *controller_name*

        :param self: Description
        :param controller_name: Name of the controller we want to retrive
        :type controller_name: str
        :return: Return the associated ControllerNode object or None if not found
        :rtype: ctrl_node.ControllerNode
        """
        return self.controller_map.get(controller_name)

    def rename_controller(self, old_name: str, new_name: str, controller_node: ctrl_node):
        self.controller_map[new_name] = controller_node
        if old_name != new_name:
            self.controller_map.pop(old_name, None)

    def get_controller_map_values(self):
        return self.controller_map.values()
