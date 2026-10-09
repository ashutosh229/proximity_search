"""Environment-driven configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in os.getenv(name, "").split(",") if x.strip())


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "data")))
    locations_file: str = field(
        default_factory=lambda: os.getenv("LOCATIONS_FILE", "locations.csv")
    )
    default_link: str | None = field(
        default_factory=lambda: os.getenv("DEFAULT_LINK") or None
    )
    preload_links: tuple[str, ...] = field(
        default_factory=lambda: _csv("PRELOAD_LINKS")
    )
    # "geographic": weight = euclidean length of the road; "grid": every link costs 1.
    edge_weight_mode: str = field(
        default_factory=lambda: os.getenv("EDGE_WEIGHT_MODE", "geographic")
    )
    # Linkage semantics are unconfirmed -> configurable. Undirected is the usual road reading.
    directed_links: bool = field(default_factory=lambda: _bool("DIRECTED_LINKS", False))
    k: int = field(default_factory=lambda: int(os.getenv("TOP_K", "10")))
    cache_size: int = field(
        default_factory=lambda: int(os.getenv("CACHE_SIZE", "1024"))
    )
    graph_cache_size: int = field(
        default_factory=lambda: int(os.getenv("GRAPH_CACHE_SIZE", "4"))
    )
    use_kdtree: bool = field(default_factory=lambda: _bool("USE_KDTREE", True))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    api_key: str | None = field(default_factory=lambda: os.getenv("API_KEY") or None)
    redis_url: str | None = field(
        default_factory=lambda: os.getenv("REDIS_URL") or None
    )
    redis_ttl: int = field(default_factory=lambda: int(os.getenv("REDIS_TTL", "3600")))
    algorithm_version: str = "dijkstra-v1"

    def __post_init__(self):
        if self.edge_weight_mode not in {"geographic", "grid"}:
            raise ValueError("EDGE_WEIGHT_MODE must be 'geographic' or 'grid'")
