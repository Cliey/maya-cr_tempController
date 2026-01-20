# Cython Preparation for cr_tempController

## Overview

This document outlines the steps needed to compile cr_tempController with Cython for code protection and distribution.

---

## Compatibility Assessment

### What Works Well

| Feature | Status | Notes |
|---------|--------|-------|
| Standard classes | ✅ Compatible | All class definitions compile cleanly |
| Dataclasses | ✅ Compatible | `controller_context.py`, etc. |
| Enums | ✅ Compatible | `controller_mode.py`, `controller_shapes.py` |
| Type hints | ✅ Compatible | Cython can use these for optimization |
| Context managers | ✅ Compatible | `UndoChunk`, `AutoKeyOff` |
| f-strings | ✅ Compatible | Requires Cython 3.0+ |
| `maya.cmds` calls | ✅ Compatible | Standard Python API calls |
| `maya.api.OpenMaya` | ✅ Compatible | API 2.0 works fine |

### Requires Attention

| Feature | Location | Issue | Solution |
|---------|----------|-------|----------|
| Match statements | `controller_shapes.py:24`, `control_tree.py:483` | Python 3.10+ syntax | Requires Cython 3.0+ OR rewrite as if/elif |
| Lambda in scriptJobs | `pivot_tools.py:106`, `temp_controller_window.py:222-225`, `temp_controller_window.py:398-405` | Dynamic callbacks | Convert to named methods |
| `reload.py` | Root module | Hot-reload won't work compiled | Exclude from distribution |
| `importlib.reload()` | `reload.py` | Development only | Exclude from distribution |

---

## Maya Python Version Compatibility

**Critical**: Compiled extensions must match Maya's Python version exactly.

| Maya Version | Python Version | Notes |
|--------------|----------------|-------|
| Maya 2024+ | Python 3.10.8 | Match statements supported |
| Maya 2023 | Python 3.9.7 | No match statements |
| Maya 2022 | Python 3.7.7 | Older syntax only |

### Check Maya's Python Version
```python
# Run in Maya Script Editor
import sys
print(sys.version)
```

---

## Code Changes Required

### 1. Convert Lambda Callbacks to Named Functions

**Before** (`temp_controller_window.py:398-400`):
```python
cmds.scriptJob(
    event=["Undo", lambda: cmds.evalDeferred(self.__rebuild_tree)],
    parent=self.window,
    protected=True)
```

**After**:
```python
def _on_undo(self):
    cmds.evalDeferred(self.__rebuild_tree)

cmds.scriptJob(
    event=["Undo", self._on_undo],
    parent=self.window,
    protected=True)
```

### 2. Match Statements (if targeting Maya 2022/2023)

**Before** (`controller_shapes.py:24-34`):
```python
match shape:
    case ControllerShape.ROUNDED_SQUARE:
        return create_rounded_square(name=name, ratio=ratio)
    case ControllerShape.SQUARE:
        return create_square(name=name, ratio=ratio)
    # ...
```

**After**:
```python
if shape == ControllerShape.ROUNDED_SQUARE:
    return create_rounded_square(name=name, ratio=ratio)
elif shape == ControllerShape.SQUARE:
    return create_square(name=name, ratio=ratio)
# ...
```

### 3. Fix `freeze_children` Bug

**Before** (`utils/nodes.py:110`):
```python
def freeze_children(self, children: list[str]):  # Bug: 'self' shouldn't be here
```

**After**:
```python
def freeze_children(children: list[str]):
```

---

## Project Structure for Compilation

### Recommended: Selective Compilation

Compile core logic, keep UI as Python for easier updates:

```
cr_tempController/
├── __init__.py              # Keep as .py (entry point)
├── cr_tempController.py     # Keep as .py (entry point)
├── constants.py             # Keep as .py (easy config changes)
├── reload.py                # EXCLUDE from distribution
│
├── core/
│   ├── __init__.py          # Keep as .py
│   ├── controller_context.pyd    # Compile
│   ├── controller_mode.pyd       # Compile
│   ├── controller_node.pyd       # Compile
│   ├── pivot_tools.pyd           # Compile
│   └── temp_controller.pyd       # Compile
│
├── ui/
│   ├── __init__.py          # Keep as .py
│   ├── control_tree.py      # Keep as .py (UI changes often)
│   └── temp_controller_window.py  # Keep as .py
│
└── utils/
    ├── __init__.py          # Keep as .py
    ├── animation.pyd        # Compile
    ├── context.pyd          # Compile
    ├── controller_shapes.pyd # Compile
    ├── hierarchy.pyd        # Compile
    ├── logging.pyd          # Compile
    ├── naming.pyd           # Compile
    └── nodes.pyd            # Compile
```

---

## Build Setup

### setup.py

```python
from setuptools import setup, find_packages
from Cython.Build import cythonize
import os

# Files to compile
compile_modules = [
    "core/controller_context.py",
    "core/controller_mode.py",
    "core/controller_node.py",
    "core/pivot_tools.py",
    "core/temp_controller.py",
    "utils/animation.py",
    "utils/context.py",
    "utils/controller_shapes.py",
    "utils/hierarchy.py",
    "utils/logging.py",
    "utils/naming.py",
    "utils/nodes.py",
]

# Files to exclude from compilation
exclude_files = [
    "reload.py",
    "__init__.py",
]

setup(
    name="cr_tempController",
    version="1.0.0",
    packages=find_packages(),
    ext_modules=cythonize(
        compile_modules,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
        },
        annotate=True,  # Generates HTML showing optimization opportunities
    ),
    zip_safe=False,
)
```

### Build Commands

```bash
# Install Cython (use Maya's mayapy if possible)
mayapy -m pip install cython

# Build extensions
mayapy setup.py build_ext --inplace

# Or for distribution wheel
mayapy setup.py bdist_wheel
```

---

## Distribution Structure

### Final Package (what you ship)

```
cr_tempController/
├── __init__.py
├── cr_tempController.py
├── constants.py
│
├── core/
│   ├── __init__.py
│   ├── controller_context.cp310-win_amd64.pyd
│   ├── controller_mode.cp310-win_amd64.pyd
│   ├── controller_node.cp310-win_amd64.pyd
│   ├── pivot_tools.cp310-win_amd64.pyd
│   └── temp_controller.cp310-win_amd64.pyd
│
├── ui/
│   ├── __init__.py
│   ├── control_tree.py
│   └── temp_controller_window.py
│
└── utils/
    ├── __init__.py
    ├── animation.cp310-win_amd64.pyd
    ├── context.cp310-win_amd64.pyd
    ├── controller_shapes.cp310-win_amd64.pyd
    ├── hierarchy.cp310-win_amd64.pyd
    ├── logging.cp310-win_amd64.pyd
    ├── naming.cp310-win_amd64.pyd
    └── nodes.cp310-win_amd64.pyd
```

### Multi-Platform Distribution

For cross-platform support, build on each target:

| Platform | Extension | Build Environment |
|----------|-----------|-------------------|
| Windows | `.cp310-win_amd64.pyd` | Windows + Maya 2024 |
| macOS Intel | `.cpython-310-darwin.so` | macOS Intel + Maya 2024 |
| macOS ARM | `.cpython-310-darwin.so` | macOS M1/M2 + Maya 2024 |
| Linux | `.cpython-310-x86_64-linux-gnu.so` | Linux + Maya 2024 |

---

## Testing Compiled Code

### Test Script

```python
# test_compiled.py - Run in Maya
import sys
import importlib

# Force reimport of compiled modules
modules_to_test = [
    "cr_tempController.core.controller_mode",
    "cr_tempController.core.controller_node",
    "cr_tempController.utils.animation",
    "cr_tempController.utils.controller_shapes",
]

for mod_name in modules_to_test:
    if mod_name in sys.modules:
        del sys.modules[mod_name]

    mod = importlib.import_module(mod_name)
    print(f"✓ {mod_name} loaded from: {mod.__file__}")

# Run the tool
import cr_tempController.cr_tempController as tc
tc.run()

print("Test complete - verify UI works correctly")
```

### Verification Checklist

- [ ] Tool window opens without errors
- [ ] Create temp controller on object
- [ ] Add child controller
- [ ] Edit pivot (no animation)
- [ ] Edit pivot (with animation)
- [ ] Bake and delete controller
- [ ] Undo/Redo operations work
- [ ] Close and reopen window
- [ ] Rename controller in tree
- [ ] Color and shape selection work

---

## Security Notes

### What Cython Protects

- ✅ Source code logic is compiled to C, then to machine code
- ✅ Variable names and most structure hidden
- ✅ Algorithm implementation protected

### What Cython Does NOT Protect

- ❌ String literals (error messages, attribute names) are visible
- ❌ Maya command calls (`cmds.createNode`, etc.) can be traced
- ❌ Constants file remains readable if kept as .py
- ❌ Determined reverse engineers can still analyze bytecode

### Additional Protection (Optional)

1. **Obfuscate string literals**: Use encoding for sensitive strings
2. **License checking**: Add license validation in compiled code
3. **Anti-debugging**: Detect debugger attachment (advanced)

---

## Effort Estimate

| Task | Effort |
|------|--------|
| Convert lambda callbacks | 1-2 hours |
| Convert match statements (if needed) | 1 hour |
| Fix `freeze_children` bug | 5 minutes |
| Create setup.py and build scripts | 1-2 hours |
| Test compiled code in Maya | 2-3 hours |
| Multi-platform builds | 2-4 hours per platform |
| **Total** | **8-12 hours** |

---

## Recommended Order

1. Complete refactoring from `Plan.md` first (cleaner code compiles better)
2. Fix the `freeze_children` bug
3. Convert lambda callbacks to named methods
4. Convert match statements if targeting Maya 2022/2023
5. Create `setup.py`
6. Build and test on primary platform (Windows)
7. Build for additional platforms as needed
