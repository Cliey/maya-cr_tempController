---
topics:
  - Maya
  - Programming
---

# Refactoring Plan for cr_tempController

## Overview
Refactor the Maya plugin to improve maintainability by addressing 5 key areas of technical debt.

---

## Area 1: Split `ControlTreeMayaUI` (936 lines → ~200 lines)

### New Files to Create

**`core/controller_manager.py`** - Tree state management
- Move: `controller_map`, `root_nodes`, `rebuild_tree()`, `_install_tree()`, `__build_nodes()`, `_register_child_node()`, `_remove_controller_from_model()`, `contains()`, `__is_root_temp_controller()`

**`core/controller_factory.py`** - Controller creation
- Move: `create_new_temporary_controller_from_base_controller()`, `__create_temp_controller()`, `create_child_controller()`, `__create_new_controller()`, `__create_data_node()`, `__create_controller_tree()`, `_finalize_temp_controller()`, `__build_context()`, `controller_ratio()`

**`core/baking_service.py`** - Baking operations
- Move: `__bake_and_delete()`, `__bake_temporary_controller_to_parent()`, `__bake_temporary_controller_to_base()`, `_bake_with_constraint()`, `_transfer_animation_child_to_parent()`, `__get_first_last_keyframe()`, keyframe helpers

### Keep in `ui/control_tree.py`
- Pure UI: `create_tree_ui()`, `__updateTree()`, `populate_tree()`, `select_item()`, `clear_selection()`, `__on_select()`, `__on_edit_label()`, dialogs

---

## Area 2: Consolidate Baking Logic

### Enhance `utils/animation.py`

```python
class BakeMode(Enum):
    EVERY_FRAME = "every_frame"
    SPARSE = "sparse"
    SMART = "smart"

@dataclass
class BakeOptions:
    mode: BakeMode = BakeMode.EVERY_FRAME
    sample_by: float = 1.0
    maintain_offset: bool = False
    apply_filter: bool = False

def bake_with_constraint(driver, driven, time_range, options=None, delete_constraint=True):
    """Unified baking: constraint + bake + optional filter + cleanup"""

def transfer_animation(source, target, time_range=None, options=None):
    """High-level animation transfer wrapper"""

def get_animation_range(node, fallback_to_timeline=True):
    """Get keyframe range for a node"""

def get_combined_animation_range(nodes):
    """Get range spanning multiple nodes"""
```

Replace scattered baking calls in `control_tree.py`, `pivot_tools.py`, and existing `utils/animation.py` functions.

---

## Area 3: Move Business Logic from UI

### Enhance `utils/hierarchy.py`

Move from `temp_controller_window.py`:
- `__get_tempcontrol_root()` → `get_tempcontrol_root()`
- `__is_under_tempcontrol()` → `is_under_tempcontrol()`
- `__controller_child_exists()` → `has_temp_controller_children()`
- `build_controller_tree()` → `build_controller_tree_from_scene()`

---

## Area 4: Unified Error Handling

### New File: `utils/errors.py`

```python
class ErrorSeverity(Enum):
    INFO, WARNING, ERROR, CRITICAL

@dataclass
class OperationResult:
    success: bool
    message: str
    severity: ErrorSeverity

def user_warning(message):     # Script editor + log
def user_error(message):       # Script editor + log + dialog
def internal_error(message, exception=None):  # Log only
def critical_error(message, exception=None):  # Log + dialog
```

Replace inconsistent error handling patterns throughout codebase.

---

## Area 5: PivotTool State Machine

### Refactor `core/pivot_tools.py`

```python
class PivotEditState(Enum):
    IDLE = auto()       # Not editing
    EDITING = auto()    # Locator active, waiting for user
    APPLYING = auto()   # User deselected, applying changes
    CLEANING = auto()   # Cleaning up
    COMPLETED = auto()  # Success
    FAILED = auto()     # Error occurred

@dataclass
class PivotEditContext:
    controller: str
    parent_is_root: bool
    has_animation: bool
    pivot_locator: Optional[str]
    selection_job: Optional[int]

class PivotTool:
    def _transition_to_editing(self): ...
    def _transition_to_applying(self): ...
    def _transition_to_cleaning(self): ...
    def _on_selection_changed(self): ...
```

Clear state transitions replace callback chain.

---

## Implementation Phases

| Phase | Description | Files Changed | Risk |
|-------|-------------|---------------|------|
| 1 | Foundation: Create `utils/errors.py`, enhance `utils/animation.py`, expand `utils/hierarchy.py` | 3 new/modified | Low |
| 2 | Extract `core/controller_manager.py` from `control_tree.py` | 2 files | Medium |
| 3 | Extract `core/baking_service.py` and `core/controller_factory.py` | 3 files | Medium |
| 4 | Refactor `core/pivot_tools.py` to state machine | 1 file | Medium |
| 5 | Update `temp_controller_window.py`, cleanup deprecated code | 2 files | Low |

---

## Final Structure

```
cr_tempController/
├── core/
│   ├── controller_manager.py    [NEW]
│   ├── controller_factory.py    [NEW]
│   ├── baking_service.py        [NEW]
│   ├── pivot_tools.py           [MODIFIED]
│   └── (existing files unchanged)
├── ui/
│   ├── control_tree.py          [MODIFIED - 936→~200 lines]
│   └── temp_controller_window.py [MODIFIED]
└── utils/
    ├── animation.py             [MODIFIED - unified API]
    ├── errors.py                [NEW]
    ├── hierarchy.py             [MODIFIED - scene functions]
    └── (existing files unchanged)
```

---

## Verification

After each phase, test in Maya:
1. Open tool: `import cr_tempController.cr_tempController as tc; tc.run()`
2. Create temp controller on a cube
3. Add child controller
4. Edit pivot (with and without animation)
5. Bake and delete controller
6. Undo/Redo operations
7. Close and reopen window

---

## Bug Fix (Side Note)

In `utils/nodes.py:110`, fix the function signature:
```python
# Before (bug):
def freeze_children(self, children: list[str]):

# After (fixed):
def freeze_children(children: list[str]):
```
