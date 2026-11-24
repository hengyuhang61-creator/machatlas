import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const data = JSON.parse(readFileSync(new URL("./site/native-study.json", import.meta.url), "utf8"));
test("Mach 5 records preserve all six planned cells and the documented HOLD", () => {
  for (const level of ["coarse", "medium", "fine"]) {
    for (const model of ["sa", "sst"]) {
      const row = data.cases.find((value) => value.id === "m5-" + level + "-" + model);
      assert.ok(row?.cells > 35000);
      assert.ok(row.totalIterations > 1000);
      assert.ok(Number.isFinite(row.massPercent));
    }
  }
  const held = data.cases.find((row) => row.id === "m5-wilcox-drift");
  assert.ok(held.massPercent < .004);
  assert.ok(held.edge_drift_mm > 7.19);
  assert.equal(held.checks, "Stationarity hold");
  assert.equal(data.status, "SCIENTIFIC_VALIDATION_HOLD");
});
test("Research plots are actual PNGs", () => {
  assert.ok(data.cases.length >= 8);
  for (const path of [...data.cases.map((row) => row.image).filter(Boolean),
    "figures/native/m5-wall-comparison.png", "figures/native/m205-transfer.png"]) {
    assert.match(path, /^figures\/native\/[a-z0-9-]+\.png$/);
    const bytes = readFileSync(new URL("./site/" + path, import.meta.url));
    assert.equal(bytes.subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
    assert.ok(bytes.length > 10000);
  }
});
test("Mach 2.05 rows expose the controlled inlet and all planned cells", () => {
  assert.equal(data.ramp.length, 12);
  assert.match(data.rampSummaries[0], /5% with full sample support/);
  assert.equal(new Set(data.ramp.map((row) => row.id)).size, 12);
  for (const row of data.ramp) {
    assert.equal(row.state, "Numerical and inlet checks met");
    assert.ok(row.mass <= .1 && row.upstream_max_mae_pct <= 5);
    assert.ok([2100, 2700].includes(row.totalIterations));
  }
});
