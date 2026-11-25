import {paired} from "./compare.mjs";

export function scoreAt(row, discount) {
  if (!Number.isFinite(discount) || discount < 0 || discount > 1) throw new RangeError("Use a discount between zero and one.");
  const values = row.mae.map((mae, i) => (1 - discount) * mae + discount * row.absBias[i]);
  return paired("SA", "SST", values, row.n + " common samples", true);
}

export function crossover(row) {
  const start = row.mae[0] - row.mae[1];
  const end = row.absBias[0] - row.absBias[1];
  return start * end < 0 ? start / (start - end) : null;
}
