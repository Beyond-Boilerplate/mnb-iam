(() => {
  const $ = (sel) => document.querySelector(sel);
  const actionsEl = $("#actions");
  const transcript = $("#transcript");
  const composer = $("#composer");
  const messageEl = $("#message");
  const sendBtn = $("#send");
  const statusEl = $("#status");
  const llmHint = $("#llm-hint");
  const filterEl = $("#action-filter");
  const groupTabsEl = $("#group-tabs");
  const matchCountEl = $("#match-count");
  const favoritesEl = $("#favorites");
  const favoriteChipsEl = $("#favorite-chips");
  const railEl = $("#rail");
  const railToggle = $("#rail-toggle");
  const railClose = $("#rail-close");
  const railBackdrop = $("#rail-backdrop");
  const newChatBtn = $("#new-chat");
  const suggestEl = $("#suggest");
  const playbookRow = $("#playbook-row");
  const detailEl = $("#detail");
  const detailKindEl = $("#detail-kind");
  const detailTitleEl = $("#detail-title");
  const detailSummaryEl = $("#detail-summary");
  const detailJsonEl = $("#detail-json");
  const detailClose = $("#detail-close");
  const detailCopy = $("#detail-copy");
  const detailBackdrop = $("#detail-backdrop");
  const slashMenuEl = $("#slash-menu");
  const stopBtn = $("#stop");
  const readOnlyEl = $("#read-only");
  const helpBtn = $("#help-btn");
  const helpModal = $("#help-modal");
  const helpClose = $("#help-close");
  const paletteBtn = $("#palette-btn");
  const paletteModal = $("#palette-modal");
  const paletteClose = $("#palette-close");
  const paletteInput = $("#palette-input");
  const paletteList = $("#palette-list");
  const confirmModal = $("#confirm-modal");
  const confirmToolEl = $("#confirm-tool");
  const confirmArgsEl = $("#confirm-args");
  const confirmLeadEl = $("#confirm-lead");
  const confirmApprove = $("#confirm-approve");
  const confirmDeny = $("#confirm-deny");
  const feedbackModal = $("#feedback-modal");
  const feedbackComment = $("#feedback-comment");
  const feedbackSkip = $("#feedback-skip");
  const feedbackSubmit = $("#feedback-submit");
  const degradeBanner = $("#degrade-banner");
  const agentLive = $("#agent-live");
  const suggestRow = $("#suggest-row");
  const sbMcp = $("#sb-mcp");
  const sbModel = $("#sb-model");
  const sbMode = $("#sb-mode");
  const sbLatency = $("#sb-latency");

  const FAV_KEY = "meridian.teller.favorites";
  const COLLAPSE_KEY = "meridian.teller.collapsed";
  const READONLY_KEY = "meridian.teller.readOnly";
  const RECENT_KEY = "meridian.teller.recentTools";
  const RAIL_COLLAPSED_KEY = "meridian.teller.railCollapsed";
  const ROLE_KEY = "meridian.teller.playbookRole";
  const SLASH_LIMIT = 14;
  let PLAYBOOKS = Array.isArray(window.TELLER_PLAYBOOKS) ? window.TELLER_PLAYBOOKS : [];
  let SUGGEST = Array.isArray(window.TELLER_SUGGEST) ? window.TELLER_SUGGEST : [];
  let playbookRole = null;
  let toolsOnlyMode = false;
  let mcpFlaky = false;
  let lastCorrelationId = "";
  let feedbackContext = null;
  let feedbackReason = null;
  let focusTrapCleanup = null;

  let menuMode = null; // 'slash' | 'mention' | null
  let slashOpen = false;
  let slashItems = [];
  let slashIndex = 0;
  let slashQuery = "";
  let mentionToken = null; // { query, tokenStart, tokenEnd }
  let mentionTimer = null;
  let mentionSeq = 0;
  let readOnly = false;
  let activeRunId = null;
  let activeAbort = null;
  let confirmResolver = null;
  let lastModel = "";
  let lastUserMessage = "";
  let recentTools = [];
  let railCollapsed = false;
  let paletteOpen = false;
  let paletteItems = [];
  let paletteIndex = 0;
  let detailPayload = null;
  const GROUP_ORDER = [
    "Favorites",
    "Health",
    "Identities",
    "Apps",
    "Access",
    "Work items",
    "Certifications",
    "Policies",
    "Tasks",
    "Admin",
    "Catalog",
    "Other",
  ];

  const history = [];
  let allActions = [];
  let activeGroup = "All";
  let favorites = [];
  let collapsed = new Set();
  let busy = false;

  function loadJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      if (raw == null) return fallback;
      return JSON.parse(raw);
    } catch {
      return fallback;
    }
  }

  function saveJson(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* ignore quota */
    }
  }

  readOnly = Boolean(loadJson(READONLY_KEY, false));
  favorites = loadJson(FAV_KEY, []);
  recentTools = loadJson(RECENT_KEY, []);
  if (!Array.isArray(recentTools)) recentTools = [];
  railCollapsed = Boolean(loadJson(RAIL_COLLAPSED_KEY, false));
  playbookRole = loadJson(ROLE_KEY, null);
  collapsed = new Set(loadJson(COLLAPSE_KEY, null) ?? ["Apps", "Identities", "Work", "Governance", "Ops", "Catalog"]);
  if (readOnlyEl) readOnlyEl.checked = readOnly;
  // Drop retired chat-history keys from earlier builds
  try {
    localStorage.removeItem("meridian.teller.sessions");
    localStorage.removeItem("meridian.teller.activeSession");
  } catch {
    /* ignore */
  }

  function isMobileRail() {
    return window.matchMedia("(max-width: 960px)").matches;
  }

  function updateRailToggleUi() {
    if (!railToggle) return;
    const mobile = isMobileRail();
    const open = mobile
      ? document.body.classList.contains("rail-open")
      : !document.body.classList.contains("rail-collapsed");
    railToggle.setAttribute("aria-expanded", open ? "true" : "false");
    railToggle.title = open ? "Hide tools panel" : "Show tools panel";
    if (railClose) {
      if (mobile) railClose.hidden = !open;
      else railClose.hidden = !open;
    }
    if (railBackdrop) {
      railBackdrop.hidden = !(mobile && open);
    }
  }

  function applyRailLayout() {
    if (isMobileRail()) {
      document.body.classList.remove("rail-collapsed");
    } else {
      document.body.classList.toggle("rail-collapsed", railCollapsed);
      document.body.classList.remove("rail-open");
    }
    updateRailToggleUi();
  }

  function toggleRail() {
    if (isMobileRail()) {
      setRailOpen(!document.body.classList.contains("rail-open"));
      return;
    }
    railCollapsed = !railCollapsed;
    saveJson(RAIL_COLLAPSED_KEY, railCollapsed);
    applyRailLayout();
  }

  function rememberRecentTool(tool) {
    const name = String(tool || "").trim();
    if (!name) return;
    recentTools = [name, ...recentTools.filter((t) => t !== name)].slice(0, 8);
    saveJson(RECENT_KEY, recentTools);
  }

  function fuzzyScore(hay, needle) {
    const h = String(hay || "").toLowerCase();
    const n = String(needle || "").toLowerCase();
    if (!n) return 1;
    if (h === n) return 120;
    if (h.startsWith(n)) return 100;
    if (h.includes(n)) return 70;
    // subsequence match (a n i t a → anita)
    let hi = 0;
    for (let i = 0; i < n.length; i++) {
      const ch = n[i];
      hi = h.indexOf(ch, hi);
      if (hi === -1) return 0;
      hi += 1;
    }
    return 35;
  }

  function setStatus(state, text) {
    const dot = statusEl.querySelector(".dot");
    const label = statusEl.querySelector(".status-text");
    dot.dataset.state = state;
    label.textContent = text;
  }

  function setBusy(on) {
    busy = on;
    sendBtn.disabled = on;
    sendBtn.querySelector(".send-label").hidden = on;
    sendBtn.querySelector(".send-busy").hidden = !on;
    if (stopBtn) stopBtn.hidden = !on;
  }

  function updateModeBar() {
    if (sbMode) {
      sbMode.textContent = readOnly ? "Read-only" : "Read/Write";
      sbMode.classList.toggle("warn", readOnly);
    }
    document.body.classList.toggle("read-only", readOnly);
  }

  function setLatency(ms) {
    if (!sbLatency) return;
    if (ms == null) {
      sbLatency.hidden = true;
      sbLatency.textContent = "";
      return;
    }
    sbLatency.hidden = false;
    sbLatency.textContent = ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
  }

  function announceAgent(text) {
    if (!agentLive) return;
    agentLive.textContent = String(text || "");
  }

  function focusableIn(root) {
    if (!root) return [];
    return [
      ...root.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      ),
    ].filter((el) => el.offsetParent !== null || el === document.activeElement);
  }

  function trapFocus(backdrop) {
    if (focusTrapCleanup) {
      focusTrapCleanup();
      focusTrapCleanup = null;
    }
    if (!backdrop || backdrop.hidden) return;
    const dialog = backdrop.querySelector('[role="dialog"]') || backdrop;
    const previouslyFocused = document.activeElement;
    const nodes = () => focusableIn(dialog);
    const onKey = (e) => {
      if (e.key !== "Tab") return;
      const list = nodes();
      if (!list.length) return;
      const first = list[0];
      const last = list[list.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    backdrop.addEventListener("keydown", onKey);
    const initial = nodes()[0] || dialog;
    initial.focus?.();
    focusTrapCleanup = () => {
      backdrop.removeEventListener("keydown", onKey);
      if (previouslyFocused && previouslyFocused.focus) {
        try {
          previouslyFocused.focus();
        } catch {
          /* ignore */
        }
      }
      focusTrapCleanup = null;
    };
  }

  function showHelp(open) {
    if (!helpModal) return;
    helpModal.hidden = !open;
    if (open) trapFocus(helpModal);
    else if (focusTrapCleanup) focusTrapCleanup();
  }

  function askConfirm({ tool, arguments: args, lead }) {
    return new Promise((resolve) => {
      if (confirmResolver) {
        confirmResolver(false);
        confirmResolver = null;
      }
      confirmResolver = resolve;
      if (confirmToolEl) confirmToolEl.textContent = tool || "";
      if (confirmArgsEl) {
        confirmArgsEl.textContent =
          args && Object.keys(args).length ? JSON.stringify(args, null, 2) : "{}";
      }
      if (confirmLeadEl) {
        confirmLeadEl.textContent =
          lead || "This tool can change IdentityIQ. Approve to continue.";
      }
      if (confirmModal) confirmModal.hidden = false;
      trapFocus(confirmModal);
      announceAgent(`Approve write tool ${tool || ""}?`);
      confirmApprove?.focus();
    });
  }

  function closeConfirm(approve) {
    if (confirmModal) confirmModal.hidden = true;
    if (focusTrapCleanup) focusTrapCleanup();
    if (confirmResolver) {
      const r = confirmResolver;
      confirmResolver = null;
      r(Boolean(approve));
    }
  }

  async function stopActiveRun() {
    if (activeRunId) {
      try {
        await fetch("/api/chat/cancel", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ runId: activeRunId }),
        });
      } catch {
        /* ignore */
      }
    }
    if (activeAbort) {
      try {
        activeAbort.abort();
      } catch {
        /* ignore */
      }
    }
    closeConfirm(false);
  }

  function summarizeResult(result) {
    if (result == null) return null;
    if (typeof result === "string") return result.slice(0, 160);
    if (typeof result !== "object") return String(result);
    if (result.ok === false) {
      const err = result.error;
      if (typeof err === "string") return err;
      if (err && err.message) return err.message;
      return "Request failed";
    }
    const data = result.data !== undefined ? result.data : result;
    if (typeof data === "string") return data;
    if (Array.isArray(data)) return `${data.length} item${data.length === 1 ? "" : "s"}`;
    if (data && typeof data === "object") {
      if (Array.isArray(data.items)) {
        const total = data.totalResults ?? data.returned ?? data.items.length;
        return `${data.items.length} shown · ${total} total`;
      }
      if (data.returned != null) return `${data.returned} returned`;
      if (data.name) return String(data.name);
      if (data.status) return `status: ${data.status}`;
      const keys = Object.keys(data);
      if (keys.length <= 4) return keys.map((k) => `${k}=${fmtBrief(data[k])}`).join(" · ");
      return `${keys.length} fields`;
    }
    return null;
  }

  function fmtBrief(v) {
    if (v == null) return "—";
    if (typeof v === "object") return Array.isArray(v) ? `[${v.length}]` : "{…}";
    const s = String(v);
    return s.length > 40 ? `${s.slice(0, 37)}…` : s;
  }

  function extractEntitiesFromSteps(steps) {
    const identities = [];
    const apps = [];
    const taskIds = [];
    for (const step of steps || []) {
      const args = step.normalizedArguments || step.arguments || {};
      const result = step.result;
      const tool = String(step.tool || "");
      for (const key of ["id", "identity", "userName", "username", "name"]) {
        if (args[key] && typeof args[key] === "string") {
          if (/identity|account|password|unlock|manager|profile/i.test(tool) || key !== "name") {
            identities.push(args[key]);
          }
        }
      }
      for (const key of ["app_name", "application", "applicationName", "appName"]) {
        if (args[key] && typeof args[key] === "string") apps.push(args[key]);
      }
      if (args.app_id && typeof args.app_id === "string" && args.app_name) {
        apps.push(String(args.app_name));
      }
      const data = result && typeof result === "object" ? result.data || result : null;
      if (data && typeof data === "object") {
        const tr = data.taskResultId || data.taskResult || data.resultId;
        if (tr) taskIds.push(String(tr));
        if (Array.isArray(data.items)) {
          for (const it of data.items.slice(0, 3)) {
            if (it && typeof it === "object") {
              const u = it.userName || it.displayName;
              if (u) identities.push(String(u));
              const n = it.name || it.applicationName;
              if (n && /application|app/i.test(tool)) apps.push(String(n));
            }
          }
        }
        const un = data.userName || (data.identity && data.identity.userName);
        if (un) identities.push(String(un));
        if (data.name && /application|aggregat/i.test(tool)) apps.push(String(data.name));
      }
    }
    const uniq = (arr) => [...new Set(arr.map((x) => String(x).trim()).filter(Boolean))];
    return { identities: uniq(identities), apps: uniq(apps), taskIds: uniq(taskIds) };
  }

  function buildFollowUps(data) {
    const chips = [];
    const steps = data?.steps || [];
    const tools = steps.map((s) => s.tool);
    const { identities, apps, taskIds } = extractEntitiesFromSteps(steps);

    if (lastUserMessage) {
      chips.push({ id: "retry", label: "Retry", kind: "retry" });
    }
    if (data?.cancelled) return chips;

    const identity = identities[0];
    const app = apps[0];
    const taskId = taskIds[0];

    if (identity) {
      chips.push({
        id: "who",
        label: `Who is ${identity}?`,
        kind: "ask",
        q: `Who is ${identity}? Summarize their identity, title, and accounts.`,
      });
      if (!readOnly && !tools.includes("unlock_identity")) {
        chips.push({
          id: "unlock",
          label: `Unlock ${identity}`,
          kind: "ask",
          q: `Unlock identity ${identity}`,
        });
      }
    }
    if (app) {
      chips.push({
        id: "app",
        label: `About ${app}`,
        kind: "ask",
        q: `Tell me about application ${app}. Is it aggregated? Any recent task results?`,
      });
      if (!readOnly && !tools.some((t) => String(t).includes("aggregat"))) {
        chips.push({
          id: "agg",
          label: `Aggregate ${app}`,
          kind: "ask",
          q: `Run Account Aggregation for ${app} now`,
        });
      }
    }
    if (taskId) {
      chips.push({
        id: "poll",
        label: "Poll task result",
        kind: "ask",
        q: `Check the status of task result ${taskId}`,
      });
    }
    if (tools.includes("count_open_sod_violations") || tools.includes("list_open_sod_violations")) {
      chips.push({
        id: "sod",
        label: "List open SoD",
        kind: "ask",
        q: "List the open SoD violations with identity and policy names",
      });
    }
    // Dedup by label
    const seen = new Set();
    return chips.filter((c) => {
      if (seen.has(c.label)) return false;
      seen.add(c.label);
      return true;
    }).slice(0, 5);
  }

  function closeDetail() {
    detailPayload = null;
    document.body.classList.remove("detail-open");
    if (detailEl) detailEl.hidden = true;
    if (detailBackdrop) detailBackdrop.hidden = true;
    if (detailSummaryEl) detailSummaryEl.innerHTML = "";
    if (detailJsonEl) detailJsonEl.textContent = "";
  }

  function detailDataRoot(result) {
    if (!result || typeof result !== "object") return result;
    if (result.data != null) return result.data;
    return result;
  }

  function buildDetailView(result, tool = "") {
    const data = detailDataRoot(result);
    const toolName = String(tool || "").trim();

    // Identity card
    const card =
      (data && typeof data === "object" && data.tellerCard) ||
      (data && typeof data === "object" && data.identity && data.identity.tellerCard) ||
      null;
    const identity =
      card ||
      (data &&
      typeof data === "object" &&
      (data.displayName || data.userName) &&
      !Array.isArray(data.items)
        ? data
        : data && typeof data === "object" && data.identity
          ? data.identity
          : null);

    if (identity && (identity.displayName || identity.userName || identity.label)) {
      const label = identity.label || identity.displayName || identity.userName;
      const hints = (data && data.profileHints) || identity.profileHints || {};
      const rows = [
        ["Name", identity.displayName || label],
        ["Key", identity.userName || identity.employeeId || ""],
        ["Active", identity.active == null ? "" : identity.active ? "Yes" : "No"],
        ["Title", hints.resolvedTitle || hints.jobTitle || hints.title || ""],
        ["Manager", identity.managerLabel || hints.manager || identity.manager || ""],
        ["Location", hints.location || ""],
        ["Department", hints.departmentName || hints.department || ""],
      ].filter(([, v]) => v !== "" && v != null);
      const apps = Array.isArray(data?.items)
        ? data.items
            .map((a) => a?.application?.displayName || a?.displayName)
            .filter(Boolean)
        : [];
      let html = `<div class="detail-card"><dl>`;
      for (const [k, v] of rows) {
        html += `<div class="detail-line"><dt>${escapeHtml(k)}</dt><dd>${escapeHtml(String(v))}</dd></div>`;
      }
      html += `</dl>`;
      if (apps.length) {
        html += `<p class="detail-kind" style="margin-top:0.75rem">Accounts</p><ul class="detail-list">`;
        for (const a of apps.slice(0, 12)) html += `<li>${escapeHtml(a)}</li>`;
        html += `</ul>`;
      }
      html += `</div>`;
      return { kind: "Identity", title: String(label), summaryHtml: html };
    }

    const people =
      (data && data.peopleLabels) ||
      (data && data.reportLabels) ||
      (data && data.directReportLabels) ||
      null;
    if (Array.isArray(people) && people.length) {
      const title =
        data.managerLabel ||
        (toolName.includes("report") ? "Reports" : "People") ||
        "People";
      let html = `<ul class="detail-list">`;
      for (const p of people.slice(0, 40)) html += `<li>${escapeHtml(String(p))}</li>`;
      html += `</ul>`;
      if (people.length > 40) {
        html += `<p class="hint">${people.length - 40} more…</p>`;
      }
      return {
        kind: "People",
        title: typeof title === "string" ? title : "People",
        summaryHtml: html,
      };
    }

    if (Array.isArray(data?.items) && data.items[0]?.application) {
      const apps = data.items
        .map((a) => a?.application?.displayName || a?.displayName || a?.name)
        .filter(Boolean);
      return {
        kind: "Application",
        title: apps[0] || toolName || "Application",
        summaryHtml: `<ul class="detail-list">${apps
          .slice(0, 30)
          .map((a) => `<li>${escapeHtml(a)}</li>`)
          .join("")}</ul>`,
      };
    }

    if (data && typeof data === "object" && (data.name || data.displayName) && toolName.includes("app")) {
      const title = data.displayName || data.name;
      return { kind: "Application", title: String(title), summaryHtml: "" };
    }

    const summary = summarizeResult(result);
    return {
      kind: toolName ? "Tool result" : "JSON",
      title: summary || toolName || "Payload",
      summaryHtml: "",
    };
  }

  function openDetail(result, { tool = "", auto = false } = {}) {
    if (result == null || !detailEl) return;
    detailPayload = result;
    const view = buildDetailView(result, tool);
    if (detailKindEl) detailKindEl.textContent = view.kind;
    if (detailTitleEl) detailTitleEl.textContent = view.title;
    if (detailSummaryEl) detailSummaryEl.innerHTML = view.summaryHtml || "";
    if (detailJsonEl) {
      detailJsonEl.textContent =
        typeof result === "string" ? result : JSON.stringify(result, null, 2);
    }
    detailEl.hidden = false;
    document.body.classList.add("detail-open");
    if (detailBackdrop) detailBackdrop.hidden = !window.matchMedia("(max-width: 960px)").matches;
    if (!auto) detailEl.focus?.();
  }

  function formatExportMarkdown(payload) {
    const q = payload?.question || "";
    const a = payload?.answer || "";
    const steps = Array.isArray(payload?.steps) ? payload.steps : [];
    const lines = ["# Meridian Teller export", "", "## Question", "", q || "—", "", "## Answer", "", a || "—", ""];
    if (steps.length) {
      lines.push("## Trace", "");
      steps.forEach((s, i) => {
        const tool = s.tool || "tool";
        const args = s.normalizedArguments || s.arguments || {};
        let argBit = "";
        try {
          argBit = Object.keys(args).length ? ` \`${JSON.stringify(args)}\`` : "";
        } catch {
          argBit = "";
        }
        const summary = s.summary ? ` → ${s.summary}` : "";
        lines.push(`${i + 1}. \`${tool}\`${argBit}${summary}`);
      });
      lines.push("");
    }
    if (payload?.model) {
      lines.push(`_Model: ${payload.model}_`, "");
    }
    return lines.join("\n");
  }

  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
      if (btn) {
        const prev = btn.textContent;
        btn.textContent = "Copied";
        setTimeout(() => {
          btn.textContent = prev;
        }, 1200);
      }
      return true;
    } catch {
      if (btn) btn.textContent = "Failed";
      return false;
    }
  }

  function renderTriageCards(cards) {
    if (!Array.isArray(cards) || !cards.length) return null;
    const wrap = document.createElement("div");
    wrap.className = "triage-cards";
    wrap.setAttribute("aria-label", "Structured triage cards");
    cards.forEach((card) => {
      const el = document.createElement("article");
      el.className = `triage-card ${card.type || ""}`;
      const h = document.createElement("h4");
      h.textContent = card.title || card.type || "Card";
      el.appendChild(h);
      const dl = document.createElement("dl");
      const fields = card.fields || {};
      Object.entries(fields).forEach(([key, val]) => {
        if (val == null || val === "") return;
        if (Array.isArray(val) && !val.length) return;
        const dt = document.createElement("dt");
        dt.textContent = key;
        const dd = document.createElement("dd");
        dd.textContent = Array.isArray(val) ? val.join(" · ") : String(val);
        dl.appendChild(dt);
        dl.appendChild(dd);
      });
      el.appendChild(dl);
      if (card.source) {
        const src = document.createElement("p");
        src.className = "card-source";
        src.textContent = `source: ${card.source}`;
        el.appendChild(src);
      }
      wrap.appendChild(el);
    });
    return wrap;
  }

  function attachFeedback(actionsEl, ctx) {
    const row = document.createElement("div");
    row.className = "feedback-row";
    row.setAttribute("aria-label", "Rate this answer");
    const up = document.createElement("button");
    up.type = "button";
    up.className = "fb-btn";
    up.title = "Helpful";
    up.setAttribute("aria-label", "Thumbs up");
    up.textContent = "👍";
    const down = document.createElement("button");
    down.type = "button";
    down.className = "fb-btn down";
    down.title = "Not helpful";
    down.setAttribute("aria-label", "Thumbs down");
    down.textContent = "👎";
    up.addEventListener("click", () => {
      up.setAttribute("aria-pressed", "true");
      down.removeAttribute("aria-pressed");
      submitFeedback({ ...ctx, rating: "up" });
    });
    down.addEventListener("click", () => {
      down.setAttribute("aria-pressed", "true");
      up.removeAttribute("aria-pressed");
      openFeedbackModal(ctx);
    });
    row.appendChild(up);
    row.appendChild(down);
    actionsEl.appendChild(row);
  }

  function openFeedbackModal(ctx) {
    feedbackContext = ctx;
    feedbackReason = null;
    if (feedbackComment) feedbackComment.value = "";
    feedbackModal?.querySelectorAll("[data-reason]").forEach((btn) => {
      btn.setAttribute("aria-pressed", "false");
    });
    if (feedbackModal) feedbackModal.hidden = false;
    trapFocus(feedbackModal);
  }

  function closeFeedbackModal() {
    if (feedbackModal) feedbackModal.hidden = true;
    if (focusTrapCleanup) focusTrapCleanup();
    feedbackContext = null;
    feedbackReason = null;
  }

  async function submitFeedback(payload) {
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rating: payload.rating,
          reason: payload.reason || null,
          comment: payload.comment || "",
          question: payload.question || "",
          reply: payload.reply || "",
          model: payload.model || "",
          tools: payload.tools || [],
          runId: payload.runId || null,
          correlationId: payload.correlationId || lastCorrelationId || null,
        }),
      });
      announceAgent(payload.rating === "up" ? "Thanks for the feedback." : "Feedback recorded.");
    } catch {
      announceAgent("Could not save feedback.");
    }
  }

  function addBubble({
    role,
    text,
    meta = [],
    result = null,
    detailTool = "",
    followUps = null,
    onRetry = null,
    exportPayload = null,
    openInspector = false,
    cards = null,
    feedback = null,
  }) {
    const div = document.createElement("div");
    div.className = `bubble ${role}`;

    if (meta.length) {
      const metaRow = document.createElement("div");
      metaRow.className = "meta";
      meta.forEach((m) => {
        const tag = document.createElement("span");
        tag.className = `tag${m.tone ? ` ${m.tone}` : ""}`;
        tag.textContent = m.label;
        metaRow.appendChild(tag);
      });
      div.appendChild(metaRow);
    }

    if (text) {
      if (role === "assistant") {
        const body = document.createElement("div");
        body.className = "md-body";
        body.innerHTML = renderMarkdown(text);
        div.appendChild(body);
      } else {
        const p = document.createElement("p");
        p.textContent = text;
        div.appendChild(p);
      }
    }

    const cardEl = renderTriageCards(cards);
    if (cardEl) div.appendChild(cardEl);

    if (role === "assistant" && (text || exportPayload || result != null)) {
      const actions = document.createElement("div");
      actions.className = "bubble-actions";
      if (text) {
        const copyAns = document.createElement("button");
        copyAns.type = "button";
        copyAns.className = "text-btn";
        copyAns.textContent = "Copy";
        copyAns.addEventListener("click", () => copyText(text || "", copyAns));
        actions.appendChild(copyAns);
      }
      if (exportPayload) {
        const exportBtn = document.createElement("button");
        exportBtn.type = "button";
        exportBtn.className = "text-btn";
        exportBtn.textContent = "Export";
        exportBtn.addEventListener("click", () =>
          copyText(formatExportMarkdown(exportPayload), exportBtn)
        );
        actions.appendChild(exportBtn);
      }
      if (result != null) {
        const inspect = document.createElement("button");
        inspect.type = "button";
        inspect.className = "text-btn";
        inspect.textContent = looksLikeError(result) ? "Error details" : "Inspect";
        inspect.addEventListener("click", () => openDetail(result, { tool: detailTool }));
        actions.appendChild(inspect);
      }
      if (feedback) attachFeedback(actions, feedback);
      if (actions.childNodes.length) div.appendChild(actions);
    }

    if (openInspector && result != null) {
      openDetail(result, { tool: detailTool, auto: true });
    }

    if (role === "assistant" && Array.isArray(followUps) && followUps.length) {
      const row = document.createElement("div");
      row.className = "followups";
      followUps.forEach((chip) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `followup-chip${chip.kind === "retry" ? " retry" : ""}`;
        btn.textContent = chip.label;
        btn.addEventListener("click", () => {
          if (chip.kind === "retry") {
            if (typeof onRetry === "function") onRetry();
            else if (lastUserMessage) sendChat(lastUserMessage);
            return;
          }
          if (chip.q) sendChat(chip.q);
        });
        row.appendChild(btn);
      });
      div.appendChild(row);
    }

    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
    if (suggestEl && history.length === 0 && role === "system") {
      suggestEl.hidden = false;
    } else if (suggestEl && role !== "system") {
      suggestEl.hidden = true;
    }
    return div;
  }

  function looksLikeError(result) {
    return result && typeof result === "object" && result.ok === false;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /** Safe subset of GFM for assistant answers (headings, lists, bold, code). */
  function renderMarkdown(src) {
    const text = String(src || "").replace(/\r\n/g, "\n").trim();
    if (!text) return "";

    const inline = (s) => {
      let t = escapeHtml(s);
      t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
      t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
      t = t.replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,!?:;]|$)/g, "$1<em>$2</em>");
      t = t.replace(
        /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
      );
      return t;
    };

    const lines = text.split("\n");
    const out = [];
    let i = 0;
    const flushPara = (buf) => {
      if (!buf.length) return;
      out.push(`<p>${inline(buf.join(" "))}</p>`);
      buf.length = 0;
    };

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();
      if (!trimmed) {
        i += 1;
        continue;
      }

      const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
      if (heading) {
        const level = heading[1].length;
        out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
        i += 1;
        continue;
      }

      if (/^[-*]\s+/.test(trimmed)) {
        const items = [];
        while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
          items.push(`<li>${inline(lines[i].trim().replace(/^[-*]\s+/, ""))}</li>`);
          i += 1;
        }
        out.push(`<ul>${items.join("")}</ul>`);
        continue;
      }

      if (/^\d+\.\s+/.test(trimmed)) {
        const items = [];
        while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
          items.push(`<li>${inline(lines[i].trim().replace(/^\d+\.\s+/, ""))}</li>`);
          i += 1;
        }
        out.push(`<ol>${items.join("")}</ol>`);
        continue;
      }

      const para = [];
      while (i < lines.length) {
        const t = lines[i].trim();
        if (
          !t ||
          /^(#{1,3})\s+/.test(t) ||
          /^[-*]\s+/.test(t) ||
          /^\d+\.\s+/.test(t)
        ) {
          break;
        }
        para.push(t);
        i += 1;
      }
      flushPara(para);
    }

    return out.join("");
  }

  function fmtArgValue(v) {
    if (v == null) return "—";
    if (typeof v === "object") {
      try {
        return JSON.stringify(v);
      } catch {
        return String(v);
      }
    }
    return String(v);
  }

  function renderArgList(args) {
    const wrap = document.createElement("dl");
    wrap.className = "live-kv";
    const entries = Object.entries(args || {});
    for (const [key, raw] of entries) {
      const full = fmtArgValue(raw);
      const dt = document.createElement("dt");
      dt.textContent = key;
      const dd = document.createElement("dd");
      dd.textContent = full.length > 96 ? `${full.slice(0, 93)}…` : full;
      if (full.length > 96) dd.title = full;
      wrap.appendChild(dt);
      wrap.appendChild(dd);
    }
    return wrap;
  }

  function addTyping(label = "Working") {
    const div = document.createElement("div");
    div.className = "bubble assistant typing";
    div.id = "typing";
    div.innerHTML =
      `<div class="meta"><span class="tag teal">${escapeHtml(label)}</span></div>` +
      '<p class="typing-dots" aria-label="Loading"><span></span><span></span><span></span></p>';
    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
  }

  function clearTyping() {
    const el = $("#typing");
    if (el) el.remove();
  }

  function createLivePanel() {
    clearTyping();
    const existing = $("#live-panel");
    if (existing) existing.remove();

    const startedAt = Date.now();
    const thoughts = [];
    let toolCount = 0;

    const div = document.createElement("div");
    div.className = "bubble assistant live";
    div.id = "live-panel";
    div.setAttribute("aria-live", "polite");

    const head = document.createElement("div");
    head.className = "live-head";
    head.innerHTML =
      `<div class="live-head-left">` +
      `<span class="live-badge">Working</span>` +
      `<span class="live-status-text">Starting…</span>` +
      `</div>` +
      `<span class="live-pulse" aria-hidden="true"></span>`;
    div.appendChild(head);

    const thoughtCard = document.createElement("section");
    thoughtCard.className = "live-thought";
    thoughtCard.hidden = true;
    thoughtCard.innerHTML =
      `<div class="live-thought-label">Thinking</div>` +
      `<p class="live-thought-latest"></p>` +
      `<details class="live-thought-earlier" hidden>` +
      `<summary>Earlier reasoning</summary>` +
      `<div class="live-thought-history"></div>` +
      `</details>`;
    div.appendChild(thoughtCard);

    const toolsLabel = document.createElement("div");
    toolsLabel.className = "live-section-label";
    toolsLabel.textContent = "Tools";
    toolsLabel.hidden = true;
    div.appendChild(toolsLabel);

    const log = document.createElement("ol");
    log.className = "live-log";
    div.appendChild(log);

    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;

    const toolRows = new Map();
    const statusEl = head.querySelector(".live-status-text");
    const badgeEl = head.querySelector(".live-badge");
    const latestEl = thoughtCard.querySelector(".live-thought-latest");
    const earlierWrap = thoughtCard.querySelector(".live-thought-earlier");
    const historyEl = thoughtCard.querySelector(".live-thought-history");

    function scroll() {
      transcript.scrollTop = transcript.scrollHeight;
    }

    function setStatus(text) {
      statusEl.textContent = text;
      scroll();
    }

    function appendThought(text) {
      const clean = String(text || "").trim();
      if (!clean) return;
      if (thoughts.length) {
        const prev = document.createElement("p");
        prev.className = "live-thought-chunk";
        prev.textContent = thoughts[thoughts.length - 1];
        historyEl.appendChild(prev);
        earlierWrap.hidden = false;
      }
      thoughts.push(clean);
      thoughtCard.hidden = false;
      latestEl.textContent = clean;
      scroll();
    }

    function toolStart({ tool, arguments: args, index }) {
      toolCount += 1;
      toolsLabel.hidden = false;
      const li = document.createElement("li");
      li.className = "live-step pending";
      li.dataset.index = String(index);

      const stepHead = document.createElement("div");
      stepHead.className = "live-step-head";
      stepHead.innerHTML =
        `<span class="live-step-num">${index + 1}</span>` +
        `<code class="live-tool">${escapeHtml(tool || "?")}</code>` +
        `<span class="live-step-state">Running…</span>`;
      li.appendChild(stepHead);

      if (args && typeof args === "object" && Object.keys(args).length) {
        li.appendChild(renderArgList(args));
      }

      log.appendChild(li);
      toolRows.set(index, li);
      badgeEl.textContent = "Tools";
      setStatus(`Calling ${tool || "tool"}…`);
      scroll();
    }

    function toolResult({ tool, index, ok, summary }) {
      let li = toolRows.get(index);
      if (!li) {
        toolStart({ tool, arguments: {}, index });
        li = toolRows.get(index);
      }
      li.classList.remove("pending");
      li.classList.add(ok === false ? "failed" : "done");
      const state = li.querySelector(".live-step-state");
      if (state) {
        state.textContent = ok === false ? "Failed" : summary || "Done";
        state.classList.toggle("err", ok === false);
      }
      setStatus(ok === false ? `${tool} failed` : `${tool} finished`);
      scroll();
    }

    function remove() {
      div.remove();
    }

    function detachAsTrace() {
      const elapsedSec = Math.max(1, Math.round((Date.now() - startedAt) / 1000));
      div.classList.remove("live");
      div.classList.add("trace");
      div.removeAttribute("id");

      const body = document.createElement("div");
      body.className = "trace-body";
      while (div.firstChild) body.appendChild(div.firstChild);

      const summary = document.createElement("button");
      summary.type = "button";
      summary.className = "trace-summary";
      const toolWord = toolCount === 1 ? "tool" : "tools";
      const thinkBit = thoughts.length ? " · thinking visible" : "";
      summary.innerHTML =
        `<span class="trace-summary-left">` +
        `<span class="live-badge muted">How it worked</span>` +
        `<span class="trace-summary-text">${toolCount} ${toolWord}${thinkBit} · ${elapsedSec}s</span>` +
        `</span>` +
        `<span class="trace-caret" aria-hidden="true"></span>`;

      body.hidden = true;
      summary.setAttribute("aria-expanded", "false");
      summary.addEventListener("click", () => {
        const open = body.hidden;
        body.hidden = !open;
        summary.setAttribute("aria-expanded", open ? "true" : "false");
        div.classList.toggle("trace-open", open);
      });

      // Collapse earlier walls of text in finished traces
      if (!thoughtCard.hidden) {
        earlierWrap.open = false;
      }
      log.querySelectorAll(".live-step.pending").forEach((el) => {
        el.classList.remove("pending");
        el.classList.add("done");
      });

      badgeEl.textContent = "Done";
      badgeEl.classList.add("muted");
      head.querySelector(".live-pulse")?.remove();
      statusEl.textContent = toolCount
        ? `Finished ${toolCount} ${toolWord}`
        : "Answered without tools";

      div.appendChild(summary);
      div.appendChild(body);
      return div;
    }

    function hadActivity() {
      return toolCount > 0 || thoughts.length > 0;
    }

    return {
      setStatus,
      appendThought,
      toolStart,
      toolResult,
      remove,
      detachAsTrace,
      hadActivity,
      el: div,
    };
  }

  function parseSseChunk(buffer, onEvent) {
    const parts = buffer.split("\n\n");
    const rest = parts.pop() || "";
    for (const block of parts) {
      if (!block.trim() || block.startsWith(":")) continue;
      let event = "message";
      const dataLines = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
      }
      if (!dataLines.length) continue;
      let payload = {};
      try {
        payload = JSON.parse(dataLines.join("\n"));
      } catch {
        payload = { raw: dataLines.join("\n") };
      }
      onEvent(event, payload);
    }
    return rest;
  }

  async function postDecision(runId, id, approve) {
    try {
      await fetch("/api/chat/decision", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ runId, id, approve }),
      });
    } catch {
      /* ignore */
    }
  }

  async function streamChat(message, hist, live) {
    const started = performance.now();
    const abort = new AbortController();
    activeAbort = abort;
    activeRunId = null;

    let res;
    try {
      res = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify({
          message,
          history: hist,
          readOnly,
          confirmWrites: true,
        }),
        signal: abort.signal,
      });
    } catch (err) {
      if (err && err.name === "AbortError") {
        return { ok: false, cancelled: true, error: "Stopped by operator" };
      }
      throw err;
    }

    if (!res.ok && !res.headers.get("content-type")?.includes("text/event-stream")) {
      const data = await res.json().catch(() => ({ ok: false, error: `HTTP ${res.status}` }));
      return data;
    }

    if (!res.body) {
      return { ok: false, error: "Streaming not supported in this browser" };
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    let finalPayload = null;
    let errorPayload = null;

    const onEvent = async (event, payload) => {
      if (event === "run") {
        if (payload.runId) activeRunId = payload.runId;
        if (payload.correlationId) lastCorrelationId = String(payload.correlationId);
      } else if (event === "status" && payload.message) {
        // Ignore legacy/no-op finishing labels if any still arrive
        if (/^finishing/i.test(payload.message)) return;
        live.setStatus(payload.message);
        announceAgent(payload.message);
      } else if (event === "thought" && payload.text) {
        live.appendThought(payload.text);
      } else if (event === "tool_start") {
        live.toolStart(payload);
        if (payload.tool) announceAgent(`Running ${payload.tool}`);
      } else if (event === "tool_result") {
        live.toolResult(payload);
        if (payload.ok === false) {
          mcpFlaky = true;
          setDegradeBanner({ mcpOk: true, toolsOnly: toolsOnlyMode, flaky: true });
        }
      } else if (event === "tool_confirm") {
        live.setStatus(`Awaiting approval: ${payload.tool || "write tool"}`);
        announceAgent(`Awaiting approval for ${payload.tool || "write tool"}`);
        const approved = await askConfirm({
          tool: payload.tool,
          arguments: payload.arguments || {},
          lead: "Agent wants to run a write tool. Approve to continue, or Deny to skip it.",
        });
        await postDecision(payload.runId || activeRunId, payload.id, approved);
        live.setStatus(approved ? `Approved ${payload.tool}` : `Denied ${payload.tool}`);
      } else if (event === "done") {
        finalPayload = payload;
        if (payload.correlationId) lastCorrelationId = String(payload.correlationId);
      } else if (event === "error") {
        errorPayload = payload;
        if (payload.correlationId) lastCorrelationId = String(payload.correlationId);
        if (payload.toolsOnly) {
          setDegradeBanner({ mcpOk: true, toolsOnly: true, flaky: mcpFlaky });
        }
      }
    };

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        // Process complete SSE frames; tool_confirm may await UI
        const parts = buf.split("\n\n");
        buf = parts.pop() || "";
        for (const block of parts) {
          if (!block.trim() || block.startsWith(":")) continue;
          let event = "message";
          const dataLines = [];
          for (const line of block.split("\n")) {
            if (line.startsWith("event:")) event = line.slice(6).trim();
            else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
          }
          if (!dataLines.length) continue;
          let payload = {};
          try {
            payload = JSON.parse(dataLines.join("\n"));
          } catch {
            payload = { raw: dataLines.join("\n") };
          }
          await onEvent(event, payload);
        }
      }
      if (buf.trim()) {
        parseSseChunk(buf + "\n\n", () => {});
        // flush leftover via same parser path
        const flush = buf.endsWith("\n\n") ? buf : `${buf}\n\n`;
        const parts = flush.split("\n\n").filter(Boolean);
        for (const block of parts) {
          let event = "message";
          const dataLines = [];
          for (const line of block.split("\n")) {
            if (line.startsWith("event:")) event = line.slice(6).trim();
            else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
          }
          if (!dataLines.length) continue;
          try {
            await onEvent(event, JSON.parse(dataLines.join("\n")));
          } catch {
            /* ignore */
          }
        }
      }
    } catch (err) {
      if (err && err.name === "AbortError") {
        return { ok: false, cancelled: true, error: "Stopped by operator" };
      }
      throw err;
    } finally {
      activeAbort = null;
      activeRunId = null;
      setLatency(Math.round(performance.now() - started));
    }

    if (errorPayload) return { ok: false, ...errorPayload };
    if (finalPayload) {
      if (finalPayload.model) {
        lastModel = String(finalPayload.model).split("/").pop();
        if (sbModel) sbModel.textContent = lastModel;
      }
      return finalPayload;
    }
    return { ok: false, error: "Stream ended without a reply" };
  }

  function setDegradeBanner({ mcpOk, toolsOnly, flaky }) {
    if (!degradeBanner) return;
    mcpFlaky = Boolean(flaky);
    toolsOnlyMode = Boolean(toolsOnly);
    const bits = [];
    if (!mcpOk) {
      bits.push("MCP is unreachable — retries may help; tools rail is unavailable until it recovers.");
    } else if (flaky) {
      bits.push("MCP looks flaky — if calls fail, retry or refresh tools.");
    }
    if (toolsOnly) {
      bits.push("LLM unavailable — tools-only mode. Use the tools rail or fix OPENROUTER_API_KEY.");
    }
    if (!bits.length) {
      degradeBanner.hidden = true;
      degradeBanner.textContent = "";
      degradeBanner.classList.remove("warn");
      return;
    }
    degradeBanner.hidden = false;
    degradeBanner.classList.toggle("warn", mcpOk && toolsOnly);
    degradeBanner.innerHTML = "";
    const msg = document.createElement("span");
    msg.textContent = bits.join(" ");
    degradeBanner.appendChild(msg);
    if (!mcpOk || flaky) {
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "text-btn";
      retry.textContent = "Retry MCP";
      retry.addEventListener("click", () => loadConfig());
      degradeBanner.appendChild(retry);
    }
  }

  async function loadPlaybooks() {
    const roleQ = playbookRole ? `?role=${encodeURIComponent(playbookRole)}` : "";
    const data = await fetch(`/api/playbooks${roleQ}`)
      .then((r) => r.json())
      .catch(() => ({ playbooks: [], suggest: [] }));
    PLAYBOOKS = Array.isArray(data.playbooks) ? data.playbooks : [];
    SUGGEST = Array.isArray(data.suggest) ? data.suggest : [];
    if (data.role) {
      playbookRole = data.role;
      saveJson(ROLE_KEY, playbookRole);
    }
    window.TELLER_PLAYBOOKS = PLAYBOOKS;
    window.TELLER_SUGGEST = SUGGEST;
    renderSuggestChips();
    renderPlaybookChips();
  }

  function renderSuggestChips() {
    if (!suggestRow) return;
    suggestRow.innerHTML = "";
    const items = SUGGEST.length
      ? SUGGEST
      : [
          {
            label: "Open SoD",
            prompt: "How many open SoD policy violations are there right now?",
          },
        ];
    items.slice(0, 6).forEach((item) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "suggest-chip";
      btn.textContent = item.label || "Ask";
      btn.setAttribute("data-q", item.prompt || item.label || "");
      suggestRow.appendChild(btn);
    });
  }

  async function loadConfig() {
    const [health, config, actions] = await Promise.all([
      fetch("/api/health").then((r) => r.json()).catch(() => ({ ok: false })),
      fetch("/api/config").then((r) => r.json()).catch(() => ({})),
      fetch("/api/actions").then((r) => r.json()).catch(() => ({ actions: [] })),
    ]);

    allActions = actions.actions || [];
    const toolCount = config.actionCount || allActions.length;
    const mcpOk = Boolean(health.ok);
    if (mcpOk) {
      setStatus("up", `MCP · ${toolCount} tools`);
      if (sbMcp) sbMcp.textContent = `MCP · ${toolCount}`;
    } else {
      setStatus("down", "MCP unreachable");
      if (sbMcp) sbMcp.textContent = "MCP down";
    }

    const llmReady = Boolean(config.llmConfigured && config.llmAuthOk);
    if (!config.llmConfigured) {
      llmHint.textContent = "Tools-only · set OPENROUTER_API_KEY for free-text · press ?";
      if (sbModel) sbModel.textContent = "No LLM key";
    } else if (config.llmAuthOk) {
      const model = (config.model || "openrouter").split("/").pop();
      lastModel = model;
      llmHint.textContent = `Ask anything · ${model} · press ? for shortcuts`;
      if (sbModel) sbModel.textContent = model;
    } else {
      llmHint.textContent = "Tools-only · OpenRouter key rejected · buttons still work";
      if (sbModel) sbModel.textContent = "LLM auth failed";
    }

    setDegradeBanner({
      mcpOk,
      toolsOnly: !llmReady || Boolean(config.toolsOnly),
      flaky: mcpOk && Array.isArray(config.degraded) && config.degraded.includes("mcp"),
    });
    if (!mcpOk) {
      announceAgent("MCP unreachable. Retry or use when IdentityIQ MCP is back.");
    } else if (!llmReady) {
      announceAgent("LLM unavailable. Tools-only mode.");
    }

    updateModeBar();
    renderGroupTabs();
    renderAll();
    await loadPlaybooks();
  }

  function renderGroupTabs() {
    const groups = ["All", ...GROUP_ORDER.filter((g) => allActions.some((a) => a.group === g))];
    for (const a of allActions) {
      if (!groups.includes(a.group)) groups.push(a.group);
    }
    groupTabsEl.innerHTML = "";
    groups.forEach((group) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `group-tab${group === activeGroup ? " active" : ""}`;
      btn.setAttribute("role", "tab");
      btn.setAttribute("aria-selected", group === activeGroup ? "true" : "false");
      const count =
        group === "All"
          ? allActions.length
          : allActions.filter((a) => a.group === group).length;
      btn.textContent = group === "All" ? `All (${count})` : group;
      btn.title = group === "All" ? `${count} tools` : `${count} in ${group}`;
      btn.addEventListener("click", () => {
        activeGroup = group;
        renderGroupTabs();
        renderAll();
      });
      groupTabsEl.appendChild(btn);
    });
  }

  function filteredActions() {
    const q = (filterEl?.value || "").trim().toLowerCase();
    return allActions.filter((a) => {
      if (activeGroup !== "All" && a.group !== activeGroup) return false;
      if (!q) return true;
      const hay = `${a.label} ${a.group} ${a.description} ${a.tool}`.toLowerCase();
      return hay.includes(q);
    });
  }

  function renderFavorites() {
    const favActions = favorites
      .map((id) => allActions.find((a) => a.id === id))
      .filter(Boolean);
    if (!favActions.length) {
      favoritesEl.hidden = true;
      favoriteChipsEl.innerHTML = "";
      return;
    }
    favoritesEl.hidden = false;
    favoriteChipsEl.innerHTML = "";
    favActions.forEach((item) => favoriteChipsEl.appendChild(makeChip(item, true)));
  }

  function makeChip(item, inFavorites = false) {
    const wrap = document.createElement("div");
    wrap.className = "chip-wrap";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `chip${item.write ? " write" : ""}`;
    btn.textContent = item.label;
    btn.title = `${item.description}\n→ ${item.tool}${item.write ? "\n(write)" : ""}`;
    btn.addEventListener("click", () => runAction(item, btn));

    const pin = document.createElement("button");
    pin.type = "button";
    pin.className = `pin-btn${favorites.includes(item.id) ? " pinned" : ""}`;
    pin.title = favorites.includes(item.id) ? "Unpin" : "Pin";
    pin.setAttribute("aria-label", pin.title);
    pin.textContent = favorites.includes(item.id) ? "★" : "☆";
    pin.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleFavorite(item.id);
    });

    wrap.appendChild(btn);
    if (!inFavorites) wrap.appendChild(pin);
    else {
      wrap.appendChild(pin);
    }
    return wrap;
  }

  function toggleFavorite(id) {
    if (favorites.includes(id)) {
      favorites = favorites.filter((x) => x !== id);
    } else {
      favorites = [id, ...favorites].slice(0, 8);
    }
    saveJson(FAV_KEY, favorites);
    renderAll();
  }

  function renderAll() {
    const actions = filteredActions();
    matchCountEl.textContent = `${actions.length} tool${actions.length === 1 ? "" : "s"}`;
    renderFavorites();
    renderActions(actions);
  }

  function renderActions(actions) {
    actionsEl.innerHTML = "";
    if (!actions.length) {
      const empty = document.createElement("p");
      empty.className = "rail-empty";
      empty.textContent = "No tools match. Clear the filter or pick another group.";
      actionsEl.appendChild(empty);
      return;
    }

    const groups = new Map();
    for (const a of actions) {
      if (!groups.has(a.group)) groups.set(a.group, []);
      groups.get(a.group).push(a);
    }

    const ordered = [
      ...GROUP_ORDER.filter((g) => groups.has(g)),
      ...[...groups.keys()].filter((g) => !GROUP_ORDER.includes(g)),
    ];

    for (const group of ordered) {
      const items = groups.get(group);
      const section = document.createElement("section");
      section.className = "group";
      if (collapsed.has(group) && activeGroup === "All" && !(filterEl?.value || "").trim()) {
        section.classList.add("collapsed");
      }

      const title = document.createElement("button");
      title.type = "button";
      title.className = "group-title";
      title.setAttribute("aria-expanded", section.classList.contains("collapsed") ? "false" : "true");
      title.innerHTML = `<span class="caret" aria-hidden="true"></span><span>${group}</span><span class="group-count">${items.length}</span>`;
      title.addEventListener("click", () => {
        if (collapsed.has(group)) collapsed.delete(group);
        else collapsed.add(group);
        saveJson(COLLAPSE_KEY, [...collapsed]);
        section.classList.toggle("collapsed");
        title.setAttribute(
          "aria-expanded",
          section.classList.contains("collapsed") ? "false" : "true"
        );
      });
      section.appendChild(title);

      const chips = document.createElement("div");
      chips.className = "chips";
      for (const item of items) {
        chips.appendChild(makeChip(item));
      }
      section.appendChild(chips);
      actionsEl.appendChild(section);
    }
  }

  function setRailOpen(open) {
    if (isMobileRail()) {
      document.body.classList.toggle("rail-open", open);
    } else if (open) {
      railCollapsed = false;
      saveJson(RAIL_COLLAPSED_KEY, false);
      document.body.classList.remove("rail-collapsed");
    } else {
      railCollapsed = true;
      saveJson(RAIL_COLLAPSED_KEY, true);
      document.body.classList.add("rail-collapsed");
    }
    updateRailToggleUi();
  }

  function startNewChat({ announce = true } = {}) {
    history.length = 0;
    lastUserMessage = "";
    transcript.innerHTML = "";
    clearTyping();
    closeDetail();
    if (announce) {
      addBubble({
        role: "system",
        text: "Cleared. Ask below, pick a playbook, or press ⌘K.",
      });
    }
    if (suggestEl) suggestEl.hidden = false;
  }

  function renderPlaybookChips() {
    if (!playbookRow) return;
    playbookRow.innerHTML = "";
    // Prefer recent tools as chips when available; then role playbooks
    const recent = recentTools
      .map((name) => allActions.find((a) => a.tool === name || a.id === name))
      .filter(Boolean)
      .slice(0, 2);
    recent.forEach((action) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "suggest-chip playbook";
      btn.textContent = action.label || action.tool;
      btn.title = `Recent: ${action.tool}`;
      btn.addEventListener("click", () => runAction(action));
      playbookRow.appendChild(btn);
    });
    PLAYBOOKS.slice(0, Math.max(0, 4 - recent.length)).forEach((pb) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "suggest-chip playbook";
      btn.textContent = pb.label;
      btn.title = pb.prompt;
      btn.addEventListener("click", () => {
        if (toolsOnlyMode) {
          messageEl.value = pb.prompt;
          messageEl.focus();
          announceAgent("LLM unavailable — paste the playbook into chat after LLM is restored, or run a tool from the rail.");
          return;
        }
        messageEl.value = pb.prompt;
        messageEl.focus();
        composer.requestSubmit();
      });
      playbookRow.appendChild(btn);
    });
  }

  function showPalette(open, { filter = "" } = {}) {
    if (!paletteModal) return;
    paletteOpen = Boolean(open);
    paletteModal.hidden = !paletteOpen;
    if (!paletteOpen) {
      paletteItems = [];
      paletteIndex = 0;
      if (focusTrapCleanup) focusTrapCleanup();
      return;
    }
    showHelp(false);
    closeComposerMenu();
    if (paletteInput) {
      paletteInput.value = filter;
      paletteInput.focus();
      paletteInput.select();
    }
    renderPalette(filter);
    trapFocus(paletteModal);
  }

  function renderPalette(query) {
    if (!paletteList) return;
    const q = String(query || "").trim().toLowerCase();
    const sections = [];

    const playbooks = PLAYBOOKS.filter(
      (p) =>
        !q ||
        p.label.toLowerCase().includes(q) ||
        p.group.toLowerCase().includes(q) ||
        p.prompt.toLowerCase().includes(q)
    ).slice(0, 8);
    if (playbooks.length) {
      sections.push({
        label: "Playbooks",
        items: playbooks.map((p) => ({
          kind: "playbook",
          label: p.label,
          sub: p.prompt,
          badge: p.group,
          run: () => {
            showPalette(false);
            messageEl.value = p.prompt;
            messageEl.focus();
            composer.requestSubmit();
          },
        })),
      });
    }

    const tools = allActions
      .map((a) => ({
        action: a,
        score: Math.max(fuzzyScore(a.label, q), fuzzyScore(a.tool, q), fuzzyScore(a.group, q)),
      }))
      .filter((x) => (!q ? recentTools.includes(x.action.tool) || favorites.includes(x.action.id) : x.score > 0))
      .sort((a, b) => b.score - a.score)
      .slice(0, q ? 10 : 8)
      .map((x) => x.action);
    if (tools.length) {
      sections.push({
        label: q ? "Tools" : "Pinned / recent tools",
        items: tools.map((a) => ({
          kind: "tool",
          label: a.label || a.tool,
          sub: a.tool,
          badge: a.group || "Tool",
          run: () => {
            showPalette(false);
            runAction(a, null);
          },
        })),
      });
    }

    sections.push({
      label: "Actions",
      items: [
        {
          kind: "action",
          label: "New chat",
          sub: "Start a fresh conversation",
          badge: "Chat",
          run: () => {
            showPalette(false);
            startNewChat();
          },
        },
        {
          kind: "action",
          label: (() => {
            if (isMobileRail()) {
              return document.body.classList.contains("rail-open")
                ? "Hide tools panel"
                : "Show tools panel";
            }
            return document.body.classList.contains("rail-collapsed")
              ? "Show tools panel"
              : "Hide tools panel";
          })(),
          sub: "Toggle the left tools rail",
          badge: "UI",
          run: () => {
            showPalette(false);
            toggleRail();
          },
        },
      ].filter((item) => !q || item.label.toLowerCase().includes(q)),
    });

    paletteItems = [];
    paletteList.innerHTML = "";
    let rendered = 0;
    for (const section of sections) {
      if (!section.items.length) continue;
      const h = document.createElement("div");
      h.className = "palette-section";
      h.textContent = section.label;
      paletteList.appendChild(h);
      for (const item of section.items) {
        const idx = paletteItems.length;
        paletteItems.push(item);
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "palette-item";
        btn.setAttribute("role", "option");
        btn.dataset.index = String(idx);
        btn.innerHTML =
          `<span class="palette-item-name">${escapeHtml(item.label)}</span>` +
          `<span class="palette-item-kind">${escapeHtml(item.badge || item.kind)}</span>` +
          (item.sub
            ? `<span class="palette-item-sub">${escapeHtml(String(item.sub).slice(0, 140))}</span>`
            : "");
        btn.addEventListener("click", () => item.run());
        paletteList.appendChild(btn);
        rendered += 1;
      }
    }
    if (!rendered) {
      const empty = document.createElement("div");
      empty.className = "palette-empty";
      empty.textContent = "No matches. Try another search.";
      paletteList.appendChild(empty);
    }
    paletteIndex = 0;
    highlightPalette();
  }

  function highlightPalette() {
    const nodes = paletteList?.querySelectorAll(".palette-item") || [];
    nodes.forEach((el, i) => {
      el.classList.toggle("active", i === paletteIndex);
    });
    nodes[paletteIndex]?.scrollIntoView({ block: "nearest" });
  }

  function runPaletteIndex() {
    const item = paletteItems[paletteIndex];
    if (item) item.run();
  }

  async function runAction(action, btn) {
    if (busy) return;
    if (action.needsArgs) {
      setRailOpen(false);
      closeSlashMenu();
      messageEl.value = `Use the ${action.tool} tool to help with: `;
      messageEl.focus();
      return;
    }
    if (readOnly && action.write) {
      addBubble({
        role: "assistant",
        text: `Read-only mode blocked write tool \`${action.tool}\`. Turn off Read-only to run it.`,
        meta: [
          { label: "Read-only", tone: "coral" },
          { label: action.tool },
        ],
      });
      return;
    }
    let confirmed = !action.write;
    if (action.write) {
      confirmed = await askConfirm({
        tool: action.tool,
        arguments: action.args || {},
        lead: "This rail action can change IdentityIQ. Approve to run it now.",
      });
      if (!confirmed) {
        addBubble({
          role: "assistant",
          text: `Denied \`${action.tool}\`.`,
          meta: [{ label: "Denied", tone: "coral" }],
        });
        return;
      }
    }
    setBusy(true);
    if (btn) btn.disabled = true;
    setRailOpen(false);
    rememberRecentTool(action.tool);
    addBubble({
      role: "user",
      text: action.label,
      meta: [
        { label: "Tool", tone: "teal" },
        ...(action.write ? [{ label: "Write", tone: "coral" }] : []),
      ],
    });
    addTyping(`Calling ${action.tool}`);
    const started = performance.now();
    try {
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: action.id,
          readOnly,
          confirmed: Boolean(confirmed),
        }),
      });
      const data = await res.json();
      clearTyping();
      setLatency(Math.round(performance.now() - started));
      if (!data.ok) {
        if (data.needsArgs) {
          messageEl.value = `Use the ${data.tool || action.tool} tool to help with: `;
          messageEl.focus();
        }
        addBubble({
          role: "assistant",
          text: data.error || "Action failed",
          meta: [
            { label: "Tool", tone: "teal" },
            { label: "Error", tone: "coral" },
          ],
        });
        return;
      }
      const summary = summarizeResult(data.result);
      addBubble({
        role: "assistant",
        text: summary ? `${action.tool} — ${summary}` : `${action.tool} completed.`,
        meta: [
          { label: "Tool", tone: "teal" },
          { label: action.tool },
        ],
        result: data.result,
        detailTool: action.tool,
        openInspector: true,
      });
    } catch (err) {
      clearTyping();
      addBubble({
        role: "assistant",
        text: String(err),
        meta: [{ label: "Error", tone: "coral" }],
      });
    } finally {
      setBusy(false);
      if (btn) btn.disabled = false;
    }
  }

  async function sendChat(message) {
    const textIn = String(message || "").trim();
    if (!textIn || busy) return;
    closeComposerMenu();
    messageEl.value = "";
    lastUserMessage = textIn;
    setBusy(true);
    addBubble({ role: "user", text: textIn });
    const prior = history.slice();
    history.push({ role: "user", content: textIn });
    const live = createLivePanel();
    try {
      const data = await streamChat(textIn, prior, live);
      const meta = [{ label: "Answer" }];
      if (data.model) meta.push({ label: String(data.model).split("/").pop() });
      const stepCount = Array.isArray(data.steps) ? data.steps.length : 0;
      if (stepCount) meta.push({ label: `${stepCount} tool${stepCount === 1 ? "" : "s"}`, tone: "teal" });
      if (data.cancelled) meta.push({ label: "Stopped", tone: "coral" });
      else if (!data.ok) meta.push({ label: "Error", tone: "coral" });
      const text = data.reply || data.error || "No response";

      if (live.hadActivity()) {
        live.detachAsTrace();
      } else {
        live.remove();
      }

      let result = null;
      if (!data.ok && !data.cancelled) {
        result = data;
      } else if (data.result != null) {
        result = data.result;
      }

      // Prefer the richest identity/people payload from the turn for Inspect
      let detailTool = "";
      for (const step of data.steps || []) {
        if (step.tool) rememberRecentTool(step.tool);
        if (step.result && !looksLikeError(step.result)) {
          result = step.result;
          detailTool = step.tool || detailTool;
        }
      }
      if (!detailTool && data.tool) detailTool = String(data.tool);

      const followUps = buildFollowUps(data);
      const exportPayload = {
        question: textIn,
        answer: text,
        model: data.model || lastModel || "",
        steps: (data.steps || []).map((s) => ({
          tool: s.tool,
          arguments: s.arguments,
          normalizedArguments: s.normalizedArguments,
          summary: s.summary || (s.ok === false ? "failed" : "ok"),
          ok: s.ok,
        })),
      };
      const shouldInspect =
        Boolean(result) &&
        !data.cancelled &&
        (Boolean(detailTool.match(/identity|report|manager|account|app/i)) ||
          Boolean(detailDataRoot(result)?.tellerCard) ||
          Boolean(detailDataRoot(result)?.peopleLabels) ||
          Boolean(detailDataRoot(result)?.reportLabels));
      if (data.correlationId) lastCorrelationId = String(data.correlationId);
      if (data.toolsOnly || (!data.ok && /openrouter|llm|api key/i.test(String(data.error || "")))) {
        setDegradeBanner({ mcpOk: !mcpFlaky, toolsOnly: true, flaky: mcpFlaky });
      }
      announceAgent(data.ok ? "Answer ready." : data.cancelled ? "Stopped." : "Answer failed.");
      addBubble({
        role: "assistant",
        text,
        meta,
        result,
        detailTool,
        openInspector: shouldInspect,
        followUps,
        exportPayload,
        cards: data.cards || null,
        feedback: data.ok
          ? {
              question: textIn,
              reply: text,
              model: data.model || lastModel,
              tools: (data.steps || []).map((s) => s.tool).filter(Boolean),
              runId: data.runId || activeRunId,
              correlationId: data.correlationId || lastCorrelationId,
            }
          : null,
        onRetry: () => sendChat(textIn),
      });
      history.push({ role: "assistant", content: text });
    } catch (err) {
      live.remove();
      announceAgent("Answer failed.");
      addBubble({
        role: "assistant",
        text: String(err),
        meta: [{ label: "Error", tone: "coral" }],
        followUps: lastUserMessage ? [{ id: "retry", label: "Retry", kind: "retry" }] : null,
        onRetry: () => sendChat(textIn),
      });
    } finally {
      setBusy(false);
      messageEl.focus();
      renderPlaybookChips();
    }
  }

  composer.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) return;
    if (slashOpen && slashItems[slashIndex]) {
      pickMenuItem(slashItems[slashIndex]);
      return;
    }
    const message = messageEl.value.trim();
    if (!message) return;
    // Bare `/query` that didn't resolve — don't send as chat
    if (message.startsWith("/") && !message.includes(" ") && menuMode === "slash") {
      openSlashMenu(message.slice(1));
      return;
    }
    await sendChat(message);
  });

  function parseSlashState(value, cursor) {
    const text = String(value || "");
    const pos = cursor == null ? text.length : cursor;
    const before = text.slice(0, pos);
    const match = before.match(/(^|\s)\/([^\s]*)$/);
    if (!match) return null;
    const tokenStart = before.length - match[2].length - 1;
    const after = text.slice(pos);
    if (tokenStart > 0 && text.trimStart()[0] !== "/") {
      return null;
    }
    return {
      query: match[2] || "",
      tokenStart,
      tokenEnd: pos + (after.match(/^[^\s]*/) || [""])[0].length,
    };
  }

  function parseMentionState(value, cursor) {
    const text = String(value || "");
    const pos = cursor == null ? text.length : cursor;
    const before = text.slice(0, pos);
    // @query — allow letters, digits, dots, dashes, underscores
    const match = before.match(/(^|[\s(])@([a-zA-Z0-9._-]*)$/);
    if (!match) return null;
    const query = match[2] || "";
    const tokenStart = before.length - query.length - 1;
    const after = text.slice(pos);
    const rest = (after.match(/^[a-zA-Z0-9._-]*/) || [""])[0];
    return {
      query,
      tokenStart,
      tokenEnd: pos + rest.length,
    };
  }

  function rankSlashActions(query) {
    const q = (query || "").trim().toLowerCase();
    const favSet = new Set(favorites);
    const recentSet = new Set(recentTools);
    const scored = [];
    for (const a of allActions) {
      // Prefer canonical tool rows over fav: duplicates for ranking
      if (String(a.id || "").startsWith("fav:") && allActions.some((x) => x.tool === a.tool && x.id === a.tool)) {
        continue;
      }
      const label = String(a.label || "");
      const tool = String(a.tool || "");
      const group = String(a.group || "");
      const desc = String(a.description || "");
      const toolScore = fuzzyScore(tool, q);
      const labelScore = fuzzyScore(label, q);
      const groupScore = fuzzyScore(group, q);
      const descScore = q ? fuzzyScore(desc, q) * 0.4 : 0;
      const best = Math.max(toolScore, labelScore, groupScore * 0.5, descScore);
      if (q && best <= 0) continue;

      let score = best;
      if (favSet.has(a.id) || favSet.has(a.tool) || favSet.has(`fav:${a.tool}`)) score += 40;
      const recentIdx = recentTools.indexOf(tool);
      if (recentIdx >= 0) score += 55 - recentIdx * 4;
      if (!q && recentSet.has(tool)) score += 20;
      scored.push({ action: a, score, toolL: tool.toLowerCase(), group });
    }
    scored.sort((x, y) => y.score - x.score || x.toolL.localeCompare(y.toolL));
    return scored.slice(0, SLASH_LIMIT);
  }

  function closeComposerMenu() {
    slashOpen = false;
    menuMode = null;
    slashItems = [];
    slashIndex = 0;
    slashQuery = "";
    mentionToken = null;
    if (mentionTimer) {
      clearTimeout(mentionTimer);
      mentionTimer = null;
    }
    if (slashMenuEl) {
      slashMenuEl.hidden = true;
      slashMenuEl.innerHTML = "";
    }
    messageEl?.removeAttribute("aria-activedescendant");
    messageEl?.setAttribute("aria-expanded", "false");
  }

  function closeSlashMenu() {
    closeComposerMenu();
  }

  function renderComposerMenu({ title, queryLabel, emptyText, sections }) {
    if (!slashMenuEl) return;
    slashMenuEl.hidden = false;
    slashOpen = true;
    messageEl?.setAttribute("aria-expanded", "true");
    slashMenuEl.innerHTML = "";

    const head = document.createElement("div");
    head.className = "slash-menu-head";
    head.innerHTML =
      `<span>${escapeHtml(title)}</span>` +
      `<span class="slash-menu-query">${escapeHtml(queryLabel)}</span>`;
    slashMenuEl.appendChild(head);

    if (!slashItems.length) {
      const empty = document.createElement("div");
      empty.className = "slash-empty";
      empty.textContent = emptyText;
      slashMenuEl.appendChild(empty);
      return;
    }

    const list = document.createElement("div");
    list.className = "slash-list";
    let rendered = 0;
    for (const section of sections || [{ label: null, items: slashItems }]) {
      const items = section.items || [];
      if (!items.length) continue;
      if (section.label) {
        const h = document.createElement("div");
        h.className = "slash-section";
        h.textContent = section.label;
        list.appendChild(h);
      }
      for (const item of items) {
        const i = slashItems.indexOf(item);
        if (i < 0) continue;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `slash-item${i === slashIndex ? " active" : ""}`;
        btn.id = `slash-opt-${i}`;
        btn.setAttribute("role", "option");
        btn.setAttribute("aria-selected", i === slashIndex ? "true" : "false");
        if (menuMode === "mention") {
          btn.innerHTML =
            `<span class="slash-item-main">` +
            `<span class="slash-item-name">${escapeHtml(item.label)}</span>` +
            `<span class="slash-item-tool">${escapeHtml(item.subtitle || item.type || "")}</span>` +
            `</span>` +
            `<span class="slash-item-meta">` +
            `<span class="slash-item-group ${item.type === "app" ? "app" : "id"}">${escapeHtml(item.type || "item")}</span>` +
            `</span>`;
        } else {
          const pinned = favorites.includes(item.id) || favorites.includes(`fav:${item.tool}`);
          const recent = recentTools.includes(item.tool);
          btn.innerHTML =
            `<span class="slash-item-main">` +
            `<span class="slash-item-name">${escapeHtml(item.label || item.tool)}</span>` +
            `<span class="slash-item-tool">${escapeHtml(item.tool || "")}</span>` +
            `</span>` +
            `<span class="slash-item-meta">` +
            `<span class="slash-item-group">${escapeHtml(item.group || "Other")}</span>` +
            (recent ? `<span class="slash-item-pin" title="Recent">rec</span>` : "") +
            (pinned ? `<span class="slash-item-pin" title="Pinned">★</span>` : "") +
            (item.write ? `<span class="slash-item-args">write</span>` : "") +
            (item.needsArgs ? `<span class="slash-item-args">args</span>` : "") +
            `</span>`;
          if (item.description) btn.title = item.description;
        }
        btn.addEventListener("mousedown", (ev) => {
          ev.preventDefault();
          pickMenuItem(item);
        });
        btn.addEventListener("mouseenter", () => {
          slashIndex = i;
          highlightSlash();
        });
        list.appendChild(btn);
        rendered += 1;
      }
    }
    slashMenuEl.appendChild(list);

    const foot = document.createElement("div");
    foot.className = "slash-menu-foot";
    foot.innerHTML =
      `<span><kbd>↑</kbd><kbd>↓</kbd> move</span>` +
      `<span><kbd>Enter</kbd> ${menuMode === "mention" ? "insert" : "run"}</span>` +
      `<span><kbd>Esc</kbd> close</span>`;
    slashMenuEl.appendChild(foot);

    const active = $(`#slash-opt-${slashIndex}`);
    if (active) {
      messageEl?.setAttribute("aria-activedescendant", active.id);
      active.scrollIntoView({ block: "nearest" });
    }
    if (!rendered && slashItems.length) {
      // fallback flat list if section mapping failed
      slashIndex = Math.min(slashIndex, slashItems.length - 1);
    }
  }

  function highlightSlash() {
    if (!slashMenuEl) return;
    slashMenuEl.querySelectorAll(".slash-item").forEach((el) => {
      const i = Number(String(el.id || "").replace("slash-opt-", ""));
      const on = i === slashIndex;
      el.classList.toggle("active", on);
      el.setAttribute("aria-selected", on ? "true" : "false");
    });
    const active = $(`#slash-opt-${slashIndex}`);
    if (active) {
      messageEl?.setAttribute("aria-activedescendant", active.id);
      active.scrollIntoView({ block: "nearest" });
    }
  }

  function openSlashMenu(query = "") {
    menuMode = "slash";
    mentionToken = null;
    slashQuery = query;
    const ranked = rankSlashActions(query);
    slashItems = ranked.map((r) => r.action);
    slashIndex = 0;

    const recentNames = new Set(recentTools);
    const favIds = new Set(favorites);
    const recentItems = [];
    const favItems = [];
    const rest = [];
    for (const a of slashItems) {
      if (!query && recentNames.has(a.tool) && recentItems.length < 5) {
        recentItems.push(a);
      } else if (favIds.has(a.id) || favIds.has(`fav:${a.tool}`)) {
        favItems.push(a);
      } else {
        rest.push(a);
      }
    }
    // Group remainder by group name
    const byGroup = new Map();
    for (const a of rest) {
      const g = a.group || "Other";
      if (!byGroup.has(g)) byGroup.set(g, []);
      byGroup.get(g).push(a);
    }
    const sections = [];
    if (recentItems.length) sections.push({ label: "Recent", items: recentItems });
    if (favItems.length) sections.push({ label: "Pinned", items: favItems });
    for (const g of GROUP_ORDER) {
      if (byGroup.has(g)) sections.push({ label: g, items: byGroup.get(g) });
    }
    for (const [g, items] of byGroup) {
      if (!GROUP_ORDER.includes(g)) sections.push({ label: g, items });
    }

    renderComposerMenu({
      title: "Tools",
      queryLabel: query ? `/${query}` : "type to filter",
      emptyText: allActions.length ? "No tools match that filter" : "Tools still loading…",
      sections,
    });
  }

  async function openMentionMenu(token) {
    menuMode = "mention";
    mentionToken = token;
    slashQuery = token.query || "";
    const seq = ++mentionSeq;
    slashItems = [];
    slashIndex = 0;
    renderComposerMenu({
      title: "Mention",
      queryLabel: slashQuery ? `@${slashQuery}` : "@ identity or app",
      emptyText: slashQuery ? "Searching…" : "Type a name to search IIQ",
      sections: [],
    });

    if (!slashQuery) return;
    try {
      const res = await fetch(`/api/suggest?q=${encodeURIComponent(slashQuery)}&kind=all`);
      const data = await res.json();
      if (seq !== mentionSeq || menuMode !== "mention") return;
      slashItems = Array.isArray(data.items) ? data.items : [];
      slashIndex = 0;
      const identities = slashItems.filter((i) => i.type === "identity");
      const apps = slashItems.filter((i) => i.type === "app");
      const sections = [];
      if (identities.length) sections.push({ label: "Identities", items: identities });
      if (apps.length) sections.push({ label: "Applications", items: apps });
      renderComposerMenu({
        title: "Mention",
        queryLabel: `@${slashQuery}`,
        emptyText: data.ok === false ? data.error || "Suggest failed" : "No matches in IIQ",
        sections,
      });
    } catch (err) {
      if (seq !== mentionSeq) return;
      renderComposerMenu({
        title: "Mention",
        queryLabel: `@${slashQuery}`,
        emptyText: String(err),
        sections: [],
      });
    }
  }

  function syncComposerFromInput() {
    const slash = parseSlashState(messageEl.value, messageEl.selectionStart);
    if (slash) {
      openSlashMenu(slash.query);
      return;
    }
    const mention = parseMentionState(messageEl.value, messageEl.selectionStart);
    if (mention) {
      if (mentionTimer) clearTimeout(mentionTimer);
      // Open shell immediately; debounce MCP search
      mentionToken = mention;
      menuMode = "mention";
      slashOpen = true;
      mentionTimer = setTimeout(() => openMentionMenu(mention), mention.query ? 160 : 0);
      return;
    }
    if (slashOpen) closeComposerMenu();
  }

  function pickMenuItem(item) {
    if (!item || busy) return;
    if (menuMode === "mention") {
      pickMentionItem(item);
      return;
    }
    pickSlashItem(item);
  }

  function pickSlashItem(item) {
    if (!item || busy) return;
    closeComposerMenu();
    messageEl.value = "";
    rememberRecentTool(item.tool);
    if (item.needsArgs) {
      messageEl.value = `Use the ${item.tool} tool to help with: `;
      messageEl.focus();
      const len = messageEl.value.length;
      messageEl.setSelectionRange(len, len);
      return;
    }
    runAction(item, null);
  }

  function pickMentionItem(item) {
    if (!item || !mentionToken) return;
    // Prefer rich insert from API; never drop the display name for bare IDs.
    let insert = String(item.insert || "").trim();
    if (!insert) {
      const label = String(item.label || "").trim();
      const id = String(item.id || "").trim();
      insert = label && id && label !== id ? `${label} (${id})` : label || id;
    }
    if (!insert) return;
    const value = messageEl.value;
    const before = value.slice(0, mentionToken.tokenStart);
    const after = value.slice(mentionToken.tokenEnd);
    // Keep a trailing space for continued typing
    const next = `${before}${insert} ${after}`;
    messageEl.value = next;
    const caret = before.length + insert.length + 1;
    closeComposerMenu();
    messageEl.focus();
    messageEl.setSelectionRange(caret, caret);
  }

  function openSlashShortcut() {
    setRailOpen(false);
    messageEl.focus();
    if (!messageEl.value.trim() || !messageEl.value.startsWith("/")) {
      messageEl.value = "/";
      messageEl.setSelectionRange(1, 1);
    }
    syncComposerFromInput();
  }

  messageEl.addEventListener("keydown", (e) => {
    if (slashOpen) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (slashItems.length) {
          slashIndex = (slashIndex + 1) % slashItems.length;
          highlightSlash();
        }
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        if (slashItems.length) {
          slashIndex = (slashIndex - 1 + slashItems.length) % slashItems.length;
          highlightSlash();
        }
        return;
      }
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (slashItems[slashIndex]) pickMenuItem(slashItems[slashIndex]);
        return;
      }
      if (e.key === "Tab" && slashItems[slashIndex]) {
        e.preventDefault();
        pickMenuItem(slashItems[slashIndex]);
        return;
      }
      if (e.key === "Escape") {
        e.preventDefault();
        closeComposerMenu();
        return;
      }
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      composer.requestSubmit();
    }
  });

  messageEl.addEventListener("input", () => syncComposerFromInput());
  messageEl.addEventListener("click", () => syncComposerFromInput());
  messageEl.addEventListener("blur", () => {
    setTimeout(() => {
      if (!slashMenuEl?.contains(document.activeElement)) closeComposerMenu();
    }, 120);
  });

  filterEl?.addEventListener("input", () => renderAll());

  document.addEventListener("keydown", (e) => {
    const tag = (e.target && e.target.tagName) || "";
    const typing =
      tag === "INPUT" || tag === "TEXTAREA" || (e.target && e.target.isContentEditable);
    const inPalette = paletteOpen && paletteInput && document.activeElement === paletteInput;

    if ((e.metaKey || e.ctrlKey) && String(e.key).toLowerCase() === "k") {
      e.preventDefault();
      showPalette(!paletteOpen);
      return;
    }

    if (paletteOpen) {
      if (e.key === "Escape") {
        e.preventDefault();
        showPalette(false);
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (paletteItems.length) {
          paletteIndex = (paletteIndex + 1) % paletteItems.length;
          highlightPalette();
        }
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        if (paletteItems.length) {
          paletteIndex = (paletteIndex - 1 + paletteItems.length) % paletteItems.length;
          highlightPalette();
        }
        return;
      }
      if (e.key === "Enter" && (inPalette || !typing || e.target === paletteInput)) {
        e.preventDefault();
        runPaletteIndex();
        return;
      }
    }

    if (e.key === "?" && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) {
      e.preventDefault();
      showHelp(true);
      return;
    }
    if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) {
      e.preventDefault();
      openSlashShortcut();
      return;
    }
    if (e.key === "Escape") {
      if (!confirmModal?.hidden) {
        e.preventDefault();
        closeConfirm(false);
        return;
      }
      if (!feedbackModal?.hidden) {
        e.preventDefault();
        closeFeedbackModal();
        return;
      }
      if (!helpModal?.hidden) {
        e.preventDefault();
        showHelp(false);
        return;
      }
      if (slashOpen) {
        closeSlashMenu();
        return;
      }
      if (document.body.classList.contains("detail-open")) {
        e.preventDefault();
        closeDetail();
        return;
      }
      if (busy) {
        e.preventDefault();
        stopActiveRun();
        return;
      }
      if (isMobileRail() && document.body.classList.contains("rail-open")) {
        setRailOpen(false);
      } else if (!isMobileRail() && !document.body.classList.contains("rail-collapsed")) {
        setRailOpen(false);
      } else if (filterEl && filterEl.value) {
        filterEl.value = "";
        renderAll();
      }
    }
  });

  stopBtn?.addEventListener("click", () => stopActiveRun());
  confirmApprove?.addEventListener("click", () => closeConfirm(true));
  confirmDeny?.addEventListener("click", () => closeConfirm(false));
  confirmModal?.addEventListener("click", (e) => {
    if (e.target === confirmModal) closeConfirm(false);
  });
  helpBtn?.addEventListener("click", () => showHelp(true));
  helpClose?.addEventListener("click", () => showHelp(false));
  helpModal?.addEventListener("click", (e) => {
    if (e.target === helpModal) showHelp(false);
  });
  paletteBtn?.addEventListener("click", () => showPalette(true));
  paletteClose?.addEventListener("click", () => showPalette(false));
  paletteModal?.addEventListener("click", (e) => {
    if (e.target === paletteModal) showPalette(false);
  });
  paletteInput?.addEventListener("input", () => renderPalette(paletteInput.value));
  detailClose?.addEventListener("click", () => closeDetail());
  detailBackdrop?.addEventListener("click", () => closeDetail());
  detailCopy?.addEventListener("click", () => {
    if (detailPayload == null) return;
    const payload =
      typeof detailPayload === "string" ? detailPayload : JSON.stringify(detailPayload, null, 2);
    copyText(payload, detailCopy);
  });
  feedbackModal?.querySelectorAll("[data-reason]").forEach((btn) => {
    btn.addEventListener("click", () => {
      feedbackReason = btn.getAttribute("data-reason");
      feedbackModal.querySelectorAll("[data-reason]").forEach((b) => {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
    });
  });
  feedbackSkip?.addEventListener("click", async () => {
    if (feedbackContext) {
      await submitFeedback({
        ...feedbackContext,
        rating: "down",
        reason: feedbackReason || "other",
        comment: feedbackComment?.value || "",
      });
    }
    closeFeedbackModal();
  });
  feedbackSubmit?.addEventListener("click", async () => {
    if (feedbackContext) {
      await submitFeedback({
        ...feedbackContext,
        rating: "down",
        reason: feedbackReason || "other",
        comment: feedbackComment?.value || "",
      });
    }
    closeFeedbackModal();
  });
  feedbackModal?.addEventListener("click", (e) => {
    if (e.target === feedbackModal) closeFeedbackModal();
  });
  readOnlyEl?.addEventListener("change", () => {
    readOnly = Boolean(readOnlyEl.checked);
    saveJson(READONLY_KEY, readOnly);
    updateModeBar();
  });

  railToggle?.addEventListener("click", () => toggleRail());
  railClose?.addEventListener("click", () => setRailOpen(false));
  railBackdrop?.addEventListener("click", () => setRailOpen(false));
  window.addEventListener("resize", () => applyRailLayout());

  newChatBtn?.addEventListener("click", () => startNewChat());

  suggestEl?.addEventListener("click", (e) => {
    const btn = e.target.closest(".suggest-chip");
    if (!btn || btn.classList.contains("playbook")) return;
    const q = btn.getAttribute("data-q");
    if (!q) return;
    messageEl.value = q;
    messageEl.focus();
    composer.requestSubmit();
  });

  async function handleDeepLink() {
    const path = window.location.pathname || "";
    const m = path.match(/^\/(identity|cert|app|entitlement)\/([^/]+)\/?$/i);
    if (!m) return false;
    const kind = m[1].toLowerCase();
    const key = decodeURIComponent(m[2] || "").trim();
    if (!key) return false;
    const prompts = {
      identity: `Look up identity ${key}. Summarize display name, manager, title, location, and lock/active status.`,
      cert: `Find certification or campaign matching ${key}. Summarize owners and remaining items.`,
      app: `Look up application ${key}. Summarize type, owner, and recent aggregation health if available.`,
      entitlement: `Find entitlement ${key}. Summarize which application it belongs to and a short description.`,
    };
    const toolHints = {
      identity: "get_identity",
      cert: "list_certifications",
      app: "get_application",
      entitlement: "search_entitlements",
    };
    addBubble({
      role: "system",
      text: `Deep link: ${kind}/${key} — opening Inspect after lookup.`,
    });
    announceAgent(`Deep link ${kind} ${key}`);
    // Prefetch into Inspect with a stub while chat runs
    openDetail(
      {
        ok: true,
        data: {
          deepLink: { kind, key },
          displayName: key,
          note: "Loading live data via chat…",
        },
      },
      { tool: toolHints[kind] || kind, auto: true }
    );
    await sendChat(prompts[kind] || `Look up ${kind} ${key}`);
    return true;
  }

  applyRailLayout();
  // Mobile: tools drawer is the starting surface
  if (isMobileRail()) {
    setRailOpen(true);
  }
  renderSuggestChips();
  renderPlaybookChips();
  startNewChat({ announce: false });
  addBubble({
    role: "system",
    text: "Ready. / tools · @ people · ⌘K playbooks · Inspect opens the detail pane.",
  });

  messageEl?.setAttribute("aria-expanded", "false");
  updateModeBar();
  loadConfig().then(() => handleDeepLink());
})();
