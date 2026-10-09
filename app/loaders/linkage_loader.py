from __future__ import annotations
import hashlib
import logging
import math
from collections.abc import Iterable
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from app.core.graph import Graph
from app.models.location import Location
from app.utils.distance import edge_weight

log = logging.getLogger(__name__)
_SCALE = 1_000_000
SNAP_TOL = 1e-4


def file_identity(path: Path, mode: str, directed: bool) -> str:
    st = path.stat()
    return f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}|{mode}|{'d' if directed else 'u'}"


def text_identity(text: str, mode: str, directed: bool) -> str:
    h = hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()
    return f"inline|{h}|{mode}|{'d' if directed else 'u'}"


def _q(x: float) -> int:
    return round(x * _SCALE)


class _Snapper:
    def __init__(self, locations: dict[int, Location]):
        ids = sorted(locations)
        self.exact: dict[tuple[int, int], int] = {}
        for lid in ids:
            l = locations[lid]
            self.exact.setdefault((_q(l.lat), _q(l.lon)), lid)
        self.ids = np.array(ids, dtype=np.int64)
        self.tree = cKDTree(
            np.array(
                [(locations[i].lat, locations[i].lon) for i in ids], dtype=np.float64
            )
        )

    def find(self, lat: float, lon: float) -> int | None:
        hit = self.exact.get((_q(lat), _q(lon)))
        if hit is not None:
            return hit
        d, i = self.tree.query([lat, lon], distance_upper_bound=SNAP_TOL)
        return int(self.ids[i]) if math.isfinite(d) else None


def build_graph(
    lines: Iterable[str],
    locations: dict[int, Location],
    mode: str,
    directed: bool,
    identity: str,
    name: str = "<inline>",
) -> Graph:
    stats = dict(
        lines=0, edges=0, malformed=0, unknown_node=0, self_loops=0, duplicates=0
    )
    snapper: _Snapper | None = None
    best: dict[tuple[int, int], float] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        stats["lines"] += 1
        parts = line.replace(",", " ").split()
        try:
            if len(parts) == 4:
                lon_a, lat_a, lon_b, lat_b = (float(p) for p in parts)
                if not all(map(math.isfinite, (lon_a, lat_a, lon_b, lat_b))):
                    raise ValueError
                if snapper is None:
                    snapper = _Snapper(locations)
                a = snapper.find(lat_a, lon_a)
                b = snapper.find(lat_b, lon_b)
            elif len(parts) == 2:
                a, b = int(parts[0]), int(parts[1])
            else:
                raise ValueError
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
        log.warning("linkage %s: %s", name, stats)
    return Graph(adj=adj, identity=identity, stats=stats)


def load_graph(
    path: Path, locations: dict[int, Location], mode: str, directed: bool
) -> Graph:
    ident = file_identity(path, mode, directed)
    with path.open(encoding="utf-8-sig") as f:
        return build_graph(f, locations, mode, directed, ident, path.name)


def load_graph_text(
    text: str, locations: dict[int, Location], mode: str, directed: bool
) -> Graph:
    text = text.lstrip("\ufeff")
    return build_graph(
        text.splitlines(),
        locations,
        mode,
        directed,
        text_identity(text, mode, directed),
    )
