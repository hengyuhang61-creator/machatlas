import {readFileSync} from "node:fs";
import {crossover, scoreAt} from "./site/metric.mjs";

const {ramp}=JSON.parse(readFileSync(new URL("./site/cases.json",import.meta.url),"utf8"));
const rows=Object.entries(ramp).sort(([a],[b])=>a-b).map(([x,row])=>({
  station_mm:Number(x), paired_points:row.n, crossing_discount:crossover(row),
  mae:scoreAt(row,0).values, abs_mean_bias:scoreAt(row,1).values
}));
console.log(JSON.stringify(rows,null,2));
