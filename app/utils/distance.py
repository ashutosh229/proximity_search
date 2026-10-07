import math


def euclidean(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.hypot(lat1 - lat2, lon1 - lon2)


def edge_weight(mode: str, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if mode == "grid":
        return 1.0
    if mode == "geographic":
        return euclidean(lat1, lon1, lat2, lon2)
    raise ValueError(f"unknown edge weight mode: {mode}")
