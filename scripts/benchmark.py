import random
from app.config import Settings
import time
import statistics
from app.core.search_engine import SearchEngine
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p / 100))] * 1000


link = sys.argv[1] if len(sys.argv) > 1 else "links.txt"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 500
e = SearchEngine(Settings(cache_size=0))
e.startup()
e.get_graph(link)
rnd = random.Random(1)
cats = sorted(e.index.categories)
qs = [
    (rnd.random(), rnd.random(), rnd.choice(cats), rnd.choice([0.1, 0.2, 0.4]))
    for _ in range(n)
]

for name, brute in (("brute-force", True), ("kd-tree", False)):
    ts = []
    for la, lo, c, r in qs:
        t = time.perf_counter()
        e.index.within_radius(la, lo, c, r, brute=brute)
        ts.append(time.perf_counter() - t)
    print(
        f"radius filter [{name}]: mean {statistics.mean(ts)*1000:.3f} ms  p50 {pct(ts,50):.3f}  p95 {pct(ts,95):.3f}"
    )

ts = []
for la, lo, c, r in qs:
    t = time.perf_counter()
    e.search(la, lo, c, r, link)
    ts.append(time.perf_counter() - t)
print(
    f"end-to-end search (no cache), n={n}: p50 {pct(ts,50):.2f} ms  p90 {pct(ts,90):.2f}  p95 {pct(ts,95):.2f}  p99 {pct(ts,99):.2f}  "
    f"throughput {n/sum(ts):.0f} qps (single thread)"
)
