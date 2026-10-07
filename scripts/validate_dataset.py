"""Sanity-check locations.csv and (optionally) a linkage file."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.loaders.linkage_loader import load_graph
from app.loaders.location_loader import load_locations

locs = load_locations(Path(sys.argv[1] if len(sys.argv) > 1 else "data/locations.csv"))
print("locations:", len(locs))
print("unique lat:", len({l.lat for l in locs.values()}), "unique lon:", len({l.lon for l in locs.values()}))
print("categories:", dict(Counter(l.category for l in locs.values())))
if len(sys.argv) > 2:
    g = load_graph(Path(sys.argv[2]), locs, "geographic", False)
    print("graph:", g.stats, "directed edges stored:", g.edge_count)
