import maya.cmds as cmds
import cr_tempController.utils.rotation_order as rotation_order
from enum import Enum


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
