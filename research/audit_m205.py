"""Audit the two pre-ramp Stanford PIV profiles against a native pilot."""
import argparse
import csv
import json
from pathlib import Path

from matplotlib.tri import LinearTriInterpolator
import numpy as np

from cfd_profile_audit.core import Profile, audit

from audit_run import field, scales, wall, zeroes
from plot_native import triangles


def compare(run, reference):
    data = field(run / "flow.vtu")
    interp = LinearTriInterpolator(triangles(data), data["Velocity"][:,0] * scales(run / "case.cfg")[1])
    with reference.open(newline="",encoding="utf-8") as stream:
        all_rows = list(csv.DictReader(stream))
    results = []
    stations = sorted({float(row["target_x_mm"]) for row in all_rows})
    for x in stations:
        station_rows = [row for row in all_rows if float(row["target_x_mm"]) == x]
        xs = {float(row.get("source_x_mm", x)) for row in station_rows}
        if len(xs) != 1:
            raise ValueError(f"station {x} does not resolve to one PIV column")
        x_eval, = xs
        selected = sorted((float(row["y_mm"]),float(row["U_m_s"])) for row in station_rows)
        y, u = np.asarray(selected).T
        native = interp(np.full(y.shape, x_eval*.001), y*.001)
        supported = ~np.ma.getmaskarray(native)
        good = np.flatnonzero(supported)
        if not len(good):
            results.append({"x_mm": x, "x_evaluated_mm": x_eval, "overlap_mae": None,
                            "supported_reference_samples": 0, "reference_samples": len(y),
                            "full_domain_eligible": False, "mae_over_Uinf": None})
            continue
        if len(good) != good[-1] - good[0] + 1:
            raise ValueError(f"station {x}: noncontiguous native support")
        ref = Profile(tuple(y), tuple(u))
        computed = Profile(tuple(y[supported]), tuple(native.data[supported]))
        result = audit(ref, computed)
        result.update(x_mm=x, x_evaluated_mm=x_eval, mae_over_Uinf=result["overlap_mae"]/530,
                      max_abs_error_m_s=float(max(abs(native.data[supported]-u[supported]))))
        results.append(result)
    upstream = [row for row in results if row["x_mm"] in (-30, -10)]
    coords = data["points"]
    ceiling = ((coords[:,0] >= -.04001) & (coords[:,0] < -1e-6)
               & np.isclose(coords[:,1], .045, rtol=0, atol=1e-7))
    x, cf, cp, _ = wall(data).T
    return {
        "upstream": upstream, "all_stations": results,
        "sampled_bottom_zeroes": zeroes(x, cf, 0, .065),
        "bottom_Cp_at_30_50mm": np.interp([.030,.050], x, cp).tolist(),
        "ceiling_yplus_p95_x_minus40_to_0": float(np.quantile(data["Y_Plus"][ceiling], .95)),
        "Uinf_normalizer_m_s":530, "threshold_mae_over_Uinf":.05,
        "gate":"CHECKS_MET" if len(upstream) == 2 and all(
            row["full_domain_eligible"] and row["mae_over_Uinf"] <= .05 for row in upstream)
            else "HOLD_UPSTREAM_PROFILE_MISMATCH"
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run", type=Path)
    p.add_argument("piv_csv", type=Path)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = json.dumps(compare(args.run, args.piv_csv), indent=2, allow_nan=False) + "\n"
    args.out.write_text(result, encoding="utf-8")
    print(result, end="")
