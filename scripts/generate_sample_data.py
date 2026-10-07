"""Generate a synthetic locations.csv (100x100 grid) and a links.txt for local testing.

The real linkage file was not supplied, so this is ONLY a stand-in. Links are a random
sparse subset of grid-neighbour pairs (so some direct roads are missing, as the spec says).
"""
import argparse
import csv
import random
from pathlib import Path

CATS = ["bank", "hospital", "restaurant", "school", "pharmacy"]

p = argparse.ArgumentParser()
p.add_argument("--out", default="data")
p.add_argument("--n", type=int, default=100, help="grid side length")
p.add_argument("--keep", type=float, default=0.8, help="fraction of grid links kept")
p.add_argument("--seed", type=int, default=7)
a = p.parse_args()

rnd = random.Random(a.seed)
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
n = a.n
step = 1.0 / (n - 1)
with (out / "locations.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ID", "Latitude", "Longitude", "Category"])
    for i in range(n):
        for j in range(n):
            w.writerow([i * n + j, round(i * step, 6), round(j * step, 6), rnd.choice(CATS)])
with (out / "links.txt").open("w") as f:
    for i in range(n):
        for j in range(n):
            u = i * n + j
            if j + 1 < n and rnd.random() < a.keep:
                f.write(f"{u} {u + 1}\n")
            if i + 1 < n and rnd.random() < a.keep:
                f.write(f"{u} {u + n}\n")
print(f"wrote {n*n} locations and links to {out}/")
