from dataclasses import dataclass
import maya.cmds as cmds
import logging
import cr_tempController.constants as constants

LOGGER = logging.getLogger(__name__)


def bake_with_constraint(driver, driven, time_range, maintain_offset: bool = False, smart: bool = False):
    if smart:
        bake_with_constraint_smart(driver, driven, time_range, maintain_offset)
    else:
        bake_with_constraint_all_frames(
            driver, driven, time_range, maintain_offset)


def bake_with_constraint_smart(driver, driven, time_range, maintain_offset: bool = False):
    """Unified baking: constraint + bake + optional filter + cleanup"""
    constraint = cmds.parentConstraint(
        driver, driven, maintainOffset=maintain_offset)
    cmds.bakeResults(driven,
                     time=time_range,
                     simulation=True,
                     smart=True)
    cmds.filterCurve(driven)
    cmds.delete(constraint, constraints=True)


def bake_with_constraint_all_frames(driver, driven, time_range, maintain_offset: bool = False):
    """Unified baking: constraint + bake + optional filter + cleanup"""
    constraint = cmds.parentConstraint(driver, driven, mo=maintain_offset)
    cmds.bakeResults(driven,
                     time=time_range,
                     simulation=True,
                     sampleBy=1.0,
                     sparseAnimCurveBake=True,
                     preserveOutsideKeys=True)

    cmds.filterCurve(driven)
    cmds.delete(constraint, constraints=True)


def get_start_end_time_of_animation():
    start_time = cmds.playbackOptions(q=True, animationStartTime=True)
    end_time = cmds.playbackOptions(q=True, animationEndTime=True)
    return start_time, end_time


def _get_parent_first_last_keyframe(parent):
    """
    Retrieve the first key and last key of the **parent controller**

    :param parent: Controller we want to get the first and last keyframe
    """
    start_time, end_time = get_start_end_time_of_animation()
    # TODO -> timeSlider=True to avoid get_start_end_time_of_animation (depends on future options)
    first_key = cmds.findKeyframe(parent, time=(
        start_time, end_time), which="first")
    last_key = cmds.findKeyframe(parent, time=(
        start_time, end_time), which="last")
    LOGGER.info(
        f"Parent = {parent}, first_key = {first_key} & last_key = {last_key} // start_time = {start_time}, end_time = {end_time}")
    return int(first_key), int(last_key)


def copy_anim_from_parent_to_target(parent: str, target: str, maintain_offset: bool = False):
    """
    Copy animation of the **parent controller** to the **target**
    Parent to Target

    :param parent: Parent controller to copy the animation from
    :type parent: str
    :param target: Target controller to copy the animation to
    :type target: str
    :param maintain_offset: Maintain offset boolean of the target from the parent. Default is **False**
    :type maintain_offset: bool
    """
    LOGGER.debug(f"Target = {target}; parent = {parent}")
    if not cmds.keyframe(parent, q=True, keyframeCount=True):
        return
    first_key, last_key = _get_parent_first_last_keyframe(parent)
    LOGGER.debug(f"First_key = {first_key}; last_key = {last_key}")

    bake_with_constraint(driver=parent,
                         driven=target,
                         time_range=(first_key, last_key),
                         maintain_offset=maintain_offset,
                         smart=False)


def copy_anim_from_parent_to_target_smart(parent: str, target: str, maintain_offset: bool = False):
    """
    Copy animation of the **parent controller** to the **target**
    Parent to Target

    :param parent: Parent controller to copy the animation from
    :type parent: str
    :param target: Target controller to copy the animation to
    :type target: str
    :param maintain_offset: Maintain offset boolean of the target from the parent. Default is **False**
    :type maintain_offset: bool
    """
    LOGGER.debug(f"Target = {target}; parent = {parent}")
    if not cmds.keyframe(parent, q=True, keyframeCount=True):
        return
    first_key, last_key = _get_parent_first_last_keyframe(parent)
    LOGGER.debug(f"First_key = {first_key}; last_key = {last_key}")

    LOGGER.info(
        f"copy_anim_from_parent_to_target_smart for {parent} to {target}")

    bake_with_constraint(driver=parent,
                         driven=target,
                         time_range=(first_key, last_key),
                         maintain_offset=maintain_offset,
                         smart=True)


def lock_transform_attribute(node: str):
    for attribute_name in ['t', 'r', 's']:
        for axis in ['x', 'y', 'z']:
            cmds.setAttr(
                f'{node}.{attribute_name}{axis}',
                lock=True,
                keyable=False,
                channelBox=False,
            )


def store_display_color_rgb(node: str, rgb_color: list[float]):
    # TODO Movei n another utils?
    if not cmds.attributeQuery(constants.ATTRIBUTE_DISPLAY_COLOR, node=node, exists=True):
        cmds.addAttr(node, longName=constants.ATTRIBUTE_DISPLAY_COLOR,
                     attributeType='float3')
        cmds.addAttr(node, longName=constants.ATTRIBUTE_DISPLAY_COLOR_R,
                     attributeType='float', parent=constants.ATTRIBUTE_DISPLAY_COLOR)
        cmds.addAttr(node, longName=constants.ATTRIBUTE_DISPLAY_COLOR_G,
                     attributeType='float', parent=constants.ATTRIBUTE_DISPLAY_COLOR)
        cmds.addAttr(node, longName=constants.ATTRIBUTE_DISPLAY_COLOR_B,
                     attributeType='float', parent=constants.ATTRIBUTE_DISPLAY_COLOR)

    cmds.setAttr(f'{node}.{constants.ATTRIBUTE_DISPLAY_COLOR}', *rgb_color,
                 lock=True,
                 keyable=False,
                 channelBox=False)
