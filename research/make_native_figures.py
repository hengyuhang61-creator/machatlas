"""Render the Mach 5 evidence figures from the pinned run pairs."""
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from audit_run import field
from plot_native import compare, figure, triangles


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("cases", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    pairs = json.loads(args.cases.read_text(encoding="utf-8"))
    runs = {row["id"]:(row["label"], args.study / "runs" / row["compare"][1]) for row in pairs}
    for row in pairs:
        label, path = runs[row["id"]]
        fig = args.out / (row["id"] + ".png")
        figure(field(path / "flow.vtu"), f"Mach 5 benchmark | {label} | {row['totalIterations']:,} steady iterations", fig)
        print(fig.name, flush=True)
    compare([runs[key] for key in ("m5-coarse-sa", "m5-fine-sa", "m5-coarse-sst",
             "m5-fine-sst", "m5-control-iso", "m5-wilcox-drift")],
            "Mach 5 SWBLI | native bottom-wall diagnostics", args.out / "m5-wall-comparison.png")
    _, reference = runs["m5-coarse-sa"]
    data = field(reference / "flow.vtu")
    fig, ax = plt.subplots(figsize=(9,4.0),layout="constrained")
    chart = ax.tripcolor(triangles(data),data["Mach"],shading="gouraud",cmap="viridis",vmin=0,vmax=5.1)
    ax.set(xlabel="Axial x [m]", ylabel="Vertical y [m]", title="Mach 5 · native SU2 solution · SA-neg")
    ax.set_xlim(-.01,.523)
    ax.set_ylim(0,.117)
    fig.colorbar(chart,ax=ax,label="Mach",extend="both")
    fig.savefig(args.out / "m5-hero.png",dpi=150,facecolor="white")
    plt.close(fig)
