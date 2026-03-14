"""
utils/decorators.py
-------------------
Provides reusable decorators used across the application:
  - @log_call   : logs every function call with arguments and result
  - @timer      : measures and logs execution time
  - @validate_input : checks that required keys exist in a dict argument
"""

import time
import functools
import datetime
import json
import os

LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "app.log"))


def _write_log(message: str) -> None:
    """Append a timestamped message to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


# ── Decorator 1 : log_call ────────────────────────────────────────────────────
def log_call(func):
    """
    Decorator that logs the function name, arguments, and return value
    every time the wrapped function is called.

    Concept covered: Closures + Decorators
    The inner `wrapper` closes over `func` from the enclosing scope.
    """
    @functools.wraps(func)       # preserves original function metadata
    def wrapper(*args, **kwargs):
        arg_str = ", ".join(
            [repr(a) for a in args] +
            [f"{k}={v!r}" for k, v in kwargs.items()]
        )
        _write_log(f"CALL  {func.__name__}({arg_str})")
        result = func(*args, **kwargs)
        _write_log(f"RETURN {func.__name__} -> {repr(result)[:120]}")
        return result
    return wrapper


# ── Decorator 2 : timer ───────────────────────────────────────────────────────
def timer(func):
    """
    Decorator that records how long a function takes to execute.

    Concept covered: Closures + Decorators
    `start` is captured in the closure formed by `wrapper`.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        _write_log(f"TIMER {func.__name__} completed in {elapsed:.4f}s")
        print(f"[timer] {func.__name__} → {elapsed:.4f}s")
        return result
    return wrapper


# ── Decorator 3 : validate_input ─────────────────────────────────────────────
def validate_input(*required_keys):
    """
    Parameterised decorator factory.
    Usage:  @validate_input("name", "email")
    Raises ValueError if any key is missing from the first dict argument.

    Concept covered: Decorator factory (decorator returning a decorator)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Look for the first dict argument
            data = next((a for a in args if isinstance(a, dict)), kwargs.get("data", {}))
            missing = [k for k in required_keys if k not in data or not data[k]]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
