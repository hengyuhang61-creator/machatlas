"""Render original plots from research inputs checked by SWBLI Physics Bench."""
import argparse
from pathlib import Path
import sys
from zipfile import ZipFile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def colors(fig, ax, chart):
    fig.colorbar(chart, ax=ax, label="Normalized axial velocity", extend="both",
                       shrink=0.9, pad=0.02)


def scatter(ax, x, y, u):
    return ax.scatter(x, y, c=u, cmap="viridis", vmin=0, vmax=1.15,
                      s=11, marker="s", edgecolors="none")


def style(ax, x_label, y_label):
    ax.set(xlabel=x_label, ylabel=y_label, facecolor="#f0f4f5")
    ax.grid(alpha=0.2)
    ax.set_axisbelow(True)


def save(fig, target):
    fig.savefig(target, dpi=140, facecolor="white")
    plt.close(fig)


def ramp(path, out, u_ref):
    columns = np.genfromtxt(path, delimiter=",", names=True, usecols=(1, 2, 3, 4))
    x, y, z, u = (columns[name] for name in ("x_mm", "y_mm", "z_mm", "U_m_s"))
    valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(u) & np.isclose(z, 21)
    x_edges = np.arange(-40, 91, 1)
    y_edges = np.arange(0, 46, 1)
    coords = (x[valid], y[valid])
    count, _, _ = np.histogram2d(*coords, bins=(x_edges, y_edges))
    total, _, _ = np.histogram2d(*coords, bins=(x_edges, y_edges), weights=u[valid] / u_ref)
    mean = np.divide(total, count, out=np.full_like(total, np.nan), where=count > 0)
    fig, ax = plt.subplots(figsize=(9.2, 4), layout="constrained")
    style(ax, "x from ramp foot [mm]", "y above floor [mm]")
    chart = ax.pcolormesh(x_edges, y_edges, mean.T, cmap="viridis", vmin=0, vmax=1.15)
    ax.set_title("Stanford PIV · z = 21 mm · U / 532 m/s · 1 mm measurement bins", loc="left")
    colors(fig, ax, chart)
    save(fig, out / "ramp.png")


def cone(path, out, stations, read_piv):
    fig, ax = plt.subplots(figsize=(9.2, 3.6), layout="constrained")
    with ZipFile(path) as archive:
        for x in stations:
            profile = read_piv(archive, x)
            chart = scatter(ax, np.full(len(profile), x), profile[:, 0], profile[:, 1])
    style(ax, "Absolute station x [mm]", "Radial distance from wall [mm]")
    ax.set_title("NASA TCFDVE PIV · U / 589.1 m/s · ten profile stations", loc="left")
    colors(fig, ax, chart)
    save(fig, out / "cone.png")


def hmve(path, out, profiles):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 3.8), layout="constrained", sharey=True)
    with ZipFile(path) as archive:
        for ax, re in zip(axes, ("1", "2.25")):
            for x, (_, profile) in profiles(archive, re).items():
                chart = scatter(ax, np.full(len(profile), 25.4 * x), profile[:, 1], profile[:, 2])
            style(ax, "Nominal probe x [mm]", "")
            ax.set_title(f"PIV · ReD ≈ {re} million · U / U₁", loc="left")
    axes[0].set_ylabel("Radial distance from wall [mm]")
    colors(fig, axes.tolist(), chart)
    save(fig, out / "hmve.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bench", type=Path)
    parser.add_argument("--out", type=Path, default=Path("site/figures"))
    args = parser.parse_args()
    sys.path.insert(0, str(args.bench.resolve()))
    from analysis.a08_bands import STATIONS, read_piv
    from analysis.hmve import profiles
    from analysis.io import DEFAULT_INPUTS, case_inputs
    from analysis.m205 import UINF

    ramp_dir, _ = case_inputs("m205", DEFAULT_INPUTS, fetch=False)
    cone_dir, _ = case_inputs("m25", DEFAULT_INPUTS, fetch=False)
    hmve_dir, _ = case_inputs("hmve", DEFAULT_INPUTS, fetch=False)
    args.out.mkdir(parents=True, exist_ok=True)
    ramp(ramp_dir / "m205_3mm_z21_piv_full.csv", args.out, UINF)
    cone(cone_dir / "exp_radial_profiles.zip", args.out, STATIONS, read_piv)
    hmve(hmve_dir / "HMVE2_PIVprofiles.zip", args.out, profiles)
