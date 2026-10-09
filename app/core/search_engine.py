from __future__ import annotations
import threading
from app.loaders.linkage_loader import file_identity, load_graph
from app.loaders.location_loader import load_locations, normalise_category
import logging
from app.utils.metrics import Metrics
import time
from pathlib import Path
from app.core.cache import LRUCache, RedisCache
from app.core.graph import Graph
from app.core.shortest_path import k_nearest_by_graph
from app.config import Settings
from app.core.spatial_index import NodeLocator, SpatialIndex

log = logging.getLogger(__name__)


class LinkageNotFound(Exception):
    pass


class SearchEngine:
    def __init__(self, settings: Settings, metrics: Metrics | None = None):
        self.s = settings
        self.metrics = metrics or Metrics()
        self.locations = {}
        self.index: SpatialIndex | None = None
        self.locator: NodeLocator | None = None
        self._graphs = LRUCache(settings.graph_cache_size)
        self._graph_lock = threading.Lock()
        if settings.redis_url:
            self.results = RedisCache(settings.redis_url, settings.redis_ttl)
        else:
            self.results = LRUCache(settings.cache_size)
        self.ready = False

    def startup(self):
        t0 = time.perf_counter()
        self.locations = load_locations(self.s.data_dir / self.s.locations_file)
        self.index = SpatialIndex(self.locations, self.s.use_kdtree)
        self.locator = NodeLocator(self.locations)
        for link in {
            *self.s.preload_links,
            *([self.s.default_link] if self.s.default_link else []),
        }:
            self.get_graph(link)
        dt = time.perf_counter() - t0
        self.metrics.set("ip_startup_seconds", dt)
        self.metrics.set("ip_locations_loaded", len(self.locations))
        self.ready = True
        log.info("ready: %d locations in %.3fs", len(self.locations), dt)

    def resolve_link(self, link: str) -> Path:
        try:
            base = self.s.data_dir.resolve()
            p = (base / link).resolve()
            ok = base in p.parents and p.is_file()
        except (ValueError, OSError):
            ok = False
        if not ok:
            raise LinkageNotFound(link)
        return p

    def get_graph(self, link: str) -> Graph:
        path = self.resolve_link(link)
        ident = file_identity(path, self.s.edge_weight_mode, self.s.directed_links)
        g = self._graphs.get(ident)
        if g is not None:
            self.metrics.inc("ip_graph_cache_hits_total")
            return g
        with self._graph_lock:
            g = self._graphs.get(ident)
            if g is None:
                t0 = time.perf_counter()
                g = load_graph(
                    path, self.locations, self.s.edge_weight_mode, self.s.directed_links
                )
                self._graphs.put(ident, g)
                self.metrics.inc("ip_graph_builds_total")
                self.metrics.set(
                    "ip_last_graph_build_seconds", time.perf_counter() - t0
                )
        return g

    def search(
        self, lat: float, lon: float, cat: str, rad: float, link: str
    ) -> list[int]:
        graph = self.get_graph(link)
        cat = normalise_category(cat)
        key = (lat, lon, cat, rad, graph.identity, self.s.algorithm_version, self.s.k)
        cached = self.results.get(key)
        if cached is not None:
            self.metrics.inc("ip_cache_hits_total")
            return list(cached)
        self.metrics.inc("ip_cache_misses_total")
        candidates = self.index.within_radius(lat, lon, cat, rad)
        if not candidates:
            self.results.put(key, ())
            return []
        self.metrics.inc("ip_candidates_total", len(candidates))
        source = self.locator.nearest(lat, lon)
        found, st = k_nearest_by_graph(graph, source, candidates, self.s.k)
        self.metrics.inc("ip_nodes_finalized_total", st.finalized)
        self.metrics.inc("ip_edge_relaxations_total", st.relaxations)
        ids = [i for _, i in found]
        self.results.put(key, tuple(ids))
        return ids
