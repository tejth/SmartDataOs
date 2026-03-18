"""
modules/validation.py
---------------------
Validates user-submitted form data using Regular Expressions.

Concepts covered:
  - re module (compile, match, search, fullmatch)
  - Abstract base class (abc.ABC + @abstractmethod)
  - Concrete subclass implementing the abstract interface
  - Multiple inheritance with Mixins (MRO demonstration)
"""

import re
from abc import ABC, abstractmethod
from utils.mixins import SerializableMixin, LoggableMixin, ReprMixin
from utils.decorators import log_call


# ══════════════════════════════════════════════════════════════════════════════
# Abstract base – defines the contract every validator must satisfy
# ══════════════════════════════════════════════════════════════════════════════
class BaseValidator(ABC):
    """
    Abstract class that enforces the validate() interface.

    Concept covered: Abstract Classes
      - Inherits from abc.ABC
      - @abstractmethod forces every subclass to provide validate()
    """

    @abstractmethod
    def validate(self, data: dict) -> dict:
        """
        Validate *data* and return a result dict:
            {"valid": bool, "errors": {field: message}}
        """
        ...

    @abstractmethod
    def get_rules(self) -> dict:
        """Return a dict describing each field's validation rule."""
        ...


# ══════════════════════════════════════════════════════════════════════════════
# Concrete validator – uses regex to validate form fields
# Multiple Inheritance: BaseValidator + SerializableMixin + LoggableMixin + ReprMixin
# MRO (left-to-right): UserFormValidator → BaseValidator → SerializableMixin
#                        → LoggableMixin → ReprMixin → object
# ══════════════════════════════════════════════════════════════════════════════
class UserFormValidator(BaseValidator, SerializableMixin, LoggableMixin, ReprMixin):
    """
    Validates name, email, phone, and password using compiled regex patterns.

    Concept covered:
      - Multiple Inheritance  (4 bases)
      - MRO  – see class definition above
      - Regular Expressions  – each field has a compiled pattern
      - Operator overloading  – inherited from ReprMixin (__repr__, __eq__)
    """

    # Pre-compiled regex patterns (more efficient than re.match each time)
    _PATTERNS = {
        "name": re.compile(r"^[A-Za-z\s\-']{2,60}$"),
        "email": re.compile(r"^[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}$"),
        "phone": re.compile(r"^\+?[\d\s\-\(\)]{7,15}$"),
        # Password: ≥8 chars, ≥1 uppercase, ≥1 lowercase, ≥1 digit, ≥1 special
        "password": re.compile(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]).{8,}$"
        ),
    }

    _MESSAGES = {
        "name":     "Name must be 2–60 alphabetic characters.",
        "email":    "Invalid email address format.",
        "phone":    "Phone must be 7–15 digits (spaces/dashes allowed).",
        "password": "Password ≥8 chars with upper, lower, digit & special char.",
    }

    def __init__(self):
        self.validation_count = 0

    @log_call
    def validate(self, data: dict) -> dict:
        """
        Validate the incoming form data.
        Returns {"valid": bool, "errors": {field: str}}.
        """
        errors = {}
        self.validation_count += 1

        for field, pattern in self._PATTERNS.items():
            value = data.get(field, "").strip()
            if not value:
                errors[field] = f"{field.capitalize()} is required."
            elif not pattern.fullmatch(value):
                errors[field] = self._MESSAGES[field]

        result = {"valid": len(errors) == 0, "errors": errors}
        self.log_event(f"Validated form – valid={result['valid']}, errors={errors}")
        return result

    def get_rules(self) -> dict:
        """Return human-readable descriptions of each validation rule."""
        return {field: msg for field, msg in self._MESSAGES.items()}
