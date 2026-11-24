"""Compare terminal wall diagnostics with linked literature curves on common support."""
import argparse
import json
from pathlib import Path

import numpy as np
from cfd_profile_audit.core import Profile, audit
from audit_run import zeroes


def analyze(brief, refs):
    labels = {
        "DLR experiment as hosted with MOSE": ("MOSE-SA-reference-schulein.dat", ("sa","sst","sst-wilcox")),
        "Archived SU2 SA": ("MOSE-SA-reference-SU2-SA.dat", ("sa",)),
        "Archived SU2 SST": ("MOSE-SST-reference-SU2-SST.dat", ("sst","sst-wilcox")),
        "Archived Wind-US SA": ("MOSE-SA-reference-wind-SA.dat", ("sa",)),
        "Archived Wind-US SST": ("MOSE-SST-reference-wind-SST.dat", ("sst","sst-wilcox")),
    }
    out = {"comparison_window_m": [0.32,0.40], "references": {}}
    for label,(name, models) in labels.items():
        x,cf = np.loadtxt(refs / name).T
        within = (x>=0.32)&(x<=0.40)
        record = {"file":name,"zero_brackets":[],"rows":[]}
        for cross in zeroes(x,cf):
            i = int(np.searchsorted(x,cross["x_m"]))
            record["zero_brackets"].append({**cross,"reconstruction_bracket_m":[float(x[i-1]),float(x[i])]})
        measured = Profile(tuple(x[within]),tuple(cf[within]))
        for case in brief["cases"]:
            if case["model"] not in models:
                continue
            data = np.asarray(case["wall_trace_x_cf_cp"])
            model = Profile(tuple(data[:,0]),tuple(data[:,1]))
            result = audit(measured, model)
            record["rows"].append({
                "case_id":case["id"],"matched":result["supported_reference_samples"],
                "reference":result["reference_samples"],"overlap_mae_cf":result["overlap_mae"],
                "overlap_rmse_cf":result["overlap_rmse"],
            })
        out["references"][label]=record
    return out


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mach5_evidence",type=Path)
    p.add_argument("reference_cache",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    result=analyze(json.loads(a.mach5_evidence.read_text(encoding="utf-8")),a.reference_cache)
    a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
