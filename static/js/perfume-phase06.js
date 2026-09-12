(() => {
  "use strict";

  function setTheme(theme){
    document.documentElement.dataset.perfumeTheme = theme;
    try { localStorage.setItem("velora-theme", theme); } catch (_) {}
  }

  document.addEventListener("click", event => {
    const btn = event.target.closest("[data-theme-toggle]");
    if(!btn) return;

    const current = document.documentElement.dataset.perfumeTheme || "night";
    setTheme(current === "night" ? "day" : "night");
  });

  document.addEventListener("DOMContentLoaded", () => {
    try {
      const saved = localStorage.getItem("velora-theme");
      if(saved === "day" || saved === "night"){
        document.documentElement.dataset.perfumeTheme = saved;
      }
    } catch (_) {}
  });
})();
