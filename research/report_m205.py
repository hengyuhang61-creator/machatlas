"""Summarize the realized Mach 2.05 matrix and compare on complete station support."""
import argparse
import json
from pathlib import Path


def f(number, places=3):
    return "—" if number is None else f"{number:.{places}f}"


def report(data):
    rows = data["ramp"]
    table = ["## Mach 2.05 realized matrix",
             "", "| Ramp / grid / model | Cells | Iterations | Max upstream MAE [%] | Mass error [%] | Separation / reattachment [mm] | Max edge drift [mm] | Disposition |",
             "|---|---:|---:|---:|---:|---|---:|---|"]
    for row in rows:
        roots = row.get("wallCrossings", [])
        crossings = " / ".join(f(1e3*v["x_m"],2) for v in roots) if roots else "No crossing reported"
        table.append(f"| {row['label']} | {row.get('cells','—')} | {row.get('totalIterations','—')} | "
                     f"{f(row.get('upstream_max_mae_pct'))} | {f(row.get('mass'),5)} | {crossings} | "
                     f"{f(row.get('edgeDriftMm'))} | {row['state']} |")
    table += ["","Window for the bottom-wall crossings is x = 0–65 mm. The study publishes Cp at x = 30 and 50 mm "
               "and near-wall y+ metrics in the machine-readable evidence.","",
               "### Per-station model preference on complete support","",
               "| Ramp | Grid | Comparable stations | Lower MAE with SA | Lower MAE with SST |",
               "|---|---|---|---|---|"]
    for h in (3,5):
        for g in range(3):
            pair = [next(row for row in rows if row["id"] == f"m205-{h}mm-l{g}-{m}") for m in ("sa","sst")]
            if not all(row["state"] == "Numerical and inlet checks met" for row in pair):
                table.append(f"| {h} mm | L{g+1} | — | — | — |")
                continue
            tables = [{p["x_mm"]:p for p in row["sampled_velocity_profiles"]} for row in pair]
            wins = [[],[]]
            considered = []
            for x,p in tables[0].items():
                q = tables[1].get(x)
                if not q or not p["full_domain_eligible"] or not q["full_domain_eligible"]:
                    continue
                if p["reference_samples"] != q["reference_samples"] or p["x_evaluated_mm"] != q["x_evaluated_mm"]:
                    raise ValueError(f"unequal reference support at x={x}")
                considered.append(x)
                a,b = p["overlap_mae"],q["overlap_mae"]
                if abs(a-b) > 1e-10:
                    wins[int(a>b)].append(x)
            stations = lambda group: ", ".join(format(x,"g") for x in group) or "—"
            table.append(f"| {h} mm | L{g+1} | {stations(considered)} | {stations(wins[0])} | {stations(wins[1])} |")
    return "\n".join(table + ["","Stations are nominal axial x in mm. Where available the solver is evaluated at the actual archived PIV x. "
                             "The rankings compare supported axial velocity points within one ramp, station and grid. "
                             "Differences in station sets and sample support prevent pooling rankings across ramp heights. "
                             "The two-dimensional calculations do not resolve three-dimensional side-wall effects or experimental pointwise uncertainty."])+"\n"


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("summary",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    a.out.write_text(report(json.loads(a.summary.read_text(encoding="utf-8"))),encoding="utf-8")
