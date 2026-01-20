import maya.cmds as cmds

class AutoKeyOff:
    def __enter__(self):
        self.state = cmds.autoKeyframe(q=True, state=True)
        if self.state:
            cmds.autoKeyframe(state=False)
        return self

    def __exit__(self, exc_type, exc, tb):
        cmds.autoKeyframe(state=self.state)

class UndoChunk:
    def __enter__(self):
        cmds.undoInfo(openChunk=True)
        cmds.refresh(suspend=True)
    
    def __exit__(self, exc_type, exc, tb):
        cmds.undoInfo(closeChunk=True)
        cmds.refresh(suspend=False)