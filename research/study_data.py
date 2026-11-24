"""Build the study table from actual completed run artifacts in a study directory."""
import argparse
import json
from pathlib import Path

import numpy as np

from audit_run import field, wall, zeroes
from plot_native import shock_locations


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def bubble(metrics):
    roots = metrics["wall_zero_crossings"]
    if len(roots) != 2 or [r["kind"] for r in roots] != ["separation", "reattachment"]:
        return None
    return [1e3 * r["x_m"] for r in roots]


def outcome(earlier, later, isothermal=False):
    a, b = bubble(earlier), bubble(later)
    d = max(abs(x-y) for x,y in zip(a,b)) if a and b else None
    failed = []
    if not all(row["valid_primitives"] for row in (earlier, later)):
        failed.append("primitive field")
    if max(row["native_mass_pct"] for row in (earlier, later)) > .1:
        failed.append("mass")
    if not isothermal and max(row["advective_energy_pct"] for row in (earlier, later)) > .5:
        failed.append("advective energy screen")
    if d is None or d > 1:
        failed.append("Cf zero crossing drift")
    if later["done_iterations"] < 100 or later["CD_relative_drift_last_100"] > .01:
        failed.append("iteration interval or drag drift")
    return d, failed


def study(root, plan):
    runs = {}
    for path in sorted((root / "runs").glob("*/execution.json")):
        receipt = read(path)
        if (path.parent / "metrics.json").exists():
            receipt["metrics"] = read(path.parent / "metrics.json")
        runs[path.parent.name] = receipt

    grids = {p.parent.name: read(p) for p in sorted((root / "grids").glob("*/mesh.json"))}
    for label, grid in grids.items():
        mesh = root / "grids" / label / "mesh.su2"
        for line in mesh.read_text().splitlines():
            if line.startswith("NPOIN="):
                grid["exported_flow_nodes"] = int(line.split("=")[1])
                break

    cases = []
    for spec in plan:
        earlier, later = (runs[name]["metrics"] for name in spec["compare"])
        isothermal = runs[spec["compare"][1]]["wall"] == "isothermal"
        drift, failures = outcome(earlier, later, isothermal)
        final = spec["compare"][1]
        data = field(root / "runs" / final / "flow.vtu")
        x, cf, cp, yp = wall(data).T
        traces = (x >= .305) & (x <= .400)
        cases.append({**spec, "edge_drift_mm": drift,
                      "checks": "HOLD" if failures else "CHECKS_MET", "failed_checks": failures,
                      "x_sep_reatt_mm": bubble(later),
                      "cp_at_x_360mm": float(np.interp(.360, x, cp)),
                      "shock_probe": shock_locations(data),
                      "wall_trace_x_cf_cp": np.column_stack([x[traces],cf[traces],cp[traces]]).tolist()})

    return {"grids": grids, "runs": runs, "cases": cases,
            "status": "SCIENTIFIC_VALIDATION_HOLD"}


def parse_reference(path):
    a = np.loadtxt(path)
    if not np.all(np.diff(a[:, 0]) > 0):
        raise ValueError(f"unordered reference x: {path.name}")
    result = zeroes(a[:,0],a[:,1])
    return {"count":len(a), "roots":result, "first_x_m":a[0,0], "last_x_m":a[-1,0]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study_dir", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    report = study(args.study_dir, read(args.plan))
    report["references"] = {p.name: parse_reference(p)
                            for p in sorted((args.study_dir / "upstream").glob("MOSE-*-reference-*.dat"))}
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
