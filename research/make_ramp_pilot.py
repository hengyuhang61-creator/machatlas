"""Create a two-dimensional uniform-inlet pilot for the published M2.05 ramp."""
import argparse
import json
from pathlib import Path
import re

import numpy as np

from run_native import sha

R = 287.058
GAMMA = 1.4
MACH = 2.05
T0, P0 = 303, 255300
T = T0 / (1 + .2 * MACH**2)
P = P0 / (T0/T)**3.5
U = MACH * (GAMMA * R * T)**.5


def prepare(args):
    args.out.mkdir(parents=True, exist_ok=False)
    trip = args.height_mm / 1e3
    run = trip / np.tan(np.deg2rad(20))
    factor = (1, 1.41, 2)[args.level]
    x = np.r_[np.linspace(-.04, 0, round(64*factor), endpoint=False),
              np.linspace(0, run, round(32*factor), endpoint=False),
              np.linspace(run, .09, round(96*factor)+1)]
    if args.inlet_mm < -40:
        n = round((-40 - args.inlet_mm) / .625 * factor)
        x = np.r_[np.linspace(args.inlet_mm/1000, -.04, n, endpoint=False), x]
    nx, ny = len(x)-1, round(64*factor)
    height = .045 - np.clip(x, 0, run)*np.tan(np.deg2rad(20))
    a = args.wall_stretch
    stretch = np.tanh(a * (np.linspace(0,1,ny+1)-.5)) / np.tanh(a/2)
    y = (stretch+1)/2
    nodes = (ny+1)*np.arange(nx+1)
    path = args.out / "mesh.su2"
    with path.open("w", encoding="ascii", newline="\n") as dst:
        dst.write(f"NDIME= 2\nNELEM= {nx*ny}\n")
        for i in range(nx):
            for j in range(ny):
                n, m = nodes[i]+j, nodes[i+1]+j
                dst.write(f"9 {n} {m} {m+1} {n+1}\n")
        dst.write(f"NPOIN= {(nx+1)*(ny+1)}\n")
        for xx, hh in zip(x,height):
            dst.writelines(f"{xx:.15e} {yy*hh:.15e}\n" for yy in y)
        dst.write("NMARK= 4\n")
        groups = {"bottom": zip(nodes[:-1],nodes[1:]), "inlet": zip(np.arange(ny)+1,np.arange(ny)),
                  "outlet": zip(nodes[-1]+np.arange(ny),nodes[-1]+np.arange(ny)+1),
                  "top": zip(nodes[1:]+ny,nodes[:-1]+ny)}
        for name, edges in groups.items():
            dst.write(f"MARKER_TAG= {name}\nMARKER_ELEMS= {nx if name in ('top','bottom') else ny}\n")
            dst.writelines(f"3 {i} {j}\n" for i,j in edges)

    vals = {
        "MACH_NUMBER": str(MACH), "FREESTREAM_TEMPERATURE": f"{T:.12g}",
        "FREESTREAM_PRESSURE": f"{P:.12g}", "REYNOLDS_LENGTH": ".13",
        "REF_LENGTH": ".13", "REF_AREA": ".13",
        "MARKER_SUPERSONIC_INLET": f"(inlet, {T:.12g}, {P:.12g}, {U:.12g}, 0, 0)",
        "MARKER_OUTLET": f"(outlet, {P:.12g})", "MARKER_SYM": "(NONE)",
        "NEWTON_KRYLOV": "NO", "CFL_ADAPT_PARAM": "(1, 1.05, 1, 20, .8)",
    }
    text = args.template.read_text(encoding="utf-8")
    for k,v in vals.items():
        text, n = re.subn(rf"(?m)^{k}\s*=.*$", f"{k}= {v}", text)
        if n != 1:
            raise ValueError(f"missing unique {k}")
    (args.out / "base.cfg").write_text(text, encoding="utf-8")
    record = dict(height_mm=args.height_mm, grid_level=args.level, cells=nx*ny, wall_stretch=a,
                  inlet_mm=args.inlet_mm,
                  exported_flow_nodes=(nx+1)*(ny+1), min_cell_area_m2=float(np.min(np.diff(x) *
                          (height[:-1]+height[1:])*.5)*min(np.diff(y))),
                  first_wall_height_m=[float(min(height)*y[1]),float(max(height)*y[1])],
                  mesh_sha256=sha(path), mach=MACH, U_inf_m_s=U, p_inf_pa=P, T_inf_k=T)
    (args.out / "mesh.json").write_text(json.dumps(record,indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("template", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("--height-mm", type=int, choices=[3,5], default=3)
    p.add_argument("--level", type=int, choices=[0,1,2], default=0)
    p.add_argument("--wall-stretch", type=float, choices=[6.0,9.0], default=6.0)
    p.add_argument("--inlet-mm", type=int, choices=[-40,-430], default=-40)
    prepare(p.parse_args())
