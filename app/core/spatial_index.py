from __future__ import annotations
import math
from collections import defaultdict
import numpy as np
from app.models.location import Location
from scipy.spatial import cKDTree

_EPS = 1e-9


class SpatialIndex:
    def __init__(self, locations: dict[int, Location], use_kdtree: bool = True):
        by_cat: dict[str, list[Location]] = defaultdict(list)
        for loc in locations.values():
            by_cat[loc.category].append(loc)
        self.ids: dict[str, np.ndarray] = {}
        self.coords: dict[str, np.ndarray] = {}
        self.trees: dict[str, object] = {}
        for cat, locs in by_cat.items():
            self.ids[cat] = np.array([l.id for l in locs], dtype=np.int64)
            self.coords[cat] = np.array(
                [(l.lat, l.lon) for l in locs], dtype=np.float64
            )
            if use_kdtree:
                self.trees[cat] = cKDTree(self.coords[cat])
        self.categories = set(by_cat)
        self.kdtree_enabled = bool(self.trees)

    def within_radius(
        self, lat: float, lon: float, cat: str, rad: float, *, brute: bool = False
    ) -> set[int]:
        if cat not in self.ids:
            return set()
        coords, ids = self.coords[cat], self.ids[cat]
        tree = self.trees.get(cat)
        if tree is not None and not brute:
            idx = np.asarray(
                tree.query_ball_point([lat, lon], rad + _EPS), dtype=np.int64
            )
            if idx.size == 0:
                return set()
            sub = coords[idx]
            d = np.hypot(sub[:, 0] - lat, sub[:, 1] - lon)
            return set(ids[idx[d <= rad + _EPS]].tolist())
        d = np.hypot(coords[:, 0] - lat, coords[:, 1] - lon)
        return set(ids[d <= rad + _EPS].tolist())


class NodeLocator:
    def __init__(self, locations: dict[int, Location]):
        self.ids = np.array(sorted(locations), dtype=np.int64)
        self.coords = np.array(
            [(locations[int(i)].lat, locations[int(i)].lon) for i in self.ids],
            dtype=np.float64,
        )
        self.tree = cKDTree(self.coords)

    def nearest(self, lat: float, lon: float) -> int:
        d0, _ = self.tree.query([lat, lon])
        idx = np.asarray(
            self.tree.query_ball_point([lat, lon], float(d0) + _EPS), dtype=np.int64
        )
        d = np.hypot(self.coords[idx, 0] - lat, self.coords[idx, 1] - lon)
        return int(self.ids[idx[d == d.min()]].min())


def nearest_node(locations: dict[int, Location], lat: float, lon: float) -> int:
    best_id, best_d = -1, math.inf
    for lid, l in locations.items():
        d = math.hypot(l.lat - lat, l.lon - lon)
        if d < best_d or (d == best_d and lid < best_id):
            best_id, best_d = lid, d
    return best_id
