"""Dijkstra with early termination after K accepted targets."""
from __future__ import annotations

import heapq
from dataclasses import dataclass

from app.core.graph import Graph


@dataclass
class SearchStats:
    finalized: int = 0
    relaxations: int = 0


def k_nearest_by_graph(graph: Graph, source: int, targets: set[int], k: int) -> tuple[list[tuple[float, int]], SearchStats]:
    """Return up to k (distance, id) pairs for `targets`, ascending by road distance.

    One single-source run serves every candidate. Heap entries are (dist, id), so equal
    distances finalize in ascending-ID order -> deterministic results.
    """
    stats = SearchStats()
    result: list[tuple[float, int]] = []
    if k <= 0 or not targets or not graph.has_node(source):
        return result, stats
    dist: dict[int, float] = {source: 0.0}
    done: set[int] = set()
    heap: list[tuple[float, int]] = [(0.0, source)]
    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        stats.finalized += 1
        if u in targets:
            result.append((d, u))
            if len(result) >= k:
                break
        for v, w in graph.neighbours(u):
            stats.relaxations += 1
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return result, stats


def distances_from(graph: Graph, source: int) -> dict[int, float]:
    """Full SSSP (used by tests as an independent oracle)."""
    dist = {source: 0.0}
    heap = [(0.0, source)]
    done = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        for v, w in graph.neighbours(u):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist
