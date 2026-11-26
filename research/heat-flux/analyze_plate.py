"""Read the SU2 surface VTK and compare a 2-D Neumann slab with its analytic slope."""
import argparse
import csv
import hashlib
import json
import math
import re
import struct
from pathlib import Path
from statistics import mean


def vtk_heat_flux(path):
    raw = path.read_bytes()
    points = re.search(rb"POINTS (\d+) float\r?\n", raw)
    field = re.search(rb"SCALARS Heat_Flux float 1\r?\nLOOKUP_TABLE default\r?\n", raw)
    if points is None or field is None:
        raise ValueError(f"coordinates or Heat_Flux missing from {path}")
    count = int(points[1])
    coords = struct.iter_unpack(">fff", raw[points.end():points.end() + 12 * count])
    flux = struct.unpack_from(f">{count}f", raw, field.end())
    return [(x, y, q) for (x, y, _), q in zip(coords, flux)]


def read_csv(path):
    with path.open(newline="", encoding="ascii") as stream:
        reader = csv.reader(stream, skipinitialspace=True)
        keys = [key.strip() for key in next(reader)]
        return [{key: float(value) for key, value in zip(keys, row)} for row in reader]


def summary(directory):
    wall = vtk_heat_flux(directory / "surface.vtk")
    rows = read_csv(directory / "restart.csv")
    target = float(re.search(r"MARKER_HEATFLUX= \( bottom, ([^,]+)", (directory / "slab.cfg").read_text())[1])
    interior_x = lambda x: 1e-7 < x < 0.01 - 1e-7
    bottom = [q for x, y, q in wall if abs(y) < 1e-7 and interior_x(x)]
    top = [q for x, y, q in wall if abs(y - 0.01) < 1e-7 and interior_x(x)]
    vertical = [q for _, y, q in wall if interior_x(y)]
    temp = {(row["x"], row["y"]): row["Temperature"] for row in rows}
    dy = min(y for _, y in temp if y > 0.0)
    x0 = sorted({x for x, _ in temp})[int(math.sqrt(len(temp))) // 2]
    target_gradient = -target / 0.6
    measured_gradient = (temp[x0, 0.01] - temp[x0, 0.0]) / 0.01
    last = read_csv(directory / "history.csv")[-1]
    out = {
        "nodes": len(rows), "temperature_residual_log10": last["rms[T]"],
        "bottom": [min(bottom), mean(bottom), max(bottom)],
        "top": [min(top), mean(top), max(top)],
        "vertical_max_abs": max(map(abs, vertical)),
        "wall_flux_target_bottom": -target,
        "bottom_normal_first_interval_flux": (temp[x0, dy] - temp[x0, 0.0]) / dy * 0.6,
        "analytic_temperature_gradient": target_gradient,
        "temperature_gradient": measured_gradient,
        "native_hf": last["HF"], "native_max_hf": last["maxHF"],
        "max_speed": max(math.hypot(row["Velocity_x"], row["Velocity_y"]) for row in rows),
        "configuration_sha256": hashlib.sha256((directory / "slab.cfg").read_bytes()).hexdigest(),
        "mesh_sha256": hashlib.sha256((directory / "slab.su2").read_bytes()).hexdigest(),
    }
    return out, temp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="contains matrix-pre-* and matrix-post-* runs")
    args = parser.parse_args()
    comparisons = {}
    for name in ("early", "mid", "tail", "fine-early", "fine-tail", "adiabatic"):
        before, tb = summary(args.directory / f"matrix-pre-{name}")
        after, ta = summary(args.directory / f"matrix-post-{name}")
        assert before["configuration_sha256"] == after["configuration_sha256"]
        assert before["mesh_sha256"] == after["mesh_sha256"]
        assert tb.keys() == ta.keys()
        delta_t = max(abs(tb[key] - ta[key]) for key in tb)
        assert after["bottom"][0] == after["bottom"][2] == after["wall_flux_target_bottom"]
        assert after["top"][0] == after["top"][2] == -after["wall_flux_target_bottom"]
        assert after["vertical_max_abs"] == 0
        comparisons[name] = {"pre": before, "post": after, "max_abs_delta_T_K": delta_t}
    assert comparisons["early"]["pre"]["bottom"][1] != -1000
    assert comparisons["adiabatic"]["pre"]["bottom"] == [0, 0, 0]
    print(json.dumps(comparisons, indent=2))


if __name__ == "__main__":
    main()
