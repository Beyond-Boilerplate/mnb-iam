(() => {
  const rail = document.getElementById("rail");
  const menuBtn = document.getElementById("menuBtn");
  const railClose = document.getElementById("railClose");
  const filter = document.getElementById("lessonFilter");

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

  filter?.addEventListener("input", () => {
    const q = filter.value.trim().toLowerCase();
    document.querySelectorAll(".toc-item").forEach((el) => {
      const hay = el.getAttribute("data-title") || el.textContent || "";
      el.classList.toggle("is-hidden", Boolean(q) && !hay.includes(q));
    });
  });

  // Soft entrance for lesson content
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
