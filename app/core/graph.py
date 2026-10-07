from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Graph:
    """Sparse adjacency-list graph. adj[u] = [(v, weight), ...]."""

    adj: dict[int, list[tuple[int, float]]] = field(default_factory=dict)
    identity: str = ""
    stats: dict[str, int] = field(default_factory=dict)

    def neighbours(self, u: int):
        return self.adj.get(u, ())

    def has_node(self, u: int) -> bool:
        return u in self.adj

    @property
    def edge_count(self) -> int:
        return sum(len(v) for v in self.adj.values())
