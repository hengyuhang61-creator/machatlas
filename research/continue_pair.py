"""Continue a pair on fixed inputs and stop when its wall QoIs stabilize."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from audit_run import field, metrics, wall
from run_native import run, sha


def inspect(path):
    result = metrics(path)
    trace = wall(field(path / 'flow.vtu'))
    result['cp360'] = float(np.interp(0.36, trace[:, 0], trace[:, 2]))
    result['zero_spacing_mm'] = []
    for root in result['wall_zero_crossings']:
        index = np.searchsorted(trace[:, 0], root['x_m'])
        result['zero_spacing_mm'].append(float(1e3 * (trace[index, 0] - trace[index - 1, 0])))
    (path / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def assess(rows):
    if len(rows) < 3 or any(not row['valid_primitives'] or row['native_mass_pct'] >= 0.1
                           or [x['kind'] for x in row['wall_zero_crossings']] != ['separation', 'reattachment']
                           for row in rows):
        return None
    roots = np.array([[1e3 * x['x_m'] for x in row['wall_zero_crossings']] for row in rows])
    qoi = np.column_stack((roots, roots[:, 1] - roots[:, 0], [r['cp360'] for r in rows], [r['CD'] for r in rows]))
    limit = np.r_[np.min([r['zero_spacing_mm'] for r in rows], axis=0) / 2,
                  0.02 * abs(qoi[-1, 2]), 0.002, 0.005 * abs(qoi[-1, 4])]
    span = np.ptp(qoi, axis=0)
    changes = np.diff(qoi, axis=0)
    monotone = (np.all(changes >= 0, axis=0) | np.all(changes <= 0, axis=0)) & (span > limit / 4)
    return {'order': ['separation_mm', 'reattachment_mm', 'length_mm', 'cp360', 'CD'],
            'span': span.tolist(), 'limit': limit.tolist(), 'monotone': monotone.tolist(),
            'pass': bool(np.all(span <= limit) and not monotone.any())}


def continue_run(args):
    chain = []
    current = args.start
    mode = args.label
    completed = args.at
    for _ in range(args.blocks + 1):
        receipt = json.loads((current / 'execution.json').read_text())
        if receipt['exit_code'] != 0 or receipt['artifacts']['restart.dat']['sha256'] != sha(current / 'restart.dat'):
            raise ValueError(f'Unusable restart: {current}')
        data = inspect(current)
        chain.append({'path': current.name, 'at': completed, 'metrics': data})
        gate = assess([row['metrics'] for row in chain[-3:]])
        destination = args.out / f'{mode}-chain.json'
        temporary = destination.with_suffix('.tmp')
        temporary.write_text(json.dumps({'stages': chain, 'gate': gate}, indent=2) + '\n')
        temporary.replace(destination)
        print(mode, completed, [round(x['x_m'] * 1e3, 4) for x in data['wall_zero_crossings']], gate, flush=True)
        if (gate and gate['pass']) or not data['valid_primitives'] or len(chain) > args.blocks:
            return
        completed += args.cadence
        stage = args.out / f'{mode}-{completed}'
        options = SimpleNamespace(exe=args.exe, template=args.template, grid=current / 'mesh.su2',
                                  out=stage, restart=current / 'restart.dat', walls=args.walls,
                                  iters=args.cadence, threads=args.threads, seconds=480, max_rss_mib=2048)
        if run(options):
            raise RuntimeError(f'Native solver stage failed: {stage}')
        current = stage


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('template', type=Path)
    parser.add_argument('start', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('label')
    parser.add_argument('--at', type=int, required=True)
    parser.add_argument('--walls', choices=['adiabatic', 'isothermal'], default='adiabatic')
    parser.add_argument('--threads', type=int, default=3)
    parser.add_argument('--cadence', type=int, default=900)
    parser.add_argument('--blocks', type=int, default=6)
    continue_run(parser.parse_args())
