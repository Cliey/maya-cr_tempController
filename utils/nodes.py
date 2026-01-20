import maya.api.OpenMaya as om
import maya.cmds as cmds
import cr_tempController.constants as constants
import logging
import cr_tempController.utils.logging as utils_logging

LOGGER = logging.getLogger(__name__)


def get_source_controller(data_node: str) -> str | None:
    attr = f"{data_node}.{constants.DATA_SOURCE_NODE}"
    if cmds.connectionInfo(attr, isDestination=True):
        source = cmds.connectionInfo(attr, sourceFromDestination=True)
        LOGGER.debug(f"Source Controller from DataNode: {source}")
        return source.replace(".message", "")
    return None


def retrieve_data_node(node: str) -> str | None:
    """
    Walk up the hierarchy to find a temp control data node.
    """
    current = node
    while True:
        parent = cmds.listRelatives(current, parent=True)
        if not parent:
            return None
        current = parent[0]
        if constants.SUFFIXE_TEMP_CONTROL_DATA in current:
            return current


def get_base_controller(temp_ctrl: str) -> str | None:
    """
    Retrieve the base controller name from the temp controller

    :param temp_ctrl: Temporary controller we want to know the base controller
    :type temp_ctrl: str

    :return connection: The string of the base controller. **None** if it doesnt exist.
    """

    data_node = retrieve_data_node(temp_ctrl)
    if not data_node:
        return None

    connections = cmds.listConnections(
        f"{data_node}.{constants.DATA_SOURCE_NODE}",
        source=True,
        destination=False
    )
    return connections[0] if connections else None


def freeze_translate_parent_space(node: str, pivot_locator: str):
    """
    NOTE & LIMITATION
        - If change pivot AFTER moving the controller (ex controller at 1,0,0) and Edit Pivot
        New pivot will be 0,0,0 and not 1,0,0
        -> TODO : Fix? or OK Behavior?
    TODO : Write test step
    """
    locator_world_position = om.MVector(
        cmds.xform(pivot_locator, q=True, t=True, ws=True)
    )
    node_world_position = om.MVector(
        cmds.xform(node, q=True, t=True, ws=True)
    )

    world_delta = locator_world_position - node_world_position

    parent = cmds.listRelatives(node, parent=True)
    if parent:  # Have to deal with rotation if it has a parent
        parent_world_matrix = om.MMatrix(
            cmds.xform(parent[0], q=True, m=True, ws=True)
        )
        parent_inv = parent_world_matrix.inverse()
        parent_delta = world_delta * parent_inv
        utils_logging.print_data(logger=LOGGER,
                                 level=logging.INFO,
                                 parent_world_matrix=parent_world_matrix,
                                 parent_inv=parent_inv,
                                 parent_delta=parent_delta)
    else:
        parent_delta = world_delta

    offset_matrix = om.MMatrix(
        cmds.getAttr(f"{node}.offsetParentMatrix")
    )

    offset_matrix[12] += parent_delta.x
    offset_matrix[13] += parent_delta.y
    offset_matrix[14] += parent_delta.z

    utils_logging.print_data(logger=LOGGER,
                             level=logging.INFO,
                             node=node,
                             locator_world_position=locator_world_position,
                             node_world_position=node_world_position,
                             world_delta=world_delta,
                             parent_delta=parent_delta,
                             offset_matrix=offset_matrix)
    cmds.setAttr(
        f"{node}.offsetParentMatrix",
        list(offset_matrix),
        type="matrix"
    )


def freeze_children(children: list[str]):
    """
    Freeze Translate transform of node in children list

    :param children: List of children to freeze transform
    :type children: list[str]
    """
    # TODO : what about rotation?
    for child in children:
        child_relation_position = om.MVector(
            cmds.xform(child, q=True, t=True)
        )
        offset_matrix = om.MMatrix(
            cmds.getAttr(f"{child}.offsetParentMatrix")
        )

        offset_matrix[12] += child_relation_position.x
        offset_matrix[13] += child_relation_position.y
        offset_matrix[14] += child_relation_position.z

        cmds.setAttr(
            f"{child}.offsetParentMatrix",
            list(offset_matrix),
            type="matrix"
        )
        cmds.setAttr(f"{child}.translate", 0, 0, 0)


def reconnect_constraints(child_controller: str) -> None:
    """
    Rewire parent constraints so the new controller drives the source.
    """
    data_node = retrieve_data_node(child_controller)
    source_controller = get_source_controller(data_node)

    parent_group = cmds.listRelatives(
        child_controller, parent=True, fullPath=True
    )[0]

    cmds.parentConstraint(
        child_controller,
        source_controller,
        maintainOffset=True
    )

    cmds.parentConstraint(
        parent_group,
        source_controller,
        edit=True,
        remove=True
    )
