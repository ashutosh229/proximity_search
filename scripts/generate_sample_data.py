import argparse
import csv
import random
from pathlib import Path

CATS = ["bank", "hospital", "restaurant", "school", "pharmacy", "store", "park", "cafe"]

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


def c(k: int) -> str:
    return f"{k * step:.6f}"


with (out / "locations.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ID", "Latitude", "Longitude", "Category"])
    for i in range(n):
        for j in range(n):
            w.writerow([i * n + j + 1, c(i), c(j), rnd.choice(CATS)])


lines = []
for i in range(n):
    for j in range(n):
        if j + 1 < n and rnd.random() < a.keep:
            lines.append(f"{c(j)} {c(i)} {c(j + 1)} {c(i)}")
        if i + 1 < n and rnd.random() < a.keep:
            lines.append(f"{c(j)} {c(i)} {c(j)} {c(i + 1)}")
rnd.shuffle(lines)
(out / "link.txt").write_text("\n".join(lines) + "\n")
print(f"wrote {n*n} locations and {len(lines)} links to {out}/")
