ROWS = [(i, 0.0, i / 100, "bank") for i in range(12)] + [(100, 0.0, 0.0, "hospital")]
CHAIN = "\n".join(f"{i} {i+1}" for i in range(11)) + "\n"
COORD_CHAIN = (
    "\n".join(f"{i/100:.6f} 0.000000 {(i+1)/100:.6f} 0.000000" for i in range(11))
    + "\n"
)


def post(c, **kw):
    data = dict(lat=0.0, long=0.0, cat="bank", rad=1.0, link="chain.txt")
    data.update(kw)
    return c.post("/IP/search/", data=data)


def test_valid_search_returns_ten_in_graph_order(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN}) as c:
        r = post(c)
        assert r.status_code == 200
        assert r.json() == {"locations": list(range(10))}


def test_coordinate_format_end_to_end(make_client):
    with make_client(ROWS, {"link.txt": COORD_CHAIN}) as c:
        r = post(c, link="link.txt")
        assert r.status_code == 200
        assert r.json() == {"locations": list(range(10))}


def test_coordinate_and_id_formats_give_same_result(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN, "link.txt": COORD_CHAIN}) as c:
        assert post(c, link="chain.txt").json() == post(c, link="link.txt").json()


def test_category_and_radius_enforced(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN}) as c:
        assert post(c, cat="hospital").json()["locations"] in (
            [],
            [100],
        )
        ids = post(c, rad=0.05).json()["locations"]
        assert all(i <= 5 for i in ids)
        ids = post(c, cat="BANK").json()["locations"]
        assert len(ids) == 10


def test_ranking_uses_road_distance_not_euclid(make_client):
    rows = [
        (0, 0.0, 0.0, "bank"),
        (1, 0.0, 0.01, "bank"),
        (2, 0.0, 0.02, "bank"),
        (3, 0.5, 0.0, "x"),
        (4, 0.5, 0.5, "x"),
    ] + [(10 + i, 0.9, i / 100, "bank") for i in range(7)]
    links = "0 2\n0 3\n3 4\n4 1\n" + "\n".join(f"2 {10+i}" for i in range(7)) + "\n"
    with make_client(rows, {"l.txt": links}) as c:
        ids = post(c, link="l.txt", rad=2.0).json()["locations"]
        assert ids.index(2) < ids.index(1)
        assert ids[0] == 0 and ids[1] == 2


def test_changing_topology_changes_result(make_client):
    rows = [(i, 0.0, i / 100, "bank") for i in range(12)]
    forward = "\n".join(f"{i} {i+1}" for i in range(11)) + "\n"
    broken = "\n".join(f"{i} {i+1}" for i in range(5)) + "\n"
    with make_client(rows, {"a.txt": forward, "b.txt": broken}) as c:
        a = post(c, link="a.txt").json()["locations"]
        b = post(c, link="b.txt").json()["locations"]
        assert len(a) == 10 and len(b) == 6 and a != b


def test_grid_mode_unit_weights(make_client):
    rows = [(0, 0, 0, "bank"), (1, 0, 0.9, "bank"), (2, 0, 0.1, "bank")]
    with make_client(rows, {"l.txt": "0 1\n0 2\n"}, edge_weight_mode="grid") as c:
        assert post(c, link="l.txt").json()["locations"] == [0, 1, 2]
    with make_client(rows, {"l.txt": "0 1\n0 2\n"}, edge_weight_mode="geographic") as c:
        assert post(c, link="l.txt").json()["locations"] == [0, 2, 1]


def test_validation_and_errors(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN}) as c:
        assert post(c, link="missing.txt").status_code == 404
        assert post(c, link="../etc/passwd").status_code == 404
        assert post(c, rad=-1).status_code == 422
        assert post(c, lat="abc").status_code == 422
        assert post(c, rad="nan").status_code == 422
        assert c.post("/IP/search/", data={"lat": 0}).status_code == 422


def test_nul_byte_link_is_404(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN}) as c:
        assert post(c, link="a\x00b").status_code == 404


def test_no_candidates_returns_empty(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN}) as c:
        assert post(c, cat="nonexistent").json() == {"locations": []}


def test_api_key_enforced(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN}, api_key="secret") as c:
        assert post(c).status_code == 401
        data = dict(lat=0.0, long=0.0, cat="bank", rad=1.0, link="chain.txt")
        assert (
            c.post("/IP/search/", data=data, headers={"x-api-key": "wrong"}).status_code
            == 401
        )
        assert (
            c.post(
                "/IP/search/", data=data, headers={"x-api-key": "secret"}
            ).status_code
            == 200
        )


def test_cache_and_ops_endpoints(make_client):
    with make_client(ROWS, {"chain.txt": CHAIN}) as c:
        assert c.get("/health").json() == {"status": "ok"}
        assert c.get("/ready").status_code == 200
        a = post(c).json()
        b = post(c).json()
        assert a == b
        m = c.get("/metrics").text
        assert "ip_cache_hits_total 1.0" in m and "ip_requests_total 2.0" in m
