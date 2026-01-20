# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**cr_tempController** is a Maya Python plugin for creating and managing temporary animation controllers. It allows animators to create temporary control hierarchies on top of existing rigs, animate with them, then bake the animation back to the original controllers.

## Running the Tool

```python
# In Maya Script Editor (Python)
import cr_tempController.cr_tempController as tc
tc.run()

# For development - reload all modules
import cr_tempController.reload as reload
reload.reload_package("cr_tempController")
```

## Architecture

### Core Components

- **`cr_tempController.py`** - Entry point, calls `TempController().show()`
- **`core/temp_controller.py`** - Main controller class, creates the root group `cr_TempControls`
- **`ui/temp_controller_window.py`** - Maya UI window using `maya.cmds`, handles user interactions
- **`ui/control_tree.py`** - Tree view widget managing the controller hierarchy display and all controller operations (create, bake, delete, edit pivot)

### Data Model

- **`core/controller_node.py`** - `ControllerNode` class representing tree nodes (name, parent, children, depth)
- **`core/controller_mode.py`** - `ControllerCreationMode` enum (WORLD_SPACE, OBJECT_SPACE, RELATIVE_SPACE, CAMERA_SPACE)
- **`core/controller_context.py`** - `TempControllerCreationContext` dataclass (mode, color, size_ratio, shape)
- **`core/pivot_tools.py`** - `PivotTool` class for interactive pivot editing with scriptJob-based selection tracking

### Utilities

- **`utils/animation.py`** - Animation baking, keyframe queries, constraint-based animation transfer
- **`utils/controller_shapes.py`** - Shape creation (rounded square, square, circle, star, locator)
- **`utils/nodes.py`** - Node traversal, finding data nodes, getting base controllers
- **`utils/context.py`** - Context managers (`UndoChunk`, `AutoKeyOff`)
- **`utils/hierarchy.py`** - Recursive hierarchy traversal
- **`utils/naming.py`** - Name building utilities

### Key Patterns

**Temporary Controller Structure:**
```
|cr_TempControls                          # Root group (locked, colored)
  |<baseCtrl>_TempControl_Data           # Data node with sourceNode message attr
    |<baseCtrl>_TempControl_Ctrl         # Actual temp controller
      |<child controllers...>
```

**Controller-to-Base Link:** Data nodes have a `sourceNode` message attribute connected to the original controller's `message` attribute.

**Animation Transfer:** Uses parent constraints + `cmds.bakeResults()` to copy animation between controllers. Smart bake vs sample-by-frame controlled via constants.

**Undo Support:** Operations wrapped in `UndoChunk` context manager. Tree rebuilds on Undo/Redo via scriptJobs.

## Constants

All naming conventions, UI element names, attribute names, and default values are in `constants.py`. Key suffixes:
- `_TempControl_Data` - Data node suffix
- `_TempControl_Ctrl` - Controller suffix
- `_TMP_PIVOT` - Temporary pivot locator suffix

## Maya API Usage

- Uses `maya.cmds` for most operations
- Uses `maya.api.OpenMaya` (API 2.0) for matrix math in `utils/nodes.py` and `core/pivot_tools.py`
- ScriptJobs for selection change callbacks and undo/redo events
- OptionVars for persistent user preferences
