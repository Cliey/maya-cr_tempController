# Automated Testing Infrastructure

## Overview

Added pytest-based automated testing to cr_tempController, focusing on pure Python code that can run without Maya.

## Files Created

```
tests/
├── __init__.py              # Package marker
├── import_helper.py         # Module import helper (bypasses Maya dependencies)
├── conftest.py              # Shared pytest fixtures
├── test_controller_node.py  # ControllerNode tests (14 tests)
├── test_controller_mode.py  # ControllerCreationMode tests (18 tests)
├── test_controller_manager.py # ControllerManager tests (34 tests)
└── test_naming.py           # Naming utility tests (9 tests)

pytest.ini                   # pytest configuration
.venv/                       # Virtual environment with pytest installed
```

## Test Coverage

### test_controller_node.py (14 tests)
- Node creation with/without parent
- Depth calculation (0 for root, increments for children)
- `add_child()` validation and type checking
- Parent-child relationship integrity
- String representation (`__str__`, `__repr__`)

### test_controller_mode.py (18 tests)
- All enum values exist with correct integer values
- `MODE_LABEL_TO_ENUM` mapping completeness
- `MODE_ENUM_TO_LABEL` mapping completeness
- Bidirectional consistency (label -> enum -> label roundtrip)

### test_controller_manager.py (34 tests)
- `rebuild_tree()` from dict structure
- `register_first_temporary_controller()`
- `register_child_node()`
- `remove_controller_from_model()`
- `contains()` / `node_is_temporary_controller()` / `node_is_base_controller()`
- `rename_controller()` updates maps correctly
- `clear()` resets state
- `get_controller_node_from_controller_map()`
- `get_controller_map_values()`

### test_naming.py (9 tests)
- `build_temp_control_data_name()` generates correct suffix
- Edge cases (empty string, special characters, namespaces)
- Constants verification (`SUFFIXE_TEMP_CONTROL_DATA`, `SUFFIXE_TEMP_CONTROL_CTRLLER`, `SUFFIXE_TEMP_PIVOT`)

## Import Helper

The `tests/import_helper.py` module solves the problem of importing cr_tempController modules without triggering Maya-dependent imports. It:

1. Sets up a fake package hierarchy in `sys.modules`
2. Uses `importlib.util` to load modules directly from file paths
3. Bypasses the `core/__init__.py` which imports Maya-dependent modules

## Running Tests

```bash
# Activate virtual environment
source .venv/Scripts/activate   # Git Bash / Linux / macOS
.venv\Scripts\activate          # Windows CMD

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_controller_manager.py -v

# Run with coverage (requires pytest-cov)
pip install pytest-cov
pytest --cov=cr_tempController --cov-report=html
```

## Results

```
============================= test session starts =============================
collected 77 items
...
============================= 77 passed in 0.10s ==============================
```

## What's Testable Without Maya

| Module | Testable | Notes |
|--------|----------|-------|
| `core/controller_node.py` | Yes | Pure Python data structure |
| `core/controller_mode.py` | Yes | Enum with label mappings |
| `core/controller_manager.py` | Yes | Tree state management |
| `utils/naming.py` | Yes | Name generation utilities |
| `constants.py` | Yes | Configuration values |
| `utils/animation.py` | No | Uses `maya.cmds` |
| `utils/nodes.py` | No | Uses `maya.cmds` and `maya.api.OpenMaya` |
| `core/controller_factory.py` | No | Uses `maya.cmds` |
| `core/baking_service.py` | No | Uses `maya.cmds` |
| `core/pivot_tools.py` | No | Uses `maya.cmds` and `maya.api.OpenMaya` |
| All UI code | No | Uses `maya.cmds` |
