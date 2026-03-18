"""
modules/filter_engine.py
------------------------
Smart Filter & Search Engine — filter datasets by any column/condition.

Features:
  - Filter by column value (equals, contains, greater than, less than, between)
  - Sort by any column ascending/descending
  - Search across all text columns simultaneously
  - Returns filtered rows + summary stats

Concepts used:
  - Abstract Base Class + @abstractmethod
  - @log_call, @timer decorators
  - Generator (filtered_row_generator)
  - Pandas boolean masking
  - SerializableMixin, LoggableMixin, ReprMixin
"""

import io
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

from utils.mixins     import SerializableMixin, LoggableMixin, ReprMixin
from utils.decorators import log_call, timer


class BaseFilterEngine(ABC):
    @abstractmethod
    def apply_filters(self, df: pd.DataFrame, filters: list, search: str,
                      sort_col: str, sort_dir: str) -> pd.DataFrame:
        ...


class SmartFilterEngine(BaseFilterEngine, SerializableMixin, LoggableMixin, ReprMixin):
    """
    Applies multiple filter conditions + global search to a DataFrame.
    Each filter: {"col": "salary", "op": "gt", "val": "50000"}
    """

    OPERATORS = {
        "eq":       "Equals",
        "neq":      "Not Equals",
        "contains": "Contains",
        "gt":       "Greater Than",
        "gte":      "Greater or Equal",
        "lt":       "Less Than",
        "lte":      "Less or Equal",
        "between":  "Between (use val as lo,hi)",
        "isnull":   "Is Empty",
        "notnull":  "Is Not Empty",
    }

    def __init__(self):
        LoggableMixin.__init__(self)

    # ── Generator: yield filtered rows lazily ─────────────────────────────────
    def filtered_row_generator(self, df: pd.DataFrame):
        """Generator — yields rows from a filtered DataFrame one at a time."""
        for _, row in df.iterrows():
            yield row.to_dict()

    @log_call
    @timer
    def apply_filters(self, df: pd.DataFrame, filters: list,
                      search: str = "", sort_col: str = "",
                      sort_dir: str = "asc") -> pd.DataFrame:
        """Apply filters, global search, and sort. Returns filtered DataFrame."""
        result = df.copy()

        # Global search across all text columns
        if search and search.strip():
            s = search.strip().lower()
            text_cols = result.select_dtypes(exclude=[np.number]).columns.tolist()
            if text_cols:
                mask = result[text_cols].apply(
                    lambda col: col.astype(str).str.lower().str.contains(s, na=False)
                ).any(axis=1)
                result = result[mask]

        # Apply each filter condition
        for f in filters:
            col = f.get("col", "").strip()
            op  = f.get("op",  "eq").strip()
            val = f.get("val", "").strip()

            if col not in result.columns or not op:
                continue

            try:
                series = result[col]
                is_num = pd.api.types.is_numeric_dtype(series)

                if op == "isnull":
                    result = result[series.isnull()]
                elif op == "notnull":
                    result = result[series.notnull()]
                elif op == "contains":
                    result = result[series.astype(str).str.contains(val, case=False, na=False)]
                elif op == "eq":
                    if is_num and val:
                        result = result[series == float(val)]
                    else:
                        result = result[series.astype(str).str.lower() == val.lower()]
                elif op == "neq":
                    if is_num and val:
                        result = result[series != float(val)]
                    else:
                        result = result[series.astype(str).str.lower() != val.lower()]
                elif op == "gt"  and is_num and val:
                    result = result[series > float(val)]
                elif op == "gte" and is_num and val:
                    result = result[series >= float(val)]
                elif op == "lt"  and is_num and val:
                    result = result[series < float(val)]
                elif op == "lte" and is_num and val:
                    result = result[series <= float(val)]
                elif op == "between" and is_num and "," in val:
                    lo, hi = [float(x.strip()) for x in val.split(",", 1)]
                    result = result[(series >= lo) & (series <= hi)]
            except Exception:
                pass

        # Sort
        if sort_col and sort_col in result.columns:
            result = result.sort_values(
                sort_col, ascending=(sort_dir == "asc")
            ).reset_index(drop=True)

        self.log_event(f"apply_filters — {len(filters)} filters, {len(result)} rows returned")
        return result

    def to_csv_bytes(self, df: pd.DataFrame) -> bytes:
        buf = io.StringIO()
        df.to_csv(buf, index=False, encoding="utf-8")
        return buf.getvalue().encode("utf-8")
