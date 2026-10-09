import hmac
import math
import time

from fastapi import (
    APIRouter,
    File,
    Form,
    Header,
    HTTPException,
    Request,
    UploadFile,
)
from starlette.concurrency import run_in_threadpool

from app.core.search_engine import LinkageNotFound
from app.models.request import SearchResponse

router = APIRouter()


@router.post("/IP/search/", response_model=SearchResponse)
async def search(
    request: Request,
    lat: float = Form(...),
    long_: float = Form(..., alias="long"),
    cat: str = Form(...),
    rad: float = Form(...),
    link: UploadFile = File(...),
    x_api_key: str | None = Header(None),
):
    engine = request.app.state.engine
    metrics = engine.metrics
    start_time = time.perf_counter()

    metrics.inc("ip_requests_total")

    try:
        expected = engine.s.api_key

        if expected and not hmac.compare_digest(
            (x_api_key or "").encode(),
            expected.encode(),
        ):
            raise HTTPException(status_code=401, detail="invalid api key")

        if not engine.ready:
            raise HTTPException(status_code=503, detail="service not ready")

        for field, value in {
            "lat": lat,
            "long": long_,
            "rad": rad,
        }.items():
            if not math.isfinite(value):
                raise HTTPException(
                    status_code=422,
                    detail=f"{field} must be a finite number",
                )

        if rad < 0:
            raise HTTPException(status_code=422, detail="rad must be >= 0")

        cat = cat.strip()

        if not 1 <= len(cat) <= 64:
            raise HTTPException(
                status_code=422,
                detail="cat must be 1-64 characters",
            )

        raw = await link.read()

        if not raw:
            raise HTTPException(
                status_code=422,
                detail="link file must not be empty",
            )

        linkage_text = raw.decode("utf-8-sig", errors="replace")

        try:
            ids = await run_in_threadpool(
                engine.search,
                lat,
                long_,
                cat,
                rad,
                None,
                linkage_text,
            )
        except LinkageNotFound:
            raise HTTPException(
                status_code=404,
                detail=f"linkage file not found: {link.filename}",
            )

        return {"locations": ids}

    except HTTPException:
        metrics.inc("ip_request_errors_total")
        raise

    finally:
        metrics.observe_latency(time.perf_counter() - start_time)
