/**
 * Meridian academy progress (localStorage) + lesson verify report ingest.
 * No server submission — learners keep reports under ~/iiq-lab-evidence/verify/.
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

  const renderPanel = () => {
    const host = document.getElementById("verifyPanel");
    if (!host) return;
    const stem = stemFromPath() || host.dataset.stem;
    const data = load();
    const entry = stem ? data[stem] : null;
    const status = entry
      ? `<p class="verify-status verify-${(entry.verdict || "").toLowerCase()}">Last result: <strong>${entry.verdict}</strong> · ${entry.checkedAt || ""}</p>`
      : `<p class="verify-status">No verify report saved yet for this lesson.</p>`;

    let gaps = "";
    if (entry?.gaps?.length) {
      gaps =
        "<ul class='verify-gaps'>" +
        entry.gaps.map((g) => `<li><code>${g.id}</code> — ${g.message}<br/><span class="muted">${g.detail || ""}</span></li>`).join("") +
        "</ul>";
    }

    host.innerHTML = `
      <h2>Lesson verify</h2>
      <p class="muted">After you finish the lab, run the CLI against your IIQ (local by default), then paste the JSON report here. Progress stays in this browser only.</p>
      <pre class="verify-cmd">./tools/iiq-verify/verify-lesson.sh ${lessonNum(stem) || "NN"}</pre>
      ${status}
      ${gaps}
      <label class="verify-label">Paste verify JSON
        <textarea id="verifyJson" rows="8" placeholder='{ "schema": "mnb-lesson-verify-report/v1", ... }'></textarea>
      </label>
      <div class="verify-actions">
        <button type="button" class="btn primary" id="verifyIngest">Save result</button>
        <button type="button" class="btn ghost" id="verifyClear">Clear this lesson</button>
      </div>
      <p id="verifyMsg" class="muted" role="status"></p>
    `;

    host.querySelector("#verifyIngest")?.addEventListener("click", () => {
      const msg = host.querySelector("#verifyMsg");
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

  // Index progress chip
  const ensureProgressChip = () => {
    const top = document.querySelector(".topbar");
    if (!top || document.getElementById("progressBar")) return;
    const el = document.createElement("span");
    el.id = "progressBar";
    el.className = "progress-chip";
    el.title = "Lessons with a PASS verify report in this browser";
    top.insertBefore(el, top.querySelector(".lab-link"));
  };

  // Inject verify panel before pager on lesson pages
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

  ensureProgressChip();
  ensurePanel();
  paintToc();
  renderPanel();

  // Expose for debugging
  window.MnbAcademyProgress = { load, save, ingestReport, paintToc };
})();
