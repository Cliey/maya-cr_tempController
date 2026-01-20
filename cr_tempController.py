import cr_tempController.core.temp_controller as temp_controller
import maya.cmds as cmds
import cr_tempController.constants as constants


def run():
    if cmds.window(constants.TOOL_WINDOW_NAME, exists=True):
        cmds.deleteUI(constants.TOOL_WINDOW_NAME)
    temp_controller.TempController().show()
