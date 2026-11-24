import { readFileSync, statSync } from "node:fs";
import { strict as assert } from "node:assert";
import { test } from "node:test";

test("public pair data retains stable independent solver results and source brackets", () => {
  const root = new URL("./site/", import.meta.url);
  const data = JSON.parse(readFileSync(new URL("discrepancy.json", root), "utf8"));
  const [current, earlier, cold] = data.cases;
  assert.deepEqual(data.cases.map((entry) => entry.id), ["current", "earlier", "cold"]);
  assert.ok(current.length - earlier.length > 15);
  assert.ok(current.length - cold.length > 4 && current.length - cold.length < 5);
  for (const entry of data.cases) {
    assert.ok(entry.qualifiedWallTail);
    assert.ok(entry.mass < 0.1);
    assert.ok(Math.abs(entry.reattachment - entry.separation - entry.length) < 1e-8);
    assert.ok(entry.trace[0][0] < 310 && entry.trace.at(-1)[0] > 370);
    for (const image of Object.values(entry.images)) assert.ok(statSync(new URL(image, root)).size < 150_000);
  }
  const [separation, reattachment] = data.references["DLR experiment as hosted with MOSE"];
  for (const reference of [separation, reattachment]) {
    assert.ok(reference.bracket_mm[0] < reference.x_mm && reference.x_mm < reference.bracket_mm[1]);
  }
});
