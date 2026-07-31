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
  const clearChatBtn = $("#clear-chat");
  const suggestEl = $("#suggest");

  const FAV_KEY = "meridian.teller.favorites";
  const COLLAPSE_KEY = "meridian.teller.collapsed";
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
  let favorites = loadJson(FAV_KEY, []);
  let collapsed = new Set(loadJson(COLLAPSE_KEY, null) ?? ["Apps", "Identities", "Work", "Governance", "Ops", "Catalog"]);
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

  function addBubble({ role, text, meta = [], result = null }) {
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
      const p = document.createElement("p");
      p.textContent = text;
      div.appendChild(p);
    }

    if (result != null) {
      const summary = summarizeResult(result);
      const details = document.createElement("details");
      details.className = "result-panel";
      if (role === "assistant" && summary && !looksLikeError(result)) {
        details.open = false;
      } else {
        details.open = true;
      }

      const summaryEl = document.createElement("summary");
      summaryEl.innerHTML = `<span>${escapeHtml(summary || "Result payload")}</span>`;
      const actions = document.createElement("span");
      actions.className = "result-actions";
      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "text-btn";
      copyBtn.textContent = "Copy";
      copyBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        const payload = typeof result === "string" ? result : JSON.stringify(result, null, 2);
        try {
          await navigator.clipboard.writeText(payload);
          copyBtn.textContent = "Copied";
          setTimeout(() => {
            copyBtn.textContent = "Copy";
          }, 1200);
        } catch {
          copyBtn.textContent = "Failed";
        }
      });
      actions.appendChild(copyBtn);
      summaryEl.appendChild(actions);
      details.appendChild(summaryEl);

      const pre = document.createElement("pre");
      pre.textContent =
        typeof result === "string" ? result : JSON.stringify(result, null, 2);
      details.appendChild(pre);
      div.appendChild(details);
    }

    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
    if (suggestEl && history.length === 0 && role === "system") {
      suggestEl.hidden = false;
    } else if (suggestEl && role !== "system") {
      suggestEl.hidden = true;
    }
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

  function addTyping() {
    const div = document.createElement("div");
    div.className = "bubble assistant typing";
    div.id = "typing";
    div.innerHTML =
      '<div class="meta"><span class="tag">Working</span></div><p class="typing-dots" aria-label="Loading"><span></span><span></span><span></span></p>';
    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
  }

  function clearTyping() {
    const el = $("#typing");
    if (el) el.remove();
  }

  async function loadConfig() {
    const [health, config, actions] = await Promise.all([
      fetch("/api/health").then((r) => r.json()).catch(() => ({ ok: false })),
      fetch("/api/config").then((r) => r.json()).catch(() => ({})),
      fetch("/api/actions").then((r) => r.json()).catch(() => ({ actions: [] })),
    ]);

    allActions = actions.actions || [];
    if (health.ok) {
      setStatus("up", `MCP · ${config.actionCount || allActions.length} tools`);
    } else {
      setStatus("down", "MCP unreachable");
    }

    if (!config.llmConfigured) {
      llmHint.textContent = "Buttons work offline from LLM — set OPENROUTER_API_KEY for free-text";
    } else if (config.llmAuthOk) {
      const model = (config.model || "openrouter").split("/").pop();
      llmHint.textContent = `Ask anything · ${model}`;
    } else {
      llmHint.textContent = "OpenRouter key rejected — buttons still work";
    }

    renderGroupTabs();
    renderAll();
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
    btn.className = "chip";
    btn.textContent = item.label;
    btn.title = `${item.description}\n→ ${item.tool}`;
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
    document.body.classList.toggle("rail-open", open);
    railToggle.setAttribute("aria-expanded", open ? "true" : "false");
    railBackdrop.hidden = !open;
    railClose.hidden = !open;
  }

  async function runAction(action, btn) {
    if (busy) return;
    if (action.needsArgs) {
      setRailOpen(false);
      messageEl.value = `Use the ${action.tool} tool to help with: `;
      messageEl.focus();
      return;
    }
    setBusy(true);
    if (btn) btn.disabled = true;
    setRailOpen(false);
    addBubble({
      role: "user",
      text: action.label,
      meta: [{ label: "Tool", tone: "teal" }],
    });
    addTyping();
    try {
      const res = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: action.id }),
      });
      const data = await res.json();
      clearTyping();
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
      addBubble({
        role: "assistant",
        text: `${action.tool} completed.`,
        meta: [
          { label: "Tool", tone: "teal" },
          { label: action.tool },
        ],
        result: data.result,
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

  composer.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (busy) return;
    const message = messageEl.value.trim();
    if (!message) return;
    messageEl.value = "";
    setBusy(true);
    addBubble({ role: "user", text: message });
    history.push({ role: "user", content: message });
    addTyping();
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });
      const data = await res.json();
      clearTyping();
      const meta = [{ label: "Ask" }];
      if (data.model) meta.push({ label: String(data.model).split("/").pop() });
      const stepCount = Array.isArray(data.steps) ? data.steps.length : 0;
      if (stepCount > 1) meta.push({ label: `${stepCount} tools`, tone: "teal" });
      else if (data.tool) meta.push({ label: data.tool, tone: "teal" });
      if (!data.ok) meta.push({ label: "Error", tone: "coral" });
      const text = data.reply || data.error || "No response";
      addBubble({
        role: "assistant",
        text,
        meta,
        result: stepCount ? { steps: data.steps, last: data.result } : data.result,
      });
      history.push({ role: "assistant", content: text });
    } catch (err) {
      clearTyping();
      addBubble({
        role: "assistant",
        text: String(err),
        meta: [{ label: "Error", tone: "coral" }],
      });
    } finally {
      setBusy(false);
      messageEl.focus();
    }
  });

  messageEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      composer.requestSubmit();
    }
  });

  filterEl?.addEventListener("input", () => renderAll());

  document.addEventListener("keydown", (e) => {
    const tag = (e.target && e.target.tagName) || "";
    const typing =
      tag === "INPUT" || tag === "TEXTAREA" || (e.target && e.target.isContentEditable);
    if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey && !e.altKey) {
      e.preventDefault();
      setRailOpen(true);
      filterEl?.focus();
      filterEl?.select();
    }
    if (e.key === "Escape") {
      if (document.body.classList.contains("rail-open")) {
        setRailOpen(false);
      } else if (filterEl && filterEl.value) {
        filterEl.value = "";
        renderAll();
      }
    }
  });

  railToggle?.addEventListener("click", () => {
    setRailOpen(!document.body.classList.contains("rail-open"));
  });
  railClose?.addEventListener("click", () => setRailOpen(false));
  railBackdrop?.addEventListener("click", () => setRailOpen(false));

  clearChatBtn?.addEventListener("click", () => {
    history.length = 0;
    transcript.innerHTML = "";
    addBubble({
      role: "system",
      text: "Conversation cleared. Pin frequent tools with ★, filter with /, or ask below.",
    });
    if (suggestEl) suggestEl.hidden = false;
  });

  suggestEl?.addEventListener("click", (e) => {
    const btn = e.target.closest(".suggest-chip");
    if (!btn) return;
    const q = btn.getAttribute("data-q");
    if (!q) return;
    messageEl.value = q;
    messageEl.focus();
    composer.requestSubmit();
  });

  addBubble({
    role: "system",
    text: "Meridian Teller is ready. Use Tools for instant lookups, pin favorites with ★, or ask in plain language when OpenRouter is configured.",
  });

  loadConfig();
})();
