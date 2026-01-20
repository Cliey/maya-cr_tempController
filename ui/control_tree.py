import maya.api.OpenMaya as om
import maya.cmds as cmds
import cr_tempController.core.controller_factory as controller_factory
import cr_tempController.core.controller_node as ctrl_node
import cr_tempController.core.pivot_tools as pivot_tools
import cr_tempController.constants as constants
import cr_tempController.utils.animation as utils_animation
import cr_tempController.utils.nodes as utils_nodes
import cr_tempController.utils.context as utils_context
import logging

LOGGER = logging.getLogger(__name__)

ControllerNodeMap = dict[str, ctrl_node.ControllerNode]


class ControlTreeMayaUI:
    def __init__(self, on_select_update_ui_callback: callable, controller_tree: dict = {}):
        self.tree = constants.TREE_NAME

        self.controller_map: ControllerNodeMap = {}  # string → ControllerNode
        # list of top-level controller (the one from which we want to create a temporary controller)
        self.root_nodes: list[str] = []

        self.active_pivot_tool = None  # keep a reference to prevent Garbage Collector
        self.on_select_update_ui_callback = on_select_update_ui_callback

        self.rebuild_tree(controller_tree)

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

    def _install_tree(self, root_nodes: list[ctrl_node.ControllerNode]) -> None:
        """
        Install a freshly built controller tree into internal state.
        """
        self.root_nodes = []
        self.controller_map.clear()

        def register(node: ctrl_node.ControllerNode):
            self.controller_map[node.name] = node
            for child in node.children:
                register(child)

        for node in root_nodes:
            self.root_nodes.append(node.name)
            register(node)

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

        self._install_tree(root_nodes)

    def rebuild_tree_view(self):
        cmds.treeView(self.tree, e=True, removeAll=True)
        self.populate_tree()

    def populate_tree(self):
        """
        Populate the treeView object with the controllers found into the scene
        """

        def _populate(parent_name, node: ctrl_node.ControllerNode):
            self.__updateTree(parent_name, node.name)
            for child in node.children:
                _populate(node.name, child)

        for root_name, node in self.controller_map.items():
            if node.parent is None:
                _populate("", node)

    def create_tree_ui(self, layout):
        """
        Create the treeView object into the UI under **layout**.

        :param layout: Layout where the treeView will be added 
        """

        self.tree = cmds.treeView(self.tree,
                                  parent=layout,
                                  numberOfButtons=1,
                                  abr=True,
                                  height=200,
                                  allowMultiSelection=False,
                                  selectCommand=self.__on_select,
                                  editLabelCommand=self.__on_edit_label,
                                  itemRenamedCommand=self.__on_item_renamed,
                                  pressCommand=[(1, self.__on_add_child)])

        # self.__init_undo_redo_scriptjob()

    def __init_undo_redo_scriptjob(self):
        """
        Initialize scriptJobs for Undo and Redo command to rebuild the tree.
        """
        cmds.scriptJob(
            event=["Undo", self.__rebuild_tree],
            parent=self.tree,
            protected=True)
        cmds.scriptJob(
            event=["Redo", self.__rebuild_tree],
            parent=self.tree,
            protected=True)

    def __on_select(self, node, is_selected):
        if not is_selected:
            return True

        cmds.select(node, replace=True)
        return True

    def contains(self, node: str) -> bool:
        """
        Check if the Tree View contains the specified item

        :param node: Controller to test
        :type node: str
        :return: Description
        :rtype: bool
        """
        return node in self.controller_map or node in self.root_nodes

    def select_item(self, node: str):
        """
        Select the item specified in the Tree View.
        Force single selection in the tree.

        :param node: Name of the item to select
        :type node: str
        """
        self.clear_selection()
        cmds.treeView(self.tree, edit=True, selectItem=[node, True])

    def clear_selection(self):
        """
        Clear the current selection in the Tree View

        """
        current = cmds.treeView(self.tree, q=True, selectItem=True) or []
        for item in current:
            cmds.treeView(self.tree, edit=True, selectItem=[item, False])

    def __on_edit_label(self, old_name: str, new_name: str) -> str:
        """
        Called when label in the tree is edited. Won't be renamed if the controller is a root_node

        :param old_name: Old name of the controller
        :param new_name: New name of the controller
        """
        LOGGER.debug(f"Edit name from: {old_name} to {new_name}")
        if (old_name == new_name) or (old_name in self.root_nodes):
            self.__defered_force_tree_label(old_name, old_name)
            return old_name
        try:
            controller_node = self.controller_map.get(old_name)
            if not controller_node:
                LOGGER.warning(
                    f"Node {old_name} not found in controller_map. Aborting rename.")
                return old_name

            actual_new_name = cmds.rename(old_name, f"{new_name}")

            # Update model using the real Maya name
            controller_node.name = actual_new_name
            self.controller_map[actual_new_name] = controller_node
            if old_name != actual_new_name:
                self.controller_map.pop(old_name, None)

            # Should be used to rename it into the UI, treeView quirk
            self.__defered_force_tree_label(old_name, actual_new_name)

            return actual_new_name
        except Exception as e:
            LOGGER.warning(f"Rename failed: {e}")
            self.__defered_force_tree_label(old_name, old_name)
            return old_name  # prevent treeView label change on error

    def __on_item_renamed(self, old_name, new_name):
        LOGGER.debug(f"Tree item renamed: {old_name} -> {new_name}")
        return

    def __defered_force_tree_label(self, old_name, new_name):
        def _force_tree_label():
            if cmds.treeView(self.tree, q=True, itemExists=old_name):
                cmds.treeView(
                    self.tree,
                    edit=True,
                    displayLabel=(old_name, new_name)
                )

        cmds.evalDeferred(
            lambda: _force_tree_label()
        )

    def __on_add_child(self, node, _):
        """
        Add a child to a temporary controller

        :param node: the temporary controller we add a child to        
        """
        LOGGER.debug(f"Add child on: {node}")

        # Get the parent ControllerNode from the map
        parent_node = self.controller_map.get(node)
        if not parent_node:
            LOGGER.warning(
                f"Parent controller '{node}' not found in controller map.")
            return

        with utils_context.UndoChunk():
            try:
                self.create_child_controller(parent_node)

            except Exception:
                LOGGER.exception("Error when adding a child.")
                raise

    def create_child_controller(self, parent_node: ctrl_node.ControllerNode):
        """
        Create a child controller from the parent_node

        :param parent_node: Description
        :type parent_node: ctrl_node.ControllerNode
        """
        # Factory creates the Maya node
        child_controller = controller_factory.create_child_controller(
            parent_node=parent_node)

        # Rewire constraints
        utils_nodes.reconnect_constraints(child_controller)

        # Register in tree state
        self._register_child_node(parent_node, child_controller)

        self.__updateTree(parent_node.name, child_controller)

    def _register_child_node(self, parent_node: ctrl_node.ControllerNode, child_controller: str):
        """
        Create ControllerNode instance and register it internally.
        """
        child_node = ctrl_node.ControllerNode(
            name=child_controller,
            parent=parent_node
        )

        parent_node.add_child(child_node)
        self.controller_map[child_node.name] = child_node

    def register_controller_in_tree(self, base_controller: str, temp_controller: str):
        """
        Finalize temp controller creation: run factory operations + update UI state.

        :param base_controller: Name of the original controller
        :param temp_controller: Name of the newly created temp controller
        :param context: Creation context
        """
        # 2. Register in tree data model
        self.__create_controller_tree(
            base_controller_name=base_controller,
            temp_controller_name=temp_controller
        )

        # 3. Update tree UI
        self.__updateTree('', base_controller)
        self.__updateTree(base_controller, temp_controller)
        cmds.select(temp_controller)

    def __create_controller_tree(self, base_controller_name: str, temp_controller_name: str,):
        base_controller_node = ctrl_node.ControllerNode(
            name=base_controller_name)  # First node as it's base controller
        temp_controller_node = ctrl_node.ControllerNode(
            name=temp_controller_name, parent=base_controller_node)
        base_controller_node.add_child(temp_controller_node)
        self.controller_map[temp_controller_name] = temp_controller_node
        self.root_nodes.append(base_controller_node.name)

    def __get_min_first_keyframe(self, parent, controller, start_time, end_time):
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

    def __get_max_last_keyframe(self, parent, controller, start_time, end_time):
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

    def __get_first_last_keyframe(self, parent, controller):
        """
        TODO If parent not animated => get from controller
        But if child of parent has key after -> need to take them
        """
        start_time, end_time = utils_animation.get_start_end_time_of_animation()
        first_key = self.__get_min_first_keyframe(
            parent, controller, start_time, end_time)
        last_key = self.__get_max_last_keyframe(
            parent, controller, start_time, end_time)
        return int(first_key), int(last_key)

    def confirm_action(self, title: str, message: str, icon: str, on_confirm: callable):
        result = cmds.confirmDialog(
            title=title,
            message=message,
            icon=icon,
            button=["Cancel", "Continue"],
            defaultButton="Continue",
            cancelButton="Cancel",
            dismissString="Cancel"
        )

        if result == "Continue":
            on_confirm()

    def on_edit_pivot(self, *args):
        """
        Called when user want to change pivot of the selected controller

        :param *args: Not used
        """
        selected_controller = cmds.treeView(
            self.tree, query=True, selectItem=True)[0]

        if selected_controller in self.root_nodes:
            LOGGER.warning(
                f"{selected_controller} is a base controller. You can't change the pivot of this controller.")
            self.error_dialog(
                title="Error during Edit Pivot",
                message=f"Controller '{selected_controller}' is a base controller. You can't change the pivot of this controller.")
            return

        LOGGER.debug(f"Change pivot on: {selected_controller}")
        self.__on_change_pivot(selected_controller)

    def __on_change_pivot(self, node):
        """
        Called when user want to change pivot of a controller

        :param node: Controller name we want to update the pivot
        """
        LOGGER.info(f"Change change pivot on: {node}")

        children_controller = cmds.listRelatives(
            node, children=True, type="transform", fullPath=True) or []
        children_with_animation = [child for child in children_controller if cmds.keyframe(
            child, q=True, keyframeCount=True)]

        if children_with_animation:
            LOGGER.warning(
                "Pivot change with heavy animation. Children of controller also has animation!")

            children_text = "\n- ".join(
                cmds.ls(children_with_animation, shortNames=True))
            LOGGER.warning(
                "Children with animation:\n" + children_text
            )
            self.confirm_action(
                title="Animation on controller and children",
                message=f"The controller {node} and its children have animation. Are you sure you want to edit the pivot of that controller?\n"
                "This may result in significant changes for the children to keep the current animation.\n\n"
                "Children with animation:\n- " + children_text,
                icon="warning",
                on_confirm=lambda: self.__confirm_change_pivot(node))

            return

        if cmds.keyframe(node, q=True, keyframeCount=True):
            LOGGER.warning(f"Controller {node} has animation.")
            self.confirm_action(title="Animation on controller",
                                message=f"Controller {node} has animation. Are you sure you want to edit the pivot of that controller?",
                                icon="question",
                                on_confirm=lambda: self.__confirm_change_pivot(node))
            return

        self.__confirm_change_pivot(node)

    def __confirm_change_pivot(self, node):
        selected_controller = self.controller_map.get(node)
        parent_is_root = selected_controller.parent.name in self.root_nodes
        self.active_pivot_tool = pivot_tools.PivotTool(
            node, parent_is_root=parent_is_root)
        self.active_pivot_tool.exec()

    def on_bake_and_delete(self, *args):
        """
            Public entry point: bake animation for selected controller in Tree and remove it.
            This will recursively process children first.

        :param *args: Not used
        """
        selected_controller = cmds.treeView(
            self.tree, query=True, selectItem=True)[0]

        if selected_controller in self.root_nodes:
            LOGGER.warning(
                f"{selected_controller} is a base controller. You can't bake or delete this controller.")
            self.error_dialog(title="Error during Bake and Delete",
                              message=f"Controller '{selected_controller}' is a base controller. You can't bake or delete this controller.")

            return

        result = self.__on_bake_and_delete(selected_controller)
        if not result:
            self.error_dialog(title="Error during Bake and Delete",
                              message="An error occured during the Bake and Delete operation.")
            return

    def __on_bake_and_delete(self, node):
        """
        Bake animation for `node` (ctrl_node.ControllerNode) and remove it.
        This will recursively process children first.

        :param node: Controller name to bake
        :return: Result of the operation. False if an error occured. True if everything was fine
        """
        controller_node = self.controller_map.get(node, None)
        # Ensure node exists in our runtime map
        if not controller_node:
            LOGGER.warning(
                f"Node {node} not found in controller_map. Aborting bake.")
            return False

        with utils_context.UndoChunk():
            try:
                self.__bake_and_delete(controller_node)
            except Exception:
                LOGGER.exception("Error during Bake & Delete.")
                raise
        return True

    def __bake_and_delete(self, node: ctrl_node.ControllerNode):
       # If parent is base constroller, can bake it direct
        if self.__is_root_temp_controller(node):
            self.__bake_temporary_controller_to_base(node)
        else:
            # 1. Bake children first (copy list to avoid mutation issues)
            for child in list(node.children):
                """
                    TODO -> will not work if has multiple children 
                    NOT OK if parent -> child1/child2
                    OK if parent -> child -> child -> ...
                """
                self.__bake_temporary_controller_to_parent(child)

            # 2. Bake the current node
            self.__bake_temporary_controller_to_parent(node)

    def __is_root_temp_controller(self, node: ctrl_node.ControllerNode) -> bool:
        return node.parent.name in self.root_nodes

    def __bake_temporary_controller_to_parent(self, node: ctrl_node.ControllerNode):
        time_range = self.__get_first_last_keyframe(
            node.parent.name, node.name
        )

        node_parent_name = node.parent.name
        base_controller = utils_nodes.get_base_controller(node_parent_name)
        # Save matrix of base controller before transfer animation to retrieve the offset after
        base_matrix = self._preserve_world_transform(base_controller)

        self._transfer_animation_child_to_parent(node, time_range)

        LOGGER.debug(
            f"Rebuild constraint {base_controller} -> {node_parent_name}")

        self._restore_matrix_no_autokey(base_controller, base_matrix)
        cmds.parentConstraint(node_parent_name, base_controller, mo=True)

        self._remove_controller_from_model(node)

    def _preserve_world_transform(self, node):
        return cmds.xform(node, q=True, ws=True, matrix=True)

    def _transfer_animation_child_to_parent(self, child: ctrl_node.ControllerNode, time_range):
        parent_name = child.parent.name
        tmp_locator = cmds.spaceLocator(name=f"{parent_name}_TMP_LOC")[0]
        try:
            utils_animation.bake_with_constraint(driver=child.name,
                                                 driven=tmp_locator,
                                                 time_range=time_range,
                                                 maintain_offset=False,
                                                 smart=False)
            cmds.delete(child.name)
            utils_animation.bake_with_constraint(driver=tmp_locator,
                                                 driven=parent_name,
                                                 time_range=time_range,
                                                 maintain_offset=False,
                                                 smart=False)

        finally:
            cmds.delete(tmp_locator)

    def _restore_matrix_no_autokey(self, node, matrix):
        with utils_context.AutoKeyOff():
            cmds.xform(node, ws=True, matrix=matrix)

    def _remove_controller_from_model(self, node):
        cmds.treeView(self.tree, e=True, removeItem=node.name)
        self.controller_map.pop(node.name)
        node.parent.children.remove(node)

    def __bake_temporary_controller_to_base(self, node: ctrl_node.ControllerNode):
        """Bake the temporary controller to the base controller."""
        node_name = node.name
        parent_node_name = node.parent.name

        time_range = self.__get_first_last_keyframe(
            parent_node_name, node_name)

        # destinationLayer = "LayerName if bake on new layer"
        cmds.bakeResults(
            parent_node_name,
            time=time_range,
            simulation=True,
            sparseAnimCurveBake=True,
            preserveOutsideKeys=True,
            sampleBy=1.0
        )
        cmds.filterCurve(parent_node_name)

        # Remove all from tree
        self.__delete_root_node(node)

    def __delete_root_node(self, node: ctrl_node.ControllerNode):
        node_name = node.name
        node_parent_name = node.parent.name
        data_node = utils_nodes.retrieve_data_node(node_name)

        cmds.delete(node_name, data_node)
        # Remove node and all its child
        self._remove_node_tree_from_map(node)

        # Remove parent (Base controller) from controller_map AND root_nodes list
        self.controller_map.pop(node_parent_name)
        self.root_nodes.remove(node_parent_name)
        cmds.treeView(self.tree, e=True, removeItem=node_parent_name)

    def _remove_node_tree_from_map(self, node: ctrl_node.ControllerNode):
        """
        Recursively remove node and all children from controller_map

        :param node: Node we want to delete from the controller_map
        :type node: ctrl_node.ControllerNode
        """

        for child in node.children:
            self._remove_node_tree_from_map(child)

        self.controller_map.pop(node.name)

    def __updateTree(self, parent, node):
        """
        Update the tree view UI to add *node* to *parent*

        :param parent: Parent to add the node under
        :param node: Node to add
        """
        cmds.treeView(self.tree, e=True, addItem=(node, parent))
        if not parent:
            cmds.treeView(self.tree,
                          e=True,
                          buttonVisible=[(node, 1, False)],
                          labelBackgroundColor=(node, 0.47, 0.2, 0.39))
            return

        cmds.treeView(self.tree,
                      e=True,
                      buttonTextIcon=[(node, 1, "+")],
                      buttonTooltip=[(node, 1, "Add a child to this controller")])

    def on_delete(self, *args):
        """
        Called when user want to delete the selected controller.

        :param *args: Not used
        """
        LOGGER.info("Delete controller, no baking, data will be lost")
        selected_controller = cmds.treeView(
            self.tree, query=True, selectItem=True)[0]

        if selected_controller in self.root_nodes:
            LOGGER.warning(
                f"{selected_controller} is a base controller. You can't delete this controller.")
            self.error_dialog(
                title="Error during Delete Controller",
                message=f"Controller '{selected_controller}' is a base controller. You can't delete this controller.")
            return

        self.__on_delete_checks(selected_controller)

    def __on_delete_checks(self, node: str):
        """
        Called when user want to delete a controller

        :param node: Controller name we want to delete
        :type node: str
        """
        LOGGER.info(f"Check before deleting: {node}")
        if self.__has_children(node) or self.__has_animation(node):
            self.confirm_action(
                title="Confirm delete controller",
                message="This controller has children and/or animation.\nAre you sure?",
                icon="warning",
                on_confirm=lambda: self.__confirm_delete(node)
            )
        else:
            self.__confirm_delete(node)

    def __has_children(self, node: str) -> bool:
        children = cmds.listRelatives(
            node, children=True, type="transform", fullPath=True) or []
        LOGGER.debug(f"{node} children: {children}")
        return len(children) > 0

    def __has_animation(self, node: str) -> bool:
        key_count = cmds.keyframe(node, q=True, keyframeCount=True)
        LOGGER.debug(f"{node} keyframes: {key_count}")
        return key_count > 0

    def __confirm_delete(self, node: str):
        result = self.__on_delete_controller(node)
        if not result:
            self.error_dialog(title="Error during Delete operation",
                              message="An error occured during the Delete operation.")
        return

    def __on_delete_controller(self, node: str):
        controller_node = self.controller_map.get(node, None)
        # Ensure node exists in our runtime map
        if not controller_node:
            LOGGER.warning(
                f"Node {node} not found in controller_map. Aborting bake.")
            return False

        with utils_context.UndoChunk():
            try:
                self.__delete_controller(controller_node)
            except Exception:
                LOGGER.exception("Error during Delete.")
                raise
        return True

    def __delete_controller(self, node: ctrl_node.ControllerNode):
       # If parent is base constroller
        if self.__is_root_temp_controller(node):
            self.__delete_root_node(node)
            return

        self.__delete_node(node)

    def __delete_node(self, node: ctrl_node.ControllerNode):
        """
        Delete the node specified

        :param node: The node to delete
        :type node: ctrl_node.ControllerNode
        """

        node_name = node.name
        node_parent_name = node.parent.name
        base_controller_name = utils_nodes.get_base_controller(
            node_parent_name)

        # Reset each child transform
        for child in node.children:
            cmds.setAttr(f"{child.name}.translate", 0, 0, 0)
            cmds.setAttr(f"{child.name}.rotate", 0, 0, 0)

        cmds.setAttr(f"{node_name}.translate", 0, 0, 0)
        cmds.setAttr(f"{node_name}.rotate", 0, 0, 0)
        base_controller_world_position = self._preserve_world_transform(
            base_controller_name)

        cmds.delete(node_name)

        self._restore_matrix_no_autokey(node=base_controller_name,
                                        matrix=base_controller_world_position)

        cmds.parentConstraint(
            node_parent_name,
            base_controller_name,
            mo=True
        )[0]
        self._remove_controller_from_model(node)

    def error_dialog(self, title: str, message: str):
        cmds.confirmDialog(title=title,
                           message=message,
                           messageAlign="center",
                           icon="critical",
                           button=["Cancel"],
                           defaultButton="Cancel",
                           cancelButton="Cancel",
                           dismissString="Cancel")

    def on_close(self):
        self.controller_map.clear()
        self.root_nodes.clear()
