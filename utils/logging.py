from logging import Logger, INFO
import time
import inspect


def print_data(logger: Logger, level: int = INFO, ordered: bool = False, **data):
    if not data:
        logger.log(level, "Printed data: <empty>")
        return
    
    items = sorted(data.items()) if ordered else data.items()

    lines = ["Printed data:"]

    for name, value in items:
        lines.append(f'  "{name}" = {value}')
    
    logger.log(level, "\n".join(lines))

def print_data_one_line(logger: Logger, level: int = INFO, ordered: bool = False, **data):
    if not data:
        logger.log(level, "Printed data: <empty>")
        return
    
    items = sorted(data.items()) if ordered else data.items()

    payload = ", ".join(f'"{key}" = {value}' for key, value in items)
    logger.log(level, f"Printed data: {payload}")

def log_call_stack(logger: Logger, depth: int = 3, level: int = INFO):
    """
    Docstring for log_call_stack
    
    :param logger: Logger used to log the timing
    :type logger: Logger
    :param depth: Depth of the call stack (Default: 3)
    :type depth: int
    :param level: Level of the log added (Default: INFO)
    :type level: int
    """
    stack = inspect.stack()[1:depth+1]
    lines = ["Call stack:"]
    for frame in stack:
        lines.append(f'  {frame.function} ({frame.filename}:{frame.lineno})')
    logger.log(level, "\n".join(lines))

# @contextmanager
def log_timing(logger: Logger, label: str, level: int = INFO):
    """
    Utility function to time a part of a function and log it afterward.
    Example:
        ```
        with log_timing(LOGGER, "myLbale"):
            # Code to Monitor
        ```

    
    :param logger: Logger used to log the timing
    :type logger: Logger
    :param label: Label to be used to easily find it into the logs
    :type label: str
    :param level: Level of the log added (Default: INFO)
    :type level: int
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        logger.log(level, f'[TIMING] {label}: {elapsed:.3f} ms')

def print_locals(logger: Logger, level: int = INFO, one_line: bool = False, ordered: bool = False):
    frame = inspect.currentframe()
    try:
        caller = frame.f_back if frame else None
        if not caller:
            logger.log(level, "Printed locals: <no frame>")
            return

        data = caller.f_locals

        if one_line:
            print_data_one_line(logger, level, ordered, **data)
        else:
            print_data(logger, level, ordered, **data)
    finally:
        del frame