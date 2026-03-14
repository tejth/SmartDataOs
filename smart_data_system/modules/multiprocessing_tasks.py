"""
modules/multiprocessing_tasks.py
---------------------------------
Demonstrates Python's multiprocessing module for CPU-bound tasks.

Concepts covered:
  - multiprocessing.Pool   (process pool for parallel CPU work)
  - multiprocessing.Manager (shared state across processes)
  - os and sys modules
"""

import multiprocessing
import os
import sys
import math
import time
from utils.decorators import timer, log_call


# ── CPU-bound worker (must be top-level for pickling) ────────────────────────
def _compute_stats_worker(args):
    """
    Worker executed in a separate OS process.
    Computes basic statistics for a list of numbers.

    Running in a separate process bypasses the GIL – true parallelism.
    """
    chunk_id, values = args
    if not values:
        return {"chunk_id": chunk_id, "error": "empty chunk"}

    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)

    # Simulate CPU-intensive work
    _ = [math.factorial(10) for _ in range(500)]

    return {
        "chunk_id": chunk_id,
        "pid": os.getpid(),
        "count": n,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


@timer
@log_call
def run_multiprocess_statistics(values: list, num_processes: int = None) -> dict:
    """
    Distribute `values` across multiple processes using Pool.map().

    Concept covered:
      - multiprocessing.Pool  – spawns separate Python processes
      - os.cpu_count()        – reads available CPU cores (os module)
      - sys.version           – reads runtime info (sys module)

    Returns aggregated statistics from all worker processes.
    """
    if not values:
        return {"status": "no_data"}

    num_processes = num_processes or min(4, os.cpu_count() or 2)

    # Split values into chunks
    chunk_size = max(1, len(values) // num_processes)
    chunks = [values[i: i + chunk_size] for i in range(0, len(values), chunk_size)]
    indexed_chunks = list(enumerate(chunks))

    start = time.perf_counter()

    # Use 'spawn' context for safety across platforms
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=num_processes) as pool:
        chunk_results = pool.map(_compute_stats_worker, indexed_chunks)

    elapsed = round(time.perf_counter() - start, 4)

    # Aggregate across chunks
    all_means = [r["mean"] for r in chunk_results if "mean" in r]
    grand_mean = round(sum(all_means) / len(all_means), 4) if all_means else None

    return {
        "status": "completed",
        "python_version": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "processes_used": num_processes,
        "total_values": len(values),
        "elapsed_seconds": elapsed,
        "grand_mean": grand_mean,
        "chunk_results": chunk_results,
    }
