"use strict";
const printButton = document.getElementById("print-labels");
if (printButton) {
  printButton.hidden = false;
  printButton.addEventListener("click", () => window.print());
}
