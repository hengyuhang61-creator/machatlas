# Replay native Mach 5

Use Python 3.13 and the [SU2 8.6.0 release](https://github.com/su2code/SU2/releases/tag/v8.6.0). SHA-256 for Windows OpenMP is `4bc28b656def415b4d22c8274af2473dd719aa5ebfa6bc1c95c08b1bac26508c`. The Linux OpenMP archive has digest `b306dcb7e76caec54e376542916aae14a32abd6c2f6fa8b871ec10ffe80b41ac`. Gmsh may require the system OpenGL Utility library on Linux. Execute the following from this directory. Replace the example executable path with the local path. Use a dedicated Python environment.

```sh
python -m pip install -r requirements.txt
python fetch_inputs.py upstream
python make_mesh.py upstream/VandV-geometry.geo coarse grids/coarse
python run_native.py /path/to/SU2_CFD grids/coarse/mesh.su2 upstream/official-v8.6.0-sa.cfg runs/m5-coarse-sa-pilot --iters 300 --threads 6 --seconds 600
python audit_run.py runs/m5-coarse-sa-pilot --out runs/m5-coarse-sa-pilot/metrics.json
python run_native.py /path/to/SU2_CFD grids/coarse/mesh.su2 upstream/official-v8.6.0-sa.cfg runs/m5-coarse-sa-1200 --restart runs/m5-coarse-sa-pilot/restart.dat --iters 900 --threads 6 --seconds 900
python run_native.py /path/to/SU2_CFD grids/coarse/mesh.su2 upstream/official-v8.6.0-sa.cfg runs/m5-coarse-sa-confirm --restart runs/m5-coarse-sa-1200/restart.dat --iters 150 --threads 6 --seconds 300
python audit_run.py runs/m5-coarse-sa-confirm --out runs/m5-coarse-sa-confirm/metrics.json
python plot_native.py runs/m5-coarse-sa-confirm coarse.png --title "Mach 5 | coarse SA-neg"
```

For medium and fine, pass those names to `make_mesh.py`. For SST use `upstream/sst-v2003m.cfg` for the legacy-style matrix and `upstream/official-v8.6.0-sst.cfg` for the Wilcox branch. Use fresh directories. A continuation supplies the previous `restart.dat`. Preserve all generations. A mismatched upstream digest must be resolved before using a fetched input. The run inventory records stage order, iteration caps, elapsed times, initial restart hashes and output hashes. Reproducibility across platforms permits small numerical and Gmsh node-order differences.

For the Mach 2.05 pilot choose the ramp height and level with `make_ramp_pilot.py`, and use its generated `mesh.su2` and `base.cfg` as native inputs. The upstream profile check imports the public [cfd-profile-audit](https://github.com/hengyuhang61-creator/cfd-profile-audit/tree/657a81d888186e89a5ff30d83cd2c8b1453a179b) package in that Python environment. Download the 3 mm PIV station CSV through the [pinned SWBLI benchmark input manifest](https://github.com/hengyuhang61-creator/swbli-physics-bench/blob/d1f488778142859aff05bca5d766a7da4f9afa7d/sources/inputs.json). For 5 mm, download the [original archive](https://tmbwg.github.io/turbmodels/Other_exp_Data/sbliM2.05_exp.html) and run `extract_piv5.py` with SciPy to obtain the two qualified columns in a local cache. Then pass the appropriate file to `audit_m205.py` and record the support, error and disposition.

The GitHub Actions smoke test generates the real coarse geometry and starts a small native Linux solve. It checks a finite field and output structure at 20 iterations. The scientific study is the much longer Windows run series recorded separately.

### Final Mach 2.05 matrix

Use `--inlet-mm -430 --wall-stretch 9` on the grid generator. Levels 0, 1 and 2 are L1, L2 and L3 in the report. Use `upstream/official-v8.6.0-sa.cfg` or `upstream/sst-v2003m.cfg` as the generator template. Add `--sections` to the 5 mm PIV extractor to reproduce the downstream station comparison. Keep these PIV CSVs in a local cache.

The Windows driver `run_m205_candidate.ps1` uses the initial 1,800-iteration stage and stops if the early gates are missed. For both 5 mm L3 cases, continue from the 1,800 checkpoint for 600 iterations on the identical grid and setup, then continue from that restart for 300 iterations. Run both auditors on the resulting 2,400 and 2,700 checkpoints. Coarse 3 mm SA uses the completed extended pilot with 1,600 + 500 iterations. The remaining nine cells use 1,800 + 300 iterations. The [execution inventory](NATIVE_RUNS.csv) records the stage names and restart linkage.

For a populated study directory, run `study_data.py STUDY M5_PLAN.json M5_EVIDENCE.json` and `publish_results.py STUDY M5_EVIDENCE.json NATIVE_STUDY.json` to reconstruct the machine-readable results. Run `report_m205.py NATIVE_STUDY.json M205_RESULTS.md` for the matrix and station comparison. The release logs support auditing the published checks without rerunning the complete study.
