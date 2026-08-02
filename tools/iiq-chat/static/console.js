/* Meridian Console — Waves 1–3 central shell */
(() => {
  const VIEWS = new Set([
    "hub",
    "orphans",
    "ops",
    "inbox",
    "catalog",
    "certs",
    "sod",
    "identity",
    "jml",
    "evidence",
    "provisioning",
    "heatmap",
    "workgroups",
    "audit",
  ]);

  const TITLES = {
    hub: ["Command hub", "Hub"],
    orphans: ["Ops", "Orphan desk"],
    ops: ["Ops", "Aggregation pipeline"],
    inbox: ["Business", "Approval inbox"],
    catalog: ["Business", "Access catalog"],
    certs: ["Business", "Cert console"],
    sod: ["Control room", "SoD war room"],
    identity: ["Control room", "Identity 360"],
    jml: ["Control room", "JML timeline"],
    evidence: ["Control room", "Evidence pack"],
    provisioning: ["Ops", "Provisioning debugger"],
    heatmap: ["Explore", "Risk heatmap"],
    workgroups: ["Explore", "Workgroups"],
    audit: ["Explore", "Audit activity"],
  };

  const FALLBACK_MENU = {
    groups: [
      {
        id: "ops",
        title: "Ops",
        subtitle: "Nightly health & remediation",
        items: [
          { id: "hub", title: "Command hub", blurb: "Counts across every desk" },
          { id: "orphans", title: "Orphan desk", blurb: "Merge & correlate" },
          { id: "ops", title: "Aggregation pipeline", blurb: "Stop/go board" },
          { id: "provisioning", title: "Provisioning debugger", blurb: "Failed plans" },
        ],
      },
      {
        id: "business",
        title: "Business",
        subtitle: "Approvers, requesters, managers",
        items: [
          { id: "inbox", title: "Approval inbox", blurb: "Work items" },
          { id: "catalog", title: "Access catalog", blurb: "Roles & ents" },
          { id: "certs", title: "Cert console", blurb: "Campaigns" },
          { id: "orgchart", title: "Org chart", blurb: "Hierarchy", href: "/orgchart.html" },
        ],
      },
      {
        id: "control",
        title: "Control room",
        subtitle: "Bank-grade governance",
        items: [
          { id: "sod", title: "SoD war room", blurb: "Violations" },
          { id: "identity", title: "Identity 360", blurb: "Helpdesk" },
          { id: "jml", title: "JML timeline", blurb: "Lifecycle personas" },
          { id: "evidence", title: "Evidence pack", blurb: "Exam binder" },
        ],
      },
      {
        id: "explore",
        title: "Explore",
        subtitle: "Deep dives",
        items: [
          { id: "heatmap", title: "Risk heatmap", blurb: "Privileged ents" },
          { id: "workgroups", title: "Workgroups", blurb: "Membership" },
          { id: "audit", title: "Audit activity", blurb: "Event stream" },
          { id: "teller", title: "Teller chat", blurb: "NL agent", href: "/" },
        ],
      },
    ],
    version: "local",
  };

  const el = {
    status: document.getElementById("mc-status"),
    main: document.getElementById("mc-main"),
    meta: document.getElementById("mc-meta"),
    menu: document.getElementById("mc-menu"),
    ver: document.getElementById("mc-side-ver"),
    crumb: document.getElementById("mc-crumb"),
    title: document.getElementById("mc-page-title"),
    reload: document.getElementById("mc-reload"),
    toggle: document.getElementById("mc-menu-toggle"),
    backdrop: document.getElementById("mc-backdrop"),
    shell: document.querySelector(".mc-shell"),
  };

  const cache = {};
  let menuData = FALLBACK_MENU;

  function setStatus(msg, isError) {
    el.status.textContent = msg;
    el.status.dataset.state = isError ? "error" : "ok";
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function view() {
    const h = (location.hash || "#hub").replace(/^#/, "").split("?")[0];
    return VIEWS.has(h) ? h : "hub";
  }

  function closeMenu() {
    el.shell.classList.remove("menu-open");
    el.backdrop.hidden = true;
  }

  function markNav() {
    const v = view();
    const [crumb, title] = TITLES[v] || ["Console", v];
    el.crumb.textContent = crumb;
    el.title.textContent = title;
    el.menu.querySelectorAll("a[data-view]").forEach((a) => {
      a.classList.toggle("active", a.dataset.view === v);
    });
  }

  function renderMenu() {
    el.menu.innerHTML = (menuData.groups || [])
      .map(
        (g) => `<div class="mc-group">
        <p class="mc-group-label">${escapeHtml(g.title)}</p>
        <p class="mc-group-sub">${escapeHtml(g.subtitle || "")}</p>
        ${(g.items || [])
          .map((it) => {
            if (it.href) {
              return `<a href="${escapeHtml(it.href)}"><span class="t">${escapeHtml(it.title)}</span><span class="b">${escapeHtml(it.blurb || "")}</span></a>`;
            }
            return `<a href="#${escapeHtml(it.id)}" data-view="${escapeHtml(it.id)}"><span class="t">${escapeHtml(it.title)}</span><span class="b">${escapeHtml(it.blurb || "")}</span></a>`;
          })
          .join("")}
      </div>`,
      )
      .join("");
    el.ver.textContent = `toolkit ${menuData.version || "…"}`;
    markNav();
  }

  async function apiGet(path) {
    const res = await fetch(path);
    const body = await res.json().catch(() => ({}));
    if (!res.ok || body.ok === false) {
      throw new Error(body.error || body.detail || `HTTP ${res.status}`);
    }
    return body.data || body;
  }

  async function apiPost(path, payload) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok || body.ok === false) {
      throw new Error(body.error || body.detail || `HTTP ${res.status}`);
    }
    return body.data || body;
  }

  function fmtDate(v) {
    if (!v) return "—";
    try {
      return new Date(v).toLocaleString();
    } catch {
      return String(v);
    }
  }

  function pill(text, cls) {
    return `<span class="mc-pill ${cls || ""}">${escapeHtml(text)}</span>`;
  }

  function emptyRow(cols, msg) {
    return `<tr><td colspan="${cols}" class="mc-empty">${escapeHtml(msg)}</td></tr>`;
  }

  async function load(force) {
    const v = view();
    markNav();
    closeMenu();
    setStatus(`Loading ${v}…`);
    try {
      const fn = {
        hub: renderHub,
        orphans: renderOrphans,
        ops: renderOps,
        inbox: renderInbox,
        catalog: renderCatalog,
        certs: renderCerts,
        sod: renderSod,
        identity: renderIdentity,
        jml: renderJml,
        evidence: renderEvidence,
        provisioning: renderProv,
        heatmap: renderHeatmap,
        workgroups: renderWorkgroups,
        audit: renderAudit,
      }[v];
      await fn(force);
      setStatus(`Ready · ${v}`);
      el.meta.textContent = new Date().toLocaleTimeString();
    } catch (err) {
      setStatus(err.message || String(err), true);
      el.main.innerHTML = `<div class="mc-panel"><p class="mc-empty">${escapeHtml(err.message)}</p></div>`;
    }
  }

  async function renderHub(force) {
    if (force || !cache.summary) cache.summary = await apiGet("/api/console/summary");
    const s = cache.summary;
    const cards = [
      { label: "Login orphans", key: "loginNamedCount", href: "#orphans", warn: true },
      { label: "Uncorrelated", key: "uncorrelatedCount", href: "#orphans", warn: true },
      { label: "Pipeline fails", key: "pipelineFailCount", href: "#ops", bad: true },
      { label: "Prov fails", key: "provFailCount", href: "#provisioning", bad: true },
      { label: "Work items", key: "inboxCount", href: "#inbox" },
      { label: "Cert campaigns", key: "certCount", href: "#certs" },
      { label: "Open SoD", key: "sodOpenCount", href: "#sod", bad: true },
    ];
    const groupsHtml = (menuData.groups || [])
      .map(
        (g) => `<div class="mc-hub-card">
        <h3>${escapeHtml(g.title)}</h3>
        <p>${escapeHtml(g.subtitle || "")}</p>
        ${(g.items || [])
          .map((it) => {
            const href = it.href || `#${it.id}`;
            return `<a href="${escapeHtml(href)}">${escapeHtml(it.title)}</a>`;
          })
          .join("")}
      </div>`,
      )
      .join("");

    el.main.innerHTML = `
      <div class="mc-grid">
        ${cards
          .map((c) => {
            const n = Number(s[c.key] || 0);
            const cls = n > 0 && c.bad ? "bad" : n > 0 && c.warn ? "warn" : "";
            return `<a class="mc-stat ${cls}" href="${c.href}"><span class="label">${c.label}</span><span class="value">${n}</span></a>`;
          })
          .join("")}
      </div>
      <div class="mc-panel">
        <h2>Central menu</h2>
        <p class="hint">All Wave 1–3 desks in one shell. Pick a lane or use the sidebar.</p>
      </div>
      <div class="mc-hub-groups">${groupsHtml}</div>`;
  }

  async function renderOrphans(force) {
    if (force || !cache.orphans) cache.orphans = await apiGet("/api/console/orphans?limit=200");
    const d = cache.orphans;
    const login = d.loginNamedOrphans || [];
    const unc = d.uncorrelatedAccounts || [];
    const loginRows = login.length
      ? login
          .map(
            (r) => `<tr>
          <td><div>${escapeHtml(r.orphanDisplayName || r.orphanName)}</div><div class="mc-mono">${escapeHtml(r.orphanName)}</div></td>
          <td>${escapeHtml((r.apps || []).join(", ") || "—")}</td>
          <td>${r.twinName ? `<div>${escapeHtml(r.twinDisplayName || r.twinName)}</div><div class="mc-mono">${escapeHtml(r.twinName)}</div>` : "—"}</td>
          <td>${pill(r.disposition || "review", r.disposition === "merge" ? "" : "warn")}</td>
          <td class="mc-actions">${
            r.twinName
              ? `<button type="button" class="mc-btn primary" data-merge="${escapeHtml(r.orphanName)}" data-into="${escapeHtml(r.twinName)}">Merge</button>`
              : ""
          }</td></tr>`,
          )
          .join("")
      : emptyRow(5, "No login-named orphan cubes.");
    const uncRows = unc.length
      ? unc
          .map(
            (r) => `<tr>
          <td class="mc-mono">${escapeHtml(r.application)}</td>
          <td class="mc-mono">${escapeHtml(r.nativeIdentity)}</td>
          <td>${escapeHtml(r.employeeId || "—")}</td>
          <td>${r.privileged ? pill("privileged", "bad") : "—"}</td>
          <td class="mc-actions">${
            r.employeeId
              ? `<button type="button" class="mc-btn primary" data-correlate-app="${escapeHtml(r.application)}" data-correlate-ni="${escapeHtml(r.nativeIdentity)}" data-correlate-id="${escapeHtml(r.employeeId)}">Correlate</button>`
              : ""
          }</td></tr>`,
          )
          .join("")
      : emptyRow(5, "No uncorrelated accounts in sample.");

    el.main.innerHTML = `
      <div class="mc-panel">
        <h2>Login-named orphans (${login.length})</h2>
        <p class="hint">${escapeHtml(d.guidance || "")}</p>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>Orphan</th><th>Apps</th><th>Twin</th><th>Disposition</th><th></th></tr></thead>
          <tbody>${loginRows}</tbody>
        </table></div>
      </div>
      <div class="mc-panel">
        <h2>Uncorrelated accounts (${unc.length})</h2>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>App</th><th>Native ID</th><th>employeeId</th><th>Risk</th><th></th></tr></thead>
          <tbody>${uncRows}</tbody>
        </table></div>
      </div>`;

    bindMergeCorrelate();
  }

  function bindMergeCorrelate() {
    el.main.querySelectorAll("[data-merge]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm(`Merge ${btn.dataset.merge} into ${btn.dataset.into}?`)) return;
        btn.disabled = true;
        try {
          await apiPost("/api/console/merge", { orphan: btn.dataset.merge, into: btn.dataset.into });
          delete cache.orphans;
          delete cache.summary;
          await load(true);
        } catch (err) {
          setStatus(err.message, true);
          btn.disabled = false;
        }
      });
    });
    el.main.querySelectorAll("[data-correlate-app]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await apiPost("/api/console/correlate", {
            application: btn.dataset.correlateApp,
            nativeIdentity: btn.dataset.correlateNi,
            identity: btn.dataset.correlateId,
          });
          delete cache.orphans;
          delete cache.summary;
          await load(true);
        } catch (err) {
          setStatus(err.message, true);
          btn.disabled = false;
        }
      });
    });
  }

  async function renderOps(force) {
    if (force || !cache.pipeline) cache.pipeline = await apiGet("/api/console/pipeline?limit=40");
    const d = cache.pipeline;
    const tasks = d.tasks || [];
    const rows = tasks.length
      ? tasks
          .map((t) => {
            const st = t.completionStatus || "—";
            const cls = /error|terminated/i.test(st) ? "bad" : /success/i.test(st) ? "" : "warn";
            return `<tr><td>${escapeHtml(t.name)}</td><td>${pill(st, cls)}</td><td>${fmtDate(t.launched)}</td><td>${fmtDate(t.completed)}</td><td class="mc-mono">${t.durationMs != null ? Math.round(t.durationMs / 1000) + "s" : "—"}</td></tr>`;
          })
          .join("")
      : emptyRow(5, "No recent aggregation/refresh results.");
    el.main.innerHTML = `
      <div class="mc-grid">
        <div class="mc-stat"><span class="label">Recent</span><span class="value">${d.count || 0}</span></div>
        <div class="mc-stat"><span class="label">Success</span><span class="value">${d.successCount || 0}</span></div>
        <div class="mc-stat ${(d.failCount || 0) > 0 ? "bad" : ""}"><span class="label">Failures</span><span class="value">${d.failCount || 0}</span></div>
      </div>
      <div class="mc-panel"><h2>Stop / go</h2><p class="hint">${escapeHtml(d.stopGo || "")}</p>
        <ol class="mc-ol">${(d.canonicalOrder || []).map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ol>
      </div>
      <div class="mc-panel"><h2>Recent results</h2>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>Task</th><th>Status</th><th>Launched</th><th>Completed</th><th>Duration</th></tr></thead>
          <tbody>${rows}</tbody>
        </table></div>
      </div>`;
  }

  async function renderInbox(force) {
    if (force || !cache.inbox) cache.inbox = await apiGet("/api/console/inbox?limit=75");
    const items = cache.inbox.items || [];
    const rows = items.length
      ? items
          .map(
            (w) => `<tr>
          <td><input type="checkbox" class="mc-check" value="${escapeHtml(w.id)}" aria-label="Select" /></td>
          <td><div>${escapeHtml(w.description || w.name || "—")}</div><div class="mc-mono">${escapeHtml(w.id)}</div></td>
          <td>${escapeHtml(w.type || "—")}</td>
          <td>${escapeHtml(w.ownerDisplay || w.owner || "—")}</td>
          <td>${pill(w.state || "—")}</td>
          <td class="mc-actions">
            <button type="button" class="mc-btn primary" data-decide="${escapeHtml(w.id)}" data-decision="approve">Approve</button>
            <button type="button" class="mc-btn danger" data-decide="${escapeHtml(w.id)}" data-decision="reject">Reject</button>
          </td></tr>`,
          )
          .join("")
      : emptyRow(6, "No work items.");
    el.main.innerHTML = `
      <div class="mc-panel">
        <h2>Approval inbox (${items.length})</h2>
        <p class="hint">Bulk actions + single decide. Requires mutateGovernanceEnabled.</p>
        <div class="mc-actions" style="padding:0.75rem 1.1rem;border-bottom:1px solid var(--line)">
          <button type="button" class="mc-btn" id="inbox-all">Select all</button>
          <button type="button" class="mc-btn primary" id="inbox-bulk-approve">Bulk approve</button>
          <button type="button" class="mc-btn danger" id="inbox-bulk-reject">Bulk reject</button>
        </div>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th></th><th>Item</th><th>Type</th><th>Owner</th><th>State</th><th></th></tr></thead>
          <tbody>${rows}</tbody>
        </table></div>
      </div>`;
    const selected = () => [...el.main.querySelectorAll(".mc-check:checked")].map((c) => c.value);
    document.getElementById("inbox-all")?.addEventListener("click", () => {
      el.main.querySelectorAll(".mc-check").forEach((c) => {
        c.checked = true;
      });
    });
    const bulk = async (decision) => {
      const ids = selected();
      if (!ids.length) {
        setStatus("Select at least one work item", true);
        return;
      }
      if (!confirm(`${decision} ${ids.length} work item(s)?`)) return;
      try {
        const r = await apiPost("/api/console/bulk-decide-workitems", { ids, decision });
        setStatus(`Bulk ${decision}: ${r.decided || 0}/${r.total || ids.length}`);
        delete cache.inbox;
        delete cache.summary;
        await load(true);
      } catch (err) {
        setStatus(err.message, true);
      }
    };
    document.getElementById("inbox-bulk-approve")?.addEventListener("click", () => bulk("approve"));
    document.getElementById("inbox-bulk-reject")?.addEventListener("click", () => bulk("reject"));
    el.main.querySelectorAll("[data-decide]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm(`${btn.dataset.decision} this work item?`)) return;
        btn.disabled = true;
        try {
          await apiPost("/api/console/decide-workitem", {
            id: btn.dataset.decide,
            decision: btn.dataset.decision,
          });
          delete cache.inbox;
          delete cache.summary;
          await load(true);
        } catch (err) {
          setStatus(err.message, true);
          btn.disabled = false;
        }
      });
    });
  }

  async function renderCatalog(force) {
    if (force || !cache.catalog) cache.catalog = await apiGet("/api/console/catalog?limit=100");
    const d = cache.catalog;
    const roles = d.roles || [];
    const ents = d.entitlements || [];
    el.main.innerHTML = `
      <div class="mc-panel">
        <h2>Launch access request</h2>
        <p class="hint">Calls toolkit access/grant (LCM). Pick a requestable role or entitlement below, or type the name.</p>
        <div class="mc-search-row">
          <input id="ar-identity" type="text" placeholder="Target identity (e.g. MNB00090)" />
          <input id="ar-access" type="text" placeholder="Role or entitlement name" />
          <select id="ar-type">
            <option value="">auto</option>
            <option value="role">role</option>
            <option value="entitlement">entitlement</option>
          </select>
          <button type="button" class="mc-btn primary" id="ar-go">Request</button>
        </div>
        <p class="hint" id="ar-status" style="border:0"></p>
      </div>
      <div class="mc-panel"><h2>Roles (${roles.length})</h2>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>Display</th><th>Name</th><th>Type</th><th>Requestable</th><th></th></tr></thead>
          <tbody>${
            roles.length
              ? roles
                  .map(
                    (r) =>
                      `<tr><td>${escapeHtml(r.displayName || r.name)}</td><td class="mc-mono">${escapeHtml(r.name)}</td><td>${escapeHtml(r.type || "—")}</td><td>${r.requestable ? pill("yes") : pill("no", "warn")}</td><td><button type="button" class="mc-btn" data-pick-access="${escapeHtml(r.name)}" data-pick-type="role">Use</button></td></tr>`,
                  )
                  .join("")
              : emptyRow(5, "No roles.")
          }</tbody>
        </table></div>
      </div>
      <div class="mc-panel"><h2>Entitlements (${ents.length})</h2>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>Display</th><th>App</th><th>Value</th><th>Risk</th><th></th></tr></thead>
          <tbody>${
            ents.length
              ? ents
                  .map(
                    (e) =>
                      `<tr><td>${escapeHtml(e.displayName || e.value)}</td><td class="mc-mono">${escapeHtml(e.application || "—")}</td><td class="mc-mono">${escapeHtml(e.value || "—")}</td><td>${e.privileged ? pill("privileged", "bad") : "—"}</td><td><button type="button" class="mc-btn" data-pick-access="${escapeHtml(e.value)}" data-pick-type="entitlement">Use</button></td></tr>`,
                  )
                  .join("")
              : emptyRow(5, "No entitlements.")
          }</tbody>
        </table></div>
      </div>`;
    el.main.querySelectorAll("[data-pick-access]").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.getElementById("ar-access").value = btn.dataset.pickAccess;
        document.getElementById("ar-type").value = btn.dataset.pickType || "";
      });
    });
    document.getElementById("ar-go")?.addEventListener("click", async () => {
      const identityName = document.getElementById("ar-identity").value.trim();
      const accessName = document.getElementById("ar-access").value.trim();
      const accessType = document.getElementById("ar-type").value;
      const st = document.getElementById("ar-status");
      if (!identityName || !accessName) {
        st.textContent = "Identity and access name required.";
        return;
      }
      st.textContent = "Launching…";
      try {
        const r = await apiPost("/api/console/grant-access", { identityName, accessName, accessType });
        st.textContent = `Launched · status=${r.launchStatus || "ok"} · case=${r.workflowCaseId || "—"}`;
        setStatus("Access request launched");
      } catch (err) {
        st.textContent = err.message;
        setStatus(err.message, true);
      }
    });
  }

  async function renderCerts(force) {
    if (force || !cache.certs) cache.certs = await apiGet("/api/console/certs?limit=50");
    const camps = cache.certs.campaigns || [];
    const openId = new URLSearchParams(location.hash.split("?")[1] || "").get("id") || "";
    el.main.innerHTML = `
      <div class="mc-panel">
        <h2>Cert campaigns (${camps.length})</h2>
        <p class="hint">${escapeHtml(cache.certs.guidance || "")}</p>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>Campaign</th><th>Type</th><th>Phase</th><th>Certifier</th><th></th></tr></thead>
          <tbody>${
            camps.length
              ? camps
                  .map(
                    (c) => `<tr>
              <td><div>${escapeHtml(c.name)}</div><div class="mc-mono">${escapeHtml(c.id)}</div></td>
              <td>${escapeHtml(c.type || "—")}</td>
              <td>${pill(c.phase || "—", /end|complete/i.test(c.phase || "") ? "" : "warn")}</td>
              <td>${escapeHtml(c.certifier || "—")}</td>
              <td class="mc-actions">
                <button type="button" class="mc-btn primary" data-open-cert="${escapeHtml(c.id)}">Open</button>
                <button type="button" class="mc-btn" data-sign-cert="${escapeHtml(c.id)}">Sign</button>
              </td>
            </tr>`,
                  )
                  .join("")
              : emptyRow(5, "No campaigns.")
          }</tbody>
        </table></div>
      </div>
      <div id="cert-detail"></div>`;

    const showDetail = async (id) => {
      history.replaceState(null, "", `#certs?id=${encodeURIComponent(id)}`);
      const box = document.getElementById("cert-detail");
      box.innerHTML = `<div class="mc-panel"><p class="mc-empty">Loading items…</p></div>`;
      try {
        const d = await apiGet(`/api/console/certs/${encodeURIComponent(id)}?limit=100`);
        const items = d.items || [];
        box.innerHTML = `
          <div class="mc-panel">
            <h2>${escapeHtml(d.name || id)} · undecided ${d.undecidedCount || 0}</h2>
            <p class="hint">${escapeHtml(d.guidance || "")}</p>
            <div class="mc-actions" style="padding:0.75rem 1.1rem;border-bottom:1px solid var(--line)">
              <button type="button" class="mc-btn" data-sign-cert="${escapeHtml(d.id)}">Sign campaign</button>
            </div>
            <div class="mc-table-wrap"><table class="mc-table">
              <thead><tr><th>Identity</th><th>Type</th><th>Bundle / apps</th><th>Status</th><th></th></tr></thead>
              <tbody>${
                items.length
                  ? items
                      .map(
                        (it) => `<tr>
                  <td class="mc-mono">${escapeHtml(it.identity || "—")}</td>
                  <td>${escapeHtml(it.type || "—")}</td>
                  <td>${escapeHtml(it.bundle || (it.applications || []).join(", ") || "—")}</td>
                  <td>${pill(it.decision || it.summaryStatus || "open", it.decision ? "" : "warn")}</td>
                  <td class="mc-actions">
                    <button type="button" class="mc-btn primary" data-cert-decide="${escapeHtml(it.id)}" data-decision="approve">Approve</button>
                    <button type="button" class="mc-btn danger" data-cert-decide="${escapeHtml(it.id)}" data-decision="revoke">Revoke</button>
                    <button type="button" class="mc-btn" data-cert-decide="${escapeHtml(it.id)}" data-decision="mitigate">Mitigate</button>
                  </td>
                </tr>`,
                      )
                      .join("")
                  : emptyRow(5, "No items in sample (campaign may be empty or finished).")
              }</tbody>
            </table></div>
          </div>`;
        box.querySelectorAll("[data-cert-decide]").forEach((btn) => {
          btn.addEventListener("click", async () => {
            btn.disabled = true;
            try {
              await apiPost("/api/console/decide-cert", {
                id: btn.dataset.certDecide,
                decision: btn.dataset.decision,
                comment: "Meridian console decision",
              });
              await showDetail(id);
              setStatus(`Item ${btn.dataset.decision}`);
            } catch (err) {
              setStatus(err.message, true);
              btn.disabled = false;
            }
          });
        });
        box.querySelectorAll("[data-sign-cert]").forEach((btn) => {
          btn.addEventListener("click", async () => {
            if (!confirm("Sign this certification campaign?")) return;
            try {
              await apiPost("/api/console/sign-cert", { id: btn.dataset.signCert });
              delete cache.certs;
              setStatus("Campaign signed");
              await load(true);
            } catch (err) {
              setStatus(err.message, true);
            }
          });
        });
      } catch (err) {
        box.innerHTML = `<div class="mc-panel"><p class="mc-empty">${escapeHtml(err.message)}</p></div>`;
      }
    };

    el.main.querySelectorAll("[data-open-cert]").forEach((btn) => {
      btn.addEventListener("click", () => showDetail(btn.dataset.openCert));
    });
    el.main.querySelectorAll("[data-sign-cert]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Sign this certification campaign?")) return;
        try {
          await apiPost("/api/console/sign-cert", { id: btn.dataset.signCert });
          delete cache.certs;
          setStatus("Campaign signed");
          await load(true);
        } catch (err) {
          setStatus(err.message, true);
        }
      });
    });
    if (openId) showDetail(openId);
  }

  async function renderSod(force) {
    if (force || !cache.sod) cache.sod = await apiGet("/api/console/sod?limit=100");
    const d = cache.sod;
    const viols = d.violations || [];
    const by = d.byPolicy || {};
    const max = Math.max(1, ...Object.values(by), 1);
    const bars = Object.entries(by)
      .map(
        ([k, v]) => `<div class="mc-bar-row">
        <span>${escapeHtml(k)}</span>
        <div class="mc-bar-track"><div class="mc-bar-fill" style="width:${Math.round((v / max) * 100)}%"></div></div>
        <span>${v}</span>
      </div>`,
      )
      .join("");
    el.main.innerHTML = `
      <div class="mc-grid">
        <div class="mc-stat ${(d.openCount || 0) > 0 ? "bad" : ""}"><span class="label">Open SoD</span><span class="value">${d.openCount || 0}</span></div>
        <div class="mc-stat"><span class="label">Listed</span><span class="value">${viols.length}</span></div>
      </div>
      <div class="mc-panel"><h2>By policy</h2><div class="mc-bars">${bars || '<p class="mc-empty">No open violations.</p>'}</div></div>
      <div class="mc-panel">
        <h2>Violations</h2>
        <p class="hint">${escapeHtml(d.guidance || "")}</p>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>Identity</th><th>Policy</th><th>Constraint</th><th></th></tr></thead>
          <tbody>${
            viols.length
              ? viols
                  .map(
                    (v) => `<tr>
              <td><div>${escapeHtml(v.identityDisplay || v.identity || "—")}</div><div class="mc-mono">${escapeHtml(v.identity || "")}</div></td>
              <td>${escapeHtml(v.policyName || "—")}</td>
              <td>${escapeHtml(v.constraintName || "—")}</td>
              <td><button type="button" class="mc-btn primary" data-mitigate="${escapeHtml(v.id)}">Mitigate</button></td>
            </tr>`,
                  )
                  .join("")
              : emptyRow(4, "No open SoD violations.")
          }</tbody>
        </table></div>
      </div>`;
    el.main.querySelectorAll("[data-mitigate]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const comment = prompt("Mitigation comment (exam evidence):", "Accepted risk — Meridian console");
        if (comment == null) return;
        btn.disabled = true;
        try {
          await apiPost("/api/console/mitigate-sod", { id: btn.dataset.mitigate, comment });
          delete cache.sod;
          delete cache.summary;
          await load(true);
        } catch (err) {
          setStatus(err.message, true);
          btn.disabled = false;
        }
      });
    });
  }

  async function renderIdentity() {
    const q0 = new URLSearchParams(location.hash.split("?")[1] || "").get("q") || "";
    el.main.innerHTML = `
      <div class="mc-panel">
        <h2>Helpdesk Identity 360</h2>
        <div class="mc-search-row">
          <input id="id360-q" type="search" placeholder="MNB00090, Priya, email…" value="${escapeHtml(q0)}" />
          <button type="button" class="mc-btn primary" id="id360-go">Lookup</button>
        </div>
        <div id="id360-body"><p class="mc-empty">Search an identity to load accounts, roles, SoD, capabilities.</p></div>
      </div>`;
    const run = async () => {
      const q = document.getElementById("id360-q").value.trim();
      if (q.length < 2) return;
      history.replaceState(null, "", `#identity?q=${encodeURIComponent(q)}`);
      const body = document.getElementById("id360-body");
      body.innerHTML = `<p class="mc-empty">Loading…</p>`;
      try {
        const d = await apiGet(`/api/console/identity360?q=${encodeURIComponent(q)}`);
        body.innerHTML = `
          <div class="mc-actions" style="padding:0.75rem 1.1rem;border-bottom:1px solid var(--line)">
            <button type="button" class="mc-btn primary" id="id360-unlock" data-idn="${escapeHtml(d.name)}">Unlock</button>
            <button type="button" class="mc-btn" id="id360-reset" data-idn="${escapeHtml(d.name)}">Reset password</button>
            <a class="mc-btn" href="#catalog">Request access</a>
            <a class="mc-btn" href="/orgchart.html?mode=subtree&root=${encodeURIComponent(d.name)}">Org subtree</a>
          </div>
          <dl class="mc-dl">
            <dt>Name</dt><dd>${escapeHtml(d.displayName)} <span class="mc-mono">${escapeHtml(d.name)}</span></dd>
            <dt>Status</dt><dd>${d.inactive ? pill("inactive", "bad") : pill("active")}</dd>
            <dt>Manager</dt><dd>${escapeHtml(d.managerDisplay || d.manager || "—")}</dd>
            <dt>Title / Dept</dt><dd>${escapeHtml(d.title || "—")} · ${escapeHtml(d.department || "—")}</dd>
            <dt>Email</dt><dd>${escapeHtml(d.email || "—")}</dd>
            <dt>Type / Loc</dt><dd>${escapeHtml(d.employeeType || "—")} · ${escapeHtml(d.location || "—")}</dd>
            <dt>Roles</dt><dd>${escapeHtml((d.assignedRoles || []).join(", ") || "—")}</dd>
            <dt>Capabilities</dt><dd>${escapeHtml((d.capabilities || []).join(", ") || "—")}</dd>
            <dt>Workgroups</dt><dd>${escapeHtml((d.workgroups || []).join(", ") || "—")}</dd>
            <dt>Open SoD</dt><dd>${pill(String(d.openSodCount || 0), (d.openSodCount || 0) > 0 ? "bad" : "")}</dd>
          </dl>
          <h3 style="padding:0.75rem 1.1rem 0;margin:0;font-family:var(--font-display)">Accounts (${(d.accounts || []).length})</h3>
          <div class="mc-table-wrap"><table class="mc-table">
            <thead><tr><th>App</th><th>Native ID</th><th>State</th><th>Risk</th></tr></thead>
            <tbody>${
              (d.accounts || []).length
                ? d.accounts
                    .map(
                      (a) =>
                        `<tr><td>${escapeHtml(a.application)}</td><td class="mc-mono">${escapeHtml(a.nativeIdentity)}</td><td>${a.disabled ? pill("disabled", "warn") : pill("enabled")}</td><td>${a.privileged ? pill("privileged", "bad") : "—"}</td></tr>`,
                    )
                    .join("")
                : emptyRow(4, "No accounts.")
            }</tbody>
          </table></div>`;
        document.getElementById("id360-unlock")?.addEventListener("click", async (ev) => {
          const idn = ev.currentTarget.dataset.idn;
          try {
            await apiPost("/api/console/identity-password", { identity: idn, op: "unlock" });
            setStatus(`Unlocked ${idn}`);
          } catch (err) {
            setStatus(err.message, true);
          }
        });
        document.getElementById("id360-reset")?.addEventListener("click", async (ev) => {
          const idn = ev.currentTarget.dataset.idn;
          const password = prompt("New temporary password:", "ChangeMe1!");
          if (!password) return;
          try {
            await apiPost("/api/console/identity-password", { identity: idn, op: "reset", password });
            setStatus(`Password reset for ${idn}`);
          } catch (err) {
            setStatus(err.message, true);
          }
        });
      } catch (err) {
        body.innerHTML = `<p class="mc-empty">${escapeHtml(err.message)}</p>`;
      }
    };
    document.getElementById("id360-go").addEventListener("click", run);
    document.getElementById("id360-q").addEventListener("keydown", (e) => {
      if (e.key === "Enter") run();
    });
    if (q0) run();
  }

  async function renderJml(force) {
    if (force || !cache.jml) cache.jml = await apiGet("/api/console/jml");
    const personas = cache.jml.personas || [];
    el.main.innerHTML = `
      <div class="mc-panel">
        <h2>JML lifecycle timeline</h2>
        <p class="hint">${escapeHtml(cache.jml.guidance || "")}</p>
      </div>
      ${personas
        .map(
          (p) => `<div class="mc-panel">
          <h2>${escapeHtml(p.displayName || p.identityKey)} · ${pill(p.eventType)}${p.found === false ? " " + pill("missing", "warn") : ""}</h2>
          <p class="hint">${escapeHtml(p.narrative || "")} · apps: ${escapeHtml((p.apps || []).join(", ") || "—")}</p>
          <ul class="mc-timeline">
            ${(p.timeline || [])
              .map(
                (e) =>
                  `<li><strong>${escapeHtml(e.label)}</strong> — ${escapeHtml(e.detail || "—")}${e.when ? ` <span class="mc-mono">(${fmtDate(e.when)})</span>` : ""}</li>`,
              )
              .join("")}
          </ul>
          <div class="mc-actions" style="padding:0 1.1rem 1rem">
            <a class="mc-btn" href="#identity?q=${encodeURIComponent(p.identityKey)}">Open Identity 360</a>
          </div>
        </div>`,
        )
        .join("") || '<div class="mc-panel"><p class="mc-empty">No personas.</p></div>'}`;
  }

  async function renderEvidence(force) {
    if (force || !cache.evidence) cache.evidence = await apiGet("/api/console/evidence?limit=40");
    const pack = cache.evidence.pack || {};
    const json = JSON.stringify(pack, null, 2);
    el.main.innerHTML = `
      <div class="mc-panel">
        <h2>Evidence pack</h2>
        <p class="hint">${escapeHtml(cache.evidence.downloadHint || "")}</p>
        <div class="mc-actions" style="padding:0.9rem 1.1rem">
          <button type="button" class="mc-btn primary" id="ev-dl">Download JSON</button>
          <button type="button" class="mc-btn" id="ev-copy">Copy</button>
        </div>
        <ol class="mc-ol">${(pack.checklist || []).map((c) => `<li>${escapeHtml(c)}</li>`).join("")}</ol>
        <pre class="mc-mono" style="padding:1rem 1.1rem;margin:0;max-height:360px;overflow:auto;background:rgba(232,237,243,0.4)">${escapeHtml(json)}</pre>
      </div>`;
    document.getElementById("ev-dl").addEventListener("click", () => {
      const blob = new Blob([json], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `mnb-evidence-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    });
    document.getElementById("ev-copy").addEventListener("click", async () => {
      await navigator.clipboard.writeText(json);
      setStatus("Evidence pack copied");
    });
  }

  async function renderProv(force) {
    if (force || !cache.prov) cache.prov = await apiGet("/api/console/provisioning?limit=50");
    const d = cache.prov;
    const txs = d.transactions || [];
    el.main.innerHTML = `
      <div class="mc-grid">
        <div class="mc-stat"><span class="label">Transactions</span><span class="value">${d.count || 0}</span></div>
        <div class="mc-stat ${(d.failCount || 0) > 0 ? "bad" : ""}"><span class="label">Failures</span><span class="value">${d.failCount || 0}</span></div>
      </div>
      <div class="mc-panel">
        <h2>Provisioning debugger</h2>
        <p class="hint">${escapeHtml(d.guidance || "")}</p>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>Identity</th><th>App</th><th>Op</th><th>Status</th><th>When</th><th></th></tr></thead>
          <tbody>${
            txs.length
              ? txs
                  .map((t) => {
                    const st = t.status || "—";
                    const bad = /fail|error/i.test(st);
                    return `<tr>
                  <td>${escapeHtml(t.identityDisplay || t.identity || "—")}</td>
                  <td class="mc-mono">${escapeHtml(t.application || "—")}</td>
                  <td>${escapeHtml(t.operation || "—")}</td>
                  <td>${pill(st, bad ? "bad" : "")}</td>
                  <td>${fmtDate(t.created)}</td>
                  <td>${bad ? `<button type="button" class="mc-btn" data-retry="${escapeHtml(t.id)}">Retry</button>` : ""}</td>
                </tr>`;
                  })
                  .join("")
              : emptyRow(6, "No provisioning transactions.")
          }</tbody>
        </table></div>
      </div>`;
    el.main.querySelectorAll("[data-retry]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await apiPost("/api/console/retry-prov", { id: btn.dataset.retry });
          delete cache.prov;
          await load(true);
        } catch (err) {
          setStatus(err.message, true);
          btn.disabled = false;
        }
      });
    });
  }

  async function renderHeatmap(force) {
    if (force || !cache.heat) cache.heat = await apiGet("/api/console/heatmap?limit=200");
    const d = cache.heat;
    const priv = d.privilegedByApp || {};
    const max = Math.max(1, ...Object.values(priv), 1);
    const bars = Object.entries(priv)
      .sort((a, b) => b[1] - a[1])
      .map(
        ([k, v]) => `<div class="mc-bar-row">
        <span>${escapeHtml(k)}</span>
        <div class="mc-bar-track"><div class="mc-bar-fill" style="width:${Math.round((v / max) * 100)}%"></div></div>
        <span>${v}</span>
      </div>`,
      )
      .join("");
    const hot = d.hotEntitlements || [];
    el.main.innerHTML = `
      <div class="mc-panel"><h2>Privileged entitlements by app</h2>
        <p class="hint">${escapeHtml(d.guidance || "")}</p>
        <div class="mc-bars">${bars || '<p class="mc-empty">No privileged entitlements tagged.</p>'}</div>
      </div>
      <div class="mc-panel"><h2>Hot list (${hot.length})</h2>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>App</th><th>Value</th><th>Display</th><th>Requestable</th></tr></thead>
          <tbody>${
            hot.length
              ? hot
                  .map(
                    (h) =>
                      `<tr><td>${escapeHtml(h.application)}</td><td class="mc-mono">${escapeHtml(h.value)}</td><td>${escapeHtml(h.displayName || "—")}</td><td>${h.requestable ? pill("yes", "warn") : pill("no")}</td></tr>`,
                  )
                  .join("")
              : emptyRow(4, "None.")
          }</tbody>
        </table></div>
      </div>`;
  }

  async function renderWorkgroups(force) {
    if (force || !cache.wg) cache.wg = await apiGet("/api/console/workgroups?limit=50");
    const groups = cache.wg.workgroups || [];
    const allCaps = [...new Set(groups.flatMap((g) => g.capabilities || []))].sort();
    const matrix =
      allCaps.length && groups.length
        ? `<div class="mc-panel">
        <h2>Capability map</h2>
        <p class="hint">Which workgroups carry which IIQ capabilities (security-relevant).</p>
        <div class="mc-table-wrap"><table class="mc-table mc-matrix">
          <thead><tr><th>Workgroup</th>${allCaps.map((c) => `<th title="${escapeHtml(c)}">${escapeHtml(c.length > 18 ? c.slice(0, 16) + "…" : c)}</th>`).join("")}<th>Members</th></tr></thead>
          <tbody>${groups
            .map((g) => {
              const set = new Set(g.capabilities || []);
              return `<tr><td>${escapeHtml(g.name)}</td>${allCaps
                .map((c) => `<td class="${set.has(c) ? "on" : ""}">${set.has(c) ? "●" : "·"}</td>`)
                .join("")}<td>${g.memberCount || 0}</td></tr>`;
            })
            .join("")}</tbody>
        </table></div>
      </div>`
        : "";
    el.main.innerHTML =
      matrix +
      (groups.length
        ? groups
            .map(
              (g) => `<div class="mc-panel">
          <h2>${escapeHtml(g.displayName || g.name)} · ${pill(String(g.memberCount || 0) + " members")}</h2>
          <p class="hint">Capabilities: ${escapeHtml((g.capabilities || []).join(", ") || "—")}</p>
          <div class="mc-cap-chips">${(g.capabilities || [])
            .map((c) => pill(c))
            .join(" ")}${!(g.capabilities || []).length ? "—" : ""}</div>
          <div class="mc-table-wrap"><table class="mc-table">
            <thead><tr><th>Member</th><th>Key</th><th>Email</th><th></th></tr></thead>
            <tbody>${
              (g.members || []).length
                ? g.members
                    .map(
                      (m) =>
                        `<tr><td>${escapeHtml(m.displayName || m.name)}</td><td class="mc-mono">${escapeHtml(m.name)}</td><td>${escapeHtml(m.email || "—")}</td><td><a class="mc-btn" href="#identity?q=${encodeURIComponent(m.name)}">360</a></td></tr>`,
                    )
                    .join("")
                : emptyRow(4, "No members found.")
            }</tbody>
          </table></div>
        </div>`,
            )
            .join("")
        : `<div class="mc-panel"><p class="mc-empty">No workgroups.</p></div>`);
  }

  async function renderAudit(force) {
    if (force || !cache.audit) cache.audit = await apiGet("/api/console/audit?limit=75");
    const d = cache.audit;
    const by = d.byAction || {};
    const max = Math.max(1, ...Object.values(by), 1);
    const bars = Object.entries(by)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12)
      .map(
        ([k, v]) => `<div class="mc-bar-row">
        <span>${escapeHtml(k)}</span>
        <div class="mc-bar-track"><div class="mc-bar-fill" style="width:${Math.round((v / max) * 100)}%"></div></div>
        <span>${v}</span>
      </div>`,
      )
      .join("");
    const events = d.events || [];
    el.main.innerHTML = `
      <div class="mc-panel"><h2>Actions (top)</h2><div class="mc-bars">${bars || '<p class="mc-empty">No events.</p>'}</div></div>
      <div class="mc-panel"><h2>Recent audit (${events.length})</h2>
        <div class="mc-table-wrap"><table class="mc-table">
          <thead><tr><th>When</th><th>Action</th><th>Source</th><th>Target</th></tr></thead>
          <tbody>${
            events.length
              ? events
                  .map(
                    (e) =>
                      `<tr><td>${fmtDate(e.created)}</td><td>${escapeHtml(e.action || "—")}</td><td class="mc-mono">${escapeHtml(e.source || "—")}</td><td class="mc-mono">${escapeHtml(e.target || "—")}</td></tr>`,
                  )
                  .join("")
              : emptyRow(4, "No audit events.")
          }</tbody>
        </table></div>
      </div>`;
  }

  async function boot() {
    try {
      menuData = await apiGet("/api/console/menu");
    } catch {
      menuData = FALLBACK_MENU;
    }
    renderMenu();
    el.reload.addEventListener("click", () => {
      Object.keys(cache).forEach((k) => delete cache[k]);
      load(true);
    });
    el.toggle.addEventListener("click", () => {
      el.shell.classList.toggle("menu-open");
      el.backdrop.hidden = !el.shell.classList.contains("menu-open");
    });
    el.backdrop.addEventListener("click", closeMenu);
    window.addEventListener("hashchange", () => load(false));
    load(false);
  }

  boot();
})();
