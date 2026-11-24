"""Export a flat run index. Simulation-only stages and scientific cases have separate labels."""
import argparse
import csv
import json
from pathlib import Path
import re


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_index(root):
    for receipt in sorted((root/"runs").glob("*/execution.json")):
        run=receipt.parent
        rec=read(receipt)
        log=run/"solver.log"
        if rec["status"] != "RUNNING" and log.exists():
            cfg=(run/"case.cfg").read_text(encoding="utf-8")
            match=lambda key: re.search(rf"(?m)^{re.escape(key)}\s*=\s*([^%\r\n]+)",cfg)[1].strip()
            with (run/"mesh.su2").open(encoding="ascii") as stream:
                first=[next(stream) for _ in range(2)]
            metrics=read(run/"metrics.json") if (run/"metrics.json").exists() else {}
            yield dict(run=run.name,solver="SU2 8.6.0",mesh_cells=int(first[1].split("=")[1]),
                       mesh_sha256=rec["grid_sha256"],mach=match("MACH_NUMBER"),closure=match("KIND_TURB_MODEL"),
                       wall=rec["wall"],started_utc=rec["started_utc"],elapsed_s=rec["wall_seconds"],
                       cpu_sampled_s=rec.get("sampled_cpu_seconds"),peak_rss_mib=rec.get("peak_working_set_mib"),
                       iterations=metrics.get("done_iterations"),exit=rec["exit_code"],status=rec["status"],
                       raw_relative_dir=f"runs/{run.name}",restart_sha256=rec["artifacts"].get("restart.dat",{}).get("sha256"),
                       source_restart_sha256=rec["restart_input_sha256"])


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    rows=list(run_index(a.root))
    with a.out.open("w",encoding="utf-8",newline="") as output:
        writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
