## Mach 2.05 realized matrix

| Ramp / grid / model | Cells | Iterations | Max upstream MAE [%] | Mass error [%] | Separation / reattachment [mm] | Max edge drift [mm] | Disposition |
|---|---:|---:|---:|---:|---|---:|---|
| 3 mm · L1 · SA | 52224 | 2100 | 2.287 | 0.01156 | 32.03 / 40.39 | 0.002 | Numerical and inlet checks met |
| 3 mm · L1 · SST | 52224 | 2100 | 1.422 | 0.01165 | 29.12 / 42.86 | 0.008 | Numerical and inlet checks met |
| 3 mm · L2 · SA | 103500 | 2100 | 2.290 | 0.01553 | 31.77 / 40.53 | 0.009 | Numerical and inlet checks met |
| 3 mm · L2 · SST | 103500 | 2100 | 1.228 | 0.01716 | 28.36 / 42.67 | 0.084 | Numerical and inlet checks met |
| 3 mm · L3 · SA | 208896 | 2100 | 2.285 | 0.05805 | 31.77 / 40.44 | 0.178 | Numerical and inlet checks met |
| 3 mm · L3 · SST | 208896 | 2100 | 1.124 | 0.06116 | 28.43 / 42.36 | 0.412 | Numerical and inlet checks met |
| 5 mm · L1 · SA | 52224 | 2100 | 1.954 | 0.01017 | 17.88 / 37.40 | 0.009 | Numerical and inlet checks met |
| 5 mm · L1 · SST | 52224 | 2100 | 1.798 | 0.01399 | 10.91 / 40.01 | 0.079 | Numerical and inlet checks met |
| 5 mm · L2 · SA | 103500 | 2100 | 1.980 | 0.01866 | 17.58 / 37.26 | 0.075 | Numerical and inlet checks met |
| 5 mm · L2 · SST | 103500 | 2100 | 1.764 | 0.03889 | 10.57 / 39.39 | 0.444 | Numerical and inlet checks met |
| 5 mm · L3 · SA | 208896 | 2700 | 1.995 | 0.03744 | 17.67 / 37.17 | 0.233 | Numerical and inlet checks met |
| 5 mm · L3 · SST | 208896 | 2700 | 1.802 | 0.06750 | 10.69 / 38.99 | 0.547 | Numerical and inlet checks met |

Window for the bottom-wall crossings is x = 0–65 mm. The study publishes Cp at x = 30 and 50 mm and near-wall y+ metrics in the machine-readable evidence.

### Per-station model preference on complete support

| Ramp | Grid | Comparable stations | Lower MAE with SA | Lower MAE with SST |
|---|---|---|---|---|
| 3 mm | L1 | -30, -20, -10, 0, 10, 20, 30, 40, 50, 60 | 0, 10, 20, 40, 50 | -30, -20, -10, 30, 60 |
| 3 mm | L2 | -30, -20, -10, 0, 10, 20, 30, 40, 50, 60 | 0, 20, 40, 50 | -30, -20, -10, 10, 30, 60 |
| 3 mm | L3 | -30, -20, -10, 0, 10, 20, 30, 40, 50, 60 | 0, 20, 40, 50 | -30, -20, -10, 10, 30, 60 |
| 5 mm | L1 | -30, -10, 0, 10, 30, 50 | 10 | -30, -10, 0, 30, 50 |
| 5 mm | L2 | -30, -10, 0, 10, 30, 50 | 10, 50 | -30, -10, 0, 30 |
| 5 mm | L3 | -30, -10, 0, 10, 30, 50 | 10, 50 | -30, -10, 0, 30 |

Stations are nominal axial x in mm. Where available the solver is evaluated at the actual archived PIV x. The rankings compare supported axial velocity points within one ramp, station and grid. Differences in station sets and sample support prevent pooling rankings across ramp heights. The two-dimensional calculations do not resolve three-dimensional side-wall effects or experimental pointwise uncertainty.
