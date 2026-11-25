import {scoreAt, crossover} from "./metric.mjs";

const section = document.querySelector("#metric-lab");
const status = section.querySelector("output");
try {
  const response = await fetch(new URL("./cases.json", import.meta.url));
  if (!response.ok) throw Error("Missing comparison data.");
  const {ramp} = await response.json();
  const query = new URLSearchParams(location.search);
  const slider = section.querySelector("input");
  const raw = Number(query.get("discount"));
  slider.value = Number.isFinite(raw) && raw >= 0 && raw <= 100 ? raw : 0;
  let selected = Object.hasOwn(ramp, query.get("x")) ? query.get("x") : "10";
  const strip = section.querySelector(".stations");
  const entries = Object.keys(ramp).sort((a,b) => Number(a)-Number(b));
  for (const x of entries) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.x = x;
    button.addEventListener("click", () => {selected=x; render(true);});
    strip.append(button);
  }
  function render(updateUrl) {
    const d = Number(slider.value)/100;
    section.querySelector(".percent").textContent = slider.value + "%";
    let flips=0;
    for (const b of strip.children) {
      const x=b.dataset.x, row=ramp[x];
      const result=scoreAt(row,d).outcome.split(" ")[0];
      if (result !== scoreAt(row,0).outcome.split(" ")[0]) flips++;
      b.textContent = x + " mm · " + result;
      b.dataset.model=result;
      b.setAttribute("aria-pressed",String(x===selected));
    }
    const row=ramp[selected], current=scoreAt(row,d), cross=crossover(row);
    status.textContent = "At " + selected + " mm: " + current.outcome + " · SA " +
      current.values[0].toFixed(5) + " / SST " + current.values[1].toFixed(5) + " · " + row.n + " paired points.";
    section.querySelector(".threshold").textContent = (cross===null ?
      "The same model leads across this sweep." : "The scores cross at " + (cross*100).toFixed(2) + "% here.") +
      " Across all stations, " + flips + " of " + entries.length + " outcomes differ from zero discount.";
    const link=new URL(location.href);
    link.searchParams.set("x",selected);
    link.searchParams.set("discount",slider.value);
    link.hash="metric-lab";
    section.querySelector(".permalink").href=link;
    if (updateUrl) history.replaceState(null,"",link);
  }
  slider.addEventListener("input",()=>render(true));
  section.querySelector(".reverse").addEventListener("click",()=>{slider.value=Number(slider.value)===100?0:100;render(true);});
  render(false);
} catch {
  status.textContent="Comparison data unavailable. Open the source table below.";
}
