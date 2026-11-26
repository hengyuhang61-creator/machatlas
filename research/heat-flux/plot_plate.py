"""Render the native heat-flux comparison from the measured JSON."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

results = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
runs = [results[key] for key in ("early", "mid", "tail")]
iteration = [1, 400, 6000]
fig, (wall, temperature) = plt.subplots(1, 2, figsize=(10.5, 3.7), layout="constrained")
for ax in (wall, temperature):
    ax.set_xscale("log")
    ax.set_xticks(iteration, labels=["1", "400", "6,000"])
    ax.set_xlabel("Steady solver iteration")
    ax.grid(alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)

wall.plot(iteration, [r["pre"]["bottom"][1] for r in runs], "o-", color="#b34c24", label="SU2 v8.1.0")
wall.plot(iteration, [r["post"]["bottom"][1] for r in runs], "s--", color="#146a8a", label="SU2 v8.2.0")
wall.set_title("Exported bottom-wall heat flux")
wall.set_ylabel("Interior-node mean (W/m²)")
wall.legend(loc="upper right", frameon=False)

temperature.plot(iteration, [r["post"]["temperature_gradient"] for r in runs], "o-",
                 color="#146a8a", label="Both binaries")
temperature.axhline(runs[0]["post"]["analytic_temperature_gradient"], color="#555555",
                    linewidth=1.3, linestyle="--", label="Steady analytic slope")
temperature.set_title("Centerline temperature difference per thickness")
temperature.set_ylabel("Slope (K/m)")
temperature.legend(loc="upper right", frameon=False)
fig.savefig(sys.argv[2], dpi=165)
