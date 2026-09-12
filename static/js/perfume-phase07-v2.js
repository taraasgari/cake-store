(() => {
  "use strict";

  const root = document.documentElement;
  const key = "velora-theme";

  const valid = value => (
    value === "day"
    || value === "night"
  );

  function storedTheme() {
    try {
      const candidates = [
        localStorage.getItem(key),
        localStorage.getItem("perfume-theme"),
        localStorage.getItem("theme"),
      ];

      for (const item of candidates) {
        if (valid(item)) {
          return item;
        }
      }
    } catch (_) {}

    const current = root.dataset.perfumeTheme;
    return valid(current) ? current : "night";
  }

  function apply(theme) {
    if (!valid(theme)) {
      theme = "night";
    }

    root.dataset.perfumeTheme = theme;
    root.style.colorScheme = (
      theme === "day"
        ? "light"
        : "dark"
    );

    if (document.body) {
      document.body.dataset.perfumeTheme = theme;
      document.body.classList.toggle(
        "theme-day",
        theme === "day"
      );
      document.body.classList.toggle(
        "theme-night",
        theme === "night"
      );
    }

    try {
      localStorage.setItem(key, theme);
      localStorage.setItem("perfume-theme", theme);
      localStorage.setItem("theme", theme);
    } catch (_) {}

    document
      .querySelectorAll("[data-theme-toggle]")
      .forEach(button => {
        const toDay = theme === "night";

        button.setAttribute(
          "title",
          toDay ? "حالت روز" : "حالت شب"
        );

        button.setAttribute(
          "aria-label",
          toDay
            ? "فعال کردن حالت روز"
            : "فعال کردن حالت شب"
        );
      });
  }

  apply(storedTheme());

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      apply(storedTheme());
      setTimeout(
        () => apply(storedTheme()),
        0
      );
    }
  );

  window.addEventListener(
    "click",
    event => {
      const target = event.target;

      if (
        !target
        || !(target instanceof Element)
      ) {
        return;
      }

      const button = target.closest(
        "[data-theme-toggle]"
      );

      if (!button) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();

      const current = (
        valid(root.dataset.perfumeTheme)
          ? root.dataset.perfumeTheme
          : storedTheme()
      );

      apply(
        current === "night"
          ? "day"
          : "night"
      );
    },
    true
  );
})();
