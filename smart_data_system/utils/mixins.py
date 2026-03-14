"""
utils/mixins.py
---------------
Mixin classes that add reusable behaviour to any class that inherits them.

Concepts covered:
  - Mixin pattern (multiple inheritance without diamond-problem pitfalls)
  - Method Resolution Order (MRO) – Python resolves methods left-to-right
    through the MRO chain (C3 linearisation).
  - Operator overloading (__repr__, __str__, __eq__, __add__)
"""

import json
import datetime


# ══════════════════════════════════════════════════════════════════════════════
# Mixin 1 : SerializableMixin
# ══════════════════════════════════════════════════════════════════════════════
class SerializableMixin:
    """
    Adds JSON serialization / deserialization to any class.

    Concept covered: Mixin 1 – provides `to_json` and `from_dict` without
    forcing a particular base class.
    """

    def to_dict(self) -> dict:
        """Return a plain-dict snapshot of all public instance attributes."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the object to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: dict):
        """Create an instance from a dictionary (shallow)."""
        obj = cls.__new__(cls)
        obj.__dict__.update(data)
        return obj


# ══════════════════════════════════════════════════════════════════════════════
# Mixin 2 : LoggableMixin
# ══════════════════════════════════════════════════════════════════════════════
class LoggableMixin:
    """
    Adds a simple activity log to any class.

    Concept covered: Mixin 2 – composed in without inheritance from a
    concrete base.
    """

    def __init_log(self):
        if not hasattr(self, "_log"):
            self._log: list = []

    def log_event(self, message: str) -> None:
        self.__init_log()
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "class": type(self).__name__,
            "message": message,
        }
        self._log.append(entry)

    def get_log(self) -> list:
        self.__init_log()
        return list(self._log)

    def clear_log(self) -> None:
        self._log = []


# ══════════════════════════════════════════════════════════════════════════════
# Mixin 3 : ReprMixin  (operator overloading)
# ══════════════════════════════════════════════════════════════════════════════
class ReprMixin:
    """
    Provides human-readable __repr__ and __str__ for any class.

    Concept covered: Operator overloading (__repr__, __str__)
    Python calls __repr__ in the REPL and when repr() is used;
    __str__ is called by print() and str().
    """

    def __repr__(self) -> str:
        attrs = ", ".join(
            f"{k}={v!r}"
            for k, v in self.__dict__.items()
            if not k.startswith("_")
        )
        return f"{type(self).__name__}({attrs})"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        return self.__dict__ == other.__dict__
