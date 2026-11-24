"""Plot native SU2 states without temporal interpolation."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import LinearTriInterpolator, Triangulation
import numpy as np

from audit_run import field, wall, zeroes

COLORS = ("#147b8a", "#b44727", "#6553aa", "#487439", "#955067", "#3b4b78")


def triangles(data):
    begin = np.r_[0, data["offsets"][:-1]]
    actual = data["connectivity"]
    nodes = []
    for size in (3, 4):
        start = begin[data["offsets"] - begin == size]
        indices = actual[start[:, None] + np.arange(size)]
        nodes.append(indices[:, :3])
        if size == 4:
            nodes.append(indices[:, [0, 2, 3]])
    tris = np.concatenate(nodes)
    x, y = data["points"][:, :2].T.astype(float)
    a, b, c = tris.T
    orient = (x[b]-x[a])*(y[c]-y[a]) - (x[c]-x[a])*(y[b]-y[a])
    tris[orient < 0] = tris[orient < 0][:, [0, 2, 1]]
    return Triangulation(x, y, tris)


def shock_locations(data):
    tri = triangles(data)
    interp = LinearTriInterpolator(tri, data["Density"])
    x = np.linspace(.24, .36, 1201)
    result = []
    for y in (.015, .020, .025):
        sampled = interp(x, np.full(x.shape, y))
        if np.any(sampled.mask):
            raise ValueError("shock probe outside mesh support")
        # The steepest rise of a 1 mm secant, rather than a pointwise derivative.
        change = sampled[10:] - sampled[:-10]
        i = int(np.argmax(change))
        result.append({"y_mm": y*1000, "x_mm": float((x[i] + x[i+10])*500),
                       "density_rise_over_rho_inf": float(change[i])})
    return result


def figure(data, title, output):
    tri = triangles(data)
    wall_data = wall(data)
    fig, ax = plt.subplots(2, 2, figsize=(12.2, 7.2), layout="constrained")
    fig.suptitle(title, fontsize=18, weight="bold")
    for pane, z, label, limits, bounds in (
        (ax[0,0], data["Mach"], "Mach number", (0,5.1), (-.01,.523,0,.117)),
        (ax[0,1], data["Velocity"][:,0]/5, "Axial velocity U / U∞", (-.15,1.05), (.300,.385,0,.016)),
    ):
        chart = pane.tripcolor(tri, z, shading="gouraud", cmap="viridis", vmin=limits[0], vmax=limits[1])
        pane.axis(bounds)
        pane.set(xlabel="Axial x [m]", ylabel="Wall-normal y [m]", title=label)
        fig.colorbar(chart, ax=pane, extend="both")
    x, cf, cp, _ = wall_data.T
    for pane, values, title, scale in (
        (ax[1,0], cf, "Bottom-wall skin friction", 1e3),
        (ax[1,1], cp, "Bottom-wall static pressure", 1),
    ):
        pane.plot(x, values * scale, color=COLORS[0], lw=1.8)
        pane.set_xlim(.300,.410)
        pane.set_xlabel("Axial x [m]")
        pane.set_title(title)
        pane.grid(alpha=.22)
    ax[1,0].set_ylabel("1,000 × Cf,x")
    ax[1,0].axhline(0, lw=.9, color="#474f59")
    for crossing in zeroes(x, cf):
        if .300 <= crossing["x_m"] <= .410:
            ax[1,0].scatter(crossing["x_m"], 0, marker="o", color=COLORS[1], zorder=4)
    ax[1,1].set_ylabel("Cp = (p − p∞) / q∞")
    fig.savefig(output, dpi=145, facecolor="white")
    plt.close(fig)


def compare(runs, title, output):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.0), layout="constrained")
    fig.suptitle(title, fontsize=16, weight="bold")
    for (label, path), color in zip(runs, COLORS, strict=False):
        x, cf, cp, _ = wall(field(path / "flow.vtu")).T
        axes[0].plot(1e3*x, 1e3*cf, lw=1.6, color=color, label=label)
        axes[1].plot(1e3*x, cp, lw=1.6, color=color)
    for pane in axes:
        pane.set_xlim(310, 390)
        pane.set_xlabel("Axial x [mm]")
        pane.grid(alpha=.22)
    axes[0].axhline(0, lw=.8, color="#505963")
    axes[0].set_ylabel("1,000 × Cf,x")
    axes[0].legend(fontsize="small", frameon=False)
    axes[1].set_ylabel("Cp = (p − p∞) / q∞")
    fig.savefig(output, dpi=145, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--title", required=True)
    args = p.parse_args()
    d = field(args.run / "flow.vtu")
    figure(d, args.title, args.out)
    print(shock_locations(d))
