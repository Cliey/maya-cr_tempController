import maya.cmds as cmds
import cr_tempController.core.controller_node as ctrl_node
import cr_tempController.core.controller_context as controller_context
import cr_tempController.utils.animation as utils_animation
import cr_tempController.utils.nodes as utils_nodes
import cr_tempController.utils.context as utils_context
import logging

LOGGER = logging.getLogger(__name__)


def bake_temporary_controller_to_base(node: ctrl_node.ControllerNode, bake_options: controller_context.BakeOptionContext):
    """
    Bake the temporary controller (*node*) to the base controller (its parent)

    :param node: Node we want to bake
    :type node: ctrl_node.ControllerNode

    """
    node_name = node.name
    parent_node_name = node.parent.name

    time_range = _get_first_last_keyframe(parent_node_name, node_name)

    # destinationLayer = "LayerName if bake on new layer"
    cmds.bakeResults(parent_node_name,
                     time=time_range,
                     **bake_options.to_bake_kwargs()
                     )
    if bake_options.apply_filter:
        cmds.filterCurve(parent_node_name)


def bake_temporary_controller_to_parent(node: ctrl_node.ControllerNode, bake_options: controller_context.BakeOptionContext):
    time_range = _get_first_last_keyframe(
        node.parent.name, node.name)

    node_parent_name = node.parent.name
    base_controller = utils_nodes.get_base_controller(node_parent_name)
    # Save matrix of base controller before transfer animation to retrieve the offset after
    base_matrix = preserve_world_transform(base_controller)

    _transfer_animation_child_to_parent(node, time_range, bake_options)

    LOGGER.debug(
        f"Rebuild constraint {base_controller} -> {node_parent_name}")

    restore_matrix_no_autokey(base_controller, base_matrix)
    cmds.parentConstraint(node_parent_name, base_controller, mo=True)


def _transfer_animation_child_to_parent(child: ctrl_node.ControllerNode, time_range: tuple[int, int], bake_options: controller_context.BakeOptionContext):
    parent_name = child.parent.name
    tmp_locator = cmds.spaceLocator(name=f"{parent_name}_TMP_LOC")[0]
    try:

        utils_animation.bake(driver=child.name,
                             driven=tmp_locator,
                             time_range=time_range,
                             maintain_offset=False,
                             bake_options=bake_options)
        cmds.delete(child.name)
        utils_animation.bake(driver=tmp_locator,
                             driven=parent_name,
                             time_range=time_range,
                             maintain_offset=False,
                             bake_options=bake_options)

    finally:
        cmds.delete(tmp_locator)


def preserve_world_transform(node):
    return cmds.xform(node, q=True, ws=True, matrix=True)


def restore_matrix_no_autokey(node, matrix):
    with utils_context.AutoKeyOff():
        cmds.xform(node, ws=True, matrix=matrix)


"""
Keyframes Helper, only used in Baking Service
"""


def _get_min_first_keyframe(parent, controller, start_time, end_time):
    # TODO rework cf below (__get_first_last_keyframe)
    LOGGER.info("-- __get_min_first_keyframe --")
    LOGGER.info(
        f"parameter = parent = {parent}, controller = {controller}, start_time = {start_time}, end_time = {end_time}")
    first_controller = cmds.findKeyframe(
        controller, time=(start_time, end_time), which="first")
    first_parent = cmds.findKeyframe(
        parent, time=(start_time, end_time), which="first")
    LOGGER.info(
        f"first_controller = {first_controller} / first_parent = {first_parent}")
    return min(cmds.findKeyframe(controller, time=(start_time, end_time), which="first") or start_time,
               cmds.findKeyframe(parent, time=(start_time, end_time), which="first") or start_time)


def _get_max_last_keyframe(parent, controller, start_time, end_time):
    # TODO rework cf below (__get_first_last_keyframe)
    LOGGER.info("-- __get_max_last_keyframe --")
    LOGGER.info(
        f"parameter = parent = {parent}, controller = {controller}, start_time = {start_time}, end_time = {end_time}")
    last_controller = cmds.findKeyframe(
        controller, time=(start_time, end_time), which="last")
    last_parent = cmds.findKeyframe(
        parent, time=(start_time, end_time), which="last")
    LOGGER.info(
        f"last_controller = {last_controller} / last_parent = {last_parent}")
    return max(cmds.findKeyframe(controller, time=(start_time, end_time), which="last") or end_time,
               cmds.findKeyframe(parent, time=(start_time, end_time), which="last") or end_time)


def _get_first_last_keyframe(parent, controller):
    """
    TODO If parent not animated => get from controller
    But if child of parent has key after -> need to take them
    """
    start_time, end_time = utils_animation.get_start_end_time_of_animation()
    first_key = _get_min_first_keyframe(
        parent, controller, start_time, end_time)
    last_key = _get_max_last_keyframe(
        parent, controller, start_time, end_time)
    return int(first_key), int(last_key)
