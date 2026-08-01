/**
 * Meridian academy progress — localStorage + live Verify only (no JSON paste).
 */
(() => {
  const KEY = "mnb-academy-progress-v1";
  let apiAvailable = null; // null=unknown, true/false after probe

  const load = () => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}");
    } catch {
      return {};
    }
  };
  const save = (data) => localStorage.setItem(KEY, JSON.stringify(data));

  const stemFromPath = () => {
    const m = location.pathname.match(
      /\/((?:\d{2,3}[a-z]?-|mid-\d+-|first-90-days)[^/]*)\.html$/
    );
    return m ? m[1] : null;
  };

  const lessonNum = (stem) => (stem || "").split("-", 1)[0];

  const paintToc = () => {
    const data = load();
    document.querySelectorAll(".toc-item").forEach((el) => {
      const href = el.getAttribute("href") || "";
      const stem = href.replace(/\.html$/, "");
      const entry = data[stem];
      el.classList.remove("is-passed", "is-failed");
      if (!entry) return;
      if (entry.verdict === "PASS") el.classList.add("is-passed");
      if (entry.verdict === "FAIL") el.classList.add("is-failed");
    });
    const bar = document.getElementById("progressBar");
    if (bar) {
      const mode = (() => {
        try {
          return localStorage.getItem("mnb-academy-path-v1") || "core";
        } catch {
          return "core";
        }
      })();
      const items = [...document.querySelectorAll(".toc-item")].filter((el) => {
        if (mode === "all") return true;
        return (el.getAttribute("data-path") || "core") === "core";
      });
      const total = items.length || 1;
      const stems = new Set(
        items.map((el) => (el.getAttribute("href") || "").replace(/\.html$/, ""))
      );
      const passed = Object.entries(data).filter(
        ([stem, e]) => stems.has(stem) && e && e.verdict === "PASS"
      ).length;
      bar.textContent = `${passed} / ${total} verified`;
      bar.style.setProperty("--pct", `${Math.min(100, Math.round((passed / total) * 100))}%`);
      bar.title =
        mode === "core"
          ? "Core Path lessons with a live PASS verify in this browser"
          : "All lessons with a live PASS verify in this browser";
    }
  };

  const probeApi = async () => {
    try {
      const res = await fetch("/api/health", { method: "GET", cache: "no-store" });
      apiAvailable = res.ok;
    } catch {
      apiAvailable = false;
    }
    return apiAvailable;
  };

  /** Persist only reports produced by the live verify API. */
  const applyLiveReport = (report, expectedStem) => {
    if (!report || typeof report !== "object") {
      throw new Error("Empty verify response");
    }
    const stem = report.stem || expectedStem;
    if (!stem) throw new Error("Report missing stem");
    if (expectedStem && report.stem && report.stem !== expectedStem) {
      throw new Error(`Report stem mismatch (got ${report.stem}, expected ${expectedStem})`);
    }
    const verdict = report.verdict === "PASS" ? "PASS" : "FAIL";
    const data = load();
    data[stem] = {
      verdict,
      source: "live-verify",
      checkedAt: report.checkedAt || new Date().toISOString(),
      gaps: report.gaps || [],
      summary: report.summary,
      target: report.target,
      error: report.error,
    };
    save(data);
    paintToc();
    return data[stem];
  };

  const runVerify = async (stem, msgEl, btn) => {
    const num = lessonNum(stem);
    msgEl.textContent = "Running checks against your IIQ lab…";
    if (btn) btn.disabled = true;
    try {
      const ok = await probeApi();
      if (!ok) {
        throw new Error(
          "Verify API is not on this host. On a laptop run ./tools/lab/up.sh (or docker/up.sh), then open http://localhost:4173/ — or wait for the academy image with /api/verify to deploy."
        );
      }
      const res = await fetch(`/api/verify/${encodeURIComponent(num)}`, { method: "POST" });
      const ctype = res.headers.get("content-type") || "";
      if (!ctype.includes("application/json")) {
        const hint =
          res.status === 405
            ? "This page is still being served as static HTML (no Verify API). Redeploy mnb-iam-learn or use ./tools/lab/up.sh locally."
            : `HTTP ${res.status}`;
        throw new Error(hint);
      }
      const report = await res.json();
      if (!report.stem) report.stem = stem;
      const saved = applyLiveReport(report, stem);
      const gapN = saved.gaps?.length || 0;
      msgEl.textContent =
        saved.verdict === "PASS"
          ? `PASS — all checks green`
          : `FAIL — ${gapN} gap(s). Fix in IIQ, then Verify now again.`;
      renderPanel();
    } catch (e) {
      msgEl.textContent = String(e.message || e);
    } finally {
      if (btn) btn.disabled = false;
    }
  };

  const renderPanel = () => {
    const host = document.getElementById("verifyPanel");
    if (!host) return;
    const stem = stemFromPath() || host.dataset.stem;
    const data = load();
    const entry = stem ? data[stem] : null;
    const status = entry
      ? `<p class="verify-status verify-${(entry.verdict || "").toLowerCase()}">Last live verify: <strong>${entry.verdict}</strong> · ${entry.checkedAt || ""}</p>`
      : `<p class="verify-status">Not verified yet — run <strong>Verify now</strong> against your IIQ lab.</p>`;

    let gaps = "";
    if (entry?.gaps?.length) {
      gaps =
        "<ul class='verify-gaps'>" +
        entry.gaps
          .map(
            (g) =>
              `<li><code>${g.id}</code> — ${g.message}<br/><span class="muted">${g.detail || ""}</span>${
                g.hint ? `<br/><span class="muted">hint: ${g.hint}</span>` : ""
              }</li>`
          )
          .join("") +
        "</ul>";
    }

    const apiNote =
      apiAvailable === false
        ? `<p class="verify-status verify-fail">Verify API not reachable here. Use <code>./tools/lab/up.sh</code> or <code>./tools/lab/docker/up.sh</code> and open <a href="http://localhost:4173/${stem || ""}.html">localhost:4173</a>, or wait for the public academy deploy that includes <code>/api/verify</code>.</p>`
        : `<p class="muted">Progress updates only from a <strong>live</strong> check of your IIQ lab. Pasting or editing JSON cannot mark a lesson PASS.</p>`;

    host.innerHTML = `
      <h2>Lesson verify</h2>
      ${apiNote}
      ${status}
      ${gaps}
      <div class="verify-actions">
        <button type="button" class="btn primary" id="verifyRun" ${apiAvailable === false ? "disabled" : ""}>Verify now</button>
        <button type="button" class="btn ghost" id="verifyClear">Clear this lesson</button>
      </div>
      <p id="verifyMsg" class="muted" role="status"></p>
    `;

    const msg = host.querySelector("#verifyMsg");
    host.querySelector("#verifyRun")?.addEventListener("click", () => {
      runVerify(stem, msg, host.querySelector("#verifyRun"));
    });
    host.querySelector("#verifyClear")?.addEventListener("click", () => {
      if (!stem) return;
      const next = load();
      delete next[stem];
      save(next);
      paintToc();
      renderPanel();
    });
  };

  const ensureProgressChip = () => {
    const top = document.querySelector(".topbar");
    if (!top || document.getElementById("progressBar")) return;
    const el = document.createElement("span");
    el.id = "progressBar";
    el.className = "progress-chip";
    el.title = "Lessons with a live PASS verify in this browser";
    top.insertBefore(el, top.querySelector(".lab-link"));
  };

  const ensurePanel = () => {
    const stem = stemFromPath();
    if (!stem || stem === "first-90-days") return;
    if (document.getElementById("verifyPanel")) return;
    const main = document.getElementById("main");
    const pager = main?.querySelector(".pager");
    if (!main || !pager) return;
    const panel = document.createElement("section");
    panel.id = "verifyPanel";
    panel.className = "verify-panel";
    panel.dataset.stem = stem;
    main.insertBefore(panel, pager);
  };

  const pointLabLinkLocal = () => {
    const link = document.querySelector(".lab-link");
    if (!link) return;
    if (location.hostname === "localhost" || location.hostname === "127.0.0.1") {
      link.href = "http://localhost:8080/identityiq/login.jsf";
      link.textContent = "Open local IIQ ↗";
    }
  };

  ensureProgressChip();
  ensurePanel();
  pointLabLinkLocal();
  paintToc();
  renderPanel();
  probeApi().then(() => renderPanel());

  window.MnbAcademyProgress = { load, paintToc, runVerify, probeApi };
})();
