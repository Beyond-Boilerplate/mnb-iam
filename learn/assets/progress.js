/**
 * Meridian academy progress (localStorage) + live verify via local academy server.
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

  const ingestReport = (report) => {
    if (!report || report.schema !== "mnb-lesson-verify-report/v1") {
      if (report && report.verdict) {
        // tolerate minimal payload from API errors
        const stem = report.stem || stemFromPath();
        if (!stem) throw new Error("Report missing stem");
        const data = load();
        data[stem] = {
          verdict: report.verdict,
          checkedAt: report.checkedAt || new Date().toISOString(),
          gaps: report.gaps || [],
          summary: report.summary,
          target: report.target,
          error: report.error,
        };
        save(data);
        paintToc();
        return data[stem];
      }
      throw new Error("Not a Meridian verify report (expected schema mnb-lesson-verify-report/v1)");
    }
    const stem = report.stem;
    if (!stem) throw new Error("Report missing stem");
    const data = load();
    data[stem] = {
      verdict: report.verdict,
      checkedAt: report.checkedAt,
      gaps: report.gaps || [],
      summary: report.summary,
      target: report.target,
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
      const report = await res.json();
      if (!report.stem) report.stem = stem;
      if (!report.schema && report.verdict) {
        // attach schema if verifier returned full report already
      }
      const saved = ingestReport(
        report.schema === "mnb-lesson-verify-report/v1"
          ? report
          : { ...report, schema: "mnb-lesson-verify-report/v1", stem, lesson: num }
      );
      msgEl.textContent = `${saved.verdict} — ${saved.gaps?.length || 0} gap(s)`;
      renderPanel();
    } catch (e) {
      msgEl.textContent =
        "Verify API unavailable. Start the academy server: python3 tools/academy/serve.py — " +
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
      ? `<p class="verify-status verify-${(entry.verdict || "").toLowerCase()}">Last result: <strong>${entry.verdict}</strong> · ${entry.checkedAt || ""}</p>`
      : `<p class="verify-status">No verify result yet for this lesson.</p>`;

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
      <p class="muted">Click <strong>Verify now</strong> to check your local (or configured) IIQ lab. Progress stays in this browser.</p>
      ${status}
      ${gaps}
      <div class="verify-actions">
        <button type="button" class="btn primary" id="verifyRun">Verify now</button>
        <button type="button" class="btn ghost" id="verifyClear">Clear this lesson</button>
      </div>
      <details class="verify-advanced">
        <summary>Advanced: paste CLI JSON</summary>
        <label class="verify-label">Paste verify JSON
          <textarea id="verifyJson" rows="6" placeholder='{ "schema": "mnb-lesson-verify-report/v1", ... }'></textarea>
        </label>
        <button type="button" class="btn ghost" id="verifyIngest">Save pasted result</button>
      </details>
      <p id="verifyMsg" class="muted" role="status"></p>
    `;

    const msg = host.querySelector("#verifyMsg");
    host.querySelector("#verifyRun")?.addEventListener("click", () => {
      runVerify(stem, msg, host.querySelector("#verifyRun"));
    });
    host.querySelector("#verifyIngest")?.addEventListener("click", () => {
      try {
        const report = JSON.parse(host.querySelector("#verifyJson").value);
        const saved = ingestReport(report);
        msg.textContent = `Saved ${saved.verdict} for ${stem || report.stem}`;
        renderPanel();
      } catch (e) {
        msg.textContent = String(e.message || e);
      }
    });
    host.querySelector("#verifyClear")?.addEventListener("click", () => {
      if (!stem) return;
      const data = load();
      delete data[stem];
      save(data);
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
    el.title = "Lessons with a PASS verify report in this browser";
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

  window.MnbAcademyProgress = { load, save, ingestReport, paintToc, runVerify };
})();
