import maya.cmds as cmds
import logging

LOGGER = logging.getLogger(__name__)


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
