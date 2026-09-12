(() => {
  "use strict";
  document.addEventListener("click", (event) => {
    document.querySelectorAll("details[data-pa-account][open]").forEach((menu) => {
      if (!menu.contains(event.target)) menu.removeAttribute("open");
    });
  });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    document.querySelectorAll("details[data-pa-account][open]").forEach((menu) => {
      menu.removeAttribute("open");
    });
  });
})();
