import maya.cmds as cmds
import cr_tempController.constants as constants


class MenuBarLayout:
    def __init__(self, window):
        self.window = window
        self._build()

    def _build(self):
        cmds.menuBarLayout()
        cmds.menu(label='Help', helpMenu=True)
        cmds.menuItem(label='About...', command=self.__open_about_window)
        cmds.menuItem(label='Quickstart', command=self.__open_how_to_window)
        cmds.menuItem(label='Close',
                      command=lambda *_: cmds.deleteUI(self.window))

    def __open_about_window(self, _):
        import webbrowser

        def build_ui():
            cmds.columnLayout(adjustableColumn=True,
                              rowSpacing=8,
                              margins=16,
                              parent=cmds.setParent(q=True))
            cmds.text(label=f"cr_tempController  v{constants.VERSION}",
                      align="left",
                      font="boldLabelFont")
            cmds.text(label="Temporary animation controllers for Maya.",
                      align="left")
            cmds.separator()
            cmds.text(label="Author: Cyril R.  |  Maya 2024+", align="center")
            cmds.separator()
            cmds.button(label="Get latest version (Gumroad)",
                        command=lambda _: webbrowser.open("https://gumroad.com/your-link"))
            cmds.button(label="Buy me a coffee (Ko-fi)",
                        command=lambda _: webbrowser.open("https://ko-fi.com/your-link"))
            cmds.separator()
            cmds.text(label="© 2025 Cyril R. All rights reserved.",
                      align="center",
                      font="smallPlainLabelFont")
            cmds.button(label="Close",
                        command=lambda _: cmds.layoutDialog(dismiss="close"))

        cmds.layoutDialog(ui=build_ui, title="About cr_tempController")

    def __open_how_to_window(self, _):
        import webbrowser
        win = "quickStart"
        if cmds.window(win, exists=True):
            cmds.deleteUI(win)
        cmds.window(win, title="Quick Start",
                    widthHeight=(300, 260),
                    sizeable=False,
                    minimizeButton=False,
                    maximizeButton=False,
                    parent=self.window)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=6, margins=16)
        cmds.text(label="Quick Start", align="left", font="boldLabelFont")
        cmds.separator()
        cmds.text(label="1. Select a controller in your scene.", align="left")
        cmds.text(label="2. Click 'Create Controller' to add a temp controller.",
                  align="left")
        cmds.text(label="3. Animate using the temp controller.", align="left")
        cmds.text(label="4. Select it and click 'Bake and Delete' to", align="left")
        cmds.text(label="   transfer animation back to the original.", align="left")
        cmds.separator()
        cmds.text(label="Full tutorial coming soon.",
                  align="left",
                  font="smallPlainLabelFont")
        cmds.button(label="Watch Tutorial (YouTube)", command=lambda _:
                    webbrowser.open("https://youtube.com/your-link"))
        cmds.separator()
        cmds.button(label="Close", command=lambda _: cmds.deleteUI(win))
        cmds.showWindow(win)
