# Supersonic outlet shear traction in SU2 8.5.0 and 8.6.0

An identical planar shear field exposes a difference in the first update to the transverse momentum density at a supersonic outlet. The 8.5.0 dedicated outlet and both versions' ordinary pressure outlet give about −2,000 kg/(m² s²) on the coarse grid. The 8.6.0 dedicated outlet gives $4.65\times10^{-9}$ kg/(m² s²), close to the analytic zero. The ordinary pressure outlet remains a missing-traction control within the same 8.6.0 executable. [Case data and hashes](../../site/viscous-outlet.json)

## Physical balance

The initial field has $u(y)=700+S(y-H/2)$ m/s, $v=0$, $\rho=1$ kg/m³ and $p=100{,}000$ Pa. Here $H=0.016$ m, the streamwise length is 0.04 m, $S=2{,}000$ s⁻¹ and the constant viscosity is 0.001 Pa·s. At the outlet, the transverse traction on the $+x$ face is $\tau_{yx}=\mu\,\partial u/\partial y=2$ Pa. This balances the traction on the opposite face of the boundary control volume. The transverse convective contribution has zero divergence in the initial field. If the outlet traction is omitted while the opposite face remains, the control-volume rate becomes $-\mu S/(\Delta x/2)$. This predicts −2,000 on $\Delta x=2$ mm and −4,000 on $\Delta x=1$ mm.

| SU2 | Outlet marker | Cells | Slope (s⁻¹) | Median $\Delta(\rho v)/\Delta t$ (kg/(m² s²)) |
| --- | --- | ---: | ---: | ---: |
| 8.5.0 | Dedicated supersonic | 20×16 | 2,000 | −2,000 |
| 8.5.0 | Ordinary pressure | 20×16 | 2,000 | −2,000 |
| 8.6.0 | Dedicated supersonic | 20×16 | 2,000 | $4.65\times10^{-9}$ |
| 8.6.0 | Ordinary pressure | 20×16 | 2,000 | −2,000 |
| 8.5.0 / 8.6.0 | Dedicated supersonic | 20×16 | 0 | 0 / $-8.91\times10^{-12}$ |
| 8.6.0 | Dedicated supersonic | 40×32 | 2,000 | $9.29\times10^{-9}$ |
| 8.6.0 | Ordinary pressure | 40×32 | 2,000 | −4,000 |

The check uses the center half of the outlet, with 9 coarse and 17 fine nodes whose normal Mach numbers exceed 1.8. The same strip one cell inside and at mid-domain remains at zero. The offset on the ordinary pressure outlet doubles when the boundary control-volume width halves, while both 8.6.0 coarse configurations give the same outlet mass flow to the tested precision. The data support a change to the local solution update. The quantities follow from one explicit $10^{-7}$ s step. The mesh pair tests the mechanism's scaling. Steady convergence, general grid uncertainty, turbulence response and experiment validation remain unassessed.

## Source and reuse

The 8.5.0 dedicated outlet has its viscous block commented out. [SU2 PR #2829](https://github.com/su2code/SU2/pull/2829) restores the block at the dedicated outlet, uses the interior primitive state on both sides, and adds a separate Mach 4 laminar flat-plate regression with fixed iteration-100 outputs. The ordinary-pressure-outlet viscous block remains commented out in both versions. Its supersonic branch extrapolates the convective state from inside. These source facts, the same-binary marker comparison, zero-shear control and finite-volume prediction support attribution in this case. An isolated source-patch build and the upstream Mach 4 regression were outside the run matrix. [8.5.0 source](https://github.com/su2code/SU2/blob/12eb826f049ef7f67df974dfcb44cf36ee07c0f8/SU2_CFD/src/solvers/CEulerSolver.cpp#L7508) · [8.6.0 source](https://github.com/su2code/SU2/blob/7048fd35f56d4bf52e586429d6746a36a10255f8/SU2_CFD/src/solvers/CEulerSolver.cpp#L7715)

Download and extract the [native archive](https://github.com/hengyuhang61-creator/machatlas/releases/download/v0.3.2/viscous-outlet-native.zip). It contains all eight native runs with original configuration, mesh, initial ASCII restart, final ASCII restart, history, log and recording hashes. [Archive release and SHA-256 list](https://github.com/hengyuhang61-creator/machatlas/releases/tag/v0.3.2)

```sh
python research/viscous-outlet/analyze_archive.py viscous-outlet-native --out local-results.json
python research/viscous-outlet/replay.py /path/to/SU2_CFD local-supersonic
python research/viscous-outlet/replay.py /path/to/SU2_CFD local-pressure --marker pressure
```

Use Python 3.11 or later. Replaying the cases uses the OpenMP release executable with one thread and a 60-second timeout. The analyzer verifies the archived Windows binary IDs, case inputs, node coordinates, step size and rate. To compare a fresh Linux or other build, use the individual replay JSON and the documented tolerances. The archive contains original study inputs and outputs. [SU2 8.5.0 binaries](https://github.com/su2code/SU2/releases/tag/v8.5.0) · [SU2 8.6.0 binaries](https://github.com/su2code/SU2/releases/tag/v8.6.0) · [Upstream LGPL-2.1](https://github.com/su2code/SU2/blob/v8.6.0/LICENSE.md)
