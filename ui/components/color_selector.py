import maya.cmds as cmds
import cr_tempController.constants as constants


class ColorSelector:
    def __init__(self, name, parent, size=20):
        self.name = name
        self.parent = parent
        self.size = size
        self.row_layout = f"{name}_rowLayout"

        self.radio_collection = f"{name}_radioCollection"
        self.palette_radio = None
        self.custom_radio = None
        self.palette = None
        self.picker_btn = None

        self._build()

    def _build(self):
        self.row_layout = cmds.rowLayout(self.row_layout,
                                         numberOfColumns=5,
                                         generalSpacing=6,
                                         parent=self.parent,
                                         enable=False)

        if not cmds.radioCollection(self.radio_collection, exists=True):
            cmds.radioCollection(self.radio_collection)

        self.palette_radio = cmds.radioButton(
            label="",
            collection=self.radio_collection,
            select=True
        )
        self.palette_radio = self.palette_radio.split("|")[-1]

        number_of_colors = len(constants.COLORS_RGB)
        self.palette = cmds.palettePort(
            f"{self.name}_palette",
            dimensions=(number_of_colors, 1),
            width=self.size * number_of_colors,
            height=self.size,
            colorEditable=False,
            changeCommand=self._on_palette_changed
        )

        for i, rgb in enumerate(constants.COLORS_RGB):
            cmds.palettePort(self.palette, e=True, rgbValue=(i, *rgb))

        self.custom_radio = cmds.radioButton(
            label="",
            collection=self.radio_collection
        )
        self.custom_radio = self.custom_radio.split("|")[-1]

        cmds.text(label="Custom:", align="left")

        self.picker_btn = cmds.iconTextButton(
            f"{self.name}_picker",
            style="iconOnly",
            width=self.size,
            height=self.size,
            enableBackground=True,
            backgroundColor=(0.18, 0.18, 0.18),
            annotation="Pick custom color",
            command=self._open_color_picker
        )

    def _on_palette_changed(self):
        cmds.radioButton(self.palette_radio, e=True, select=True)

    def _open_color_picker(self, *_):
        current = cmds.iconTextButton(
            self.picker_btn, q=True, backgroundColor=True)
        result = cmds.colorEditor(rgb=current)
        if not result:
            return

        if cmds.colorEditor(q=True, result=True):
            rgb = cmds.colorEditor(q=True, rgb=True)
            cmds.iconTextButton(self.picker_btn, e=True, backgroundColor=rgb)
            cmds.radioButton(self.custom_radio, e=True, select=True)

    def get_color(self):
        if self.is_custom_selected():
            return cmds.iconTextButton(self.picker_btn, q=True, backgroundColor=True)

        return cmds.palettePort(self.palette, q=True, rgb=True)

    def is_custom_selected(self):
        selected = cmds.radioCollection(
            self.radio_collection, q=True, select=True)
        return selected == self.custom_radio

    def select_custom(self, select: bool):
        cmds.radioButton(self.custom_radio, e=True, select=select)

    def change_custom_color(self, r, g, b):
        cmds.iconTextButton(
            self.picker_btn,
            edit=True,
            backgroundColor=(r, g, b)
        )

    def set_enabled(self, state=True):
        cmds.rowLayout(self.row_layout, e=True, enable=state)
        cmds.palettePort(self.palette, e=True, enable=state)
        cmds.iconTextButton(self.picker_btn, e=True, enable=state)
        cmds.radioButton(self.palette_radio, e=True, enable=state)
        cmds.radioButton(self.custom_radio, e=True, enable=state)
