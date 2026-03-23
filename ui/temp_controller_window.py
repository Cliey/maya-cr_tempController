import maya.cmds as cmds
import cr_tempController.constants as constants
from . import control_tree
import cr_tempController.core.controller_context as controller_context
import cr_tempController.core.controller_factory as controller_factory
import cr_tempController.core.controller_mode as controller_mode
import cr_tempController.utils.controller_shapes as controller_shapes
import cr_tempController.utils.hierarchy as utils_hierarchy
import cr_tempController.utils.naming as utils_naming
import cr_tempController.utils.rotation_order as rotation_order
import cr_tempController.ui.bake_options_frame as bake_options_frame
import logging
from enum import Enum

LOGGER = logging.getLogger(__name__)


class TempControllerWindowMayaUI:
    def __init__(self):
        self.window = constants.TOOL_WINDOW_NAME

        self.current_controller_tree = utils_hierarchy.build_controller_tree_from_scene()

        self.tree_view_control = control_tree.ControlTreeMayaUI(
            on_select_update_ui_callback=self._update_ui_from_selection,
            build_context_callback=self._build_child_context,
            get_bake_options_callback=self._build_bake_options_context,
            controller_tree=self.current_controller_tree)

        self.create_controller_frame = constants.FRAME_CREATE_CONTROLLER
        self.button_create_controller = constants.BUTTON_CREATE_CONTROLLER
        self.bake_all_frames_new_controller = constants.CHECKBOX_BAKE_ALL_FRAMES_NEW_CONTROLLER
        self.controller_mode_radio = constants.RADIO_GROUP_CONTROLLER_MODE
        self.selected_frame = constants.FRAME_SELECTED_CONTROLLER
        self.details_frame = constants.FRAME_CONTROLLER_DETAILS
        self.general_options_frame = constants.FRAME_GENERAL_OPTIONS
        self.color_creation = None
        self.color_properties = None
        self.shape_menu_creation = constants.SHAPE_MENU_CREATION_NAME
        self.shape_menu_properties = constants.SHAPE_MENU_PROPERTIES_NAME
        self.rotate_order_menu_creation = None
        self.bake_options_frame = None

    def _update_ui_from_selection(self, selected_object: str | None):
        """
        Update UI based on current viewport selection
        """
        if not selected_object:
            self.__update_ui_nothing_selected()
            return

        cmds.frameLayout(self.general_options_frame, edit=True, enable=True)
        is_controller = self.tree_view_control.node_is_temporary_controller(
            selected_object)
        is_root_node = self.tree_view_control.node_is_base_controller(
            selected_object)
        in_tree = is_controller or is_root_node

        # Enable create button ONLY if object is NOT in tree
        cmds.frameLayout(self.create_controller_frame,
                         edit=True,
                         enable=not in_tree)

        if self.color_creation:
            self.color_creation.set_enabled(not in_tree)

        # Details only if object exists in tree AND is not a base controller
        enable_details = in_tree and not is_root_node
        cmds.frameLayout(self.selected_frame, edit=True, enable=enable_details)
        cmds.frameLayout(self.details_frame, edit=True, enable=enable_details)

        """
            #TODO -> enable shape_menu_properties etc
        if self.color_properties:
            self.color_properties.set_enabled(enable_details)
        """

    def __update_ui_nothing_selected(self):
        cmds.frameLayout(self.selected_frame, edit=True, enable=False)
        cmds.frameLayout(self.details_frame, edit=True, enable=False)
        cmds.frameLayout(self.create_controller_frame, edit=True, enable=False)
        cmds.frameLayout(self.general_options_frame, edit=True, enable=False)

    def _build_child_context(self, parent_node):
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

        ro = self.rotate_order_menu_creation.get_rotate_order()
        rotate_order = ro if ro is not None else cmds.getAttr(
            f"{parent_node.name}.rotateOrder")

        return controller_context.TempControllerCreationContext(
            size_ratio=__controller_ratio(parent_node.depth),
            rgb_color=parent_color,
            shape=shape,
            rotate_order=rotate_order
        )

    def _build_bake_options_context(self):
        return self.bake_options_frame.get_context()

    def __job_on_selection_changed_callback(self):
        """
        Callback called on SelectionChanged event. Used to update the UI of the plugin.
        """
        list_selected_objects = cmds.ls(selection=True)
        if not list_selected_objects:
            self.tree_view_control.clear_selection()
            self._update_ui_from_selection(selected_object=None)
            return

        select_object = list_selected_objects[0]

        if self.tree_view_control.contains(select_object):
            self.tree_view_control.select_item(select_object)
        else:
            self.tree_view_control.clear_selection()

        self._update_ui_from_selection(select_object)

        return

    def create_shape_dropdown_menu(self, shape_menu_name, parent):
        shape_menu = cmds.optionMenu(shape_menu_name, parent=parent)
        for key in controller_shapes.SHAPE_LABEL_TO_ENUM.keys():
            cmds.menuItem(label=key)

        return shape_menu

    def show(self):
        """
        New UI
            [ Create Controller ] [ Reparent (? what should it does?)] [ x ] Bake animation on all frames
            Color:          (•) [ Predefined ] ( ) [ Color swatch ▼ ]

            --------------------------------
            GENERAL OPTIONS
            --------------------------------
            Mode:  (•) World Space  ( ) Object Space ( ) Relative Space (Select 2 controllers) ( ) Camera Space
                For mode -> Can create different type of temp controller -> TempControllerWorldSpace, TempControllerObjectSpace
                Inherit fro ma common TempController -> just add function for the specific baking/operation for each
                 = > To check & design

            Rotate Order:   [ Dropdown ] [ Custom DropDown ]
            Shape:          [ Dropdown ]

            --------------------------------
            TEMP CONTROLLERS
            --------------------------------
            [ Tree View ]
            Pcube1
            ├─ ctrl_tmp_1
            └─ ctrl_tmp_2
            Pcube2
            └─ ctrl_tmp_1

            --------------------------------
            SELECTED CONTROLLER
            --------------------------------
            [ Edit Pivot ]   [ Bake & Delete ]   [ Delete Only ]

            Name:        [ pCube1_tmp_ctrl ]
            Shape:       [ Dropdown ]
            Color:       [ Color swatch ▼ ]
            Active:      [ ☑ Driver Enabled ]

            --------------------------------
            ADVANCED OPTION
            --------------------------------            
            ▼ Bake Options (click arrow to expand/collapse)
                    [The arrow (▼) is part of a frameLayout with collapse = True
                    Default state: collapsed (hidden)
                    When user clicks it, panel expands showing the options]
                Sample by: [Dropdown: "1" / "5" / "10"]
                Bake method: [Dropdown: "Sample By" / "Smart"] (Tooltip -> "Smart bake can lose precision, Sample By is safer for animated children")
                [ ] Apply filter
            [ CLOSE ]
        """
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window)

        self.window = cmds.window(
            self.window,
            title=constants.TOOL_WINDOW_TITLE,
            widthHeight=(310, 650),
            maximizeButton=False,
            sizeable=True,
            closeCommand=self.__on_window_close
        )

        column_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

        # TODO - Check current selected when opening the window, if in controller_node map -> enable = true

        # -------------------------------------------------
        # CREATE CONTROLLER
        # -------------------------------------------------
        self.__build_create_controller_frame(parent=column_layout)

        cmds.setParent(column_layout)

        # -------------------------------------------------
        # OPTIONS FRAME
        # -------------------------------------------------
        self.__build_options_controller_frame(parent=column_layout)

        cmds.setParent(column_layout)

        # -------------------------------------------------
        # TEMP CONTROLLERS
        # -------------------------------------------------
        self.__build_tree_frame(parent=column_layout)

        cmds.setParent(column_layout)

        # -------------------------------------------------
        # SELECTED CONTROLLER
        # -------------------------------------------------
        self.__build_selected_controller(parent=column_layout)

        cmds.setParent(column_layout)

        # -------------------------------------------------
        # ADVANCED OPTIONS
        # -------------------------------------------------
        self.bake_options_frame = bake_options_frame.BakeOptionFrame(
            parent=column_layout)

        cmds.setParent(column_layout)
        # Close button
        cmds.button(label="Close", height=30,
                    command=lambda *_: cmds.deleteUI(self.window))

        # -------------------------------------------------
        # LOAD INFO FROM OPTION VAR
        # -------------------------------------------------
        self.__update_ui_on_launch()

        # -------------------------------------------------
        # SHOW
        # -------------------------------------------------
        cmds.showWindow(self.window)

        # Create job when Selection Changed, to update the UI
        job_on_selection = cmds.scriptJob(
            event=["SelectionChanged", self.__job_on_selection_changed_callback],
            parent=self.window,
            protected=True)
        LOGGER.debug(
            f"Temp Controller Window, on SelectionChanged job number = {job_on_selection}")

    def __update_ui_on_launch(self):
        self.__load_from_optionVar()
        self.__job_on_selection_changed_callback()

    def __load_from_optionVar(self):
        """
        Load persistent data saved before to init the UI with last value selected by the user the last time he used the plugin.        
        """
        if cmds.optionVar(exists=constants.LAST_MODE_SELECTED):
            last_mode_selected = cmds.optionVar(q=constants.LAST_MODE_SELECTED)
            cmds.radioButtonGrp(self.controller_mode_radio,
                                edit=True,
                                select=last_mode_selected)

        if cmds.optionVar(exists=constants.LAST_SHAPE_SELECTED):
            last_shape_selected = cmds.optionVar(
                q=constants.LAST_SHAPE_SELECTED)
            cmds.optionMenu(self.shape_menu_creation,
                            edit=True,
                            select=last_shape_selected)

        if cmds.optionVar(exists=constants.LAST_COLOR_SELECTED_IS_CUSTOM):
            last_color_selected_is_custom = cmds.optionVar(
                q=constants.LAST_COLOR_SELECTED_IS_CUSTOM)
            self.color_creation.select_custom(last_color_selected_is_custom)

        if cmds.optionVar(exists=constants.LAST_CUSTOM_COLOR_R):
            r = cmds.optionVar(q=constants.LAST_CUSTOM_COLOR_R) / 255
            g = cmds.optionVar(q=constants.LAST_CUSTOM_COLOR_G) / 255
            b = cmds.optionVar(q=constants.LAST_CUSTOM_COLOR_B) / 255
            self.color_creation.change_custom_color(r, g, b)

        if (cmds.optionVar(exists=constants.BAKE_OPTIONS_FRAME_COLLAPSE_STATE) and
            cmds.optionVar(exists=constants.BAKE_OPTIONS_BAKE_METHOD) and
            cmds.optionVar(exists=constants.BAKE_OPTIONS_SAMPLE_BY) and
                cmds.optionVar(exists=constants.BAKE_OPTIONS_APPLY_FILTER)):
            frame_collapsed = cmds.optionVar(
                q=constants.BAKE_OPTIONS_FRAME_COLLAPSE_STATE)
            bake_method = cmds.optionVar(q=constants.BAKE_OPTIONS_BAKE_METHOD)
            sample_by = cmds.optionVar(q=constants.BAKE_OPTIONS_SAMPLE_BY)
            apply_filter = cmds.optionVar(
                q=constants.BAKE_OPTIONS_APPLY_FILTER)

            self.bake_options_frame.init_fields_from_option_var(frame_collapsed=frame_collapsed,
                                                                bake_method=bake_method,
                                                                sample_by=sample_by,
                                                                apply_filter=apply_filter)

    def __on_window_close(self, *args):
        if self.tree_view_control:
            # TODO -> close Pivot Tool if active
            self.tree_view_control.on_close()
            pass

        self._save_to_optionVar()

    def _save_to_optionVar(self):
        """
        Save persistent data to Maya memory to retrieve it when the user will open the plugin again.        
        """
        # Save Creation Selection
        last_mode_selected = cmds.radioButtonGrp(self.controller_mode_radio,
                                                 query=True,
                                                 select=True)
        cmds.optionVar(iv=(constants.LAST_MODE_SELECTED,
                           last_mode_selected))
        last_shape_selected = cmds.optionMenu(self.shape_menu_creation,
                                              q=True,
                                              select=True)
        cmds.optionVar(iv=(constants.LAST_SHAPE_SELECTED,
                           last_shape_selected))

        cmds.optionVar(iv=(constants.LAST_COLOR_SELECTED_IS_CUSTOM,
                           self.color_creation.is_custom_selected()))

        # Save custom RGB
        rgb_color = self.color_creation.get_color()
        if rgb_color:
            cmds.optionVar(
                fv=(constants.LAST_CUSTOM_COLOR_R, rgb_color[0] * 255))
            cmds.optionVar(
                fv=(constants.LAST_CUSTOM_COLOR_G, rgb_color[1] * 255))
            cmds.optionVar(
                fv=(constants.LAST_CUSTOM_COLOR_B, rgb_color[2] * 255))

        # Save Bake options
        frame_collapsed, bake_method, sample_by, apply_filter = self.bake_options_frame.get_fields_to_save()

        cmds.optionVar(
            iv=(constants.BAKE_OPTIONS_FRAME_COLLAPSE_STATE, frame_collapsed))
        cmds.optionVar(sv=(constants.BAKE_OPTIONS_BAKE_METHOD, bake_method))
        cmds.optionVar(iv=(constants.BAKE_OPTIONS_SAMPLE_BY, sample_by))
        cmds.optionVar(iv=(constants.BAKE_OPTIONS_APPLY_FILTER, apply_filter))

    def __build_create_controller_frame(self, parent):
        self.create_controller_frame = cmds.frameLayout(
            label="Create Controller",
            collapsable=False,
            marginWidth=6,
            marginHeight=6,
            parent=parent
        )

        # Top buttons row
        cmds.rowLayout(
            numberOfColumns=4,
            adjustableColumn=2,
            columnAlign=(1, "left"),
            columnAttach=[(1, "both", 0), (2, "both", 8),
                          (3, "both", 4), (4, "both", 0)],
            parent=self.create_controller_frame
        )

        self.button_create_controller = cmds.button(
            self.button_create_controller, label="Create Controller", command=self.__new_controller)
                # Bake on all frame if animation
        self.bake_all_frames_new_controller = cmds.checkBox(
            self.bake_all_frames_new_controller,
            label="Bake animation on all frames",
            value=False,
            align="left",
            statusBarMessage="When checked, if controller has animation, the new temporary controller will be baked on all frames."

        )
        cmds.separator(style="none")
        cmds.separator(style="none")
        """
        TODO in the future ?
        cmds.button(label="Reparent",
                    enable=False,
                    statusBarMessage='#TODO - Select controller to reparent first, then the controller you want to parent it to')
        cmds.button(label="More", enable=False)"""

        option_color_layout = cmds.rowColumnLayout(
            numberOfColumns=2,
            columnWidth=[(1, 80), (2, 260)],
            columnSpacing=[(2, 10)],
            rowSpacing=(1, 6),
            parent=self.create_controller_frame
        )

        cmds.text(label="Color:", align="right")
        self.color_creation = ColorSelector(
            name=constants.COLOR_CREATION,
            parent=option_color_layout)

        cmds.setParent(self.create_controller_frame)

    def __build_options_controller_frame(self, parent):
        self.general_options_frame = cmds.frameLayout(
            label="General Options",
            collapsable=False,
            marginWidth=6,
            marginHeight=6,
            parent=parent
        )

        # Mode options
        cmds.text(label="Mode:", align="left")

        cmds.rowLayout(
            numberOfColumns=4,
            columnAlign=(1, "left"),
            adjustableColumn=4
        )

        self.controller_mode_radio = cmds.radioButtonGrp(
            self.controller_mode_radio,
            numberOfRadioButtons=3,
            labelArray3=[
                controller_mode.MODE_ENUM_TO_LABEL[controller_mode.ControllerCreationMode.WORLD_SPACE],
                controller_mode.MODE_ENUM_TO_LABEL[controller_mode.ControllerCreationMode.OBJECT_SPACE],
                controller_mode.MODE_ENUM_TO_LABEL[controller_mode.ControllerCreationMode.RELATIVE_SPACE]
            ],
            enable3=False,  # TODO develop the Relative Space feature
            # TODO -> All option relevant? Relative VS Object?
            select=1,
            columnAlign=[1, "left"],
            columnWidth=[(1, 90), (2, 90), (3, 110), (4, 90)]
        )

        cmds.setParent(self.general_options_frame)

        # Rotate order
        self.rotate_order_menu_creation = RotateOrderMenu(
            name=constants.ROTATE_ORDER_MENU_CREATION_NAME,
            parent=self.general_options_frame)

        cmds.setParent(self.general_options_frame)

        # Shape and color
        option_shape_layout = cmds.rowColumnLayout(
            numberOfColumns=2,
            columnWidth=[(1, 80), (2, 260)],
            columnSpacing=[(2, 10)],
            rowSpacing=(1, 6)
        )

        cmds.text(label="Shape:", align="right")
        self.shape_menu_creation = self.create_shape_dropdown_menu(
            shape_menu_name=self.shape_menu_creation,
            parent=option_shape_layout)

        cmds.setParent(self.general_options_frame)

    def __build_tree_frame(self, parent):
        temp_frame = cmds.frameLayout(
            label="Temp Controllers",
            collapsable=False,
            marginWidth=6,
            marginHeight=6,
            parent=parent
        )

        self.tree_view_control.create_tree_ui(temp_frame)

        self.tree_view_control.populate_tree()
        self.__init_undo_redo_scriptjob()

    def __init_undo_redo_scriptjob(self):
        """
        Initialize scriptJobs for Undo and Redo command to rebuild the tree.
        """
        cmds.scriptJob(
            event=["Undo", lambda: cmds.evalDeferred(self.__rebuild_tree)],
            parent=self.window,
            protected=True)
        cmds.scriptJob(
            event=["Redo", lambda: cmds.evalDeferred(self.__rebuild_tree)],
            parent=self.window,
            protected=True)

    def __rebuild_tree(self):
        """
        Rebuild the entire tree if change has been detected
        """
        new_controller_tree = utils_hierarchy.build_controller_tree_from_scene()

        """
        [BUG-7] self.current_controller_tree is evaluated at window creation
        not when adding new controller so if I create new one and Undo, it doesn't detect the change.

        -> For now it's working, but reload every undo/redo, a bit heavy.
        -> The check doesn't work because self.current_controller_tree is evaluated at window creation
            not when adding new controller so if I create new one and Undo, it doesn't detect the change.

        if self.current_controller_tree == new_controller_tree:
            LOGGER.info("Controller tree unchanged, skipping rebuild")
                return
        """
        self.current_controller_tree = new_controller_tree
        self.tree_view_control.rebuild_tree(
            controller_tree=new_controller_tree)
        self.tree_view_control.rebuild_tree_view()

    def __build_selected_controller(self, parent):
        self.selected_frame = cmds.frameLayout(
            self.selected_frame,
            label="Selected Controller",
            enable=False,
            collapsable=False,
            marginWidth=6,
            marginHeight=6,
            parent=parent
        )

        # Action buttons
        cmds.rowLayout(
            numberOfColumns=3,
            adjustableColumn=2,
            columnAttach=[(1, "both", 0), (2, "both", 6), (3, "both", 0)]
        )

        cmds.button(label='Edit Pivot',
                    command=self.tree_view_control.on_edit_pivot,
                    statusBarMessage='Edit pivot of the selected controller. If there is animation on the controller, the animate will be baked following the bake options set.')
        cmds.button(label='Bake and Delete',
                    command=self.tree_view_control.on_bake_and_delete,
                    statusBarMessage='Bake the controller on the parent controller based on the Bake Options then delete it. If the controller has children, the tool bake the children then the selected controller. If the controller is baked on the base controller, the object will disappear from the tree.')
        cmds.button(label='Delete',
                    command=self.tree_view_control.on_delete,
                    statusBarMessage='Delete the controller without baking it. Animation will be lost.')

        cmds.setParent(self.selected_frame)

        cmds.rowLayout(
            numberOfColumns=3,
            adjustableColumn=3,
            columnAttach=[(1, "left", 0), (2, "both", 6), (3, "both", 0)]
        )
        cmds.text(label="Active:", align="left")
        cmds.checkBox(
            label="Driver Enabled",
            value=True,
            enable=False,
            align="left"
        )
        cmds.separator(style="none")

        cmds.setParent(self.selected_frame)
        # ------------------------------------------
        # SELECTED CONTROLLER - PROPERTIES (HIDEABLE)
        # ------------------------------------------

        self.details_frame = cmds.frameLayout(
            self.details_frame,
            label="Controller Details",
            collapsable=True,
            collapse=True,      # hidden by default
            marginWidth=6,
            marginHeight=6,
            enable=False,
            manage=False,
            parent=self.selected_frame
        )

        properties_layout = cmds.rowColumnLayout(
            numberOfColumns=2,
            columnWidth=[(1, 80), (2, 260)],
            columnSpacing=[(2, 10)],
            rowSpacing=(1, 6),
            parent=self.details_frame
        )

        cmds.text(label="Name:", align="right", parent=properties_layout)
        cmds.textField(
            text="SOON AVAILABLE",  # TODO update based on selection!!
            editable=False,  # TODO enable in the future
            parent=properties_layout
        )

        cmds.text(label="Shape:", align="right", parent=properties_layout)
        self.shape_menu_properties = self.create_shape_dropdown_menu(
            shape_menu_name=self.shape_menu_properties,
            parent=properties_layout
        )
        cmds.optionMenu(self.shape_menu_properties, e=True,
                        enable=False)  # TODO enable in the future

        cmds.text(label="Color:", align="right", parent=properties_layout)
        self.color_properties = ColorSelector(
            name=constants.COLOR_PROPERTIES,
            parent=properties_layout)  # TODO enable in the future

        cmds.setParent(self.selected_frame)

    def __new_controller(self, _):
        # Check if selected object already has a child
        selection_list = cmds.ls(selection=True, tail=1)
        if not selection_list:
            LOGGER.warning(
                "Select an object to create the temporary controller.")
            return

        base_controller = selection_list[0]

        # Check hierarchy
        root = utils_hierarchy.get_tempcontrol_root(base_controller)
        if root:
            LOGGER.warning(
                "This object is already a Temporary Controller; cannot create a new controller here. You can only add a child.")
            return

        temp_data_name = utils_naming.build_temp_control_data_name(
            base_controller)

        if cmds.objExists(temp_data_name):
            LOGGER.warning(
                "This base object already has a temporary controller. It has been selected. You should create a child from this controller.")
            cmds.select(temp_data_name)
            return

        mode_selected = cmds.radioButtonGrp(self.controller_mode_radio,
                                            query=True,
                                            select=True)
        controller_shape_label = cmds.optionMenu(self.shape_menu_creation,
                                                 q=True,
                                                 value=True)

        ro = self.rotate_order_menu_creation.get_rotate_order()
        rotate_order = ro if ro is not None else cmds.getAttr(
            f"{base_controller}.rotateOrder")

        bake_on_all_frames = cmds.checkBox(
            self.bake_all_frames_new_controller,
            query=True,
            value=True)

        context = controller_context.TempControllerCreationContext(
            bake_on_all_frames=bake_on_all_frames,
            mode=controller_mode.ControllerCreationMode(mode_selected),
            rgb_color=self.color_creation.get_color(),
            shape=controller_shapes.SHAPE_LABEL_TO_ENUM[controller_shape_label],
            rotate_order=rotate_order)

        temp_controller = controller_factory.create_new_temporary_controller_from_base_controller(
            base_controller=base_controller,
            context=context
        )

        # Update Tree view
        self.tree_view_control.register_controller_in_tree(
            base_controller=base_controller,
            temp_controller=temp_controller
        )


class ColorSelector:
    def __init__(self, name, parent, size=20):
        self.name = name
        self.parent = parent
        self.size = size
        self.row_layout = f"{name}_rowLayout"

        self.radio_collection = f"{name}_radioCollection"
        self.palette_radio = None
        self.custom_radio = None
        self.palette = None
        self.picker_btn = None

        self._build()

    def _build(self):
        self.row_layout = cmds.rowLayout(self.row_layout,
                                         numberOfColumns=5,
                                         generalSpacing=6,
                                         parent=self.parent,
                                         enable=False)

        if not cmds.radioCollection(self.radio_collection, exists=True):
            cmds.radioCollection(self.radio_collection)

        self.palette_radio = cmds.radioButton(
            label="",
            collection=self.radio_collection,
            select=True
        )
        self.palette_radio = self.palette_radio.split("|")[-1]

        number_of_colors = len(constants.COLORS_RGB)
        self.palette = cmds.palettePort(
            f"{self.name}_palette",
            dimensions=(number_of_colors, 1),
            width=self.size * number_of_colors,
            height=self.size,
            colorEditable=False,
            changeCommand=self._on_palette_changed
        )

        for i, rgb in enumerate(constants.COLORS_RGB):
            cmds.palettePort(self.palette, e=True, rgbValue=(i, *rgb))

        self.custom_radio = cmds.radioButton(
            label="",
            collection=self.radio_collection
        )
        self.custom_radio = self.custom_radio.split("|")[-1]

        cmds.text(label="Custom:", align="left")

        self.picker_btn = cmds.iconTextButton(
            f"{self.name}_picker",
            style="iconOnly",
            width=self.size,
            height=self.size,
            enableBackground=True,
            backgroundColor=(0.18, 0.18, 0.18),
            annotation="Pick custom color",
            command=self._open_color_picker
        )

    def _on_palette_changed(self):
        cmds.radioButton(self.palette_radio, e=True, select=True)

    def _open_color_picker(self, *_):
        current = cmds.iconTextButton(
            self.picker_btn, q=True, backgroundColor=True)
        result = cmds.colorEditor(rgb=current)
        if not result:
            return

        if cmds.colorEditor(q=True, result=True):
            rgb = cmds.colorEditor(q=True, rgb=True)
            cmds.iconTextButton(self.picker_btn, e=True, backgroundColor=rgb)
            cmds.radioButton(self.custom_radio, e=True, select=True)

    def get_color(self):
        if self.is_custom_selected():
            return cmds.iconTextButton(self.picker_btn, q=True, backgroundColor=True)

        return cmds.palettePort(self.palette, q=True, rgb=True)

    def is_custom_selected(self):
        selected = cmds.radioCollection(
            self.radio_collection, q=True, select=True)
        return selected == self.custom_radio

    def select_custom(self, select: bool):
        cmds.radioButton(self.custom_radio, e=True, select=select)

    def change_custom_color(self, r, g, b):
        cmds.iconTextButton(
            self.picker_btn,
            edit=True,
            backgroundColor=(r, g, b)
        )

    def set_enabled(self, state=True):
        cmds.rowLayout(self.row_layout, e=True, enable=state)
        cmds.palettePort(self.palette, e=True, enable=state)
        cmds.iconTextButton(self.picker_btn, e=True, enable=state)
        cmds.radioButton(self.palette_radio, e=True, enable=state)
        cmds.radioButton(self.custom_radio, e=True, enable=state)


class RotateOrderMenu:
    class RotateOrderMenuChoice(Enum):
        CURRENT_SELECTION = 1
        CUSTOM = 2
        AUTO = 3

    MENU_CHOICE_LABEL_TO_ENUM = {
        "Current Selection": RotateOrderMenuChoice.CURRENT_SELECTION,
        "Custom": RotateOrderMenuChoice.CUSTOM,
        # "Auto": ControllerShape.CIRCLE,

    }

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.row_layout = f"{name}_rowLayout"

        self.rotate_order_dropdown = f"{name}_menu"
        self.custom_rotate_order = f"{name}_customRotateOrderMenu"
        self.custom_order_warning_message = f"{name}_warningMessage"

        self._build()

    def _build(self):
        column_layout = cmds.columnLayout()
        self.row_layout = cmds.rowLayout(
            self.row_layout,
            numberOfColumns=3,
            columnWidth=[(1, 90), (2, 160), (3, 80)],
            columnAttach=[(1, "right", 10), (2, "both", 0)],
            parent=column_layout
        )

        cmds.text(label="Rotate Order:",
                  align="right",
                  parent=self.row_layout)

        self.rotate_order_dropdown = self._create_option_menu(
            menu_name=self.rotate_order_dropdown,
            items=[label for label in self.MENU_CHOICE_LABEL_TO_ENUM.keys()],
            change_command=self.__on_change_rotate_order_menu,
            parent=self.row_layout
        )

        self.custom_rotate_order = self._create_option_menu(
            menu_name=self.custom_rotate_order,
            items=list(rotation_order.ROTATION_ORDERS.keys()),
            visible=False,
            parent=self.row_layout
        )

        self.custom_order_warning_message = cmds.text(label="Changing rotate order may affect animation accuracy.",
                                                      align="left",
                                                      # subtle amber
                                                      font="smallPlainLabelFont",
                                                      backgroundColor=(
                                                          0.4, 0.3, 0.0),
                                                      visible=False,
                                                      parent=column_layout)

    def __on_change_rotate_order_menu(self, selection: str):
        is_custom = (
            self.MENU_CHOICE_LABEL_TO_ENUM[selection] == self.RotateOrderMenuChoice.CUSTOM)
        cmds.optionMenu(self.custom_rotate_order,
                        edit=True,
                        visible=is_custom)
        cmds.text(self.custom_order_warning_message,
                  edit=True, visible=is_custom)

    def _create_option_menu(self, menu_name: str, items: list[str], parent: str, visible: bool = True, change_command=None):
        kwargs = {}
        if change_command is not None:
            kwargs["changeCommand"] = change_command

        option_menu = cmds.optionMenu(
            menu_name,
            visible=visible,
            parent=parent,
            **kwargs)
        for item in items:
            cmds.menuItem(label=item)
        return option_menu

    def _is_custom_selected(self) -> bool:
        """
        Check if custom rotate order is selected into DropDown menu
        """
        return cmds.optionMenu(self.rotate_order_dropdown,
                               query=True,
                               select=True) == self.RotateOrderMenuChoice.CUSTOM.value

    def get_rotate_order(self) -> int | None:
        if self._is_custom_selected():
            label = cmds.optionMenu(
                self.custom_rotate_order, query=True, value=True)
            return rotation_order.ROTATION_ORDERS[label]
        return None
