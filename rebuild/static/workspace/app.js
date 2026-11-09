(() => {
  "use strict";
  let copyTimer;
  const notify = (text) => {
    const box = document.getElementById("copy-feedback");
    if (!box) return;
    box.textContent = text;
    box.classList.add("visible");
    clearTimeout(copyTimer);
    copyTimer = setTimeout(() => box.classList.remove("visible"), 3500);
  };
  const prepare = () => {
    const field = document.getElementById("id_token");
    const token = new URLSearchParams(location.hash.slice(1)).get("token");
    if (field && token) {
      field.value = token;
      field.closest(".field")?.setAttribute("hidden", "");
      history.replaceState(null, "", location.pathname);
    }
    const error = document.querySelector(".notice-error[tabindex]");
    error?.focus();
  };
  document.addEventListener("DOMContentLoaded", prepare);
  document.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id === "app-shell") document.getElementById("page-title")?.focus();
    prepare();
  });
  document.addEventListener("click", async (event) => {
    const open = event.target.closest("[data-open-dialog]");
    if (open) document.getElementById(open.dataset.openDialog)?.showModal();
    const close = event.target.closest("[data-close-dialog]");
    if (close) close.closest("dialog")?.close();
    const copy = event.target.closest("[data-copy-target]");
    if (copy) {
      const field = document.getElementById(copy.dataset.copyTarget);
      try {
        await navigator.clipboard.writeText(field.value);
        notify("نُسخ الرابط.");
      } catch {
        field.focus();
        field.select();
        notify("حُدد الرابط؛ يمكنك نسخه من الحقل.");
      }
    }
  });
  document.addEventListener("submit", (event) => {
    if (event.target.method === "post" && event.submitter) {
      event.submitter.disabled = true;
      event.submitter.dataset.submitted = "true";
      event.submitter.setAttribute("aria-busy", "true");
    }
  });
  window.addEventListener("pageshow", () => {
    document.querySelectorAll("[data-submitted]").forEach(button => {
      button.disabled = false;
      button.removeAttribute("aria-busy");
      delete button.dataset.submitted;
    });
  });
})();
