import maya.cmds as cmds
import cr_tempController.constants as constants
import cr_tempController.core.controller_context as controller_context


class BakeOptionFrame:

    def __init__(self, parent):
        self.parent = parent
        self.bake_method = "bakeOptionsFrames_menuBakeMethod"
        self.sample_by_int = "bakeOptionsFrames_intSampleBy"
        self.apply_filter = "bakeOptionsFrames_checkboxApplyFilter"

        self.__build()

    def __build(self):
        bake_options_frame = cmds.frameLayout(
            label="Bake Options",
            collapsable=True,
            collapse=True,
            marginWidth=6,
            marginHeight=6,
            parent=self.parent
        )

        column_layout = cmds.columnLayout(
            rowSpacing=6, parent=bake_options_frame)

        # Bake method row (intField appears inline when Sample By is selected)
        bake_method_row = cmds.rowLayout(numberOfColumns=3,
                                         columnWidth=[
                                             (1, 100), (2, 110), (3, 60)],
                                         columnAttach=[(1, "right", 10)],
                                         parent=column_layout)
        cmds.text(label="Bake method:", align="right", parent=bake_method_row)
        self.bake_method = cmds.optionMenu(self.bake_method,
                                           changeCommand=self.__on_change_bake_method_menu,
                                           parent=bake_method_row)
        cmds.menuItem(label=constants.BAKE_SMART)
        cmds.menuItem(label=constants.BAKE_SAMPLE_BY)
        self.sample_by_int = cmds.intField(self.sample_by_int,
                                           minValue=1,
                                           value=1,
                                           step=1,
                                           manage=False,
                                           parent=bake_method_row)

        # Apply filter row
        apply_filter_row = cmds.rowLayout(numberOfColumns=2,
                                          columnWidth=[(1, 100), (2, 240)],
                                          columnAttach=[(1, "right", 10)],
                                          parent=column_layout)
        cmds.text(label="Apply filter:",
                  align="right",
                  parent=apply_filter_row)
        self.apply_filter = cmds.checkBox(self.apply_filter,
                                          label="",
                                          value=True,
                                          parent=apply_filter_row)

    def __on_change_bake_method_menu(self, selection):
        is_sample_by = selection == constants.BAKE_SAMPLE_BY
        cmds.intField(self.sample_by_int, edit=True, manage=is_sample_by)

    def get_context(self):
        smart_bake = cmds.optionMenu(
            self.bake_method, query=True, value=True) == constants.BAKE_SMART
        sample_by_field = cmds.intField(self.sample_by_int,
                                        query=True,
                                        value=True)
        sample_by = 1 if smart_bake else (
            sample_by_field if sample_by_field > 0 else 1)
        apply_filter = cmds.checkBox(self.apply_filter,
                                     query=True,
                                     value=True)
        return controller_context.BakeOptionContext(
            smart=smart_bake,
            sample_by=sample_by,
            apply_filter=apply_filter
        )

    def get_fields_to_save(self):
        """
        return:
            self.bake_method
            self.sample_by_int
            self.apply_filter
        """
        pass
