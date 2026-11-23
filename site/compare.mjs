export function paired(labelA, labelB, values, description, lowerIsBetter) {
  if (!Array.isArray(values) || values.length !== 2 || !values.every(Number.isFinite)) {
    throw new TypeError("Two finite archived values are required.");
  }
  const [a,b] = values;
  const outcome = lowerIsBetter
    ? (Math.abs(a - b) <= 1e-12 ? "Tie" : (a < b ? labelA : labelB) + " has lower error")
    : "Low minus high: " + (a - b).toFixed(5);
  return { labels:[labelA, labelB], values, outcome, description };
}

export function selectCase(data, key, station, choice) {
  switch (key) {
    case "ramp": {
      const row = data.ramp[station];
      return paired("SA", "SST", row[choice], row.n + " common PIV samples", true);
    }
    case "cone":
      return paired("SA", "SST-Vm", data.cone[choice], "Fixed 3 mm radial band", true);
    case "hmve":
      return paired("ReD 1.0M", "ReD 2.25M", data.hmve[station][choice], "Experiment / experiment", false);
    default:
      throw new RangeError("Unknown atlas case");
  }
}
