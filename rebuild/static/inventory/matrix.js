(() => {
  "use strict";
  const message = text => {
    const box = document.getElementById("matrix-paste-feedback");
    if (box) { box.textContent = text; box.hidden = !text; }
  };
  document.addEventListener("keydown", event => {
    if (!event.target.matches("[data-matrix-input]") || event.altKey || event.ctrlKey || event.metaKey) return;
    const steps = {ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1]};
    const step = steps[event.key];
    if (!step) return;
    const cell = event.target.closest("td");
    const row = Number(cell.dataset.matrixRow) + step[0];
    const column = Number(cell.dataset.matrixColumn) + step[1];
    const next = cell.closest("table").querySelector(`[data-matrix-row="${row}"][data-matrix-column="${column}"] input`);
    event.preventDefault();
    next?.focus();
  });
  document.addEventListener("paste", event => {
    if (!event.target.matches("[data-matrix-input]")) return;
    const text = event.clipboardData?.getData("text/plain");
    if (!text) return;
    event.preventDefault();
    const lines = text.replace(/\r/g, "").replace(/\n$/, "").split("\n").map(line => line.split("\t"));
    if (lines.reduce((sum, line) => sum + line.length, 0) > 400) return message("اللصق يتجاوز400 خلية. لم تُغيّر الكميات.");
    const origin = event.target.closest("td"), table = origin.closest("table");
    const changes = [];
    for (let i = 0; i < lines.length; i++) {
      for (let j = 0; j < lines[i].length; j++) {
        const value = lines[i][j].trim();
        if (value && (!/^\d+$/.test(value) || Number(value) > 1000000)) return message("استخدم أعدادًا صحيحة غير سالبة حتى1000000 دون عناوين SPH/CYL. لم يُطبق اللصق.");
        const row = Number(origin.dataset.matrixRow) + i, column = Number(origin.dataset.matrixColumn) + j;
        const cell = table.querySelector(`[data-matrix-row="${row}"][data-matrix-column="${column}"]`);
        const input = cell?.querySelector("input");
        if (!cell || (!input && value && Number(value) !== 0)) return message("اللصق يخرج عن النطاق أو يشمل خلية غير قابلة للإدخال. لم تُغيّر الكميات.");
        if (input) changes.push([input, value]);
      }
    }
    changes.forEach(([input, value]) => { input.value = value; input.dispatchEvent(new Event("input", {bubbles: true})); });
    message("");
  });
})();
