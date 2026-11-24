"""Run the pinned SU2 benchmark controls in a fresh, bounded run directory."""
import argparse
from datetime import datetime, timezone
from hashlib import file_digest
import json
from pathlib import Path
import re
import shutil
import subprocess
from time import perf_counter

import psutil


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def config(upstream, iters, walls, restart):
    patch = {
        "ITER": str(iters), "RESTART_SOL": "YES" if restart else "NO",
        "SOLUTION_FILENAME": "input_restart", "OUTPUT_WRT_FREQ": "100",
        "SCREEN_WRT_FREQ_INNER": "10", "HISTORY_OUTPUT": "(ITER, RMS_RES, AERO_COEFF, SURFACE_MASSFLOW)",
        "CONV_RESIDUAL_MINVAL": "-20"
    }
    if walls == "isothermal":
        patch["MARKER_HEATFLUX"] = "(NONE)"
    text = upstream.read_text(encoding="utf-8")
    for key, val in patch.items():
        text, count = re.subn(r"(?m)^" + key + r"\s*=.*$", key + "= " + val, text)
        if count != 1:
            raise ValueError(f"expected one {key} in upstream config")
    text += """
% MachAtlas evidence output, steady iterations (no physical time)
MARKER_ANALYZE= (inlet, outlet)
OUTPUT_FILES= (RESTART, PARAVIEW, SURFACE_CSV)
VOLUME_OUTPUT= (COORDINATES, SOLUTION, PRIMITIVE)
RESTART_FILENAME= restart
VOLUME_FILENAME= flow
SURFACE_FILENAME= wall
"""
    if walls == "isothermal":
        text += "MARKER_ISOTHERMAL= (bottom, 300.0, top, 300.0)\n"
    return text


def run(args):
    executable = args.exe.resolve(strict=True)
    args.out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.grid, args.out / "mesh.su2")
    if args.restart:
        shutil.copyfile(args.restart, args.out / "input_restart.dat")
    cfg = args.out / "case.cfg"
    cfg.write_text(config(args.template, args.iters, args.walls, args.restart), encoding="utf-8")
    cmd = [str(executable), "-t", str(args.threads), cfg.name]
    receipt = {
        "command": [executable.name, *cmd[1:]], "binary_sha256": sha(executable),
        "template_sha256": sha(args.template), "cfg_sha256": sha(cfg), "grid_sha256": sha(args.grid),
        "restart_input_sha256": sha(args.restart) if args.restart else None,
        "wall": args.walls, "iteration_cap": args.iters, "thread_cap": args.threads,
        "deadline_seconds": args.seconds, "memory_limit_mib": args.max_rss_mib,
        "started_utc": datetime.now(timezone.utc).isoformat()
    }
    record = args.out / "execution.json"
    record.write_text(json.dumps({**receipt, "status": "RUNNING"}, indent=2), encoding="utf-8")
    start = perf_counter()
    cpu_seconds, peak_rss = 0.0, 0
    with (args.out / "solver.log").open("wb") as log:
        try:
            with subprocess.Popen(cmd, cwd=args.out, stdin=subprocess.DEVNULL, stdout=log,
                                  stderr=subprocess.STDOUT) as proc:
                process = psutil.Process(proc.pid)
                while proc.poll() is None:
                    try:
                        cpu = process.cpu_times()
                        cpu_seconds = cpu.user + cpu.system
                        memory = process.memory_info()
                        peak_rss = max(peak_rss, getattr(memory, "peak_wset", memory.rss))
                    except psutil.NoSuchProcess:
                        break
                    limit = None
                    if perf_counter() - start > args.seconds:
                        limit = "WALL_CLOCK_LIMIT"
                    elif peak_rss > args.max_rss_mib * 2**20:
                        limit = "MEMORY_LIMIT"
                    if limit:
                        proc.kill()
                        receipt.update(exit_code=124, status=limit)
                        break
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
                if "exit_code" not in receipt:
                    code = proc.wait()
                    receipt.update(exit_code=code, status="EXIT_ZERO" if code == 0 else "SOLVER_FAILED")
        except OSError as exc:
            receipt.update(exit_code=125, status="LAUNCH_FAILED", error=str(exc))
    receipt.update(wall_seconds=round(perf_counter() - start, 3),
                   sampled_cpu_seconds=round(cpu_seconds, 3),
                   peak_working_set_mib=round(peak_rss / 2**20, 2),
                   finished_utc=datetime.now(timezone.utc).isoformat(),
                   artifacts={p.name: {"bytes": p.stat().st_size, "sha256": sha(p)}
                              for p in sorted(args.out.iterdir()) if p.is_file() and p != record})
    record.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(receipt["status"], receipt["wall_seconds"], flush=True)
    return receipt["exit_code"]


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("exe", type=Path)
    p.add_argument("grid", type=Path)
    p.add_argument("template", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--restart", type=Path)
    p.add_argument("--walls", choices=["adiabatic", "isothermal"], default="adiabatic")
    p.add_argument("--iters", type=int, default=300)
    p.add_argument("--threads", type=int, default=6)
    p.add_argument("--seconds", type=int, default=600)
    p.add_argument("--max-rss-mib", type=int, default=2048)
    a = p.parse_args()
    if min(a.iters, a.threads, a.seconds, a.max_rss_mib) < 1:
        p.error("iteration, thread, time and memory caps must be positive")
    raise SystemExit(run(a))
