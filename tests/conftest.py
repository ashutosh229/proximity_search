import csv
import pytest
from app.config import Settings
from fastapi.testclient import TestClient
from app.main import create_app
from pathlib import Path


def write_locations(path: Path, rows):
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Latitude", "Longitude", "Category"])
        w.writerows(rows)


@pytest.fixture
def make_client(tmp_path):
    def _make(rows, links: dict[str, str], **kw):
        write_locations(tmp_path / "locations.csv", rows)
        for name, text in links.items():
            (tmp_path / name).write_text(text)
        app = create_app(Settings(data_dir=tmp_path, **kw))
        return TestClient(app)

    return _make
