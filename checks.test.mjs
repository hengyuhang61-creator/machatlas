import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { selectCase } from "./site/compare.mjs";

const data = JSON.parse(readFileSync(new URL("./site/cases.json", import.meta.url), "utf8"));
const fixed = (sample) => sample.values.map((value) => value.toFixed(5));
test("same ramp station reverses the comparison when the metric changes", () => {
  assert.equal(Object.keys(data.ramp).length, 10);
  assert.deepEqual(fixed(selectCase(data, "ramp", "10", "mae")), ["0.05919", "0.04819"]);
  assert.equal(selectCase(data, "ramp", "10", "absBias").outcome, "SA has lower error");
});
test("equal-width cone bands reverse the FUN3D comparison", () => {
  const near = selectCase(data, "cone", undefined, "1.5");
  const far = selectCase(data, "cone", undefined, "12.0");
  assert.deepEqual(fixed(near), ["0.09633", "0.05982"]);
  assert.equal(near.outcome, "SST-Vm has lower error");
  assert.deepEqual(fixed(far), ["0.00740", "0.00796"]);
  assert.equal(far.outcome, "SA has lower error");
});
test("HMVE band difference remains signed and traces to 21 measurement stations", () => {
  assert.equal(Object.keys(data.hmve).length, 21);
  const band = selectCase(data, "hmve", "17.75", "1.5-5.0");
  assert.deepEqual(fixed(band), ["0.60229", "0.63663"]);
  assert.equal(band.outcome, "Low minus high: -0.03433");
});
test("missing comparison data and unknown keys fail explicitly", () => {
  assert.throws(() => selectCase(data, "cone", undefined, "no such band"), TypeError);
  assert.throws(() => selectCase(data, "unknown"), RangeError);
});
test("public cases link to real PNG files", () => {
  for (const name of ["ramp", "cone", "hmve"]) {
    const path = new URL("./site/figures/" + name + ".png", import.meta.url);
    assert.equal(readFileSync(path).subarray(0, 8).toString("hex"), "89504e470d0a1a0a");
    assert.match(readFileSync(new URL("./site/" + name + ".html", import.meta.url), "utf8"),
      new RegExp('figures/' + name + '\\.png'));
  }
});
test("fresh replay reproduces committed results when ATLAS_REPLAY is set", {
  skip: !process.env.ATLAS_REPLAY,
}, () => {
  const replayed = JSON.parse(readFileSync(process.env.ATLAS_REPLAY, "utf8"));
  function compare(expected, actual) {
    if (typeof expected === "number") {
      assert.ok(Math.abs(expected - actual) <= 1e-10, expected + " vs " + actual);
      return;
    }
    assert.deepEqual(Object.keys(expected), Object.keys(actual));
    for (const key of Object.keys(expected)) compare(expected[key], actual[key]);
  }
  compare(data, replayed);
});

test("discount sweeps preserve the endpoints and solve each interior tie", async () => {
  const {scoreAt,crossover}=await import("./site/metric.mjs");
  const flips=[];
  for (const [x,row] of Object.entries(data.ramp)) {
    assert.deepEqual(scoreAt(row,0).values,row.mae);
    const end=scoreAt(row,1);
    row.absBias.forEach((v,i)=>assert.ok(Math.abs(end.values[i]-v)<1e-12));
    const d=crossover(row);
    if (d!==null) {
      assert.equal(scoreAt(row,d).outcome,"Tie");
      flips.push(Number(x));
    }
  }
  assert.deepEqual(flips.sort((a,b)=>a-b),[10,20,50,60]);
});
