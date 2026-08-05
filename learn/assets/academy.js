(() => {
  const rail = document.getElementById("rail");
  const toc = document.getElementById("toc");
  const menuBtn = document.getElementById("menuBtn");
  const railClose = document.getElementById("railClose");
  const filter = document.getElementById("lessonFilter");
  const PATH_KEY = "mnb-academy-path-v1";
  const TOC_SCROLL_KEY = "mnb-academy-toc-scroll";

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

  const saveTocScroll = () => {
    if (!toc) return;
    try {
      sessionStorage.setItem(TOC_SCROLL_KEY, String(toc.scrollTop));
    } catch {
      /* ignore */
    }
  };

  const restoreTocScroll = () => {
    if (!toc) return;
    let restored = false;
    try {
      const raw = sessionStorage.getItem(TOC_SCROLL_KEY);
      if (raw != null) {
        const y = Number(raw);
        if (Number.isFinite(y)) {
          toc.scrollTop = y;
          restored = true;
        }
      }
    } catch {
      /* ignore */
    }
    if (restored) return;
    // First visit / no saved mark: keep the active lesson in view without jumping to top.
    toc.querySelector('.toc-item[aria-current="page"]')?.scrollIntoView({
      block: "nearest",
      inline: "nearest",
    });
  };

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
    restoreTocScroll();
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
        ? "Showing Core Path + specialist (51–110) + Enterprise Sandbox (201–250)."
        : "Entry-level: Lessons 01–50 + mid-capstones. Specialist and Sandbox stay hidden until you opt in.";
    }
    applyFilters();
  };

  const applyFilters = () => {
    const q = (filter?.value || "").trim().toLowerCase();
    const mode = getPathMode();
    const showAll = mode === "all";
    const isOptIn = (path) => path === "specialist" || path === "sandbox";
    document.querySelectorAll(".toc-item, .toc-track").forEach((el) => {
      const path = el.getAttribute("data-path") || "core";
      const pathHide = !showAll && isOptIn(path);
      const hay = el.getAttribute("data-title") || el.textContent || "";
      const textHide = Boolean(q) && el.classList.contains("toc-item") && !hay.includes(q);
      el.classList.toggle("is-hidden", pathHide || textHide);
    });
    document
      .querySelectorAll(".card[data-path], .specialist-grid, #specialist, #sandbox, .sandbox-grid")
      .forEach((el) => {
        if (
          el.id === "specialist" ||
          el.id === "sandbox" ||
          el.classList.contains("specialist-grid") ||
          el.classList.contains("sandbox-grid")
        ) {
          el.classList.toggle("is-hidden", !showAll);
          return;
        }
        const path = el.getAttribute("data-path") || "core";
        el.classList.toggle("is-hidden", !showAll && isOptIn(path));
      });
    ["specialist", "sandbox"].forEach((id) => {
      const h2 = document.getElementById(id);
      if (!h2) return;
      const lede = h2.nextElementSibling;
      if (lede && lede.classList.contains("lede-sm")) {
        lede.classList.toggle("is-hidden", !showAll);
      }
    });
  };

  document.querySelectorAll(".path-toggle .path-btn").forEach((btn) => {
    btn.addEventListener("click", () => setPathMode(btn.getAttribute("data-path") || "core"));
  });

  filter?.addEventListener("input", applyFilters);

  // Keep left-panel scroll position across full page lesson navigations.
  let scrollSaveTimer = 0;
  toc?.addEventListener(
    "scroll",
    () => {
      window.clearTimeout(scrollSaveTimer);
      scrollSaveTimer = window.setTimeout(saveTocScroll, 50);
    },
    { passive: true }
  );
  toc?.addEventListener("click", (e) => {
    if (e.target.closest("a.toc-item")) saveTocScroll();
  });
  document.querySelector(".pager")?.addEventListener("click", (e) => {
    if (e.target.closest("a[href$='.html']")) saveTocScroll();
  });

  applyPathMode(getPathMode());
  restoreTocScroll();
  requestAnimationFrame(() => {
    restoreTocScroll();
    requestAnimationFrame(restoreTocScroll);
  });

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
