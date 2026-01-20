# cr_tempController

A Maya plugin for creating and managing temporary animation controllers. Allows animators to create temporary control hierarchies on top of existing rigs, animate with them, then bake the animation back to the original controllers.

---

## Features

- **Create Temporary Controllers** - Add temp controllers to any object with a single click
- **Multiple Creation Modes**
  - World Space - Controller at world origin
  - Object Space - Controller follows object's local space
- **Hierarchical Controllers** - Add child controllers to build complex control chains
- **Edit Pivot** - Reposition controller pivot while preserving animation
- **Bake & Delete** - Transfer animation back to parent controller or base object
- **Shape Options** - Rounded Square, Square, Circle, Star, Locator
- **Color Selection** - Preset palette or custom color picker
- **Undo/Redo Support** - Full integration with Maya's undo system
- **Persistent Preferences** - Remembers last used settings

---

## Requirements

- Autodesk Maya 2024+ (Python 3.10)
- Windows / macOS / Linux

---

## Installation

1. Copy the `cr_tempController` folder to your Maya scripts directory:
   - **Windows**: `C:\Users\<username>\Documents\maya\scripts\`
   - **macOS**: `~/Library/Preferences/Autodesk/maya/scripts/`
   - **Linux**: `~/maya/scripts/`

2. Restart Maya or run the following in the Script Editor (Python):
   ```python
   import cr_tempController.cr_tempController as tc
   tc.run()
   ```

---

## Usage

### Quick Start

1. Select an object in the viewport
2. Run the tool (see Installation step 2)
3. Click **Create Controller** to add a temporary controller
4. Animate the temporary controller
5. When finished, select the controller and click **Bake and Delete**

### Creating Controllers

1. Select the object you want to control
2. Choose a **Mode**:
   - *World Space* - Controller created at world origin
   - *Object Space* - Controller created at object's local position
3. Select a **Shape** and **Color**
4. Click **Create Controller**

### Adding Child Controllers

1. In the Temp Controllers tree, click the **+** button next to any controller
2. A child controller is created, inheriting the parent's color
3. Child controllers can have their own children (unlimited depth)

### Editing Pivot

1. Select a temporary controller in the tree
2. Click **Edit Pivot**
3. Move the green pivot locator to the desired position
4. Click anywhere else to confirm (deselect the locator)
5. Animation is automatically preserved

### Baking Animation

- **Bake and Delete** - Transfers animation to parent and removes the controller
- **Delete** - Removes controller without baking (animation is lost)

---

## UI Overview

```
┌──────────────────────────────────────┐
│ Create Controller                    │
├──────────────────────────────────────┤
│ [Create Controller]                  │
│                                      │
│ Mode: (•) World  ( ) Object          │
│ Shape: [Rounded Square ▼]            │
│ Color: [● ● ● ● ●] Custom: [■]       │
├──────────────────────────────────────┤
│ Temp Controllers                     │
├──────────────────────────────────────┤
│ ▼ pCube1                             │
│   └─ pCube1_TempControl_Ctrl     [+] │
│       └─ Child1                  [+] │
├──────────────────────────────────────┤
│ Selected Controller                  │
├──────────────────────────────────────┤
│ [Edit Pivot] [Bake & Delete] [Delete]│
├──────────────────────────────────────┤
│ ▶ Bake Options (collapsed)          │
├──────────────────────────────────────┤
│ [Close]                              │
└──────────────────────────────────────┘
```

---

## Development

### Reload During Development

After making changes, reload all modules without restarting Maya:

```python
import cr_tempController.reload as reload
reload.reload_package("cr_tempController")

import cr_tempController.cr_tempController as tc
tc.run()
```

### Project Structure

```
cr_tempController/
├── __init__.py
├── cr_tempController.py    # Entry point
├── constants.py            # Configuration and constants
├── reload.py               # Development hot-reload utility
│
├── core/                   # Core logic
│   ├── temp_controller.py  # Main controller class
│   ├── controller_node.py  # Tree node data structure
│   ├── controller_mode.py  # Creation mode enums
│   ├── controller_context.py # Creation context dataclass
│   └── pivot_tools.py      # Pivot editing tool
│
├── ui/                     # User interface
│   ├── temp_controller_window.py  # Main window
│   └── control_tree.py     # Tree view and operations
│
└── utils/                  # Utilities
    ├── animation.py        # Animation baking utilities
    ├── controller_shapes.py # Shape creation functions
    ├── hierarchy.py        # Hierarchy traversal
    ├── nodes.py            # Node utilities
    ├── naming.py           # Naming conventions
    ├── context.py          # Context managers
    └── logging.py          # Logging utilities
```

---

## Keyboard Shortcuts

*No default shortcuts. Create a shelf button or hotkey to run:*

```python
import cr_tempController.cr_tempController as tc; tc.run()
```

---

## Known Limitations

- Relative Space mode not yet implemented
- Camera Space mode not yet implemented
- Baking with multiple sibling children may have issues
- Pivot edit on deeply nested controllers with animation may require manual adjustment

---

## Troubleshooting

### Tool window doesn't open
```python
# Check for errors in Script Editor
import cr_tempController.cr_tempController as tc
tc.run()
```

### Controllers not appearing in tree
- Ensure the root group `cr_TempControls` exists in the scene
- Try closing and reopening the tool window

### Animation not baking correctly
- Check Bake Options settings
- Ensure timeline range covers all animation
- For complex hierarchies, bake children before parents

---

## License

Proprietary - All rights reserved.

---

## Author

Cyril

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024 | Initial release |
