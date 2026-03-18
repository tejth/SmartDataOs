"""
modules/threading_tasks.py
--------------------------
Demonstrates Python's threading module for concurrent I/O-bound tasks.

Concepts covered:
  - threading.Thread
  - threading.Lock  (thread-safe shared state)
  - threading.Event (signalling between threads)
  - Concurrent dataset validation across multiple chunks
"""

import threading
import time
from utils.decorators import timer, log_call


# ── Shared result store (protected by a Lock) ────────────────────────────────
_lock = threading.Lock()
_results: list = []


def _process_chunk(chunk: list, chunk_id: int, result_store: list) -> None:
    """
    Worker function run in a separate thread.
    Simulates a validation / transformation pass on a data chunk.
    """
    processed = []
    for row in chunk:
        # Simulate I/O-bound work (e.g. network lookup, disk read)
        time.sleep(0.001)
        processed.append({k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()})

    # Thread-safe write to shared list
    with _lock:
        result_store.append({
            "chunk_id": chunk_id,
            "rows_processed": len(processed),
            "sample": processed[:2],
        })


@timer
@log_call
def run_threaded_processing(rows: list, num_threads: int = 4) -> dict:
    """
    Split `rows` into `num_threads` chunks and process each chunk in its
    own thread.

    Returns a summary dict with timing and per-chunk results.

    Concept covered: threading.Thread – each chunk runs concurrently.
    For I/O-bound work, threads genuinely improve throughput despite the GIL.
    """
    if not rows:
        return {"status": "no_data", "results": []}

    # Divide rows evenly
    chunk_size = max(1, len(rows) // num_threads)
    chunks = [rows[i: i + chunk_size] for i in range(0, len(rows), chunk_size)]

    shared_results: list = []
    threads: list[threading.Thread] = []

    start = time.perf_counter()

    for idx, chunk in enumerate(chunks):
        t = threading.Thread(
            target=_process_chunk,
            args=(chunk, idx, shared_results),
            name=f"DataThread-{idx}",
            daemon=True,
        )
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    elapsed = round(time.perf_counter() - start, 4)

    return {
        "status": "completed",
        "threads_used": len(threads),
        "total_rows": len(rows),
        "elapsed_seconds": elapsed,
        "chunk_results": sorted(shared_results, key=lambda x: x["chunk_id"]),
    }
