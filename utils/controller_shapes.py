import math
import maya.cmds as cmds
from enum import Enum


class ControllerShape(Enum):
    ROUNDED_SQUARE = 1
    SQUARE = 2
    CIRCLE = 3
    STAR = 4
    LOCATOR = 5


SHAPE_LABEL_TO_ENUM = {
    "Rounded Square": ControllerShape.ROUNDED_SQUARE,
    "Square": ControllerShape.SQUARE,
    "Circle": ControllerShape.CIRCLE,
    "Star": ControllerShape.STAR,
    "Locator": ControllerShape.LOCATOR,
}


def create_controller(name, shape, ratio=1):
    match shape:
        case ControllerShape.ROUNDED_SQUARE:
            return create_rounded_square(name=name, ratio=ratio)
        case ControllerShape.SQUARE:
            return create_square(name=name, ratio=ratio)
        case ControllerShape.CIRCLE:
            return create_circle(name=name, ratio=ratio)
        case ControllerShape.STAR:
            return create_star(name=name, ratio=ratio)
        case _:
            return create_locator(name=name, ratio=ratio)


def create_rounded_square(name="rounded_square_ctrl", size=1.0, radius=0.3, ratio=1):
    """
    A square with round corners (8 arcs).
    """
    s = size * ratio
    r = min(radius * ratio, s * 0.5)

    # Corner points
    pts = [
        (s, 0, s - r), (s, 0, s), (s - r, 0, s),
        (-s + r, 0, s), (-s, 0, s), (-s, 0, s - r),
        (-s, 0, -s + r), (-s, 0, -s), (-s + r, 0, -s),
        (s - r, 0, -s), (s, 0, -s), (s, 0, -s + r),
        (s, 0, s - r)  # close
    ]

    ctrl = cmds.curve(name=name, degree=3, point=pts)
    return ctrl


def create_square(name="square_ctrl", size=1.0, ratio=1):
    half = size * ratio
    points = [
        (half, 0, half),
        (-half, 0, half),
        (-half, 0, -half),
        (half, 0, -half),
        (half, 0, half)
    ]
    ctrl = cmds.curve(name=name, degree=1, point=points)
    return ctrl


def create_circle(name="circle_ctrl", radius=1.0, ratio=1):
    ctrl = cmds.circle(name=name, radius=radius * ratio,
                       normal=(1, 0, 0), ch=False)[0]
    return ctrl


def create_star(name="star_ctrl", radius=1.0, inner=0.4, ratio=1):
    """5-point star controller"""
    points = []
    outer = radius * ratio
    inner_r = radius * inner * ratio
    for i in range(10):
        angle = math.radians(i * 36)
        r = outer if i % 2 == 0 else inner_r
        x = math.cos(angle) * r
        z = math.sin(angle) * r
        points.append((x, 0, z))
    points.append(points[0])  # close curve

    ctrl = cmds.curve(name=name, degree=1, point=points)
    return ctrl


def create_locator(name, ratio=1):
    temp_control_controller = cmds.spaceLocator(name=name)[0]
    cmds.setAttr(temp_control_controller + ".localScale", ratio, ratio, ratio)
    return temp_control_controller
