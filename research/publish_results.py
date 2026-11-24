"""Make the web summary directly from preserved SU2 receipts."""
import argparse
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def profile_report(directory):
    full = directory / "piv-full.json"
    return read(full if full.exists() else directory / "piv.json")


def inspect_ramp(root, height, level, model):
    name = f"m205-{height}mm-l{level}-{model}"
    grid = root / "grids" / name / "mesh.json"
    original = f"{name}-1800"
    terminal = f"{name}-2100"
    if (height,level,model) == (3,0,"sa"):
        grid = root / "grids/m205-3mm-long-inlet/mesh.json"
        original, terminal = "m205-3mm-extended-sa-1600", "m205-3mm-extended-sa-2100"
    if height == 5 and level == 2 and (root/"runs"/f"{name}-2400"/"metrics.json").exists():
        original, terminal = f"{name}-2400", f"{name}-2700"
    last = root / "runs" / terminal
    earlier = root / "runs" / original
    if not (last / "metrics.json").exists():
        last = earlier
    if not (last / "piv.json").exists():
        return {"id":name,"label":f"{height} mm · L{level+1} · {model.upper()}",
                "state":"Awaiting usable output","run":last.name}
    grid_meta = read(grid)
    metrics, piv = read(last/"metrics.json"), profile_report(last)
    source = profile_report(earlier)
    roots = piv.get("sampled_bottom_zeroes", [])
    roots_prev = source.get("sampled_bottom_zeroes", [])
    same_type = [row["kind"] for row in roots] == [row["kind"] for row in roots_prev]
    drift = max((1e3*abs(p["x_m"]-q["x_m"]) for p,q in zip(roots,roots_prev)),default=0) if same_type else None
    qualifiers = metrics["valid_primitives"] and read(earlier/"metrics.json")["valid_primitives"] and all(
        read(path/"metrics.json")["native_mass_pct"] <= .1 and read(path/"metrics.json")["advective_energy_pct"] <= .5
        and profile_report(path)["gate"] == "CHECKS_MET" for path in (earlier,last))
    state = "Scientific hold"
    if last != earlier and qualifiers and drift is not None and drift <= 1 and metrics["CD_relative_drift_last_100"] <= .01:
        state = "Numerical and inlet checks met"
    return {"id":name,"label":f"{height} mm · L{level+1} · {model.upper()}","run":last.name,
            "earlier_run":earlier.name, "cells":grid_meta["cells"],
            "totalIterations":int(last.name.rsplit("-", 1)[-1]),
            "mass":metrics["native_mass_pct"],"energyAdvective":metrics["advective_energy_pct"],
            "cD_drift100": metrics["CD_relative_drift_last_100"],"wallCrossings":roots,"edgeDriftMm":drift,
            "bottomCp":piv.get("bottom_Cp_at_30_50mm"),"ceilingYplus95":piv.get("ceiling_yplus_p95_x_minus40_to_0"),
            "upstream_max_mae_pct":100*max((row["mae_over_Uinf"] for row in piv["upstream"]),default=0),
            "sampled_velocity_profiles":piv.get("all_stations",[]), "state":state}


def make(root, brief):
    cases = []
    for row in brief["cases"]:
        run = brief["runs"][row["compare"][1]]
        metrics = run["metrics"]
        roots = row["x_sep_reatt_mm"]
        cases.append({"id":row["id"], "label":row["label"],
                      "x_sep_reatt_mm":roots, "bubbleMm":roots[1]-roots[0] if roots else None,
                      "cells":sum(brief["grids"][row["grid"]]["cell_types"].values()),
                      "totalIterations":row["totalIterations"],"massPercent":metrics["native_mass_pct"],
                      "edge_drift_mm":row["edge_drift_mm"],
                      "checks":"Numerical checks met" if row["checks"] == "CHECKS_MET" else "Stationarity hold",
                      "yPlusP95":metrics["wall_yplus_p95"],"shockX20":row["shock_probe"][1]["x_mm"],
                      "image":f"figures/native/{row['id']}.png"})
    row = {case["id"]:case for case in cases}
    lengths = {m:[row[f"m5-{g}-{m}"]["bubbleMm"] for g in ("coarse","medium","fine")] for m in ("sa","sst")}
    a,b = [row[f"m5-control-{k}"]["bubbleMm"] for k in ("adi","iso")]
    w = row["m5-wilcox-drift"]
    findings = [
        f"All three SA-neg grids give a {min(lengths['sa']):.2f}–{max(lengths['sa']):.2f} mm separated interval. "
        f"The corresponding SST-2003m interval is {min(lengths['sst']):.2f}–{max(lengths['sst']):.2f} mm. "
        "The tested closure effect is larger than the spread across this grid family. The sequence does not establish an asymptotic grid-convergence order.",
        f"With the same starting field and 1,050 additional iterations, the coarse SA interval is {a:.2f} mm with an adiabatic wall "
        f"and {b:.2f} mm with a 300 K wall ({100*(1-b/a):.1f}% shorter). This controlled thermal change does not reconcile the entire reference spread.",
        f"The Wilcox SST branch had {w['massPercent']:.5f}% terminal mass error, yet a {w['edge_drift_mm']:.2f} mm shift in its wall separation marker. "
        "It remains on hold for steady convergence.",
    ]
    ramp = [inspect_ramp(root,h,g,m) for h in (3,5) for g in (0,1,2) for m in ("sa","sst")]
    pilots = [profile_report(root/"runs"/name) for name in (
        "m205-3mm-coarse-sa-1000","m205-3mm-coarse-sa-repacked-1000","m205-3mm-extended-sa-1600")]
    err = lambda z: [100*r["mae_over_Uinf"] for r in z["upstream"]]
    x,y,z = map(err,pilots)
    done = [entry for entry in ramp if "mass" in entry]
    qualified = sum(row["state"] == "Numerical and inlet checks met" for row in done)
    return {"status":brief["status"], "cases":cases, "findings":findings, "ramp":ramp,
            "rampSummaries": [
                f"The 3 mm uniform-inlet pilot missed both upstream profiles by {x[0]:.2f}% and {x[1]:.2f}% of 530 m/s. "
                f"Changing wall-normal packing alone gave {y[0]:.2f}% and {y[1]:.2f}%. A longer modeled inlet development segment reduced the two errors to "
                f"{z[0]:.2f}% and {z[1]:.2f}%. The working gate was 5% with full sample support.",
                f"{len(done)} of 12 candidate cells have native outputs with a profile audit. "
                f"{qualified} met the numerical and inlet screens in a two-state comparison. The table records the actual disposition for each cell."
            ]}


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("mach5_evidence", type=Path)
    p.add_argument("out", type=Path)
    a=p.parse_args()
    a.out.write_text(json.dumps(make(a.root,read(a.mach5_evidence)), indent=2,allow_nan=False)+"\n",encoding="utf-8")
