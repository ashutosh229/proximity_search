import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from app.api.search import router
from app.config import Settings
from app.core.search_engine import SearchEngine
from app.utils.metrics import Metrics


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    metrics = Metrics()
    engine = SearchEngine(settings, metrics)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine.startup()
        yield

    app = FastAPI(title="Proximity Search API", lifespan=lifespan)
    app.state.engine = engine
    app.include_router(router)

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
