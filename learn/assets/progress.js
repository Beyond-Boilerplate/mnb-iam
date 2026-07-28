/**
 * Meridian academy progress — localStorage + live Verify only (no JSON paste).
 */
(() => {
  const KEY = "mnb-academy-progress-v1";

  const load = () => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "{}");
    } catch {
      return {};
    }
  };
  const save = (data) => localStorage.setItem(KEY, JSON.stringify(data));

  const stemFromPath = () => {
    const m = location.pathname.match(/\/(\d{2,3}-[^/]+)\.html$/);
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
      const total = document.querySelectorAll(".toc-item").length || 1;
      const passed = Object.values(data).filter((e) => e && e.verdict === "PASS").length;
      bar.textContent = `${passed} / ${total} verified`;
      bar.style.setProperty("--pct", `${Math.min(100, Math.round((passed / total) * 100))}%`);
    }
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
      const res = await fetch(`/api/verify/${encodeURIComponent(num)}`, { method: "POST" });
      let report;
      try {
        report = await res.json();
      } catch {
        throw new Error(`Verify API returned non-JSON (HTTP ${res.status})`);
      }
      if (!report.stem) report.stem = stem;
      const saved = applyLiveReport(report, stem);
      const gapN = saved.gaps?.length || 0;
      msgEl.textContent =
        saved.verdict === "PASS"
          ? `PASS — all checks green`
          : `FAIL — ${gapN} gap(s). Fix in IIQ, then Verify now again.`;
      renderPanel();
    } catch (e) {
      msgEl.textContent =
        "Verify API unavailable. Use ./tools/lab/up.sh or ./tools/lab/docker/up.sh — " +
        (e.message || e);
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

    host.innerHTML = `
      <h2>Lesson verify</h2>
      <p class="muted">Progress updates only from a <strong>live</strong> check of your IIQ lab. Pasting or editing JSON cannot mark a lesson PASS.</p>
      ${status}
      ${gaps}
      <div class="verify-actions">
        <button type="button" class="btn primary" id="verifyRun">Verify now</button>
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
    if (!stemFromPath()) return;
    if (document.getElementById("verifyPanel")) return;
    const main = document.getElementById("main");
    const pager = main?.querySelector(".pager");
    if (!main || !pager) return;
    const panel = document.createElement("section");
    panel.id = "verifyPanel";
    panel.className = "verify-panel";
    panel.dataset.stem = stemFromPath();
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

  window.MnbAcademyProgress = { load, paintToc, runVerify };
})();
