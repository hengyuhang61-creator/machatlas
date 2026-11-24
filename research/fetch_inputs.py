"""Retrieve upstream inputs by checksum. Store third-party files outside the source tree."""
import argparse
from hashlib import sha256
from pathlib import Path
from urllib.request import urlopen

VANDV = "86a7f94ea29949f4d5e7f034d1d04ac3ef04a844"
SU2 = "7048fd35f56d4bf52e586429d6746a36a10255f8"
RAW = "https://raw.githubusercontent.com/"
FILES = {
    "VandV-geometry.geo": (f"su2code/VandV/{VANDV}/rans/swbli/geometry_and_mesh.geo",
                           "1ce690dc763a61052cb0a3e968789f7e9d07ffbbea12c184f7eb7e2955636f99"),
    "official-v8.6.0-sa.cfg": (f"su2code/SU2/{SU2}/TestCases/vandv/rans/swbli/config_sa.cfg",
                              "d6acdeb1d4c53bb8feecce83b4efd48175f4b8d6209edf7914d40f08b93f299f"),
    "official-v8.6.0-sst.cfg": (f"su2code/SU2/{SU2}/TestCases/vandv/rans/swbli/config_sst.cfg",
                               "27dbc3f718d2bbcc143d6ddc7497bebeaa0db5db56b46aed04f5dc393e743798"),
}


def save(path, data, expected):
    if sha256(data).hexdigest() != expected:
        raise ValueError(f"hash mismatch for {path.name}")
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"refusing to replace {path.name}")
    path.write_bytes(data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in FILES.items():
        path = args.out / name
        if path.exists():
            data = path.read_bytes()
        else:
            with urlopen(RAW + url, timeout=45) as response:
                data = response.read()
        save(path, data, expected)
        print(name, expected)
    upstream = (args.out / "official-v8.6.0-sst.cfg").read_bytes()
    key = b"SST_OPTIONS= V2003m, COMPRESSIBILITY-WILCOX"
    if upstream.count(key) != 1:
        raise ValueError("missing expected variant control")
    save(args.out / "sst-v2003m.cfg", upstream.replace(key,b"SST_OPTIONS= V2003m"),
         "4e106660c7c24d3ac3bae7a46eea39698bfd735020f883a0e9c1c522eeea60bf")
