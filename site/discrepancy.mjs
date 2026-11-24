const $ = (selector) => document.querySelector(selector);
const panel = $("#discrepancy");
const probe = $("#axial-probe");
const canvas = $("#wall-plot");
const context = canvas.getContext("2d");
const colors = ["#a7eae2", "#fbc884"];
const fields = {
  mach: {from: 250, to: 405, top: 53, height: 288, legend: "Mach 0 → 5.1"},
  reverse: {from: 305, to: 365, top: 3, height: 212, legend: "U / U∞ −0.09 → 0.60 · warm red marks reversed axial flow"},
};
let flow = "mach", wall = "cf", pairs, refs;

const fixed = (n, digits = 2) => n.toFixed(digits);
const select = () => [pairs.current, pairs[$("#factor").value]];
const rate = (x, left, right) => 100 * (x - left) / (right - left) + "%";

function interpolate(trace, x, col) {
  const index = trace.findIndex((point) => point[0] >= x);
  if (index <= 0) return null;
  const [left, right] = [trace[index - 1], trace[index]];
  return left[col] + (right[col] - left[col]) * (x - left[0]) / (right[0] - left[0]);
}

function draw() {
  const {width, height} = canvas.getBoundingClientRect();
  if (width === 0) return;
  const scale = devicePixelRatio;
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  context.scale(scale, scale);
  const column = wall === "cf" ? 1 : 2;
  const factor = wall === "cf" ? 1000 : 1;
  const low = wall === "cf" ? -1.4 : 0;
  const high = wall === "cf" ? 4 : 0.5;
  const x = (mm) => 36 + (width - 48) * (mm - 310) / 60;
  const y = (v) => 10 + (height - 45) * (high - v) / (high - low);
  const path = (points, color, dashes = []) => {
    context.beginPath();
    context.setLineDash(dashes);
    context.strokeStyle = color;
    points.forEach(([a, b], i) => i ? context.lineTo(a, b) : context.moveTo(a, b));
    context.stroke();
    context.setLineDash([]);
  };
  context.font = "11px system-ui";
  context.fillStyle = "#c6d1de";
  for (const mm of [310, 325, 340, 355, 370]) {
    path([[x(mm), 10], [x(mm), height - 30]], "#3e5067");
    context.textAlign = "center";
    context.fillText(mm, x(mm), height - 12);
  }
  const ticks = wall === "cf" ? [-1, 0, 1, 2, 3, 4] : [0, .1, .2, .3, .4, .5];
  for (const value of ticks) {
    path([[x(310), y(value)], [x(370), y(value)]], value === 0 ? "#91a7bc" : "#3e5067");
    context.textAlign = "right";
    context.fillText(String(value), x(310) - 5, y(value) + 4);
  }
  if (wall === "cf") {
    for (const point of refs["DLR experiment as hosted with MOSE"]) {
      const [a, b] = point.bracket_mm;
      context.fillStyle = "#c7a3ff33";
      context.fillRect(x(a), 10, x(b) - x(a), height - 43);
      path([[x(point.x_mm), 10], [x(point.x_mm), height - 33]], "#c7a3ff", [3, 4]);
    }
  }
  const cases = select();
  for (let i = 0; i < cases.length; i++) {
    const trace = cases[i].trace;
    const points = [310, ...trace.map((p) => p[0]).filter((mm) => mm > 310 && mm < 370), 370];
    context.lineWidth = 2;
    path(points.map((mm) => [x(mm), y(Math.max(low, Math.min(high, interpolate(trace, mm, column) * factor)))]), colors[i]);
    context.lineWidth = 1;
  }
  const position = Number(probe.value);
  path([[x(position), 10], [x(position), height - 30]], "#f4f5f6", [3, 3]);
  const historical = refs["Archived SU2 SST"];
  $("#reference-key").textContent = wall === "cf"
    ? "Scale is 1,000 × Cf. Purple bands mark DLR sample brackets, with interpolated zeros dashed. The archived SU2 SST zeros span " +
      fixed(historical[1].x_mm - historical[0].x_mm) + " mm."
    : "Cp = (p − p∞) / q∞. The DLR markers refer to wall friction zero crossings.";
  $("#probe-reading").textContent = "x = " + fixed(position) + " mm · " + cases.map((entry) =>
    entry.name + " " + fixed(interpolate(entry.trace, position, column) * factor, 3)).join(" / ");
  const limits = fields[flow];
  panel.querySelectorAll(".probe").forEach((line) => {
    line.hidden = position < limits.from || position > limits.to;
    line.style.left = rate(position, limits.from, limits.to);
  });
}

function render() {
  const limits = fields[flow];
  const figures = panel.querySelectorAll("figure");
  select().forEach((entry, i) => {
    const figure = figures[i];
    figure.querySelector("h3").textContent = entry.name;
    figure.querySelector(".score").textContent = fixed(entry.length) + " mm · x " + fixed(entry.separation) + "–" + fixed(entry.reattachment);
    const img = figure.querySelector("img");
    img.src = entry.images[flow];
    img.height = limits.height;
    img.alt = entry.name + (flow === "mach" ? " steady Mach field showing the impinging shock" : " steady near-wall axial velocity");
    figure.querySelector(".axes").textContent = "x " + limits.from + "–" + limits.to + " mm · y 0–" + limits.top + " mm";
    figure.querySelector(".mass").textContent = "Mass " + fixed(entry.mass, 4) + "%";
    const bar = figure.querySelector(".bubble");
    bar.style.left = rate(entry.separation, limits.from, limits.to);
    bar.style.right = rate(limits.to - (entry.reattachment - limits.from), limits.from, limits.to);
  });
  $(".gradient").classList.toggle("reverse", flow === "reverse");
  $("#field-key").textContent = limits.legend;
  draw();
}

try {
  const response = await fetch("discrepancy.json");
  if (!response.ok) throw new Error("Comparison data unavailable.");
  const data = await response.json();
  pairs = Object.fromEntries(data.cases.map((entry) => [entry.id, entry]));
  refs = data.references;
  $("#factor").addEventListener("change", render);
  probe.addEventListener("input", draw);
  for (const [key, action] of [["field", (v) => {flow = v; render();}], ["wall", (v) => {wall = v; draw();}]]) {
    const buttons = panel.querySelectorAll("button[data-" + key + "]");
    for (const button of buttons) button.addEventListener("click", () => {
      for (const peer of buttons) peer.setAttribute("aria-pressed", String(peer === button));
      action(button.dataset[key]);
    });
  }
  render();
  new ResizeObserver(draw).observe(canvas);
} catch (error) {
  $("#probe-reading").textContent = error.message;
}
