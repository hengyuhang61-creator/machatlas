import { selectCase } from "./compare.mjs";

function options(select, values, label, initial) {
  select.replaceChildren(...values.map((value) => new Option(label(Number(value)), value)));
  select.value = initial;
}

function bars(element, sample, scale) {
  element.replaceChildren(...sample.values.map((value, index) => {
    const row = document.createElement("div");
    row.className = "row";
    const name = document.createElement("span");
    name.textContent = sample.labels[index];
    const track = document.createElement("span");
    track.className = "track";
    const fill = document.createElement("i");
    fill.style.width = Math.min(100, Math.max(0, value / scale * 100)) + "%";
    track.append(fill);
    const number = document.createElement("span");
    number.className = "number";
    number.textContent = value.toFixed(5);
    row.append(name, track, number);
    return row;
  }));
}

const lab = document.querySelector(".lab");
if (lab) {
  const output = document.querySelector("#readout");
  try {
    const response = await fetch(new URL("./cases.json", import.meta.url));
    if (!response.ok) throw new Error("HTTP " + response.status);
    const data = await response.json();
    const key = lab.dataset.case;
    const station = lab.querySelector("#station");
    const band = lab.querySelector("#band, #metric");
    if (key === "ramp") options(station, Object.keys(data.ramp).sort((a,b) => a-b), x => "x = " + x + " mm", "10");
    if (key === "cone") options(band, Object.keys(data.cone).sort((a,b) => a-b), y => y + "–" + (y + 3) + " mm", "1.5");
    if (key === "hmve") options(station, Object.keys(data.hmve).sort((a,b) => a-b), x => "x = " + (x * 25.4).toFixed(2) + " mm", "17.75");
    // Use a fixed scale per case so the width of a bar stays comparable as the selector moves.
    const scale = {
      ramp: Math.max(...Object.values(data.ramp).flatMap(({mae,absBias}) => [...mae, ...absBias])),
      cone: Math.max(...Object.values(data.cone).flat()),
      hmve: 1.15,
    }[key];

    function render() {
      const sample = selectCase(data, key, station?.value, band.value);
      bars(lab.querySelector(".bars"), sample, scale);
      const values = sample.values.map((value, i) => sample.labels[i] + " " + value.toFixed(5));
      output.textContent = sample.outcome + " · " + values.join(" / ") + " · " + sample.description;
    }

    station?.addEventListener("change", render);
    band.addEventListener("change", render);
    render();
  } catch {
    output.textContent = "Comparison data unavailable. Follow the replay table link below.";
  }
}
