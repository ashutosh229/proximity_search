import time
from app.core.graph import Graph
from app.core.shortest_path import k_nearest_by_graph


def test_dijkstra_100x100_grid_is_fast():
    n = 100
    adj = {i: [] for i in range(n * n)}
    for i in range(n):
        for j in range(n):
            u = i * n + j
            for v in ((u + 1) if j + 1 < n else None, (u + n) if i + 1 < n else None):
                if v is not None:
                    adj[u].append((v, 1.0))
                    adj[v].append((u, 1.0))
    g = Graph(adj=adj)
    t = time.perf_counter()
    res, _ = k_nearest_by_graph(g, 0, set(range(n * n)), 10)
    assert len(res) == 10
    assert time.perf_counter() - t < 0.5
