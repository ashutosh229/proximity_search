from __future__ import annotations
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    multiprocess,
)
import os
import threading


class Metrics:
    LATENCY_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)

    def __init__(self):
        self._lock = threading.Lock()
        self.registry = CollectorRegistry()
        self._c: dict[str, Counter] = {}
        self._g: dict[str, Gauge] = {}
        self._lat = Histogram(
            "ip_request_latency_seconds",
            "request latency",
            buckets=self.LATENCY_BUCKETS,
            registry=self.registry,
        )

    def inc(self, name: str, v: float = 1.0):
        c = self._c.get(name)
        if c is None:
            with self._lock:
                c = self._c.get(name)
                if c is None:
                    c = self._c[name] = Counter(
                        name.removesuffix("_total"), name, registry=self.registry
                    )
        c.inc(v)

    def set(self, name: str, v: float):
        g = self._g.get(name)
        if g is None:
            with self._lock:
                g = self._g.get(name)
                if g is None:
                    g = self._g[name] = Gauge(
                        name, name, registry=self.registry, multiprocess_mode="max"
                    )
        g.set(v)

    def observe_latency(self, seconds: float):
        self._lat.observe(seconds)

    def render(self) -> bytes:
        if os.getenv("PROMETHEUS_MULTIPROC_DIR"):
            reg = CollectorRegistry()
            multiprocess.MultiProcessCollector(reg)
            return generate_latest(reg)
        return generate_latest(self.registry)
