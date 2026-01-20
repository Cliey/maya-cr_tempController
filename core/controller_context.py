from dataclasses import dataclass
from . import controller_mode
import cr_tempController.utils.controller_shapes as controller_shapes


@dataclass(frozen=True)
class TempControllerCreationContext:
    mode: controller_mode.ControllerCreationMode = controller_mode.ControllerCreationMode.OBJECT_SPACE
    rgb_color: list[float] = (1, 0, 1)
    size_ratio: float = 1.0
    shape: controller_shapes.ControllerShape = controller_shapes.ControllerShape.ROUNDED_SQUARE
