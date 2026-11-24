"""Extract the nearest supported upstream 5 mm PIV column from the original archive."""
import argparse
import csv
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from scipy.io import loadmat


def extract(archive, out, sections):
    with ZipFile(archive) as z:
        member, = [n for n in z.namelist() if n.endswith("h=5mm_ramp_Z=21mm_plane.mat")]
        plane = loadmat(BytesIO(z.read(member)), squeeze_me=True, struct_as_record=False)
    records = []
    targets = (-30, -10, 0, 10, 30, 50) if sections else (-30, -10)
    for target in targets:
        candidates = []
        for grid_x, grid_y, grid_u in zip(plane["X"], plane["Y"], plane["U"]):
            finite = np.isfinite(grid_x) & np.isfinite(grid_y) & np.isfinite(grid_u)
            near_wall = finite & (grid_y >= (30.75 if target < 0 else 0)) & (grid_y <= 44.75)
            if not near_wall.any():
                continue
            xs = np.unique(grid_x[near_wall])
            sample = xs[np.argmin(abs(xs-target))]
            same = near_wall & (grid_x == sample)
            if same.sum() >= 10 and abs(sample-target) <= .25:
                candidates.append((abs(sample-target), sample, grid_y[same], grid_u[same]))
        if not candidates:
            raise ValueError(f"no qualified upstream PIV column at {target}")
        _, x, ys, us = min(candidates, key=lambda a:(a[0], -len(a[2])))
        for y,u in sorted(zip(ys,us)):
            records.append([target, x, y, u])
    with out.open("w", encoding="utf-8",newline="") as stream:
        writer = csv.writer(stream,lineterminator="\n")
        writer.writerow(["target_x_mm","source_x_mm","y_mm","U_m_s"])
        writer.writerows(records)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--sections", action="store_true")
    a = p.parse_args()
    extract(a.archive,a.out,a.sections)
