import hmac
import math
import time

from fastapi import APIRouter, Header, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.core.search_engine import LinkageNotFound
from app.models.request import SearchResponse

router = APIRouter()


async def _collect(request: Request) -> dict:
    p: dict = dict(request.query_params)
    if request.method == "POST":
        ctype = request.headers.get("content-type", "").lower()
        if "json" in ctype:
            try:
                body = await request.json()
            except ValueError:
                raise HTTPException(422, "invalid JSON body")
            if not isinstance(body, dict):
                raise HTTPException(422, "JSON body must be an object")
            p.update(body)
        elif "form" in ctype:
            form = await request.form()
            for k, v in form.multi_items():
                p[k] = v
    return p


def _num(p: dict, *names: str) -> float:
    for n in names:
        if n in p:
            try:
                v = float(p[n])
            except (TypeError, ValueError):
                raise HTTPException(422, f"{n} must be a number")
            if not math.isfinite(v):
                raise HTTPException(422, "lat, long and rad must be finite numbers")
            return v
    raise HTTPException(422, f"missing field: {names[0]}")


async def _link(p: dict) -> tuple[str | None, str | None]:
    v = p.get("link")
    if v is None:
        raise HTTPException(422, "missing field: link")
    if hasattr(v, "read"):
        raw = await v.read()
        return None, raw.decode("utf-8-sig", errors="replace")
    v = str(v)
    if "\n" in v or "\r" in v or " " in v.strip():
        return None, v
    if not (1 <= len(v) <= 256):
        raise HTTPException(422, "link must be 1-256 characters")
    return v, None


@router.api_route("/IP/search/", methods=["GET", "POST"], response_model=SearchResponse)
@router.api_route(
    "/IP/search",
    methods=["GET", "POST"],
    response_model=SearchResponse,
    include_in_schema=False,
)
async def search(request: Request, x_api_key: str | None = Header(None)):
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
        p = await _collect(request)
        lat = _num(p, "lat")
        lon = _num(p, "long", "lon")
        rad = _num(p, "rad")
        if rad < 0:
            raise HTTPException(422, "rad must be >= 0")
        cat = str(p.get("cat", "")).strip()
        if not (1 <= len(cat) <= 64):
            raise HTTPException(422, "cat must be 1-64 characters")
        name, text = await _link(p)
        try:
            ids = await run_in_threadpool(engine.search, lat, lon, cat, rad, name, text)
        except LinkageNotFound:
            raise HTTPException(404, f"linkage file not found: {name}")
        return {"locations": ids}
    except HTTPException:
        m.inc("ip_request_errors_total")
        raise
    finally:
        m.observe_latency(time.perf_counter() - t0)
