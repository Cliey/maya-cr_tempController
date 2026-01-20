from enum import Enum


class ControllerCreationMode(Enum):
    WORLD_SPACE = 1
    OBJECT_SPACE = 2
    RELATIVE_SPACE = 3
    CAMERA_SPACE = 4


MODE_LABEL_TO_ENUM = {
    "World Space": ControllerCreationMode.WORLD_SPACE,
    "Object Space": ControllerCreationMode.OBJECT_SPACE,
    "Relative Space": ControllerCreationMode.RELATIVE_SPACE,
    "Camera Space": ControllerCreationMode.CAMERA_SPACE,
}

MODE_ENUM_TO_LABEL = {
    ControllerCreationMode.WORLD_SPACE: "World Space",
    ControllerCreationMode.OBJECT_SPACE: "Object Space",
    ControllerCreationMode.RELATIVE_SPACE: "Relative Space",
    ControllerCreationMode.CAMERA_SPACE: "Camera Space",
}
