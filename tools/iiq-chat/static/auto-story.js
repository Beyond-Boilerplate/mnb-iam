/* Meridian Auto-story — Ready queue + run trace UI */
(() => {
  const EVENT_TYPES = [
    "RUN_START",
    "STATUS",
    "THINK",
    "DECIDE",
    "PLAN",
    "MCP_CALL",
    "MCP_RESULT",
    "MCP_DRY",
    "JIRA",
    "VERIFY",
    "HANDOFF",
    "ERROR",
  ];

  const state = {
    view: "queue",
    runs: [],
    examples: [],
    queue: [],
    selectedIssue: null,
    selected: null,
    events: [],
    artifacts: {},
    eventIndex: null,
    typeOn: Object.fromEntries(EVENT_TYPES.map((t) => [t, true])),
    artTab: "summary",
    selectedStory: null,
    jobId: null,
    pollTimer: null,
  };

  const $ = (id) => document.getElementById(id);

  function setStatus(msg, isError = false) {
    const el = $("as-status");
    el.textContent = msg;
    el.classList.toggle("is-error", isError);
  }

  function setBusy(busy) {
    ["btn-dry", "btn-live", "poll-jira"].forEach((id) => {
      const el = $(id);
      if (el) el.disabled = busy || (id !== "poll-jira" && !state.selectedIssue && !state.selectedStory);
    });
    if (!busy) updateActionButtons();
  }

  function updateActionButtons() {
    const can = !!(state.selectedIssue || (state.selectedStory && state.selectedStory.fixture));
    $("btn-dry").disabled = !can;
    $("btn-live").disabled = !state.selectedIssue; // live only for real Jira issues
  }

  async function api(path, opts) {
    const res = await fetch(path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || res.statusText || "request failed");
    return data;
  }

  function fmtTime(ts) {
    if (!ts) return "—";
    try {
      return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return String(ts).slice(11, 19);
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function renderTypeFilters() {
    const host = $("type-filters");
    if (!host) return;
    host.innerHTML = "";
    for (const t of EVENT_TYPES) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "as-chip" + (state.typeOn[t] ? "" : " is-off");
      b.textContent = t;
      b.addEventListener("click", () => {
        state.typeOn[t] = !state.typeOn[t];
        renderTypeFilters();
        renderTimeline();
      });
      host.appendChild(b);
    }
  }

  function renderQueue() {
    const host = $("queue-list");
    host.innerHTML = "";
    if (!state.queue.length) {
      host.innerHTML =
        '<p class="as-muted" style="padding:0.5rem;opacity:0.7">No agent-ready issues. Click Poll Jira, or add label <code>agent-ready</code> on a To Do story.</p>';
      return;
    }
    for (const issue of state.queue) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "as-run-item" + (state.selectedIssue && state.selectedIssue.key === issue.key ? " is-active" : "");
      const labels = (issue.labels || []).join(", ");
      btn.innerHTML = `<span class="k">${escapeHtml(issue.key)}</span><span class="m">${escapeHtml(issue.summary || "")}</span><span class="m">${escapeHtml(labels || issue.status || "")}</span>`;
      btn.addEventListener("click", () => selectQueueIssue(issue));
      host.appendChild(btn);
    }
  }

  function selectQueueIssue(issue) {
    state.selectedIssue = issue;
    state.selectedStory = null;
    renderQueue();
    updateActionButtons();
    const labels = (issue.labels || []).map((l) => `<span class="as-badge cap-MCP_E2E">${escapeHtml(l)}</span>`).join(" ");
    $("queue-detail").innerHTML = `
      <p class="eyebrow">${escapeHtml(issue.status || "To Do")} · ${escapeHtml(issue.issuetype || "Story")}</p>
      <h3>${escapeHtml(issue.key)} — ${escapeHtml(issue.summary || "")}</h3>
      <p>${labels}</p>
      <p class="as-muted" style="white-space:pre-wrap">${escapeHtml((issue.description || "").slice(0, 2500))}</p>
      <p style="margin-top:1rem" class="as-muted">Dry-run plans without writes. Start live mutates IIQ and moves Jira → In Progress → In Review (never Done).</p>`;
    $("as-title").textContent = issue.key;
    $("as-crumb").textContent = "Ready queue";
    setStatus(`Selected ${issue.key} — Dry-run or Start live`);
  }

  function renderRunList() {
    const q = ($("run-filter").value || "").trim().toLowerCase();
    const host = $("run-list");
    host.innerHTML = "";
    const filtered = state.runs.filter((r) => {
      if (!q) return true;
      return `${r.issue} ${r.run_id} ${r.summary || ""}`.toLowerCase().includes(q);
    });
    if (!filtered.length) {
      host.innerHTML = '<p class="as-muted" style="padding:0.5rem;opacity:0.7">No runs yet. Start from Queue or Stories.</p>';
      return;
    }
    for (const r of filtered) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "as-run-item" +
        (state.selected && state.selected.issue === r.issue && state.selected.runId === r.run_id
          ? " is-active"
          : "");
      btn.innerHTML = `<span class="k">${r.issue}</span><span class="m">${r.run_id}</span><span class="m">${r.summary || r.outcome || ""}</span>`;
      btn.addEventListener("click", () => selectRun(r.issue, r.run_id));
      host.appendChild(btn);
    }
  }

  function renderStoryList() {
    const cap = $("cap-filter").value;
    const host = $("story-list");
    host.innerHTML = "";
    const list = state.examples.filter((s) => cap === "all" || s.capability === cap);
    for (const s of list) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className =
        "as-story-item" + (state.selectedStory && state.selectedStory.key === s.key ? " is-active" : "");
      btn.innerHTML = `<span class="k">${s.key}</span> <span class="as-badge cap-${s.capability}">${s.capability}</span><span class="m">${s.title}</span>`;
      btn.addEventListener("click", () => selectStory(s));
      host.appendChild(btn);
    }
  }

  function selectStory(s) {
    state.selectedStory = s;
    state.selectedIssue = null;
    renderStoryList();
    updateActionButtons();
    const tools = (s.mcp || []).map((t) => `<li>${t}</li>`).join("");
    $("story-detail").innerHTML = `
      <p class="eyebrow">${s.type} · phase ${s.phase ?? "—"}</p>
      <h3>${s.key} — ${s.title}</h3>
      <p><span class="as-badge cap-${s.capability}">${s.capability}</span></p>
      <p>${s.acceptance || ""}</p>
      <p class="as-muted">${s.why || ""}</p>
      <ul class="as-mcp-list">${tools || "<li>(none)</li>"}</ul>
      <p class="as-muted">Fixture: <code>${s.fixture || "—"}</code></p>
      <p style="margin-top:1rem">
        <button type="button" class="as-btn primary" id="story-dryrun" ${s.fixture && s.capability === "MCP_E2E" ? "" : "disabled"}>
          Dry-run this fixture
        </button>
      </p>`;
    const btn = document.getElementById("story-dryrun");
    if (btn) btn.addEventListener("click", () => startJob({ issue: s.key, fixture: s.fixture, live: false }));
    $("as-title").textContent = s.key;
    $("as-crumb").textContent = "Example story";
  }

  async function loadRuns() {
    const data = await api("/api/auto-story/runs");
    state.runs = data.runs || [];
    $("as-meta").textContent = `${state.runs.length} run(s) · ${state.queue.length} ready`;
    renderRunList();
  }

  async function loadExamples() {
    const data = await api("/api/auto-story/examples");
    state.examples = data.examples || [];
    renderStoryList();
  }

  async function pollJira() {
    setStatus("Polling Jira Ready queue…");
    try {
      const data = await api("/api/auto-story/poll");
      state.queue = data.issues || [];
      renderQueue();
      $("as-meta").textContent = `${state.runs.length} run(s) · ${state.queue.length} ready`;
      if (!state.queue.length) {
        setStatus(data.jql ? `Empty queue (${data.jql})` : "Empty Ready queue");
      } else {
        setStatus(`${state.queue.length} agent-ready issue(s)`);
        if (!state.selectedIssue) selectQueueIssue(state.queue[0]);
      }
    } catch (err) {
      setStatus(String(err.message || err), true);
    }
  }

  async function selectRun(issue, runId) {
    state.selected = { issue, runId };
    state.eventIndex = null;
    state.artTab = "summary";
    document.querySelectorAll(".as-dtab").forEach((el) => {
      el.classList.toggle("is-active", el.dataset.art === "summary");
    });
    renderRunList();
    $("as-title").textContent = `${issue} / ${runId}`;
    $("as-crumb").textContent = "Run ledger";
    setStatus("Loading run…");
    try {
      const data = await api(`/api/auto-story/runs/${encodeURIComponent(issue)}/${encodeURIComponent(runId)}`);
      state.events = data.events || [];
      state.artifacts = data.artifacts || {};
      renderTimeline();
      renderArtifact();
      setStatus(`${state.events.length} events · ${Object.keys(state.artifacts).length} artifacts`);
    } catch (err) {
      setStatus(String(err.message || err), true);
    }
  }

  function renderTimeline() {
    const host = $("timeline");
    host.innerHTML = "";
    const visible = state.events.filter((e) => state.typeOn[e.type] !== false);
    if (!visible.length) {
      host.innerHTML = '<li class="as-muted" style="padding:0.75rem">No matching events.</li>';
      return;
    }
    visible.forEach((ev, i) => {
      const idx = state.events.indexOf(ev);
      const li = document.createElement("li");
      li.className = "as-ev" + (state.eventIndex === idx ? " is-active" : "");
      li.innerHTML = `<span class="t">${fmtTime(ev.ts)}</span><div><span class="type type-${ev.type}">${ev.type}</span><span class="sum">${escapeHtml(ev.summary || ev.message || "")}</span></div>`;
      li.addEventListener("click", () => {
        state.eventIndex = idx;
        state.artTab = "event";
        document.querySelectorAll(".as-dtab").forEach((el) => {
          el.classList.toggle("is-active", el.dataset.art === "event");
        });
        renderTimeline();
        renderArtifact();
      });
      host.appendChild(li);
      if (i === visible.length - 1 && $("live-tail").checked) {
        li.scrollIntoView({ block: "nearest" });
      }
    });
  }

  function renderArtifact() {
    const pre = $("artifact");
    const tab = state.artTab;
    if (tab === "event") {
      const ev = state.events[state.eventIndex];
      pre.textContent = ev ? JSON.stringify(ev, null, 2) : "Select an event.";
      return;
    }
    if (tab === "summary") {
      const start = state.events.find((e) => e.type === "RUN_START") || {};
      const decide = state.events.find((e) => e.type === "DECIDE") || {};
      const handoff = state.artifacts.handoff;
      const verify = state.artifacts.verify;
      pre.textContent = JSON.stringify(
        {
          issue: state.selected?.issue,
          run_id: state.selected?.runId,
          dry_run: start.dry_run,
          worker: start.worker,
          decide: {
            mode: decide.mode,
            story_type: decide.story_type,
            confidence: decide.confidence,
            reasons: decide.reasons,
          },
          verify_ok: verify?.ok,
          handoff_outcome: handoff?.outcome || handoff?.status,
          event_count: state.events.length,
          artifact_keys: Object.keys(state.artifacts),
        },
        null,
        2
      );
      return;
    }
    const map = {
      feasibility: "feasibility",
      plan: "plan",
      evidence: "evidence",
      verify: "verify",
      handoff: "handoff",
    };
    const key = map[tab];
    const val = state.artifacts[key];
    if (val == null) {
      pre.textContent = `(no ${tab} artifact)`;
      return;
    }
    pre.textContent = typeof val === "string" ? val : JSON.stringify(val, null, 2);
  }

  async function startJob({ issue, fixture, live }) {
    if (live) {
      const ok = window.confirm(
        `Start LIVE run for ${issue}?\n\nThis will mutate IIQ (if allowlisted) and transition Jira → In Progress → In Review.\nNever Done.\n\nClick OK only if you intend a real run.`
      );
      if (!ok) return;
    }
    setBusy(true);
    setStatus(`Starting ${live ? "LIVE" : "dry-run"} ${issue}…`);
    try {
      const data = await api("/api/auto-story/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          issue,
          fixture: fixture || undefined,
          no_llm: !$("use-llm").checked,
          live: !!live,
          confirm_live: !!live,
        }),
      });
      state.jobId = data.job_id;
      showProcess({
        status: "running",
        issue,
        live: !!live,
        job_id: data.job_id,
        message: `starting ${live ? "LIVE" : "dry-run"}…`,
        event_count: 0,
      });
      setStatus(`Job ${data.job_id} started (${live ? "live" : "dry-run"}). Streaming…`);
      pollJob(data.job_id);
    } catch (err) {
      setStatus(String(err.message || err), true);
      setBusy(false);
    }
  }

  function showProcess(job) {
    const el = $("as-process");
    if (!el) return;
    if (!job || (job.status !== "running" && !state.jobId)) {
      if (!job || job.status === "ok") {
        el.hidden = true;
        el.classList.remove("is-error");
      }
    }
    if (!job) return;
    el.hidden = false;
    el.classList.toggle("is-error", job.status === "error");
    const mode = job.live ? "LIVE" : "dry-run";
    $("as-process-title").textContent =
      job.status === "running"
        ? `Running ${job.issue || ""} (${mode})`
        : job.status === "ok"
          ? `Completed ${job.issue || ""}`
          : `Failed ${job.issue || ""}`;
    const le = job.last_event;
    const meta = [
      job.run_id || "…",
      job.event_count != null ? `${job.event_count} events` : null,
      job.job_id ? `job ${job.job_id}` : null,
    ]
      .filter(Boolean)
      .join(" · ");
    $("as-process-meta").textContent = meta;
    $("as-process-msg").textContent =
      job.error ||
      job.message ||
      (le ? `${le.type}: ${le.summary}` : "Waiting for ledger…");
  }

  async function pollJob(jobId) {
    clearInterval(state.pollTimer);
    let attached = false;
    state.pollTimer = setInterval(async () => {
      try {
        const data = await api(`/api/auto-story/jobs/${encodeURIComponent(jobId)}`);
        showProcess(data);
        setStatus(
          data.status === "running"
            ? `${data.message || "Running…"}`
            : data.status === "ok"
              ? `Finished ${data.issue}/${data.run_id}`
              : data.error || data.message || `Job ${data.status}`,
          data.status === "error"
        );

        if (data.run_id && data.issue) {
          await loadRuns();
          if (!attached || state.selected?.runId !== data.run_id) {
            attached = true;
            switchView("runs");
            await selectRun(data.issue, data.run_id);
          } else {
            // Stream new ledger events + refresh artifacts while running
            const more = await api(
              `/api/auto-story/runs/${encodeURIComponent(data.issue)}/${encodeURIComponent(data.run_id)}/events?after=${state.events.length}`
            );
            if ((more.events || []).length) {
              state.events = state.events.concat(more.events);
              renderTimeline();
            }
            if (data.status === "running" && data.event_count && data.event_count % 3 === 0) {
              const full = await api(
                `/api/auto-story/runs/${encodeURIComponent(data.issue)}/${encodeURIComponent(data.run_id)}`
              );
              state.artifacts = full.artifacts || state.artifacts;
              if (state.artTab !== "event") renderArtifact();
            }
          }
        }

        if (data.status === "running") return;

        clearInterval(state.pollTimer);
        state.jobId = null;
        setBusy(false);
        await loadRuns();
        await pollJira();
        if (data.status === "ok" && data.issue && data.run_id) {
          switchView("runs");
          await selectRun(data.issue, data.run_id);
          // Final artifact refresh
          const full = await api(
            `/api/auto-story/runs/${encodeURIComponent(data.issue)}/${encodeURIComponent(data.run_id)}`
          );
          state.artifacts = full.artifacts || {};
          renderArtifact();
          setTimeout(() => {
            const p = $("as-process");
            if (p && !state.jobId) p.hidden = true;
          }, 4000);
        }
      } catch (err) {
        clearInterval(state.pollTimer);
        state.jobId = null;
        setBusy(false);
        showProcess({ status: "error", error: String(err.message || err), message: "failed" });
        setStatus(String(err.message || err), true);
      }
    }, 500);
  }

  async function refreshSelectedEvents() {
    if (!state.selected || !$("live-tail").checked) return;
    try {
      const data = await api(
        `/api/auto-story/runs/${encodeURIComponent(state.selected.issue)}/${encodeURIComponent(state.selected.runId)}/events?after=${state.events.length}`
      );
      const more = data.events || [];
      if (more.length) {
        state.events = state.events.concat(more);
        renderTimeline();
        setStatus(`${state.events.length} events (live)`);
      }
    } catch {
      /* ignore */
    }
  }

  function switchView(view) {
    state.view = view;
    document.querySelectorAll(".as-tab").forEach((el) => {
      const on = el.dataset.view === view;
      el.classList.toggle("is-active", on);
      el.setAttribute("aria-selected", on ? "true" : "false");
    });
    $("queue-panel").hidden = view !== "queue";
    $("runs-panel").hidden = view !== "runs";
    $("stories-panel").hidden = view !== "stories";
    $("view-queue").hidden = view !== "queue";
    $("view-runs").hidden = view !== "runs";
    $("view-stories").hidden = view !== "stories";
    if (view === "queue") {
      $("as-crumb").textContent = "Ready queue";
      if (state.selectedIssue) $("as-title").textContent = state.selectedIssue.key;
      else $("as-title").textContent = "Poll Jira for agent-ready work";
    }
  }

  function wire() {
    document.querySelectorAll(".as-tab").forEach((el) => {
      el.addEventListener("click", () => switchView(el.dataset.view));
    });
    document.querySelectorAll(".as-dtab").forEach((el) => {
      el.addEventListener("click", () => {
        state.artTab = el.dataset.art;
        document.querySelectorAll(".as-dtab").forEach((t) => {
          t.classList.toggle("is-active", t.dataset.art === state.artTab);
        });
        renderArtifact();
      });
    });
    $("run-filter").addEventListener("input", renderRunList);
    $("cap-filter").addEventListener("change", renderStoryList);
    $("refresh-runs").addEventListener("click", () => {
      loadRuns().then(() => setStatus(`Reloaded ${state.runs.length} run(s)`));
    });
    $("poll-jira").addEventListener("click", () => pollJira());
    $("refresh-queue").addEventListener("click", () => pollJira());
    $("btn-dry").addEventListener("click", () => {
      if (state.selectedIssue) {
        startJob({ issue: state.selectedIssue.key, live: false });
      } else if (state.selectedStory?.fixture) {
        startJob({ issue: state.selectedStory.key, fixture: state.selectedStory.fixture, live: false });
      }
    });
    $("btn-live").addEventListener("click", () => {
      if (state.selectedIssue) startJob({ issue: state.selectedIssue.key, live: true });
    });

    const params = new URLSearchParams(location.search);
    const issue = params.get("issue");
    const runId = params.get("run");
    const story = params.get("story");

    Promise.all([loadRuns(), loadExamples(), pollJira().catch(() => null)])
      .then(async () => {
        if (story) {
          const s = state.examples.find((e) => e.key === story);
          if (s) {
            switchView("stories");
            selectStory(s);
          }
        } else if (issue && runId) {
          switchView("runs");
          await selectRun(issue, runId);
        } else {
          switchView("queue");
          setStatus(
            state.queue.length
              ? `${state.queue.length} ready · select and Dry-run / Start live`
              : "Poll Jira or add agent-ready on a To Do issue"
          );
        }
      })
      .catch((err) => setStatus(String(err.message || err), true));

    setInterval(refreshSelectedEvents, 2000);
  }

  renderTypeFilters();
  wire();
})();
