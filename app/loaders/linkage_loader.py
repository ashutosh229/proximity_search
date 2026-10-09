from __future__ import annotations
import logging
from app.core.graph import Graph
from app.models.location import Location
from pathlib import Path
from app.utils.distance import edge_weight

log = logging.getLogger(__name__)


def file_identity(path: Path, mode: str, directed: bool) -> str:
    st = path.stat()
    return f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}|{mode}|{'d' if directed else 'u'}"


def load_graph(
    path: Path, locations: dict[int, Location], mode: str, directed: bool
) -> Graph:
    stats = dict(
        lines=0, edges=0, malformed=0, unknown_node=0, self_loops=0, duplicates=0
    )
    best: dict[tuple[int, int], float] = {}
    with path.open(encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            stats["lines"] += 1
            parts = line.replace(",", " ").split()
            try:
                if len(parts) != 2:
                    raise ValueError
                a, b = int(parts[0]), int(parts[1])
            except ValueError:
                stats["malformed"] += 1
                continue
            la, lb = locations.get(a), locations.get(b)
            if la is None or lb is None:
                stats["unknown_node"] += 1
                continue
            if a == b:
                stats["self_loops"] += 1
                continue
            w = edge_weight(mode, la.lat, la.lon, lb.lat, lb.lon)
            pairs = ((a, b),) if directed else ((a, b), (b, a))
            for key in pairs:
                if key in best:
                    stats["duplicates"] += 1
                    best[key] = min(best[key], w)
                else:
                    best[key] = w
    adj: dict[int, list[tuple[int, float]]] = {lid: [] for lid in locations}
    for (u, v), w in best.items():
        adj[u].append((v, w))
    stats["edges"] = len(best)
    if stats["malformed"] or stats["unknown_node"]:
        log.warning("linkage %s: %s", path.name, stats)
    return Graph(adj=adj, identity=file_identity(path, mode, directed), stats=stats)
