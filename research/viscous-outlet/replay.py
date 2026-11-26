"""Run one SU2 step from a manufactured planar shear field."""
import argparse
import csv
from hashlib import file_digest
import json
from math import isclose, isfinite, sqrt
from pathlib import Path
from statistics import median
import subprocess
import time

LENGTH = 0.04
HEIGHT = 0.016
PRESSURE = 100_000.0
DENSITY = 1.0
GAMMA = 1.4
GAS_CONSTANT = 287.058
VELOCITY = 700.0
VISCOSITY = 0.001
TIME_STEP = 1e-7
FIELDS = ("PointID", "x", "y", "Density", "Momentum_x", "Momentum_y", "Energy")
CONFIGURATION = """\
SOLVER= NAVIER_STOKES
KIND_TURB_MODEL= NONE
MATH_PROBLEM= DIRECT
RESTART_SOL= YES
READ_BINARY_RESTART= NO
RESTART_ITER= 1
SOLUTION_FILENAME= initial
RESTART_FILENAME= result
MESH_FORMAT= SU2
MESH_FILENAME= shear.su2
SYSTEM_MEASUREMENTS= SI
REF_DIMENSIONALIZATION= DIMENSIONAL
FLUID_MODEL= IDEAL_GAS
GAMMA_VALUE= {gamma}
GAS_CONSTANT= {gas}
MACH_NUMBER= {mach:.16g}
INIT_OPTION= TD_CONDITIONS
FREESTREAM_PRESSURE= {pressure}
FREESTREAM_TEMPERATURE= {temperature:.16g}
VISCOSITY_MODEL= CONSTANT_VISCOSITY
MU_CONSTANT= {viscosity}
CONDUCTIVITY_MODEL= CONSTANT_CONDUCTIVITY
THERMAL_CONDUCTIVITY_CONSTANT= 0.0257
MARKER_FAR= ( inlet )
MARKER_SYM= ( bottom, top )
{outlet}
TIME_DOMAIN= YES
TIME_MARCHING= TIME_STEPPING
TIME_ITER= 2
TIME_STEP= {dt}
UNST_CFL_NUMBER= 0.0
TIME_DISCRE_FLOW= EULER_EXPLICIT
NUM_METHOD_GRAD= GREEN_GAUSS
CONV_NUM_METHOD_FLOW= ROE
MUSCL_FLOW= NO
MGLEVEL= 0
CFL_NUMBER= 0.2
OUTPUT_FILES= ( RESTART_ASCII )
OUTPUT_WRT_FREQ= 1
VOLUME_OUTPUT= ( COORDINATES, SOLUTION )
TABULAR_FORMAT= CSV
HISTORY_OUTPUT= ( ITER, RMS_RES, TIME_STEP )
SCREEN_OUTPUT= ( TIME_ITER, RMS_DENSITY, RMS_MOMENTUM-Y, RMS_ENERGY )
"""


def digest(path):
    with path.open("rb") as handle:
        return file_digest(handle, "sha256").hexdigest()


def initial_state(nx, ny, slope):
    rows = []
    for j in range(ny + 1):
        y = HEIGHT * j / ny
        u = VELOCITY + slope * (y - HEIGHT / 2)
        energy = PRESSURE / (GAMMA - 1) + DENSITY * u**2 / 2
        for i in range(nx + 1):
            point = i + (nx + 1) * j
            rows.append((point, LENGTH * i / nx, y, DENSITY, DENSITY * u, 0.0, energy))
    return rows


def write_mesh(path, nx, ny, rows):
    def point(i, j):
        return i + (nx + 1) * j

    boundaries = {
        "bottom": [(point(i, 0), point(i + 1, 0)) for i in range(nx)],
        "outlet": [(point(nx, j), point(nx, j + 1)) for j in range(ny)],
        "top": [(point(i + 1, ny), point(i, ny)) for i in range(nx)],
        "inlet": [(point(0, j + 1), point(0, j)) for j in range(ny)],
    }
    lines = ["NDIME= 2", f"NELEM= {nx * ny}"]
    lines.extend(f"9 {point(i, j)} {point(i + 1, j)} {point(i + 1, j + 1)} {point(i, j + 1)}"
                 for j in range(ny) for i in range(nx))
    lines.append(f"NPOIN= {len(rows)}")
    lines.extend(f"{x:.17g} {y:.17g} {index}" for index, x, y, *_ in rows)
    lines.append("NMARK= 4")
    for name, edges in boundaries.items():
        lines.extend((f"MARKER_TAG= {name}", f"MARKER_ELEMS= {len(edges)}"))
        lines.extend(f"3 {a} {b}" for a, b in edges)
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")


def write_initial(path, rows):
    with path.open("w", encoding="ascii", newline="") as handle:
        handle.write(",".join(f'"{field}"' for field in FIELDS) + "\n")
        csv.writer(handle, lineterminator="\n").writerows(rows)
        handle.write("EXT_ITER= 0\n")


def read_solution(path, initial):
    with path.open(encoding="ascii", newline="") as handle:
        reader = csv.DictReader(handle, skipinitialspace=True)
        data = {}
        for row in reader:
            if not row["PointID"].strip().isdecimal():
                continue
            index = int(row["PointID"])
            if index in data or index >= len(initial):
                raise ValueError(f"unexpected point ID {index}")
            x, y, rho, mx, my, energy = (float(row[name]) for name in FIELDS[1:])
            p = (GAMMA - 1) * (energy - (mx**2 + my**2) / (2 * rho)) if rho else float("nan")
            if not all(isfinite(v) for v in (x, y, rho, mx, my, energy, p)) or min(p, rho) <= 0:
                raise ValueError(f"unphysical state at point {index}")
            if not (isclose(x, initial[index][1], abs_tol=1e-14)
                    and isclose(y, initial[index][2], abs_tol=1e-14)):
                raise ValueError(f"point coordinates differ at ID {index}")
            data[index] = (my, mx / sqrt(GAMMA * p * rho), mx)
    if len(data) != len(initial):
        raise ValueError(f"expected {len(initial)} output points, found {len(data)}")
    return data


def summarize(state, nx, ny):
    columns = {}
    rows = range(ny // 4, 3 * ny // 4 + 1)
    for name, i in (("outlet", nx), ("one_cell_inside", nx - 1), ("mid_domain", nx // 2)):
        values = [state[i + (nx + 1) * j] for j in rows]
        rates = [momentum / TIME_STEP for momentum, _, _ in values]
        columns[name] = {
            "count": len(values), "min_normal_mach": min(mach for _, mach, _ in values),
            "median_rate": median(rates), "min_rate": min(rates), "max_rate": max(rates),
        }
    return columns


def run(binary, directory, marker, slope, refined):
    binary = binary.resolve(strict=True)
    directory.mkdir(parents=True, exist_ok=False)
    nx, ny = (40, 32) if refined else (20, 16)
    rows = initial_state(nx, ny, slope)
    mesh = directory / "shear.su2"
    initial = directory / "initial_00000.csv"
    config = directory / "case.cfg"
    write_mesh(mesh, nx, ny, rows)
    write_initial(initial, rows)
    marker_value = ("MARKER_SUPERSONIC_OUTLET= ( outlet )" if marker == "supersonic"
                    else f"MARKER_OUTLET= ( outlet, {PRESSURE:g} )")
    config.write_text(CONFIGURATION.format(gamma=GAMMA, gas=GAS_CONSTANT,
                      mach=VELOCITY / sqrt(GAMMA * PRESSURE / DENSITY), pressure=PRESSURE,
                      temperature=PRESSURE / (DENSITY * GAS_CONSTANT), viscosity=VISCOSITY,
                      outlet=marker_value, dt=TIME_STEP), encoding="ascii", newline="\n")
    log = directory / "su2.log"
    start = time.perf_counter()
    with log.open("wb") as handle:
        result = subprocess.run([str(binary), "-t", "1", config.name], cwd=directory,
                                stdout=handle, stderr=subprocess.STDOUT, timeout=60)
    seconds = time.perf_counter() - start
    if result.returncode:
        raise RuntimeError(f"SU2 exited {result.returncode}. See {log}")
    output = directory / "result_00001.csv"
    state = read_solution(output, rows)
    qoi = summarize(state, nx, ny)
    evidence = {
        "threads": 1, "exit_code": result.returncode, "elapsed_s": seconds,
        "binary_sha256": digest(binary), "marker": marker,
        "nx": nx, "ny": ny, "time_step_s": TIME_STEP, "slope_s_inverse": slope,
        "shear_stress_pa": VISCOSITY * slope,
        "analytic_complete_flux_rate": 0.0,
        "analytic_omitted_outlet_flux_rate": -VISCOSITY * slope / (LENGTH / (2 * nx)),
        "qoi": qoi,
        "sha256": {path.name: digest(path) for path in (mesh, initial, config, output, log)},
    }
    (directory / "result.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("solver", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--marker", choices=("supersonic", "pressure"), default="supersonic")
    parser.add_argument("--slope", type=int, choices=(0, 2000), default=2000)
    parser.add_argument("--refined", action="store_true")
    args = parser.parse_args()
    run(args.solver, args.output.resolve(), args.marker, args.slope, args.refined)
