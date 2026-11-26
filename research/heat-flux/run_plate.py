"""Native SU2 comparison on a stagnant 2-D conducting slab."""
import argparse
import hashlib
import subprocess
import time
from pathlib import Path

CONFIG = """\
SOLVER= INC_NAVIER_STOKES
INC_DENSITY_MODEL= CONSTANT
INC_ENERGY_EQUATION= YES
INC_DENSITY_INIT= 1.0
INC_VELOCITY_INIT= ( 0.0, 0.0, 0.0 )
INC_TEMPERATURE_INIT= 300.0
INC_NONDIM= DIMENSIONAL
FLUID_MODEL= CONSTANT_DENSITY
SPECIFIC_HEAT_CP= 100.0
VISCOSITY_MODEL= CONSTANT_VISCOSITY
MU_CONSTANT= 0.001
CONDUCTIVITY_MODEL= CONSTANT_CONDUCTIVITY
THERMAL_CONDUCTIVITY_CONSTANT= 0.6
MARKER_HEATFLUX= ( bottom, {heat}, right, 0.0, top, {sink}, left, 0.0 )
MARKER_MONITORING= ( bottom, right, top, left )
MARKER_PLOTTING= ( bottom, right, top, left )
FREESTREAM_VELOCITY= ( 0.0, 0.0, 0.0 )
MESH_FILENAME= slab.su2
MESH_FORMAT= SU2
CONV_NUM_METHOD_FLOW= FDS
MUSCL_FLOW= NO
TIME_DISCRE_FLOW= EULER_IMPLICIT
NUM_METHOD_GRAD= GREEN_GAUSS
CFL_NUMBER= 5.0
LINEAR_SOLVER= FGMRES
LINEAR_SOLVER_PREC= ILU
LINEAR_SOLVER_ERROR= 1E-12
LINEAR_SOLVER_ITER= 40
ITER= {iterations}
CONV_RESIDUAL_MINVAL= -18
CONV_FIELD= RMS_TEMPERATURE
CONV_STARTITER= 1
OUTPUT_FILES= ( RESTART_ASCII, SURFACE_CSV, SURFACE_PARAVIEW_LEGACY )
VOLUME_OUTPUT= ( COORDINATES, SOLUTION, PRIMITIVE, HEAT_FLUX )
HISTORY_OUTPUT= ( ITER, RMS_RES, HEAT )
SCREEN_OUTPUT= ( INNER_ITER, RMS_PRESSURE, RMS_TEMPERATURE )
OUTPUT_WRT_FREQ= 500
"""


def mesh(n):
    def point(i, j):
        return i + (n + 1) * j

    sides = {
        "bottom": [(point(i, 0), point(i + 1, 0)) for i in range(n)],
        "right": [(point(n, j), point(n, j + 1)) for j in range(n)],
        "top": [(point(i + 1, n), point(i, n)) for i in range(n)],
        "left": [(point(0, j + 1), point(0, j)) for j in range(n)],
    }
    elements = [f"9 {point(i, j)} {point(i + 1, j)} {point(i + 1, j + 1)} {point(i, j + 1)}"
                for j in range(n) for i in range(n)]
    points = [f"{0.01 * i / n:.16g} {0.01 * j / n:.16g} {point(i, j)}"
              for j in range(n + 1) for i in range(n + 1)]
    lines = ["NDIME= 2", f"NELEM= {n*n}", *elements, f"NPOIN= {len(points)}", *points, "NMARK= 4"]
    for name, edges in sides.items():
        lines.extend([f"MARKER_TAG= {name}", f"MARKER_ELEMS= {len(edges)}"])
        lines.extend(f"3 {a} {b}" for a, b in edges)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", type=Path)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--n", type=int, default=12)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--heat", type=float, default=1000)
    args = parser.parse_args()
    directory = args.directory.resolve()
    directory.mkdir(parents=True)
    binary = args.binary.resolve()
    grid = mesh(args.n)
    case = CONFIG.format(heat=args.heat, sink=-args.heat, iterations=args.iterations)
    (directory / "slab.su2").write_text(grid, encoding="ascii")
    (directory / "slab.cfg").write_text(case, encoding="ascii")
    with binary.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    start = time.perf_counter()
    with (directory / "su2.log").open("wb") as log:
        result = subprocess.run([str(binary), "-t", "1", "slab.cfg"], cwd=directory,
                                stdout=log, stderr=subprocess.STDOUT, timeout=90)
    duration = time.perf_counter() - start
    (directory / "run.txt").write_text(f"binary_sha256={digest}\nreturncode={result.returncode}\nelapsed_s={duration:.6f}\n",
                                      encoding="ascii")
    print(directory, result.returncode, f"{duration:.3f} s")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
