import resource
import sys
from app.core.search_engine import SearchEngine
import time
from pathlib import Path
from app.config import Settings

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


link = sys.argv[1] if len(sys.argv) > 1 else "link.txt"
t = time.perf_counter()
e = SearchEngine(Settings())
e.startup()
t1 = time.perf_counter()
g = e.get_graph(link)
print(
    f"index build {t1 - t:.3f}s, graph build {time.perf_counter() - t1:.3f}s, edges {g.edge_count}, "
    f"peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:.1f} MB"
)
