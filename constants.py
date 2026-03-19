import logging

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | CR_Temp_Controller |  %(asctime)s | %(message)s")


# CONSTANT
TOOL_WINDOW_NAME = "tempControlMayaUI"
TOOL_WINDOW_TITLE = "Temp Controller Tool"

TEMP_PIVOT_GROUP = 'cr_TempControls'
TEMP_PIVOT_GROUP_COLOR = (0.93, 0.44, 1)
DATA_SOURCE_NODE = 'sourceNode'
ATTRIBUTE_SAVED_ANIM = 'cr_savedAnim'
ATTRIBUTE_SOURCE_CTRL = 'cr_sourceCtrl'


# SUFFIXE
SUFFIXE_TEMP_CONTROL_CTRLLER = "_TempControl_Ctrl"
SUFFIXE_TEMP_CONTROL_DATA = "_TempControl_Data"
SUFFIXE_LOCATOR_SAVE = "_Save"
SUFFIXE_TEMP_PIVOT = "_TMP_PIVOT"
SUFFIXE_PIVOT_DUPLICATE = "_PIVOT_DUP"
SAVE_ANIM = "Save_Anim"

# MENU CONSTANTS
BUTTON_CREATE_CONTROLLER = "buttonCreateController"
RADIO_GROUP_CONTROLLER_MODE = "radioGroupControllerMode"
FRAME_SELECTED_CONTROLLER = "frameSelectecController"
FRAME_CONTROLLER_DETAILS = "frameControllerDetails"
SHAPE_MENU_CREATION_NAME = "optionShapeMenu"
SHAPE_MENU_PROPERTIES_NAME = "propertiesShapeMenu"
COLOR_CREATION = "colorCreation"
COLOR_PROPERTIES = "colorProperties"
ROTATE_ORDER_MENU_CREATION_NAME = "rotateOrderCreation"

# TREE TEMP CONTROLLERS
TREE_NAME = "controlTree"

# COLORS
COLORS_RGB = [
    (1, 0, 0),  # RED
    (0, 0, 1),  # BLUE
    (0, 1, 0),  # GREEN
    (1, 0, 1),  # PINK
    (1, 1, 0),  # YELLOW
]

ATTRIBUTE_DISPLAY_COLOR = "displayColorRGB"
ATTRIBUTE_DISPLAY_COLOR_R = "displayColorR"
ATTRIBUTE_DISPLAY_COLOR_G = "displayColorG"
ATTRIBUTE_DISPLAY_COLOR_B = "displayColorB"

# Bake Constants
BAKE_EVERY_FRAME_OPTS = dict(
    simulation=True,
    sampleBy=1.0,
    sparseAnimCurveBake=True,
    preserveOutsideKeys=True,
)

# BAKE OPTION MENU
BAKE_SAMPLE_BY = "Sample By"
BAKE_SMART = "Smart"

# OPTION VAR
LAST_MODE_SELECTED = "cr_TempController.LastModeSelected"
LAST_SHAPE_SELECTED = "cr_TempController.LastShapeSelected"
LAST_COLOR_SELECTED_IS_CUSTOM = "cr_TempController.LastColorSelectedIsCustom"
LAST_CUSTOM_COLOR_R = "cr_TempController.CustomRGB_R"
LAST_CUSTOM_COLOR_G = "cr_TempController.CustomRGB_G"
LAST_CUSTOM_COLOR_B = "cr_TempController.CustomRGB_B"

SKIP_NURBS_WARNING = "cr_TempController.skipNurbsWarning"
