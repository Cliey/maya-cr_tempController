import maya.cmds as cmds
import cr_tempController.constants as constants
import cr_tempController.ui.temp_controller_window as ui
import cr_tempController.utils.animation as utils_animation
import logging

LOGGER = logging.getLogger(__name__)


class TempController:
    def __init__(self):
        if not self.__isLocalObjectExist():
            self.__createLocalObject()

    def show(self):
        ui.TempControllerWindowMayaUI().show()

    def __isLocalObjectExist(self):
        return cmds.objExists(constants.TEMP_PIVOT_GROUP)
    
    def __createLocalObject(self):
        grp_path = f'|{constants.TEMP_PIVOT_GROUP}'
        cmds.createNode('transform', name=constants.TEMP_PIVOT_GROUP, skipSelect=True)
        cmds.setAttr(f'{grp_path}.useOutlinerColor', True)
        cmds.setAttr(f'{grp_path}.outlinerColor', *constants.TEMP_PIVOT_GROUP_COLOR)
        cmds.setAttr(
                    f'{grp_path}.visibility',
                    lock=True,
                    keyable=False,
                    channelBox=False,
                )
        utils_animation.lock_transform_attribute(grp_path)