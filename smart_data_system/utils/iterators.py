"""
utils/iterators.py
------------------
Custom iterator classes used in the application.

Concepts covered:
  - __iter__ / __next__ protocol (custom iterator)
  - StopIteration to signal exhaustion
"""


# ── Custom Iterator : DatasetRowIterator ──────────────────────────────────────
class DatasetRowIterator:
    """
    Iterates over rows of a list-of-dicts dataset one at a time.

    Usage:
        it = DatasetRowIterator(rows, batch_size=1)
        for row in it:
            process(row)

    Concept covered: Custom Iterator
        __iter__ returns self (making the object its own iterator).
        __next__ advances the internal pointer and raises StopIteration
        when all rows have been yielded.
    """

    def __init__(self, rows: list, batch_size: int = 1):
        self._rows = rows
        self._batch_size = batch_size
        self._index = 0

    # Required by the iterator protocol
    def __iter__(self):
        return self

    def __next__(self):
        if self._index >= len(self._rows):
            raise StopIteration
        batch = self._rows[self._index: self._index + self._batch_size]
        self._index += self._batch_size
        return batch if self._batch_size > 1 else batch[0]

    def reset(self):
        """Allow re-iteration from the beginning."""
        self._index = 0

    def __len__(self):
        return len(self._rows)


# ── Custom Iterator : RangeStepIterator ──────────────────────────────────────
class RangeStepIterator:
    """
    Numeric iterator with a configurable step – similar to range() but
    usable as a standalone object.

    Concept covered: Custom Iterator (second example for completeness)
    """

    def __init__(self, start: float, stop: float, step: float = 1.0):
        self._current = start
        self._stop = stop
        self._step = step

    def __iter__(self):
        return self

    def __next__(self):
        if self._current >= self._stop:
            raise StopIteration
        value = self._current
        self._current += self._step
        return round(value, 10)
