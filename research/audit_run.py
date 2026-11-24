"""Extract terminal metrics from a completed SU2 point field and native history."""
import argparse
import csv
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import numpy as np

GAMMA = 1.4
R = 287.058


def scales(path):
    text = path.read_text(encoding="utf-8")
    p, t = (float(re.search(rf"(?m)^FREESTREAM_{key}\s*=\s*([\d.eE+-]+)", text)[1])
            for key in ("PRESSURE", "TEMPERATURE"))
    return t, (GAMMA * R * t) ** 0.5, p / (R * t)


def field(path):
    binary = path.read_bytes()
    head, body = binary.split(b"<AppendedData", 1)
    tree = ET.fromstring(head + b"</VTKFile>")
    if tree.attrib["byte_order"] != "LittleEndian" or tree.attrib["header_type"] != "UInt64":
        raise ValueError("unexpected SU2 VTU byte order")
    start = len(binary) - len(body) + body.index(b"_") + 1
    types = {"Float32": "<f4", "Int32": "<i4", "UInt8": "u1"}
    data = {}
    for node in tree.iter("DataArray"):
        at = start + int(node.attrib["offset"])
        size = int.from_bytes(binary[at:at + 8], "little")
        value = np.frombuffer(binary, dtype=types[node.attrib["type"]],
                              count=size // np.dtype(types[node.attrib["type"]]).itemsize, offset=at + 8)
        count = int(node.attrib.get("NumberOfComponents", 1))
        data[node.attrib["Name"] or "points"] = value.reshape(-1, count) if count > 1 else value
    if "Velocity" not in data and "Momentum" in data:
        # SU2 7.4 exports non-dimensional momentum in place of velocity.
        data["Velocity"] = data["Momentum"].astype(float) / data["Density"][:, None]
    return data


def history(path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.reader(stream, skipinitialspace=True)
        header = [s.strip() for s in next(reader)]
        return [dict(zip(header, map(float, row))) for row in reader if row]


def wall(data):
    points = data["points"].astype(float)
    bottom = np.flatnonzero((points[:, 0] > 0) & (abs(points[:, 1]) < 1e-10))
    bottom = bottom[np.argsort(points[bottom, 0])]
    return np.column_stack((points[bottom, 0], data["Skin_Friction_Coefficient"][bottom, 0],
                           data["Pressure_Coefficient"][bottom], data["Y_Plus"][bottom]))


def zeroes(x, y, lo=0.30, hi=0.45):
    mask = (x >= lo) & (x <= hi)
    x, y = x[mask], y[mask]
    flips = np.flatnonzero((y[:-1] < 0) != (y[1:] < 0))
    return [{"x_m": float(x[i] - y[i] * (x[i+1] - x[i]) / (y[i+1] - y[i])),
             "kind": "reattachment" if y[i] < 0 else "separation"} for i in flips]


def edge_flux(data, which, refs):
    t_ref, v_ref, rho_ref = refs
    points = data["points"].astype(float)
    x = points[:, 0]
    ids = np.flatnonzero(np.isclose(x, x.min() if which == "inlet" else x.max(), atol=1e-8, rtol=0))
    ids = ids[np.argsort(points[ids, 1])]
    sign = 1 if which == "inlet" else -1
    vel = data["Velocity"][ids].astype(float)
    rho_u = sign * data["Density"][ids] * vel[:, 0] * rho_ref * v_ref
    ht = GAMMA * R / (GAMMA - 1) * data["Temperature"][ids] * t_ref + 0.5 * (vel ** 2).sum(axis=1) * v_ref**2
    y = points[ids, 1]
    return {
        "mass_signed_inward_kg_s_m": float(np.trapezoid(rho_u, y)),
        "mass_positive_part_kg_s_m": float(np.trapezoid(np.maximum(rho_u, 0), y)),
        "advective_total_enthalpy_signed_W_m": float(np.trapezoid(rho_u * ht, y)),
        "advective_total_enthalpy_positive_W_m": float(np.trapezoid(np.maximum(rho_u, 0) * ht, y)),
        "boundary_points": int(len(ids)),
    }


def metrics(run):
    data = field(run / "flow.vtu")
    rows = history(run / "history.csv")
    last = rows[-1]
    props = ("Density", "Pressure", "Temperature", "Mach", "Velocity")
    valid = all(np.isfinite(data[k]).all() for k in props)
    mins = {k: float(data[k].min()) for k in props[:4]}
    trace = wall(data)
    roots = zeroes(trace[:, 0], trace[:, 1])
    n = len(rows)
    drag_drift = abs(last["CD"] - rows[max(0,n-101)]["CD"]) / max(abs(last["CD"]), 1e-20)
    mf_in, mf_out = (last["Avg_Massflow(" + k + ")"] for k in ("inlet", "outlet"))
    refs = scales(run / "case.cfg")
    flux = {k: edge_flux(data, k, refs) for k in ("inlet", "outlet")}
    return dict(
        done_iterations=n, final_inner_iter=int(last["Inner_Iter"]),
        terminal_rms={key: value for key, value in last.items() if key.startswith("rms[")},
        valid_primitives=valid and min(mins[k] for k in props[:3]) > 0,
        min_nondimensional=mins, max_mach=float(data["Mach"].max()),
        native_inlet_kg_s_m=mf_in, native_outlet_kg_s_m=mf_out,
        native_mass_pct=100 * abs(mf_in+mf_out) / mf_in,
        CD=last["CD"], CD_relative_drift_last_100=drag_drift,
        wall_zero_crossings=roots, Cf_min=float(trace[:, 1].min()),
        Cp_max=float(trace[:, 2].max()), wall_yplus_p95=float(np.quantile(trace[:, 3], .95)),
        wall_yplus_max=float(trace[:, 3].max()), field_flux=flux,
        field_mass_pct=100 * abs(sum(x["mass_signed_inward_kg_s_m"] for x in flux.values()))
        / sum(x["mass_positive_part_kg_s_m"] for x in flux.values()),
        advective_energy_pct=100 * abs(sum(x["advective_total_enthalpy_signed_W_m"] for x in flux.values()))
        / sum(x["advective_total_enthalpy_positive_W_m"] for x in flux.values()),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run", type=Path)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = json.dumps(metrics(args.run), indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.write_text(result, encoding="utf-8")
    print(result, end="")
