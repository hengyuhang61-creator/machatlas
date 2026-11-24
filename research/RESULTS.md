# Native results

## Mach 5 grid and closure comparison

These are new SU2 8.6.0 solutions. Each row is a two-state numerical comparison on an adiabatic, two-dimensional benchmark grid. The checked categories include finite positive primitives, an open-boundary mass screen, advective energy, local wall-feature drift and last-window drag drift.

| Grid | SU2 cells | Closure | Terminal cumulative iterations | Separation x [mm] | Reattachment x [mm] | Bubble [mm] | Max two-state edge drift [mm] |
|---|---:|---|---:|---:|---:|---:|---:|
| Coarse | 37,275 | SA-neg | 1,350 | 338.133 | 342.930 | 4.797 | 0.025 |
| Medium | 75,639 | SA-neg | 1,350 | 337.825 | 342.922 | 5.097 | 0.061 |
| Fine | 145,765 | SA-neg | 1,350 | 338.021 | 342.608 | 4.586 | 0.033 |
| Coarse | 37,275 | SST-2003m | 4,600 | 321.971 | 345.528 | 23.557 | 0.138 |
| Medium | 75,639 | SST-2003m | 6,000 | 322.048 | 345.186 | 23.138 | 0.225 |
| Fine | 145,765 | SST-2003m | 6,000 | 323.455 | 344.621 | 21.166 | 0.769 |

The plain SST branch predicts much earlier separation than SA on these grids. The SA interval is nonmonotonic with refinement. The SST sequence is monotonic in length, with a larger change on the last refinement. Together with residual iteration sensitivity, the short three-grid sequence does not establish the asymptotic regime or a Grid Convergence Index. The primary case report includes the pressure coefficient at x = 360 mm and the shock proxy at y = 15, 20 and 25 mm. The worst final primary-case mass imbalance was 0.0789% on fine SA. None of these tests establishes a physical error budget.

## Controlled thermal comparison

The same 1,350-iteration SA restart fed the adiabatic and 300 K branches. Each received 900 additional iterations and a 150-iteration follow-up with the same settings. Only the wall thermal condition differed.

| Terminal case | Separation [mm] | Reattachment [mm] | Bubble [mm] | Mass imbalance [%] |
|---|---:|---:|---:|---:|
| Adiabatic | 338.065 | 342.954 | 4.888 | 0.00174 |
| Isothermal 300 K | 339.976 | 342.913 | 2.937 | 0.00156 |

The wall-temperature change moved separation 1.91 mm downstream and shortened the interval by 39.9%. The reattachment changed by 0.040 mm. Small differences should be read alongside local mesh resolution and residual iteration error. The isothermal open-boundary advective-energy difference was about 0.2495% of the inlet flux. Wall heating and cooling change this balance, so no closed-energy conclusion is drawn from that number.

## Physical reference and open discrepancy

The two archived SU2 curves hosted with MOSE yield 5.506 mm for SA and 8.270 mm for SST with adjacent-point crossing interpolation. MOSE's published lengths use a different picking rule. NASA Wind-US input uses a 300 K wall, and archived Wind-US curves give 7.082 mm for SA and 17.092 mm for SST under this interpolation rule. The DLR experimental curve as hosted in MOSE gives approximately 333.74 mm separation and 345.83 mm reattachment, with 3.18 and 2.84 mm point spacing in the respective zero-crossing brackets. Those spacings are sampling intervals, rather than statistical uncertainty estimates.

Current SA is close to the archived SU2 SA interval by this scalar, while current plain SST remains substantially longer than the archived SU2 SST curve. The numerical study cannot isolate this disagreement among solver version, older pseudotime settings, restart path, grid-generation version and model internals. Published Wind-US and MOSE also differ in wall thermal treatment or closure. The DLR archive provides the citation, and NASA explains the experimental velocity dissemination restriction. Full quantitative experimental validation remains on hold.

## Low mass error with drifting wall separation

The stock 8.6.0 SST-Wilcox coarse case is a separate negative result. Native mass imbalance was 0.003997% at iteration 1,700 and 0.003452% at 3,200. The hashes link the later input to the earlier saved restart. Separation moved 7.200 mm and reattachment 1.041 mm, so the predeclared 1 mm stationarity gate rejected that comparison. This diagnosis is about the selected iterative window and leaves later asymptotic behavior open.


## Mach 2.05 matrix and recovery

All twelve ramp cases met the frozen two-station inlet and two-state numerical checks. The initial 5 mm fine-grid states exceeded the 0.1% mass screen at 1,800 iterations. Continuing on the same grids and settings brought final mass imbalance to 0.03744% (SA) and 0.06750% (SST) at 2,700 iterations. On complete support, the model with lower velocity-profile MAE changes with station and sometimes grid. See the [realized matrix and station rankings](M205_RESULTS.md) and the [inlet development and acceptance contract](M205-PILOT-CONTRACT.md).

The [native execution inventory](NATIVE_RUNS.csv) lists 52 stages including pilots, controls and continuations. The [Mach 5 reference comparison](m5-reference-comparison.json) records crossing brackets and common-support errors. The interactive site's [machine-readable tables](../site/native-study.json) include the final values, profiles and numerical checks. The release evidence archive contains the matching native text logs, histories and derived metrics.

[Replay settings](REPRODUCE.md) · [Interactive fields](https://hengyuhang61-creator.github.io/machatlas/research.html) · [Research and source notes](README.md)
