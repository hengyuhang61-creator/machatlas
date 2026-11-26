"""Verify an extracted native archive and recompute its quantitative record."""
import argparse
import csv
import json
from pathlib import Path

from replay import HEIGHT, LENGTH, TIME_STEP, VISCOSITY, digest, initial_state, read_solution, summarize

CASES = {
    "v85-supersonic": ("8.5.0", "supersonic", 2000, 20, 16, False),
    "v85-pressure": ("8.5.0", "pressure", 2000, 20, 16, False),
    "v86-supersonic": ("8.6.0", "supersonic", 2000, 20, 16, True),
    "v86-pressure": ("8.6.0", "pressure", 2000, 20, 16, False),
    "v85-uniform": ("8.5.0", "supersonic", 0, 20, 16, False),
    "v86-uniform": ("8.6.0", "supersonic", 0, 20, 16, True),
    "v86-fine-supersonic": ("8.6.0", "supersonic", 2000, 40, 32, True),
    "v86-fine-pressure": ("8.6.0", "pressure", 2000, 40, 32, False),
}
BINARIES = {
    "8.5.0": {
        "commit": "12eb826f049ef7f67df974dfcb44cf36ee07c0f8",
        "zip": "SU2-v8.5.0-win64-omp.zip",
        "zip_sha256": "4466fe21aedb5e0bad57afd45f829acbdec6ec79fe8c3f8954ddea06a4b4bc11",
        "binary_sha256": "3cb60646b31c08e468441be9f3497601960d4bb31349e6329982bcdeed599248",
    },
    "8.6.0": {
        "commit": "7048fd35f56d4bf52e586429d6746a36a10255f8",
        "zip": "SU2_v8.6.0_win64-omp.zip",
        "zip_sha256": "4bc28b656def415b4d22c8274af2473dd719aa5ebfa6bc1c95c08b1bac26508c",
        "binary_sha256": "01f22d0c9de2e9a5feea666f67adf3957f503d2e14ca6fd998a9a28a11417bf7",
    },
}


def analyze(directory):
    results = {}
    for label, (version, marker, slope, nx, ny, restored) in CASES.items():
        root = directory / label
        recorded = json.loads((root / "result.json").read_text(encoding="utf-8"))
        for name, expected in recorded["sha256"].items():
            if digest(root / name) != expected:
                raise ValueError(f"{label}/{name} hash mismatch")
        if recorded["binary_sha256"] != BINARIES[version]["binary_sha256"]:
            raise ValueError(f"{label}: wrong executable")
        log = (root / "su2.log").read_text(encoding="ascii")
        if f"Release {version}" not in log or "will run for 1 time steps." not in log or "Exit Success" not in log:
            raise ValueError(f"{label}: solver log missing version, one step or success")
        history = root / "history_00001.csv"
        with history.open(encoding="ascii", newline="") as handle:
            rows = list(csv.reader(handle, skipinitialspace=True))
        h = dict(zip((value.strip() for value in rows[0]), rows[1]))
        if len(rows) != 2 or int(h["Time_Iter"]) != 1 or float(h["Time_Step"]) != TIME_STEP:
            raise ValueError(f"{label}: wrong physical step")
        initial = initial_state(nx, ny, slope)
        state = read_solution(root / "result_00001.csv", initial)
        expected_rate = 0.0 if restored else -VISCOSITY * slope / (LENGTH / (2 * nx))
        stations = summarize(state, nx, ny)
        for name, observed in stations.items():
            expected = expected_rate if name == "outlet" else 0.0
            if observed["min_normal_mach"] <= 1.0 or any(
                    abs(observed[key] - expected) > 20 for key in ("min_rate", "max_rate")):
                raise ValueError(f"{label}/{name}: failed the manufactured balance check")
        outlet = [state[nx + (nx + 1) * j][2] for j in range(ny + 1)]
        flow = HEIGHT / ny * sum((left + right) / 2 for left, right in zip(outlet, outlet[1:]))
        results[label] = {
            **recorded, "version": version, "expected_outlet_rate": expected_rate,
            "outlet_mass_flow_kg_s_per_m_span": flow, "qoi": stations,
            "history_sha256": digest(history),
        }
    for a, b in (("v85-supersonic", "v85-pressure"), ("v86-supersonic", "v86-pressure"),
                 ("v85-supersonic", "v86-supersonic"), ("v86-fine-supersonic", "v86-fine-pressure")):
        first, second = (results[label]["sha256"] for label in (a, b))
        if any(first[name] != second[name] for name in ("shear.su2", "initial_00000.csv")):
            raise ValueError(f"{a}/{b} did not share grid and initial state")
        configs = [(directory / label / "case.cfg").read_text(encoding="ascii").splitlines() for label in (a, b)]
        if [line for line in configs[0] if "OUTLET=" not in line] != [
                line for line in configs[1] if "OUTLET=" not in line]:
            raise ValueError(f"{a}/{b} changed more than the outlet marker")
    return {
        "study": "SU2 supersonic outlet viscous traction",
        "upstream_pr": "https://github.com/su2code/SU2/pull/2829",
        "phenomenon": "planar shear at a supersonic outflow",
        "model": "2-D compressible laminar Navier-Stokes, ideal gas, constant viscosity",
        "variable": "first-step transverse momentum density rate, kg/(m^2 s^2)",
        "scope": "One-step manufactured balance; no grid uncertainty or experimental validation.",
        "binaries": BINARIES,
        "cases": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = json.dumps(analyze(args.directory), indent=2) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
    else:
        print(data, end="")
