"""Helper module to import cr_tempController modules without Maya dependencies."""
import sys
from pathlib import Path
import importlib.util
import types

_base_path = Path(__file__).parent.parent

# Add parent directory to path
parent_dir = _base_path.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))


def import_module_directly(module_name: str, file_path: Path):
    """Import a module directly from file path, bypassing package __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def setup_package_hierarchy():
    """Set up the cr_tempController package hierarchy in sys.modules."""
    # Create cr_tempController package if not exists
    if "cr_tempController" not in sys.modules:
        pkg = types.ModuleType("cr_tempController")
        pkg.__path__ = [str(_base_path)]
        sys.modules["cr_tempController"] = pkg

    # Create cr_tempController.core subpackage
    if "cr_tempController.core" not in sys.modules:
        core_pkg = types.ModuleType("cr_tempController.core")
        core_pkg.__path__ = [str(_base_path / "core")]
        sys.modules["cr_tempController.core"] = core_pkg
        sys.modules["cr_tempController"].core = core_pkg


# Set up package hierarchy on import
setup_package_hierarchy()

# Import constants first (no dependencies)
constants = import_module_directly(
    "cr_tempController.constants",
    _base_path / "constants.py"
)

# Import controller_node (no dependencies)
controller_node = import_module_directly(
    "cr_tempController.core.controller_node",
    _base_path / "core" / "controller_node.py"
)
sys.modules["cr_tempController.core"].controller_node = controller_node
ControllerNode = controller_node.ControllerNode

# Import controller_mode (no dependencies)
controller_mode = import_module_directly(
    "cr_tempController.core.controller_mode",
    _base_path / "core" / "controller_mode.py"
)
ControllerCreationMode = controller_mode.ControllerCreationMode
MODE_LABEL_TO_ENUM = controller_mode.MODE_LABEL_TO_ENUM
MODE_ENUM_TO_LABEL = controller_mode.MODE_ENUM_TO_LABEL

# Import controller_manager (depends on controller_node)
controller_manager = import_module_directly(
    "cr_tempController.core.controller_manager",
    _base_path / "core" / "controller_manager.py"
)
ControllerManager = controller_manager.ControllerManager

# Import naming (depends on constants)
naming = import_module_directly(
    "cr_tempController.utils.naming",
    _base_path / "utils" / "naming.py"
)
build_temp_control_data_name = naming.build_temp_control_data_name
