import maya.cmds as cmds
import logging
import cr_tempController.constants as constants
import cr_tempController.utils.nodes as utils_nodes


LOGGER = logging.getLogger(__name__)


def build_controller_tree_from_scene() -> dict:
    controller_tree = {}
    temp_controller_data_list = cmds.listRelatives(
        constants.TEMP_PIVOT_GROUP, type="transform") or []
    for temp_controller_data in temp_controller_data_list:
        source_controller_name = utils_nodes.get_source_controller(
            temp_controller_data)
        controller_tree[source_controller_name] = get_transform_children_recursive(
            temp_controller_data)
    return controller_tree


def get_transform_children_recursive(controller: str) -> dict:
    """
    Recursively return transform children, skipping shape nodes.
    """
    children = cmds.listRelatives(
        controller, children=True, type="transform") or []
    if not children:
        return {}

    child_dict = {}
    for child in children:
        child_dict[child] = get_transform_children_recursive(child)
    return child_dict


def get_tempcontrol_root(node):
    """
    From any node, climb the hierarchy until we find a '*_TempControl_Data' (constants.SUFFIXE_TEMP_CONTROL_DATA) group.
    Return the name or None.
    """
    while node:
        if node.endswith(constants.SUFFIXE_TEMP_CONTROL_DATA):
            return node
        parents = cmds.listRelatives(node, parent=True)
        node = parents[0] if parents else None

    return None


def is_under_tempcontrol(node):
    """Returns True if the node is inside any '*_TempControl_Data' (constants.SUFFIXE_TEMP_CONTROL_DATA) hierarchy."""
    return get_tempcontrol_root(node) is not None


def has_temp_controller_children(root):
    """
    If a TempControl_Data root is given, check if it already contains controllers.
    Here we consider ANY children to be controllers; adjust the logic if needed.
    """
    children = cmds.listRelatives(
        root, children=True, fullPath=False) or []
    return len(children) > 0
