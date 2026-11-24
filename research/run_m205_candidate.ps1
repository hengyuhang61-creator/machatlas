param(
 [Parameter(Mandatory)][ValidateSet(3,5)][int]$Height,
 [Parameter(Mandatory)][ValidateSet(0,1,2)][int]$Level,
 [Parameter(Mandatory)][ValidateSet('sa','sst')][string]$Model,
 [Parameter(Mandatory)][string]$Python,
 [Parameter(Mandatory)][string]$Piv,
 [int]$Threads=4
)
$ErrorActionPreference='Stop'
$grid="grids/m205-$($Height)mm-l$Level-$Model"
$name="m205-$($Height)mm-l$Level-$Model"
$first="runs/$name-1800"
$tail="runs/$name-2100"
$template=if($Model -eq 'sa'){'upstream/official-v8.6.0-sa.cfg'}else{'upstream/sst-v2003m.cfg'}
& $Python make_ramp_pilot.py $template $grid --height-mm $Height --level $Level --wall-stretch 9 --inlet-mm -430
if($LASTEXITCODE){throw "Grid preparation failed: $name"}
$exe='upstream/su2-8.6.0/bin/SU2_CFD.exe'
& $Python run_native.py $exe "$grid/mesh.su2" "$grid/base.cfg" $first --iters 1800 --threads $Threads --seconds 1500 --max-rss-mib 1500
if($LASTEXITCODE){throw "Native run failed: $name"}
& $Python audit_run.py $first --out "$first/metrics.json"
if($LASTEXITCODE){throw "Native state audit failed: $name"}
& $Python audit_m205.py $first $Piv --out "$first/piv.json"
if($LASTEXITCODE){throw "Profile audit failed: $name"}
$metrics=Get-Content "$first/metrics.json" -Raw | ConvertFrom-Json
$pivCheck=Get-Content "$first/piv.json" -Raw | ConvertFrom-Json
if(-not $metrics.valid_primitives -or $metrics.native_mass_pct -gt .1 -or $metrics.advective_energy_pct -gt .5 -or $pivCheck.gate -ne 'CHECKS_MET'){
 "$name ended at 1800; upstream/profile or numerical gate failed."
 exit 8
}
& $Python run_native.py $exe "$grid/mesh.su2" "$grid/base.cfg" $tail --restart "$first/restart.dat" --iters 300 --threads $Threads --seconds 480 --max-rss-mib 1500
if($LASTEXITCODE){throw "Native continuation failed: $name"}
& $Python audit_run.py $tail --out "$tail/metrics.json"
if($LASTEXITCODE){throw "Native state audit failed: $name"}
& $Python audit_m205.py $tail $Piv --out "$tail/piv.json"
if($LASTEXITCODE){throw "Continuation profile audit failed: $name"}
