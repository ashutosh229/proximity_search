"""Tiny dependency-free metrics registry with Prometheus text exposition."""
from __future__ import annotations

import threading
from collections import defaultdict


class Metrics:
    LATENCY_BUCKETS = (0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)

    def __init__(self):
        self._lock = threading.Lock()
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = {}
        self._lat_counts = [0] * (len(self.LATENCY_BUCKETS) + 1)
        self._lat_sum = 0.0
        self._lat_n = 0

    def inc(self, name: str, v: float = 1.0):
        with self._lock:
            self.counters[name] += v

    def set(self, name: str, v: float):
        with self._lock:
            self.gauges[name] = v

    def observe_latency(self, seconds: float):
        with self._lock:
            self._lat_sum += seconds
            self._lat_n += 1
            for i, b in enumerate(self.LATENCY_BUCKETS):
                if seconds <= b:
                    self._lat_counts[i] += 1
                    return
            self._lat_counts[-1] += 1

    def render(self) -> str:
        with self._lock:
            out = []
            for k, v in sorted(self.counters.items()):
                out += [f"# TYPE {k} counter", f"{k} {v}"]
            for k, v in sorted(self.gauges.items()):
                out += [f"# TYPE {k} gauge", f"{k} {v}"]
            out.append("# TYPE ip_request_latency_seconds histogram")
            cum = 0
            for b, c in zip(self.LATENCY_BUCKETS, self._lat_counts):
                cum += c
                out.append(f'ip_request_latency_seconds_bucket{{le="{b}"}} {cum}')
            cum += self._lat_counts[-1]
            out.append(f'ip_request_latency_seconds_bucket{{le="+Inf"}} {cum}')
            out.append(f"ip_request_latency_seconds_sum {self._lat_sum}")
            out.append(f"ip_request_latency_seconds_count {self._lat_n}")
            return "\n".join(out) + "\n"
