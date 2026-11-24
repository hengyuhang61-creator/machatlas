const summary = document.querySelector("#run-summary");
const selector = document.querySelector("#case-control");
const value = (number, digits) => Number.isFinite(number) ? number.toFixed(digits) : "—";

try {
  const response = await fetch(new URL("./native-study.json", import.meta.url));
  if (!response.ok) throw new Error("HTTP " + response.status);
  const data = await response.json();
  const body = document.querySelector("#matrix-body");
  const appendRow = (target, entries) => {
    const tr = document.createElement("tr");
    for (const entry of entries) {
      const td = document.createElement("td");
      td.textContent = entry;
      tr.append(td);
    }
    target.append(tr);
  };
  for (const row of data.cases) {
    appendRow(body, [row.label, row.cells.toLocaleString(), row.totalIterations.toLocaleString(),
      value(row.x_sep_reatt_mm?.[0],2), value(row.x_sep_reatt_mm?.[1],2),
      value(row.massPercent,4), value(row.edge_drift_mm,3)]);
    if (row.image) selector.add(new Option(row.label, row.id));
  }
  const ramp = document.querySelector("#ramp-body");
  for (const row of data.ramp) {
    appendRow(ramp, [row.label, row.cells?.toLocaleString() ?? "—", row.totalIterations?.toLocaleString() ?? "—",
      value(row.upstream_max_mae_pct,2), value(row.mass,4), row.state]);
  }
  function show() {
    const row = data.cases.find((item) => item.id === selector.value);
    const image = document.querySelector("#flow-image");
    const flow = document.querySelector("#flow-link");
    image.src = row.image;
    image.alt = "Computed Mach, axial velocity, wall shear and pressure for " + row.label;
    flow.href = row.image;
    summary.textContent = row.checks + " · Mass imbalance " + value(row.massPercent,4) +
      "% · wall y+ p95 " + value(row.yPlusP95,2) + " · shock marker at y=20 mm, x=" +
      value(row.shockX20,1) + " mm";
    document.querySelector("#flow-caption").textContent = row.label + " · Native SU2 terminal field · " +
      row.totalIterations.toLocaleString() + " steady iterations over preserved stages.";
  }
  function paragraphs(target, content) {
    document.querySelector(target).replaceChildren(...content.map((item) => {
      const p = document.createElement("p");
      p.textContent = item;
      return p;
    }));
  }
  selector.disabled = false;
  selector.addEventListener("change", show);
  show();
  paragraphs("#study-findings", data.findings);
  paragraphs("#ramp-result", data.rampSummaries);
} catch {
  summary.textContent = "The interactive results could not be loaded. The linked report and fixed plots remain available.";
}
