"""Render matched Mach 5 fields and export native wall traces for the public comparison."""
import argparse
import json
from pathlib import Path

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.tri import LinearTriInterpolator
import numpy as np
from PIL import Image

from audit_run import field, wall
from plot_native import triangles

FIELDS = {
    "mach": ((250, 405, 0, 53), (0, 5.1), ["#0b1223", "#283567", "#266c98", "#6dbeba", "#ffdaa1"]),
    "reverse": ((305, 365, 0, 3), (-0.09, 0.6), [(0, "#e84c42"), (0.09 / 0.69, "#30273e"), (0.36, "#183a61"), (0.72, "#2b8ca1"), (1, "#e3f4df")]),
}


def raster(case, tri, values, key, dest):
    bounds, limits, palette = FIELDS[key]
    x = np.linspace(bounds[0], bounds[1], 820) / 1000
    y = np.linspace(bounds[3], bounds[2], 288 if key == "mach" else 212) / 1000
    sample = LinearTriInterpolator(tri, values)(*np.meshgrid(x, y))
    color = LinearSegmentedColormap.from_list(key, palette)
    result = color((sample - limits[0]) / (limits[1] - limits[0]), bytes=True)
    result[sample.mask] = (12, 20, 34, 255)
    name = case + "-" + key + ".webp"
    Image.fromarray(result[:, :, :3]).save(dest / name, format="WEBP", quality=92)
    return "figures/discrepancy/" + name


def load_case(case, label, chain, data_root, picture_root):
    data = json.loads((data_root / (chain + "-chain.json")).read_text())
    tail = data["stages"][-1]
    m = tail["metrics"]
    s, r = [1000 * p["x_m"] for p in m["wall_zero_crossings"]]
    native = field(data_root / tail["path"] / "flow.vtu")
    trace = wall(native)
    trace = trace[(trace[:, 0] >= 0.30) & (trace[:, 0] <= 0.42), :3]
    trace[:, 0] *= 1000
    tri = triangles(native)
    return {
        "id": case, "name": label, "stage": tail["at"], "separation": s, "reattachment": r,
        "length": r - s, "mass": m["native_mass_pct"], "qualifiedWallTail": data["gate"]["pass"],
        "images": {"mach": raster(case, tri, native["Mach"], "mach", picture_root),
                   "reverse": raster(case, tri, native["Velocity"][:, 0] / 5, "reverse", picture_root)},
        "trace": trace.round(8).tolist(),
    }


def main(data_root, site, reference):
    dest = site / "figures" / "discrepancy"
    dest.mkdir(parents=True, exist_ok=True)
    cases = [load_case("current", "SU2 8.6.0 · adiabatic", "v86", data_root, dest),
             load_case("earlier", "SU2 7.4.0 · adiabatic", "v74", data_root, dest),
             load_case("cold", "SU2 8.6.0 · wall at 300 K", "iso", data_root, dest)]
    refs = json.loads(reference.read_text())["references"]
    keys = ["DLR experiment as hosted with MOSE", "Archived SU2 SST"]
    markers = {k: [{**root, "x_mm": root["x_m"] * 1000,
                    "bracket_mm": [x * 1000 for x in root["reconstruction_bracket_m"]]}
                   for root in refs[k]["zero_brackets"] if 0.31 <= root["x_m"] <= 0.37] for k in keys}
    (site / "discrepancy.json").write_text(
        json.dumps({"cases": cases, "references": markers}, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("data_root", type=Path)
    p.add_argument("site", type=Path)
    p.add_argument("reference", type=Path)
    a = p.parse_args()
    main(a.data_root, a.site, a.reference)
