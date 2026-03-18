"""
modules/merger.py
-----------------
Dataset Merger — merges two DataFrames on a common key column.

Features:
  - Inner / Left / Right / Outer joins
  - Auto-detect common columns for join key
  - Returns merged DataFrame + merge summary
  - Downloadable merged CSV

Concepts used:
  - Abstract Base Class + @abstractmethod
  - @log_call, @timer decorators
  - SerializableMixin, LoggableMixin, ReprMixin
  - Pandas pd.merge()
  - Generator (merged_row_generator)
"""

import io
import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

from utils.mixins     import SerializableMixin, LoggableMixin, ReprMixin
from utils.decorators import log_call, timer


class BaseMerger(ABC):
    @abstractmethod
    def merge(self, df_a: pd.DataFrame, df_b: pd.DataFrame,
              key: str, how: str) -> tuple:
        ...


class DatasetMerger(BaseMerger, SerializableMixin, LoggableMixin, ReprMixin):
    """
    Merges two DataFrames on a user-specified key column.
    Inherits: BaseMerger · SerializableMixin · LoggableMixin · ReprMixin
    """

    JOIN_TYPES = {
        "inner": "Inner Join — only rows with matching key in BOTH datasets",
        "left":  "Left Join  — all rows from Dataset A, matched rows from B",
        "right": "Right Join — all rows from Dataset B, matched rows from A",
        "outer": "Outer Join — all rows from BOTH datasets (fills missing with NaN)",
    }

    def __init__(self):
        LoggableMixin.__init__(self)

    def common_columns(self, df_a: pd.DataFrame, df_b: pd.DataFrame) -> list:
        """Return columns that exist in both DataFrames (potential join keys)."""
        return sorted(set(df_a.columns) & set(df_b.columns))

    # ── Generator: stream merged rows lazily ──────────────────────────────────
    def merged_row_generator(self, df: pd.DataFrame):
        """Generator — yields merged rows one at a time."""
        for _, row in df.iterrows():
            yield row.to_dict()

    @log_call
    @timer
    def merge(self, df_a: pd.DataFrame, df_b: pd.DataFrame,
              key: str, how: str = "inner") -> tuple:
        """
        Merge df_a and df_b on the given key using join type how.
        Returns (merged_df, summary_dict).
        """
        if key not in df_a.columns:
            raise ValueError(f"Key '{key}' not found in Dataset A")
        if key not in df_b.columns:
            raise ValueError(f"Key '{key}' not found in Dataset B")

        if how not in self.JOIN_TYPES:
            how = "inner"

        # Handle column name conflicts (suffix with _A and _B)
        cols_a = set(df_a.columns) - {key}
        cols_b = set(df_b.columns) - {key}
        overlap = cols_a & cols_b

        merged = pd.merge(df_a, df_b, on=key, how=how,
                          suffixes=("_A", "_B"))

        rows_a  = len(df_a)
        rows_b  = len(df_b)
        matched = int(df_a[key].isin(df_b[key]).sum())

        summary = {
            "join_type":     how,
            "join_desc":     self.JOIN_TYPES[how],
            "key_col":       key,
            "rows_a":        rows_a,
            "rows_b":        rows_b,
            "rows_matched":  matched,
            "rows_merged":   len(merged),
            "cols_a":        len(df_a.columns),
            "cols_b":        len(df_b.columns),
            "cols_merged":   len(merged.columns),
            "cols_overlap":  sorted(overlap),
            "missing_after": int(merged.isnull().sum().sum()),
            "only_in_a":     sorted(cols_a - cols_b),
            "only_in_b":     sorted(cols_b - cols_a),
        }

        self.log_event(f"merge() — {how} join on '{key}' → {len(merged)} rows × {len(merged.columns)} cols")
        return merged, summary

    def to_csv_bytes(self, df: pd.DataFrame) -> bytes:
        buf = io.StringIO()
        df.to_csv(buf, index=False, encoding="utf-8")
        return buf.getvalue().encode("utf-8")
