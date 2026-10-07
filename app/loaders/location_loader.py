"""Load and validate locations.csv: columns [ID, Latitude, Longitude, Category]."""
from __future__ import annotations

import csv
import math
from pathlib import Path

from app.models.location import Location


class DatasetError(ValueError):
    pass


def normalise_category(c: str) -> str:
    return c.strip().casefold()


def load_locations(path: Path) -> dict[int, Location]:
    if not path.is_file():
        raise DatasetError(f"locations file not found: {path}")
    out: dict[int, Location] = {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise DatasetError("locations file is empty")
        cols = [h.strip().casefold() for h in header]
        try:
            i_id, i_lat, i_lon, i_cat = (cols.index(n) for n in ("id", "latitude", "longitude", "category"))
        except ValueError as e:
            raise DatasetError(f"locations header must contain ID, Latitude, Longitude, Category; got {header}") from e
        for n, row in enumerate(reader, start=2):
            if not row or all(not c.strip() for c in row):
                continue
            try:
                lid = int(row[i_id])
                lat = float(row[i_lat])
                lon = float(row[i_lon])
                cat = normalise_category(row[i_cat])
            except (ValueError, IndexError) as e:
                raise DatasetError(f"malformed row at line {n}: {row}") from e
            if not (math.isfinite(lat) and math.isfinite(lon)):
                raise DatasetError(f"non-finite coordinate at line {n}")
            if lid in out:
                raise DatasetError(f"duplicate ID {lid} at line {n}")
            out[lid] = Location(lid, lat, lon, cat)
    if not out:
        raise DatasetError("no locations loaded")
    return out
