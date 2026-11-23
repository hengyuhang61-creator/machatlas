"""Build the atlas's interactive tables from SWBLI Physics Bench replay outputs."""
import argparse
import csv
from itertools import groupby
import json
from pathlib import Path


def rows(results, path):
    with (results / path).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def ramp(results):
    records = rows(results, "m205/station_metrics.csv")
    stations = {}
    for x, group in groupby(records, key=lambda row: row["x_mm"]):
        models = {row["model"]: row for row in group}
        sa, sst = models["SA"], models["SST"]
        if sa["n"] != sst["n"]:
            raise ValueError(f"Unequal PIV support at x={x}")
        stations[x] = {
            "n": int(sa["n"]),
            "mae": [float(row["mae_u"]) for row in (sa, sst)],
            "absBias": [abs(float(row["bias_u"])) for row in (sa, sst)],
        }
    if len(stations) != 10:
        raise ValueError("Expected ten ramp stations")
    return stations


def cone(results):
    records = rows(results, "m25/windows.csv")
    bands = {
        row["y_a"]: [abs(float(row["b_sa"])), abs(float(row["b_st"]))]
        for row in records
        if float(row["station"]) == 482.60 and row["solver"] == "FUN3D" and float(row["width"]) == 3
    }
    if not {"1.5", "12.0"} <= bands.keys():
        raise ValueError("Expected the documented near and outer windows")
    return bands


def hmve(results):
    records = rows(results, "hmve/band_means.csv")
    stations = {}
    for x, group in groupby(records, key=lambda row: row["nominal_x_in"]):
        stations[x] = {
            f'{row["y_lo_mm"]}-{row["y_hi_mm"]}': [
                float(row["low_re_band_mean"]), float(row["high_re_band_mean"])
            ]
            for row in group
        }
    if len(stations) != 21 or any(len(bands) != 2 for bands in stations.values()):
        raise ValueError("Expected two bands at each of 21 stations")
    return stations


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="SWBLI Physics Bench replay output directory")
    parser.add_argument("--out", type=Path, default=Path("site/cases.json"))
    args = parser.parse_args()
    data = {"ramp": ramp(args.results), "cone": cone(args.results), "hmve": hmve(args.results)}
    args.out.write_bytes((json.dumps(data, indent=2, allow_nan=False) + "\n").encode())
