import maya.api.OpenMaya as om
import maya.cmds as cmds
import cr_tempController.core.controller_context as controller_context
import cr_tempController.core.controller_mode as controller_mode
import cr_tempController.core.controller_node as ctrl_node
import cr_tempController.utils.context as utils_context
import cr_tempController.constants as constants
import cr_tempController.utils.animation as utils_animation
import cr_tempController.utils.controller_shapes as controller_shapes
import cr_tempController.utils.naming as utils_naming
import logging


LOGGER = logging.getLogger(__name__)


def create_new_temporary_controller_from_base_controller(base_controller: str, context: controller_context.TempControllerCreationContext):
    """
    Create a new temporary controller for a controller selected by the user.
    Only called when pressing "New Controller button"

    :param base_controller: Controller we want to add a temporary controller
    :type base_controller: str
    :param mode: Mode to create the controller
    :type mode: controller_mode.ControllerCreationMode
    :param rgb_color: RGB Color in viewport of the new controller
    :type rgb_color: list[float]
    """

    """ TODO
    - Add a driver to say if we want to activate the temp controller or not. Connected ot the parent constraint.
    - Driver will be the same for all child. Add in UI?"""
    LOGGER.info(f"Create controller with mode = {context.mode}")
    with utils_context.UndoChunk():
        try:
            temp_controller = _create_temp_controller(
                base_controller=base_controller,
                context=context
            )

            finalize_temp_controller(
                base_controller=base_controller,
                temp_controller=temp_controller,
                context=context
            )

            return temp_controller

        except Exception:
            LOGGER.exception(
                "Error during creation of a new Temp Controller.")
            raise


def _create_temp_controller(base_controller: str, context: controller_context.TempControllerCreationContext) -> tuple[list[float], str]:
    world_translation = cmds.xform(
        base_controller,
        q=True,
        t=True,
        ws=True
    )

    temp_controller = create_new_controller(
        name=f"{base_controller}{constants.SUFFIXE_TEMP_CONTROL_CTRLLER}",
        parent_group=constants.TEMP_PIVOT_GROUP,
        translation=world_translation,
        context=context
    )

    return temp_controller


def create_new_controller(name: str, parent_group: str, translation: list[float], context: controller_context.TempControllerCreationContext) -> str:
    """
    Create a new controller with the selected shape under parent controller

    :param name: Name of the new controller
    :type name: str
    :param parent_group: Parent of the new controller
    :type parent_group: str
    :param translation: Position where the new controller will be created
    :type translation: list[float]
    :param context: Data context for the new controller
    :type context: controller_context.TempControllerCreationContext
    :return: Name of the new controller
    :rtype: str
    """

    controller = controller_shapes.create_controller(
        name=name, shape=context.shape, ratio=context.size_ratio)
    cmds.color(controller, rgbColor=context.rgb_color)

    # Store color for later retrieval
    utils_animation.store_display_color_rgb(controller, context.rgb_color)

    cmds.parent(controller, parent_group)
    cmds.rotate(0, 0, 0, controller)
    # TODO: can adapt to boundaries
    cmds.xform(controller, t=translation, ws=True)
    return controller


def finalize_temp_controller(
    base_controller: str,
    temp_controller: str,
    context: controller_context.TempControllerCreationContext
) -> str:
    """
    Apply all post-creation Maya operations for a temp controller.

    This handles:
    - Creating the data node
    - Matching transform to base controller
    - Copying animation from base to temp
    - Creating parent constraint (temp drives base)

    NOTE: Does NOT handle UI tree state. Caller must register in tree.

    :param base_controller: Name of the original controller
    :param temp_controller: Name of the newly created temp controller
    :param context: Creation context
    :return: Name of the created data node (for UI registration)
    """
    # 1. Create Data Node and move temp controller under it
    data_node = create_data_node(
        base_controller_name=base_controller,
        temp_controller_name=temp_controller,
        context=context
    )

    # 2. Match transform once
    cmds.delete(cmds.parentConstraint(
        base_controller,
        temp_controller,
        mo=False
    ))

    # 3. Copy animation & Bake on all Keys
    utils_animation.copy_anim_from_parent_to_target_smart(
        parent=base_controller,
        target=temp_controller
    )

    # 4. Parent constraint: temp controller drives base controller
    cmds.parentConstraint(
        temp_controller,
        base_controller
    )

    return data_node


def create_data_node(base_controller_name: str, temp_controller_name: str, context: controller_context.TempControllerCreationContext):
    data_node = cmds.group(em=True,
                           name=utils_naming.build_temp_control_data_name(
                               base_controller_name),
                           parent=constants.TEMP_PIVOT_GROUP)

    cmds.addAttr(data_node, attributeType="message",
                 longName=constants.DATA_SOURCE_NODE)
    cmds.connectAttr(f'{base_controller_name}.message',
                     f'{data_node}.{constants.DATA_SOURCE_NODE}')

    translation = (0, 0, 0)  # Worldspace translation

    match context.mode:
        case controller_mode.ControllerCreationMode.WORLD_SPACE:
            translation = (0, 0, 0)

        case controller_mode.ControllerCreationMode.OBJECT_SPACE:
            world_pos = om.MVector(cmds.xform(
                base_controller_name, q=True, t=True, ws=True))

            local_pos = om.MVector(cmds.xform(
                base_controller_name, q=True, t=True))

            translation = world_pos - local_pos

        case _:
            raise NotImplementedError(
                f"Controller mode not implemented: {context.mode}")

    cmds.xform(data_node, t=translation, ws=True)
    utils_animation.lock_transform_attribute(data_node)

    cmds.parent(temp_controller_name, data_node)
    return data_node


def build_context(parent_node):
    def __controller_ratio(depth):
        return 1 * (0.9 ** depth)

    parent_color = cmds.getAttr(f"{parent_node.name}.{constants.ATTRIBUTE_DISPLAY_COLOR}")[0] if cmds.attributeQuery(
        constants.ATTRIBUTE_DISPLAY_COLOR, node=parent_node.name, exists=True) else [1, 0, 1]

    default_shape = controller_shapes.ControllerShape.ROUNDED_SQUARE  # pick a safe enum

    if cmds.control(constants.SHAPE_MENU_CREATION_NAME, exists=True):
        controller_shape_label = cmds.optionMenu(
            constants.SHAPE_MENU_CREATION_NAME, q=True, value=True
        )
        shape = controller_shapes.SHAPE_LABEL_TO_ENUM.get(
            controller_shape_label, default_shape
        )
    else:
        shape = default_shape

    return controller_context.TempControllerCreationContext(
        size_ratio=__controller_ratio(parent_node.depth),
        rgb_color=parent_color,
        shape=shape
    )


def create_child_controller(parent_node: ctrl_node.ControllerNode):
    """
    Create a child controller from the parent_node

    :param parent_node: Parent Node to create the child_controller
    :type parent_node: ctrl_node.ControllerNode

    """

    parent_name = parent_node.name
    world_translation = cmds.xform(
        parent_name,
        query=True,
        translation=True,
        worldSpace=True)

    LOGGER.warning(f"---> world_translation = {world_translation}")

    context = build_context(parent_node=parent_node)

    child_controller = create_new_controller(
        name=f"{parent_name}_Child#",
        parent_group=parent_name,
        translation=world_translation,
        context=context)

    return child_controller
