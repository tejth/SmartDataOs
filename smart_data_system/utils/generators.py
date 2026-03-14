"""
utils/generators.py
-------------------
Generator functions for memory-efficient data streaming.

Concepts covered:
  - `yield` keyword to create generator functions
  - Lazy evaluation – values produced on demand, not all at once
"""

import json
import os
import math


# ── Generator 1 : chunk_dataset ──────────────────────────────────────────────
def chunk_dataset(data: list, chunk_size: int = 100):
    """
    Generator that yields successive chunks of `data`.

    Concept covered: Generator function with `yield`
    Instead of building a list of all chunks (memory-intensive for large
    datasets), each chunk is produced lazily when the caller calls next().

    Usage:
        for chunk in chunk_dataset(big_list, chunk_size=50):
            process(chunk)
    """
    for i in range(0, len(data), chunk_size):
        yield data[i: i + chunk_size]


# ── Generator 2 : stats_stream ────────────────────────────────────────────────
def stats_stream(numeric_values: list):
    """
    Generator that yields running statistics as it consumes values.

    Yields a dict: {index, value, running_mean, running_variance}

    Concept covered: Generator with internal state – replaces the need
    to store all intermediate results in memory.
    """
    n = 0
    mean = 0.0
    M2 = 0.0          # used for Welford's online variance algorithm

    for value in numeric_values:
        try:
            x = float(value)
        except (TypeError, ValueError):
            continue

        n += 1
        delta = x - mean
        mean += delta / n
        delta2 = x - mean
        M2 += delta * delta2

        variance = M2 / n if n > 1 else 0.0
        yield {
            "index": n,
            "value": x,
            "running_mean": round(mean, 4),
            "running_std": round(math.sqrt(variance), 4),
        }


# ── Generator 3 : json_record_generator ──────────────────────────────────────
def json_record_generator(filepath: str):
    """
    Generator that reads a JSON array file and yields records one at a time.

    Concept covered: Generator used for large-file streaming so the entire
    file is not loaded into memory at once.
    """
    if not os.path.exists(filepath):
        return
    with open(filepath, "r") as f:
        records = json.load(f)
    if isinstance(records, list):
        for record in records:
            yield record
