import json
import uuid
from app.config import Settings
from app.core.search_engine import SearchEngine
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from app.api.search import router
import logging
import time
from app.utils.metrics import Metrics

access_log = logging.getLogger("access")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    metrics = Metrics()
    engine = SearchEngine(settings, metrics)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine.startup()
        yield

    app = FastAPI(title="Proximity Search API", lifespan=lifespan)
    app.state.engine = engine
    app.include_router(router)

    @app.middleware("http")
    async def request_log(request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        t = time.perf_counter()
        resp = await call_next(request)
        resp.headers["x-request-id"] = rid
        access_log.info(
            json.dumps(
                {
                    "rid": rid,
                    "method": request.method,
                    "path": request.url.path,
                    "status": resp.status_code,
                    "ms": round((time.perf_counter() - t) * 1000, 2),
                }
            )
        )
        return resp

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready(response: Response):
        if not engine.ready:
            response.status_code = 503
        return {"ready": engine.ready}

    @app.get("/metrics")
    def metrics_endpoint():
        metrics.set("ip_cache_entries", len(engine.results))
        return Response(metrics.render(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()
