import pytest
from app.core.graph import Graph
from app.core.shortest_path import distances_from, k_nearest_by_graph
from app.core.spatial_index import NodeLocator, SpatialIndex, nearest_node
from app.loaders.linkage_loader import load_graph
from app.loaders.location_loader import DatasetError, load_locations
from app.models.location import Location
from app.utils.distance import edge_weight, euclidean


def L(i, lat, lon, cat="bank"):
    return Location(i, lat, lon, cat)


def test_euclidean_and_weights():
    assert euclidean(0, 0, 3, 4) == 5
    assert edge_weight("geographic", 0, 0, 3, 4) == 5
    assert edge_weight("grid", 0, 0, 3, 4) == 1
    with pytest.raises(ValueError):
        edge_weight("nope", 0, 0, 1, 1)


def test_linkage_policies(tmp_path):
    locs = {i: L(i, i * 0.1, 0) for i in range(4)}
    f = tmp_path / "l.txt"
    f.write_text("0 1\n1 0\nbad line here\n2 2\n1 99\n\n# c\n1 2\nx y\n")
    g = load_graph(f, locs, "grid", directed=False)
    assert g.stats["malformed"] == 2
    assert g.stats["self_loops"] == 1
    assert g.stats["unknown_node"] == 1
    assert g.stats["duplicates"] >= 2
    assert sorted(v for v, _ in g.adj[1]) == [0, 2]
    assert g.adj[3] == []


def test_coordinate_linkage_format_is_lon_lat(tmp_path):
    locs = {
        1: L(1, 0.0, 0.0),
        2: L(2, 0.0, 0.010101),
        3: L(3, 0.010101, 0.0),
    }
    f = tmp_path / "l.txt"
    f.write_text(
        "0.000000 0.000000 0.010101 0.000000\n"
        "0.000000 0.000000 0.000000 0.010101\n"
        "0.500000 0.500000 0.000000 0.000000\n"
        "0.000000 nan 0.010101 0.000000\n"
    )
    g = load_graph(f, locs, "grid", directed=False)
    assert sorted(v for v, _ in g.adj[1]) == [2, 3]
    assert g.stats["unknown_node"] == 1
    assert g.stats["malformed"] == 1
    assert g.stats["edges"] == 4


def test_directed_links(tmp_path):
    locs = {0: L(0, 0, 0), 1: L(1, 0, 1)}
    f = tmp_path / "l.txt"
    f.write_text("0 1\n")
    g = load_graph(f, locs, "grid", directed=True)
    assert g.adj[0] == [(1, 1.0)] and g.adj[1] == []


def test_dijkstra_matches_oracle_and_stops_early():
    adj = {i: [] for i in range(5)}

    def add(a, b, w):
        adj[a].append((b, w))
        adj[b].append((a, w))

    for i in range(4):
        add(i, i + 1, 1.0)
    add(0, 4, 10.0)
    g = Graph(adj=adj)
    res, st = k_nearest_by_graph(g, 0, {1, 2, 3, 4}, 2)
    assert res == [(1.0, 1), (2.0, 2)]
    assert st.finalized == 3
    d = distances_from(g, 0)
    assert d[4] == 4.0
    res, _ = k_nearest_by_graph(g, 0, {4}, 5)
    assert res == [(4.0, 4)]


def test_tie_break_by_id():
    adj = {0: [(2, 1.0), (1, 1.0)], 1: [(0, 1.0)], 2: [(0, 1.0)]}
    res, _ = k_nearest_by_graph(Graph(adj=adj), 0, {1, 2}, 2)
    assert [i for _, i in res] == [1, 2]


def test_unreachable_targets_not_returned():
    g = Graph(adj={0: [], 1: []})
    res, _ = k_nearest_by_graph(g, 0, {1}, 3)
    assert res == []


def test_spatial_index_matches_bruteforce_and_inclusive_boundary():
    locs = {
        i: L(i, (i % 10) / 10, (i // 10) / 10, "a" if i % 2 else "b")
        for i in range(100)
    }
    idx = SpatialIndex(locs)
    for rad in (0.0, 0.1, 0.25, 0.5):
        assert idx.within_radius(0.3, 0.3, "a", rad) == idx.within_radius(
            0.3, 0.3, "a", rad, brute=True
        )
    assert {23, 43} <= idx.within_radius(0.3, 0.3, "a", 0.1)
    assert idx.within_radius(0.3, 0.3, "zzz", 1) == set()


def test_nearest_node_tie_lowest_id():
    locs = {5: L(5, 0, 1), 2: L(2, 0, -1)}
    assert nearest_node(locs, 0, 0) == 2


def test_node_locator_matches_reference_and_ties():
    locs = {5: L(5, 0, 1), 2: L(2, 0, -1), 9: L(9, 3, 3)}
    nl = NodeLocator(locs)
    assert nl.nearest(0, 0) == 2
    assert nl.nearest(3, 3.1) == 9
    grid = {i: L(i, (i % 10) / 10, (i // 10) / 10) for i in range(100)}
    nl = NodeLocator(grid)
    for q in [(0.05, 0.05), (0.33, 0.71), (0.5, 0.5), (2, 2), (-1, 0.2)]:
        assert nl.nearest(*q) == nearest_node(grid, *q)


def test_location_loader_errors(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("ID,Latitude,Longitude,Category\n1,0,0,Bank\n1,0,0,Bank\n")
    with pytest.raises(DatasetError):
        load_locations(p)
    p.write_text("ID,Latitude,Longitude,Category\n1,0,0, Bank \n")
    assert load_locations(p)[1].category == "bank"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(DatasetError):
        load_locations(p)
