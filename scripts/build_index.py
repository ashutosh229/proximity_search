"""Offline warm-up: build indexes + graph and report timings/memory (no persistence needed at this scale)."""
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Settings
from app.core.search_engine import SearchEngine

link = sys.argv[1] if len(sys.argv) > 1 else "links.txt"
t = time.perf_counter()
e = SearchEngine(Settings())
e.startup()
t1 = time.perf_counter()
g = e.get_graph(link)
print(f"index build {t1 - t:.3f}s, graph build {time.perf_counter() - t1:.3f}s, edges {g.edge_count}, "
      f"peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f} MB")
