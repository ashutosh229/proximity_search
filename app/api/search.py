import hmac
import math
from app.models.request import SearchResponse
import time
from fastapi import APIRouter, Form, Header, HTTPException, Request
from app.core.search_engine import LinkageNotFound

router = APIRouter()


@router.post("/IP/search/", response_model=SearchResponse)
def search(
    request: Request,
    lat: float = Form(...),
    long: float = Form(...),
    cat: str = Form(..., min_length=1, max_length=64),
    rad: float = Form(...),
    link: str = Form(..., min_length=1, max_length=128),
    x_api_key: str | None = Header(None),
):
    engine = request.app.state.engine
    m = engine.metrics
    t0 = time.perf_counter()
    m.inc("ip_requests_total")
    try:
        expected = engine.s.api_key
        if expected and not hmac.compare_digest(
            (x_api_key or "").encode(), expected.encode()
        ):
            raise HTTPException(401, "invalid api key")
        if not engine.ready:
            raise HTTPException(503, "service not ready")
        if not all(math.isfinite(x) for x in (lat, long, rad)):
            raise HTTPException(422, "lat, long and rad must be finite numbers")
        if rad < 0:
            raise HTTPException(422, "rad must be >= 0")
        try:
            ids = engine.search(lat, long, cat, rad, link)
        except LinkageNotFound:
            raise HTTPException(404, f"linkage file not found: {link}")
        return {"locations": ids}
    except HTTPException:
        m.inc("ip_request_errors_total")
        raise
    finally:
        m.observe_latency(time.perf_counter() - t0)
