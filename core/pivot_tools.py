import maya.cmds as cmds
import maya.api.OpenMaya as om
import cr_tempController.constants as constants
import logging
import cr_tempController.utils.controller_shapes as controller_shapes
import cr_tempController.utils.animation as utils_animation
import cr_tempController.utils.nodes as utils_nodes

LOGGER = logging.getLogger(__name__)


class UndoChunkController:
    def __init__(self, name="PivotTool"):
        self.name = name
        self._open = False

    def open(self):
        if self._open:
            return
        cmds.undoInfo(openChunk=True, chunkName=self.name)
        self._open = True

    def close(self):
        if not self._open:
            return
        cmds.undoInfo(closeChunk=True)
        self._open = False

    def force_close(self):
        if self._open:
            cmds.undoInfo(closeChunk=True)
            self._open = False


class PivotTool:
    def __init__(self, controller_to_change_pivot, parent_is_root=False):
        LOGGER.info(f"Change change pivot on: {controller_to_change_pivot}")
        self.controller = controller_to_change_pivot
        self.parent_is_root = parent_is_root
        self.controller_has_animation = cmds.keyframe(
            self.controller, q=True, keyframeCount=True) > 0
        self.pivot_locator = None
        self.job_selection_changed = None
        self.job_cancel = None
        self.children_base_controller = []
        self._undo_chunk = UndoChunkController()

    def exec(self):
        """            
            [BUG-5] FIXED
            - If Anim
            - Tmp controller with anim baked with Rotation
            - Change tmp controller pivot
            Result: => base object has an offset from the previous animation
            DESIRE OUTPUT : 
                -> The base object should have the same animation

            => Fix = Use
                cmds.bakeResults(target, smart = False, time = (first_key, last_key), simulation = True, sampleBy = 1, sparseAnimCurveBake = False)
            Instead of smart_bake = 
            But we have a key on all frame
            TODO
            => Solution ++
            Baking every frame during pivot edits is the correct and unavoidable solution
            Recommended production-grade fix for BUG-5 and BUG-5-a

            A) Bake only during the operation, then optionally reduce
                Pipeline friendly approach:
                    Bake every frame during pivot edit
                    Optionally run a curve reduction pass
                    Preserve original tangents where possible

                Concrete improvement:
                    After baking:
                        cmds.filterCurve(target) (filter=FILTER)
                            FILTER = butterworth, euler (default), gaussian, keyReducer, peakRemover,
                                     keySync, resample, simplify
                        cmds.keyTangent(target, itt="auto", ott="auto")
                            ??

                Optionally expose a UI toggle:
                    [ ] Keep dense keys (safe)
                    [ ] Reduce keys (lossy but animator friendly)
                You already hinted at this idea in comments. I would formalize it.
        """

        self._undo_chunk.open()

        self.pivot_locator = cmds.spaceLocator(
            name=self.controller + constants.SUFFIXE_TEMP_PIVOT)[0]
        cmds.color(self.pivot_locator, rgbColor=[0.2, 1, 0.2])

        cmds.parent(self.pivot_locator, constants.TEMP_PIVOT_GROUP)
        # Align locator with controller
        cmds.delete(cmds.parentConstraint(
            self.controller, self.pivot_locator, mo=False))

        # Query the world-space rotate pivot of the controller
        pivot_pos = cmds.xform(self.controller, q=True, ws=True, rp=True)
        # Move the locator to that position
        cmds.xform(self.pivot_locator, ws=True, t=pivot_pos)

        cmds.select(self.pivot_locator)

        # Create a job to check SelectionChanged when Pivot Locator is deselected
        self.job_selection_changed = cmds.scriptJob(event=["SelectionChanged", self.__callback],
                                                    protected=True)

        LOGGER.debug(
            f"[EDIT PIVOT] Job Number = SELECTION CHANGED ({self.job_selection_changed})")

    def __get_children(self, node):
        return cmds.listRelatives(node, children=True, type="transform") or []

    def __get_parent(self, node):
        return cmds.listRelatives(node, parent=True, type="transform") or []

    def __link_saved_anim(self, controller, locator):
        if not cmds.attributeQuery(constants.ATTRIBUTE_SAVED_ANIM, node=controller, exists=True):
            cmds.addAttr(controller, ln=constants.ATTRIBUTE_SAVED_ANIM,
                         at="message", hidden=True)

        if not cmds.attributeQuery(constants.ATTRIBUTE_SOURCE_CTRL, node=locator, exists=True):
            cmds.addAttr(locator, ln=constants.ATTRIBUTE_SOURCE_CTRL,
                         at="message", hidden=True)

        cmds.connectAttr(
            f"{controller}.{constants.ATTRIBUTE_SAVED_ANIM}",
            f"{locator}.{constants.ATTRIBUTE_SOURCE_CTRL}",
            force=True
        )

    def __callback(self):
        if not self.__is_pivot_valid():
            return

        if not self.__pivot_still_selected():
            self.__apply_pivot_change()

    def __is_pivot_valid(self) -> bool:
        if not self.pivot_locator:
            LOGGER.warning(
                "[EDIT PIVOT] Selection changed but no pivot_locator detected. Abort pivot change procedure."
            )
            return False

        LOGGER.debug(
            f"[EDIT PIVOT] Selection changed for pivot {self.pivot_locator}")
        return True

    def __pivot_still_selected(self) -> bool:
        current_selection = cmds.ls(sl=True)
        return self.pivot_locator in current_selection

    def __apply_pivot_change(self) -> list[str]:
        LOGGER.info("[EDIT PIVOT] Pivot not selected anymore!")
        cmds.refresh(suspend=True)

        try:
            duplicate_controller = self.__duplicate_controller_without_children()
            self.children_base_controller = self.__get_controller_children(
                self.controller)

            self.__save_children_animation_if_needed()
            self.__move_duplicate_to_pivot(duplicate_controller)
            self.__copy_controller_animation(duplicate_controller)

            self.__replace_controller_in_hierarchy(duplicate_controller)
            duplicate_controller = self.__restore_children_animation()

            cmds.select(duplicate_controller)
        except Exception:
            LOGGER.exception("[EDIT PIVOT] Error during pivot change.")
            return False
        finally:
            self.__cleanup_pivot_edit()

    def __duplicate_controller_without_children(self) -> str:
        color = cmds.getAttr(self.controller + ".wireColorRGB")[0]

        duplicate = cmds.duplicate(
            self.controller,
            name=self.controller + constants.SUFFIXE_PIVOT_DUPLICATE,
            returnRootsOnly=True
        )[0]

        children = cmds.listRelatives(
            duplicate, children=True, type="transform", fullPath=True) or []
        if children:
            cmds.delete(children)

        cmds.color(duplicate, rgbColor=color)
        return duplicate

    def __get_controller_children(self, controller: str) -> list[str]:
        """
        Return direct transform children of the controller.
        """
        return cmds.listRelatives(
            controller,
            children=True,
            type="transform",
            fullPath=True
        ) or []

    def __save_children_animation_if_needed(self):
        if not any(cmds.keyframe(child, q=True, keyframeCount=True) for child in self.children_base_controller):
            return

        save_anim_node = cmds.createNode(
            "transform",
            name=constants.SAVE_ANIM,
            skipSelect=True
        )
        cmds.parent(save_anim_node, f"|{constants.TEMP_PIVOT_GROUP}")

        # Save anim in a map ctrller : pivot_save
        for child in self.children_base_controller:
            short_name = cmds.ls(child, shortNames=True)[0]
            locator_animation_saved = controller_shapes.create_locator(
                f"{short_name}{constants.SUFFIXE_LOCATOR_SAVE}"
            )

            cmds.parent(locator_animation_saved,
                        f"|{constants.TEMP_PIVOT_GROUP}|{constants.SAVE_ANIM}")
            utils_animation.copy_anim_from_parent_to_target(
                child,
                locator_animation_saved,
                maintain_offset=False,
                smart=False
            )
            self.__link_saved_anim(child, locator_animation_saved)

    def __move_duplicate_to_pivot(self, duplicate_controller: str):
        # TODO -> what about pivot rotation?
        pivot_pos = cmds.xform(self.pivot_locator, q=True, ws=True, t=True)
        if not self.parent_is_root:
            utils_nodes.freeze_translate_parent_space(
                duplicate_controller, self.pivot_locator)
        else:
            cmds.xform(duplicate_controller, ws=True, t=pivot_pos)

    def __copy_controller_animation(self, duplicate_controller: str):
        if not self.controller_has_animation:
            return

        # Need to NOT smart_bake or we lose prevision.
        # TODO -> Smart Bake perso or asking if want to allow smart Bake (sparseAnimCurveBake = True) but can lose information
        # -> TODO [IDEA] Can run a script to save all position for BEFORE pivot change (for the original base controller) and then AFTER to see the difference

        utils_animation.copy_anim_from_parent_to_target(
            parent=self.controller,
            target=duplicate_controller,
            maintain_offset=True,
            smart=False
        )

    def __replace_controller_in_hierarchy(self, duplicate_controller: str):
        """
        Move children from old controller to the new one (duplicate_controller) and rebuild the constraint if it is the last controller

        :param duplicate_controller: Controller to reparent children to
        :type duplicate_controller: str
        """
        # Save parent & move children out Then Delete old controller
        children_controller = self.__get_children(self.controller)

        if children_controller:
            cmds.parent(children_controller, f"|{constants.TEMP_PIVOT_GROUP}")

        old_name = self.controller
        base_controller = utils_nodes.get_base_controller(self.controller)
        constrained = None

        if base_controller:
            constrained = cmds.parentConstraint(
                base_controller,
                targetList=True,
                q=True
            )

        # Move controller to same hierarchy as old one
        if children_controller:
            cmds.parent(children_controller, duplicate_controller)
            """
            NOTE & LIMITATION
                - If we change pivot during animation -> the children will be freezed at the frame we are
                    TODO : fix this -> check transform & get 0,0,0 position & rotation and compute the data

                - If children is not at 0,0,0, will be at 0,0,0 after pivot change
            TODO : Write test step
            """
            utils_nodes.freeze_children(children_controller)

        # Reparent with offset if last controller
        if constrained and old_name in constrained:
            cmds.parentConstraint(
                duplicate_controller,
                base_controller,
                maintainOffset=True,
                name=constants.PARENT_CONSTRAINT_NAME.replace(
                    "{name}", base_controller)
            )

        cmds.delete(self.controller)
        duplicate_controller_new_name = cmds.rename(
            duplicate_controller, old_name)
        return duplicate_controller_new_name

    def __restore_children_animation(self):
        """
        Restore animation of children of the controller we edit pivot
        """
        for child in self.children_base_controller:
            if not cmds.attributeQuery(constants.ATTRIBUTE_SAVED_ANIM, node=child, exists=True):
                continue

            locators = cmds.listConnections(
                f"{child}.{constants.ATTRIBUTE_SAVED_ANIM}",
                source=False,
                destination=True
            ) or []

            if not locators:
                LOGGER.debug(f"No saved animation for {child}")
                continue

            if len(locators) > 1:
                LOGGER.warning(
                    f"Multiple saved anim locators found for {child}, using first one")

            locator = locators[0]

            LOGGER.debug(f"Retrieve animation from {locator} to {child}")

            utils_animation.copy_anim_from_parent_to_target(
                parent=locator,
                target=child,
                maintain_offset=False,
                smart=False
            )

            cmds.delete(locator)
            cmds.deleteAttr(child, attribute=constants.ATTRIBUTE_SAVED_ANIM)

    def __cleanup_pivot_edit(self):
        LOGGER.warning("Cleaning pivot edit resources")

        job_to_kill = self.job_selection_changed
        self.job_selection_changed = None

        self.__delete_pivot_locator()
        self.__delete_saved_anim_context_in_children()
        self.__delete_save_group()

        if job_to_kill:
            cmds.evalDeferred(
                lambda: cmds.scriptJob(kill=job_to_kill, force=True)
            )

        cmds.refresh(suspend=False)
        self._undo_chunk.close()

    def __delete_pivot_locator(self):
        if self.pivot_locator and cmds.objExists(self.pivot_locator):
            cmds.delete(self.pivot_locator)
        self.pivot_locator = None

    def __delete_saved_anim_context_in_children(self):
        for child in self.children_base_controller:
            self.__delete_saved_anim_context_in_one_child(child)

    def __delete_saved_anim_context_in_one_child(self, child: str):
        if not cmds.objExists(child):
            return

        if cmds.attributeQuery(constants.ATTRIBUTE_SAVED_ANIM, node=child, exists=True):
            locators = cmds.listConnections(
                f"{child}.{constants.ATTRIBUTE_SAVED_ANIM}",
                s=False,
                d=True
            ) or []

            for locator in locators:
                if cmds.objExists(locator):
                    cmds.delete(locator)

            cmds.deleteAttr(child, attribute=constants.ATTRIBUTE_SAVED_ANIM)

    def __delete_save_group(self):
        save_group = f"|{constants.TEMP_PIVOT_GROUP}|{constants.SAVE_ANIM}"
        if cmds.objExists(save_group):
            cmds.delete(save_group)

    def __del__(self):
        try:
            self.__cleanup_pivot_edit()
        except Exception:
            pass
