(() => {
  const rail = document.getElementById("rail");
  const menuBtn = document.getElementById("menuBtn");
  const railClose = document.getElementById("railClose");
  const filter = document.getElementById("lessonFilter");
  const PATH_KEY = "mnb-academy-path-v1";

  const close = () => {
    rail?.classList.remove("is-open");
    document.body.classList.remove("rail-open");
  };
  const open = () => {
    rail?.classList.add("is-open");
    document.body.classList.add("rail-open");
  };

  menuBtn?.addEventListener("click", open);
  railClose?.addEventListener("click", close);
  document.body.addEventListener("click", (e) => {
    if (!document.body.classList.contains("rail-open")) return;
    if (rail?.contains(e.target) || menuBtn?.contains(e.target)) return;
    close();
  });

  const getPathMode = () => {
    try {
      return localStorage.getItem(PATH_KEY) || "core";
    } catch {
      return "core";
    }
  };

  const setPathMode = (mode) => {
    try {
      localStorage.setItem(PATH_KEY, mode);
    } catch {
      /* ignore */
    }
    applyPathMode(mode);
  };

  const applyPathMode = (mode) => {
    const showAll = mode === "all";
    document.body.classList.toggle("path-all", showAll);
    document.body.classList.toggle("path-core", !showAll);
    document.querySelectorAll(".path-toggle .path-btn").forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-path") === mode);
    });
    const hint = document.getElementById("pathHint");
    if (hint) {
      hint.textContent = showAll
        ? "Showing Core Path + specialist tracks (51–110)."
        : "Entry-level: Lessons 01–50 + mid-capstones. Specialist tracks stay hidden until you opt in.";
    }
    applyFilters();
  };

  const applyFilters = () => {
    const q = (filter?.value || "").trim().toLowerCase();
    const mode = getPathMode();
    const showAll = mode === "all";
    document.querySelectorAll(".toc-item, .toc-track").forEach((el) => {
      const path = el.getAttribute("data-path") || "core";
      const pathHide = !showAll && path === "specialist";
      const hay = el.getAttribute("data-title") || el.textContent || "";
      const textHide = Boolean(q) && el.classList.contains("toc-item") && !hay.includes(q);
      el.classList.toggle("is-hidden", pathHide || textHide);
    });
    document.querySelectorAll(".card[data-path], .specialist-grid, #specialist").forEach((el) => {
      if (el.id === "specialist" || el.classList.contains("specialist-grid")) {
        el.classList.toggle("is-hidden", !showAll);
        return;
      }
      const path = el.getAttribute("data-path") || "core";
      el.classList.toggle("is-hidden", !showAll && path === "specialist");
    });
    const specH2 = document.getElementById("specialist");
    if (specH2) {
      const lede = specH2.nextElementSibling;
      if (lede && lede.classList.contains("lede-sm")) {
        lede.classList.toggle("is-hidden", !showAll);
      }
    }
  };

  document.querySelectorAll(".path-toggle .path-btn").forEach((btn) => {
    btn.addEventListener("click", () => setPathMode(btn.getAttribute("data-path") || "core"));
  });

  filter?.addEventListener("input", applyFilters);

  applyPathMode(getPathMode());

  const main = document.getElementById("main");
  if (main && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    main.animate(
      [
        { opacity: 0, transform: "translateY(6px)" },
        { opacity: 1, transform: "translateY(0)" },
      ],
      { duration: 320, easing: "cubic-bezier(.2,.7,.2,1)" }
    );
  }
})();
