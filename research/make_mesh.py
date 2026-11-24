"""Generate and audit one 2-D grid from the pinned upstream Gmsh geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

import gmsh
import numpy as np

GEOMETRY_SHA = "1ce690dc763a61052cb0a3e968789f7e9d07ffbbea12c184f7eb7e2955636f99"
LEVELS = {"coarse": 1.0, "medium": 1.41, "fine": 2.0}


def mesh(source, level, out):
    original = source.read_bytes()
    digest = hashlib.sha256(original).hexdigest()
    if digest != GEOMETRY_SHA:
        raise ValueError(f"unexpected upstream geometry SHA-256: {digest}")
    factor = LEVELS[level]
    geometry, count = re.subn(r"(?m)^f\s*=\s*1\.41;", f"f = {factor};", original.decode())
    if count != 1:
        raise ValueError("expected exactly one mesh factor declaration")
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(dir=out) as temp:
        geo = Path(temp) / "grid.geo"
        geo.write_text(geometry, encoding="utf-8")
        gmsh.initialize()
        try:
            gmsh.option.setNumber("General.NumThreads", 1)
            gmsh.open(str(geo))
            gmsh.model.mesh.generate(2)
            types, tags, _ = gmsh.model.mesh.getElements(2)
            sicn = gmsh.model.mesh.getElementQualities(np.concatenate(tags), "minSICN")
            groups = {gmsh.model.getPhysicalName(dim, tag): [
                int(i) for i in gmsh.model.getEntitiesForPhysicalGroup(dim, tag)
            ] for dim, tag in gmsh.model.getPhysicalGroups(1)}
            if set(groups) != {"bottom", "inlet", "outlet", "top", "sym"} or min(sicn) <= 0:
                raise ValueError("wrong boundary set or nonpositive signed cell quality")
            gmsh.write(str(out / "mesh.su2"))
            report = dict(gmsh=gmsh.__version__, level=level, factor=factor, source_sha256=digest,
                          nodes=len(gmsh.model.mesh.getNodes()[0]),
                          cell_types={gmsh.model.mesh.getElementProperties(t)[0]: len(x)
                                      for t, x in zip(types, tags)},
                          min_sicn=float(min(sicn)), quantiles_sicn=np.quantile(sicn, [0.01,.5,.99]).tolist(),
                          geometry_groups=groups)
        finally:
            gmsh.finalize()
    report["mesh_sha256"] = hashlib.sha256((out / "mesh.su2").read_bytes()).hexdigest()
    (out / "mesh.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("geometry", type=Path)
    cli.add_argument("level", choices=LEVELS)
    cli.add_argument("out", type=Path)
    args = cli.parse_args()
    mesh(args.geometry, args.level, args.out)
