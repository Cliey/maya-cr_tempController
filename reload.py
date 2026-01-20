import sys
import importlib
import logging
import cr_tempController
import cr_tempController.constants
import cr_tempController.ui
import cr_tempController.core
import cr_tempController.utils

LOGGER = logging.getLogger(__name__)

def reload_package(package_name: str):
    """
    Reload a package and all its submodules.
    """
    LOGGER.info("Reload package")

    modules = sorted(
        [
            name for name in sys.modules
            if name == package_name or name.startswith(package_name + ".")
        ],
        key=lambda m: m.count("."),
        reverse=True
    )

    LOGGER.info(f"Modules found -> {modules}")

    for name in modules:
        if name == package_name:
            continue
        
        module = sys.modules.get(name)
        if not module:
            continue

        try:
            LOGGER.info(f"Reload -> {name}")
            importlib.reload(module)
        except Exception:
            LOGGER.exception(f"Failed to reload {name}")