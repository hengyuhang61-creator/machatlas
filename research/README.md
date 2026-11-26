# Native shock–boundary-layer interaction study

**Publication scope.** These are new two-dimensional steady RANS solutions generated with native SU2 8.6.0. Numerical checks are reported separately from experimental validation. The solver data and settings underpin the [interactive research page](https://hengyuhang61-creator.github.io/machatlas/research.html).

## Mach 5

The Schülein benchmark uses an oblique shock from a 10° generator impinging on the opposite flat plate. This study uses the public SU2 V&V geometry, including its 10 mm slip-wall inlet extension. Gmsh 4.15.2 generates three meshes using the published factors 1, 1.41 and 2. Their quadrilateral and triangle counts are read after generation. The Gmsh node count contains a construction-curve inventory; use the exported SU2 flow-node count when quoting solver size.

The free-stream input is Mach 5, 4006.88 Pa and 68.3333 K. The solver uses calorically perfect air, Sutherland viscosity, Roe flux with limited MUSCL and first-order turbulence advection. The default walls in both archived SU2 VTU setups carry zero heat flux. This differs from NASA Wind-US study 2 (540 °R, 300 K) and MOSE's isothermal cases. An explicitly labeled same-grid SA continuation changes only the thermal wall condition, with both branches starting from the same restart and receiving the same number of iterations.

SA uses `WITHFT2, NEGATIVE`. The legacy-style SST grid comparison uses `V2003m`. A separate coarse SST branch retains the stock SU2 8.6.0 `COMPRESSIBILITY-WILCOX` option. The archived SU2 7.4 input had no Wilcox flag and different pseudotime controls. Even the current plain-label SST branch does not establish equal implementations with SU2 7.4, MOSE or Wind-US.

## Numerical evidence

- The raw run directory contains the SU2 log, generated case, mesh, history, binary restart and full native VTU. Receipt hashes link each continuation to its input restart and preserve the exact settings. The public release bundles metrics and figures, input recipes and selected histories, so full solver fields can be rebuilt from the original inputs.
- Per-marker native mass is signed inward. With impermeable walls and slip boundaries the scope is inlet and outlet. The screen is |signed net mass| / gross inflow ≤ 0.1%. A second integral uses trapezoids of exported density and normal velocity along the same boundaries.
- The energy screen uses the advective total enthalpy (c_p T + |u|^2/2) and a 0.5% working tolerance on adiabatic runs. Boundary diffusive terms and, for SST, additional modeled-energy terms are outside that independent estimate. The isothermal branch has heat exchange, so it is excluded from a zero-net advection test.
- Compute (C_f) zero crossings with linear interpolation between adjacent wall points. Compare two terminal states separated by at least 100 iterations. A local movement above 1 mm or last-100 integrated drag drift above 1% fails the stationarity screen. The Mach 5 shock marker is the steepest normalized density rise over a 1 mm secant at y = 20 mm. It is a spatial proxy, not a tracked material front.
- Working tolerances were frozen before the first run. Snapshots represent pseudo-iterations of steady equations. The media compare computed states without representing physical time.

## Mach 2.05

The Stanford TMR campaign measured three-dimensional confined flows for 3 and 5 mm top ramps. The 2-D numerical test section follows a 45 mm-height idealization at (−40 ≤ x ≤ 90) mm. For the uniform inlet, published nominal stagnation conditions of 303 K and 255.3 kPa produce 164.629 K, 30.184 kPa and 527.298 m/s at Mach 2.05 under the stated gas assumption. The existing public 3 mm CFD config lists 4006.88 Pa, which cannot be treated as equivalent to that unit-Reynolds condition.

An upstream comparison at two pre-ramp x stations is required before grid/model comparison. The initial short-domain variants fall outside this gate. The controlled lead-in experiment added a 390 mm section upstream with unchanged test-section mesh and wall clustering. This is a two-dimensional boundary-layer development model; the Stanford facility's incoming three-dimensional state and spanwise variation remain independent evidence requirements. The 5 mm comparison evaluates the CFD at actual native PIV x coordinates nearest the two nominal stations, both within 0.25 mm.

## Sources and rights

- [SU2 V&V public Mach 5 study](https://su2code.github.io/vandv/swbli/) · [pinned geometry](https://github.com/su2code/VandV/blob/86a7f94ea29949f4d5e7f034d1d04ac3ef04a844/rans/swbli/geometry_and_mesh.geo) · [SU2 8.6.0 LGPL-2.1 license](https://github.com/su2code/SU2/blob/v8.6.0/LICENSE.md). Input files are fetched at pinned digests, including the VandV geometry without a declared repository license. Third-party code and geometry files remain in the replay cache.
- [NASA NPARC Mach 5 benchmark](https://www.grc.nasa.gov/www/wind/valid/m5swbli/m5swbli.html) · [Wind-US input](https://www.grc.nasa.gov/www/wind/valid/m5swbli/study02/uns_SA.dat) · [DLR report catalog](https://elib.dlr.de/21724/). The NASA archive restricts dissemination of experimental velocity data. Public reference scalar comparisons use only the curves hosted with MOSE and their stated provenance.
- [MOSE 2D SWBLI reference](https://github.com/open-hydra/MOSE/blob/001ff493ead61833744c522267ef53cb01b2a562/docs/vv/2D-swbli.md) · [source and reference files](https://github.com/open-hydra/MOSE/tree/001ff493ead61833744c522267ef53cb01b2a562/test/2D/viscous/swbli) · [model-variant PR #46](https://github.com/open-hydra/MOSE/pull/46). Raw MOSE, Wind-US and experimental data files are outside the release.
- [TMR Stanford ramp data](https://tmbwg.github.io/turbmodels/Other_exp_Data/sbliM2.05_exp.html) · [pinned public computational example](https://github.com/ofirnirr/SU2-SWBLI-Mach-2-RANS-Validation/tree/2b2be8c4e982af6e97542237aeaaf9da615707bd) · [benchmark coverage audit](https://github.com/hengyuhang61-creator/cfd-profile-audit/tree/657a81d888186e89a5ff30d83cd2c8b1453a179b). Neither raw PIV nor third-party model exports are bundled. Reports, derived own outputs and original tooling are covered by the project license.

[Native results](RESULTS.md) · [Upstream review](UPSTREAM_REVIEW.md) · [Replay commands](REPRODUCE.md)

[Mach 5 discrepancy investigation and replay](DISCREPANCY.md)

[SU2 wall heat-flux output, paired native releases and analytic control](heat-flux/README.md)

[SU2 8.5.0 / 8.6.0 supersonic viscous outlet, one-step laminar transverse momentum balance](viscous-outlet/README.md) · [Machine-readable study record](../site/viscous-outlet.json)
