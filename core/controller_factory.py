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

    # Change Rotate Order
    cmds.setAttr(f"{controller}.rotateOrder", context.rotate_order)
    cmds.rotate(0, 0, 0, controller)
    # TODO: can adapt to boundaries
    cmds.xform(controller, t=translation, ws=True)

    # Warning if NurbCurves are hidden
    if not cmds.optionVar(exists=constants.SKIP_NURBS_WARNING) or not cmds.optionVar(q=constants.SKIP_NURBS_WARNING):
        panel = cmds.getPanel(withFocus=True)
        if cmds.getPanel(typeOf=panel) == 'modelPanel':
            state = cmds.modelEditor(panel, query=True, nurbsCurves=True)
            if not state:
                show_nurb_warning(panel)

    # TODO: option to always reveal nurbs, a checkbox into main window

    return controller


def show_nurb_warning(panel: str):

    if cmds.window("nurbsWarningWin", exists=True):
        cmds.deleteUI("nurbsWarningWin")

    warning_window = cmds.window(
        "nurbsWarningWin",
        title="NURBS Curves Hidden",
        sizeable=False
    )

    # ===== MAIN LAYOUT =====
    main_col = cmds.columnLayout(adjustableColumn=True)

    cmds.separator(h=10,
                   style='none',
                   parent=main_col)  # TOP MARGIN

    # ===== HORIZONTAL MARGIN CONTAINER =====
    outer_row = cmds.rowLayout(
        numberOfColumns=3,
        adjustableColumn=2,
        parent=main_col
    )

    cmds.separator(w=10,
                   style='none',
                   parent=outer_row)  # LEFT MARGIN

    # ===== CONTENT COLUMN =====
    content_col = cmds.columnLayout(adjustableColumn=True,
                                    rowSpacing=10,
                                    parent=outer_row)

    # ---- ICON + TEXT ----
    row_message = cmds.rowLayout(
        numberOfColumns=2,
        columnWidth2=(50, 300),
        adjustableColumn=2,
        parent=content_col
    )

    cmds.iconTextStaticLabel(
        style='iconOnly',
        image1='infoModal.png',  # Maya built-in icon
        align="left",
        width=40,
        height=40,
        parent=row_message
    )

    text_col = cmds.columnLayout(
        adjustableColumn=True,
        rowSpacing=5,
        parent=row_message)

    cmds.text(
        label="NURBS Curves are hidden in the viewport.\n"
              "Controllers may not be visible.",
        align="left",
        parent=text_col
    )

    cmds.separator(h=10, style='none', parent=text_col)

    never_show_checkbox = cmds.checkBox(label="Never show again",
                                        parent=text_col)

    cmds.separator(h=5, style='none', parent=content_col)

    # ---- BUTTONS ----
    def _on_reveal_nurbs_curves(_):
        save_pref(cmds.checkBox(never_show_checkbox, q=True, value=True))
        cmds.modelEditor(panel, edit=True, nurbsCurves=True)
        cmds.deleteUI(warning_window)

    def _on_continue(_):
        save_pref(cmds.checkBox(never_show_checkbox, q=True, value=True))
        cmds.deleteUI(warning_window)

    button_row = cmds.rowLayout(
        numberOfColumns=3,
        adjustableColumn=1,
        parent=content_col)

    cmds.separator(style='none', parent=button_row)  # pushes buttons right

    cmds.button(
        label="Reveal Curves",
        command=_on_reveal_nurbs_curves,
        w=130,
        parent=button_row
    )

    cmds.button(
        label="Continue",
        command=_on_continue,
        w=90,
        parent=button_row
    )

    cmds.separator(w=15, style='none', parent=outer_row)  # RIGHT MARGIN
    cmds.separator(h=10, style='none', parent=main_col)  # BOTTOM MARGIN

    cmds.showWindow(warning_window)


def save_pref(never_show: bool):
    if never_show:
        cmds.optionVar(iv=(constants.SKIP_NURBS_WARNING, 1))


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
    if context.bake_on_all_frames:
        utils_animation.copy_anim_from_parent_to_target(
            parent=base_controller,
            target=temp_controller,
            smart=False)
    else:
        utils_animation.copy_anim_from_parent_to_target(
            parent=base_controller,
            target=temp_controller,
            smart=True)

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


def create_child_controller(parent_node: ctrl_node.ControllerNode, context: controller_context.TempControllerCreationContext):
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

    child_controller = create_new_controller(
        name=f"{parent_name}_Child#",
        parent_group=parent_name,
        translation=world_translation,
        context=context)

    return child_controller
