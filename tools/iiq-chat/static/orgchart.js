/* Meridian Org Chart — card nodes, zoomable / collapsible (D3). */
(() => {
  const NODE_W = 200;
  const NODE_H = 104;
  const GAP_X = 36;
  const GAP_Y = 48;

  const svg = d3.select("#oc-svg");
  const gRoot = svg.append("g").attr("class", "oc-viewport");
  const gLinks = gRoot.append("g").attr("class", "oc-links");
  const gNodes = gRoot.append("g").attr("class", "oc-nodes");

  const state = {
    forest: [],
    meta: {},
    collapsed: new Set(),
    selected: null,
    hitIds: new Set(),
    layout: "tree",
    mode: "company",
    zoom: null,
  };

  const el = {
    status: document.getElementById("oc-status"),
    search: document.getElementById("oc-search"),
    layout: document.getElementById("oc-layout"),
    mode: document.getElementById("oc-mode"),
    root: document.getElementById("oc-root"),
    rootField: document.querySelector(".oc-root-field"),
    inactive: document.getElementById("oc-inactive"),
    meta: document.getElementById("oc-meta"),
    drawer: document.getElementById("oc-drawer"),
  };

  function setStatus(msg, isError) {
    el.status.textContent = msg;
    el.status.dataset.state = isError ? "error" : "ok";
  }

  function qs() {
    const p = new URLSearchParams(location.search);
    return {
      root: p.get("root") || "",
      mode: p.get("mode") || "company",
      layout: p.get("layout") || "tree",
      q: p.get("q") || "",
    };
  }

  function writeUrl() {
    const p = new URLSearchParams();
    p.set("mode", state.mode);
    p.set("layout", state.layout);
    if (state.mode === "subtree" && el.root.value.trim()) p.set("root", el.root.value.trim());
    if (el.search.value.trim()) p.set("q", el.search.value.trim());
    history.replaceState(null, "", `${location.pathname}?${p}`);
  }

  async function fetchChart() {
    const params = new URLSearchParams();
    params.set("mode", state.mode);
    params.set("depth", "14");
    if (el.inactive.checked) params.set("includeInactive", "true");
    if (state.mode === "subtree") {
      const root = el.root.value.trim();
      if (!root) {
        setStatus("Subtree mode needs a root identity (e.g. MNB00002).", true);
        return;
      }
      params.set("root", root);
    }
    setStatus("Loading hierarchy from IdentityIQ…");
    const res = await fetch(`/api/orgchart?${params}`);
    const body = await res.json().catch(() => ({}));
    if (!res.ok || body.ok === false) {
      throw new Error(body.error || body.detail || `HTTP ${res.status}`);
    }
    const data = body.data || body;
    state.forest = data.forest || [];
    state.meta = data;
    state.collapsed = new Set();
    el.meta.textContent = `${data.nodeCount || 0} people · ${data.forestCount || 0} root trees · universe ${data.identityUniverse || "—"}`;
    setStatus(
      `Loaded ${data.nodeCount || 0} identities. Scroll-wheel zoom · drag canvas · click a card.`,
    );
    render();
    fit();
  }

  function cloneFiltered(node) {
    const id = node.id || node.name;
    const kids = Array.isArray(node.children) ? node.children : [];
    const collapsed = state.collapsed.has(id);
    const out = { ...node, _id: id, children: undefined, _rawChildren: kids };
    if (!collapsed && kids.length) {
      out.children = kids.map(cloneFiltered);
    }
    out._childCount = kids.length;
    out._collapsed = collapsed;
    return out;
  }

  function forestHierarchy() {
    if (!state.forest.length) {
      return d3.hierarchy({ displayName: "Empty", name: "_empty", children: [] });
    }
    if (state.forest.length === 1) {
      return d3.hierarchy(cloneFiltered(state.forest[0]));
    }
    return d3.hierarchy({
      displayName: "Meridian National Bank",
      name: "_company",
      title: "Full company",
      userId: "MNB",
      directReports: state.forest.length,
      children: state.forest.map(cloneFiltered),
      _synthetic: true,
    });
  }

  function layoutHierarchy(root) {
    const horizontal = state.layout === "tree-h";
    const radial = state.layout === "radial";

    if (radial) {
      const leaves = Math.max(root.leaves().length, 4);
      const radius = Math.max(320, leaves * 28);
      d3
        .tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => ((a.parent === b.parent ? 1.2 : 1.6) / Math.max(a.depth, 1)))(root);
      root.each((d) => {
        const angle = d.x;
        const r = d.y;
        d.x = r * Math.cos(angle - Math.PI / 2);
        d.y = r * Math.sin(angle - Math.PI / 2);
      });
      return;
    }

    // d3 nodeSize: [breadth separation, depth separation] before any axis swap
    const breadth = horizontal ? NODE_H + GAP_Y : NODE_W + GAP_X;
    const depth = horizontal ? NODE_W + GAP_X + 24 : NODE_H + GAP_Y;
    const layoutFn = state.layout === "cluster" ? d3.cluster() : d3.tree();
    layoutFn.nodeSize([breadth, depth]).separation(() => 1.15)(root);

    if (horizontal) {
      root.each((d) => {
        const bx = d.x;
        d.x = d.y;
        d.y = bx;
      });
    }
  }

  function linkPath(d) {
    const sx = d.source.x;
    const sy = d.source.y;
    const tx = d.target.x;
    const ty = d.target.y;
    if (state.layout === "tree-h") {
      const mx = (sx + tx) / 2;
      return `M${sx},${sy} C${mx},${sy} ${mx},${ty} ${tx},${ty}`;
    }
    if (state.layout === "radial") {
      return d3
        .linkRadial()
        .angle((n) => Math.atan2(n.y, n.x) + Math.PI / 2)
        .radius((n) => Math.hypot(n.x, n.y) || 0.01)(d);
    }
    const my = (sy + ty) / 2;
    return `M${sx},${sy} C${sx},${my} ${tx},${my} ${tx},${ty}`;
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function riskChips(data) {
    const flags = Array.isArray(data.riskFlags) ? data.riskFlags : [];
    const chips = [];
    if (data.inactive || flags.includes("inactive")) {
      chips.push(`<span class="oc-risk inactive" title="Inactive">INA</span>`);
    }
    if (data.brokenManager || flags.includes("brokenManager")) {
      chips.push(`<span class="oc-risk broken" title="Broken manager link">MGR</span>`);
    }
    if (data.privilegedAccess || flags.includes("privileged")) {
      chips.push(`<span class="oc-risk priv" title="Privileged access">PRIV</span>`);
    }
    return chips.length ? `<div class="oc-risks">${chips.join("")}</div>` : "";
  }

  function cardHtml(d) {
    const data = d.data;
    const name = escapeHtml(data.displayName || data.name || "—");
    const title = escapeHtml(data.title || data.department || "—");
    const key = escapeHtml(data.userId || data.name || "");
    const count = data._childCount || 0;
    const collapsed = data._collapsed;
    const toggle =
      count > 0
        ? `<button type="button" class="oc-card-toggle" data-toggle="1" title="Collapse/expand">${collapsed ? "+" : "−"}</button>`
        : "";
    const badge = count > 0 ? `<span class="oc-card-badge">${count > 99 ? "99+" : count}</span>` : "";
    const riskClass = [
      data.inactive ? "is-inactive" : "",
      data.brokenManager ? "is-broken" : "",
      data.privilegedAccess ? "is-priv" : "",
    ]
      .filter(Boolean)
      .join(" ");
    return `<div class="oc-card ${riskClass}" xmlns="http://www.w3.org/1999/xhtml">
      <div class="oc-card-top">
        <div class="oc-card-name">${name}</div>
        <div class="oc-card-actions">${badge}${toggle}</div>
      </div>
      <div class="oc-card-title">${title}</div>
      <div class="oc-card-key">${key}</div>
      ${riskChips(data)}
    </div>`;
  }

  function render() {
    const root = forestHierarchy();
    layoutHierarchy(root);
    const nodes = root.descendants().filter((d) => d.data.name !== "_empty");
    const links = root.links().filter((d) => d.source.data.name !== "_empty");

    gLinks
      .selectAll("path.oc-link")
      .data(links, (d) => `${d.source.data._id}->${d.target.data._id}`)
      .join(
        (enter) =>
          enter
            .append("path")
            .attr("class", "oc-link")
            .attr("fill", "none")
            .attr("stroke", "#6b7c90")
            .attr("stroke-width", 1.75)
            .attr("d", linkPath),
        (update) => update.attr("d", linkPath),
        (exit) => exit.remove(),
      );

    const nodeSel = gNodes.selectAll("g.oc-node").data(nodes, (d) => d.data._id || d.data.name);

    const nodeEnter = nodeSel
      .enter()
      .append("g")
      .attr("class", "oc-node")
      .attr("transform", (d) => `translate(${d.x},${d.y})`);

    nodeEnter
      .append("foreignObject")
      .attr("class", "oc-fo")
      .attr("x", -NODE_W / 2)
      .attr("y", -NODE_H / 2)
      .attr("width", NODE_W)
      .attr("height", NODE_H)
      .style("overflow", "visible");

    const merged = nodeEnter.merge(nodeSel);
    merged.attr("transform", (d) => `translate(${d.x},${d.y})`);
    merged
      .classed("inactive", (d) => !!d.data.inactive)
      .classed(
        "selected",
        (d) =>
          !!(
            state.selected &&
            (d.data._id === state.selected._id || d.data.name === state.selected.name)
          ),
      )
      .classed("hit", (d) => state.hitIds.has(d.data._id) || state.hitIds.has(d.data.name))
      .classed("synthetic", (d) => !!d.data._synthetic);

    merged.each(function (d) {
      const fo = d3.select(this).select("foreignObject").node();
      if (fo) fo.innerHTML = cardHtml(d);
    });

    merged.on("click", (event, d) => {
      const t = event.target;
      if (t && t.closest && t.closest("[data-toggle='1']")) {
        event.stopPropagation();
        toggleCollapse(d);
        return;
      }
      event.stopPropagation();
      selectNode(d);
    });

    nodeSel.exit().remove();
  }

  function toggleCollapse(d) {
    const id = d.data._id || d.data.name;
    if (!d.data._childCount) return;
    if (state.collapsed.has(id)) state.collapsed.delete(id);
    else state.collapsed.add(id);
    render();
  }

  function selectNode(d) {
    if (d.data._synthetic) return;
    state.selected = d.data;
    render();
    el.drawer.hidden = false;
    document.getElementById("d-name").textContent = d.data.displayName || d.data.name;
    document.getElementById("d-key").textContent = d.data.name || "—";
    document.getElementById("d-title").textContent = d.data.title || "—";
    document.getElementById("d-dept").textContent = d.data.department || "—";
    document.getElementById("d-job").textContent = d.data.jobCode || "—";
    document.getElementById("d-email").textContent = d.data.email || "—";
    document.getElementById("d-type").textContent = d.data.employeeType || "—";
    document.getElementById("d-loc").textContent = d.data.location || "—";
    document.getElementById("d-reports").textContent = String(
      d.data.directReports ?? d.data._childCount ?? 0,
    );
    const risks = Array.isArray(d.data.riskFlags) ? d.data.riskFlags : [];
    const bits = [d.data.inactive ? "Inactive" : "Active"];
    if (d.data.brokenManager || risks.includes("brokenManager")) bits.push("broken manager");
    if (d.data.privilegedAccess || risks.includes("privileged")) bits.push("privileged");
    document.getElementById("d-status").textContent = bits.join(" · ");
  }

  function fit() {
    const node = gRoot.node();
    if (!node) return;
    let box;
    try {
      box = node.getBBox();
    } catch {
      return;
    }
    const width = svg.node().clientWidth || 1200;
    const height = svg.node().clientHeight || 700;
    if (!box.width || !box.height) return;
    const scale = Math.min(1.15, 0.88 / Math.max(box.width / width, box.height / height));
    const tx = width / 2 - scale * (box.x + box.width / 2);
    const ty = Math.max(24, height / 2 - scale * (box.y + box.height / 2));
    svg.transition().duration(350).call(state.zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
  }

  function expandAll() {
    state.collapsed.clear();
    render();
    fit();
  }

  function collapseBelowRoots() {
    state.collapsed.clear();
    const walk = (n, depth) => {
      const id = n.id || n.name;
      if (depth >= 1 && (n.children || []).length) state.collapsed.add(id);
      (n.children || []).forEach((c) => walk(c, depth + 1));
    };
    state.forest.forEach((r) => walk(r, 0));
    render();
    fit();
  }

  async function runSearch(q) {
    state.hitIds = new Set();
    if (!q || q.length < 2) {
      render();
      return;
    }
    const res = await fetch(`/api/orgchart/search?q=${encodeURIComponent(q)}`);
    const body = await res.json().catch(() => ({}));
    const rows = (body.data && body.data.results) || body.results || [];
    rows.forEach((r) => {
      if (r.id) state.hitIds.add(r.id);
      if (r.name) state.hitIds.add(r.name);
    });
    const ql = q.toLowerCase();
    const walk = (n) => {
      const blob = `${n.displayName || ""} ${n.name || ""} ${n.userId || ""} ${n.email || ""}`.toLowerCase();
      if (blob.includes(ql)) {
        if (n.id) state.hitIds.add(n.id);
        if (n.name) state.hitIds.add(n.name);
      }
      (n.children || []).forEach(walk);
    };
    state.forest.forEach(walk);
    render();
    if (state.hitIds.size) setStatus(`Highlighting ${state.hitIds.size} match(es) for “${q}”.`);
    else setStatus(`No matches for “${q}”.`, true);
  }

  function buildPrintableSvg() {
    // Expand for print, layout with native SVG shapes (foreignObject often prints blank).
    const prevCollapsed = new Set(state.collapsed);
    state.collapsed.clear();
    const root = forestHierarchy();
    layoutHierarchy(root);
    state.collapsed = prevCollapsed;

    const nodes = root.descendants().filter((d) => d.data.name !== "_empty");
    const links = root.links().filter((d) => d.source.data.name !== "_empty");
    if (!nodes.length) return null;

    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    nodes.forEach((d) => {
      minX = Math.min(minX, d.x - NODE_W / 2);
      minY = Math.min(minY, d.y - NODE_H / 2);
      maxX = Math.max(maxX, d.x + NODE_W / 2);
      maxY = Math.max(maxY, d.y + NODE_H / 2);
    });
    const pad = 48;
    const width = Math.ceil(maxX - minX + pad * 2);
    const height = Math.ceil(maxY - minY + pad * 2);

    const ns = "http://www.w3.org/2000/svg";
    const out = document.createElementNS(ns, "svg");
    out.setAttribute("xmlns", ns);
    out.setAttribute("viewBox", `0 0 ${width} ${height}`);
    out.setAttribute("width", String(width));
    out.setAttribute("height", String(height));

    const bg = document.createElementNS(ns, "rect");
    bg.setAttribute("x", "0");
    bg.setAttribute("y", "0");
    bg.setAttribute("width", String(width));
    bg.setAttribute("height", String(height));
    bg.setAttribute("fill", "#ffffff");
    out.appendChild(bg);

    const title = document.createElementNS(ns, "text");
    title.setAttribute("x", String(pad));
    title.setAttribute("y", "28");
    title.setAttribute("fill", "#0a1f38");
    title.setAttribute("font-family", "Figtree, Helvetica, Arial, sans-serif");
    title.setAttribute("font-size", "16");
    title.setAttribute("font-weight", "700");
    title.textContent = "Meridian National Bank — Org Chart";
    out.appendChild(title);

    const g = document.createElementNS(ns, "g");
    g.setAttribute("transform", `translate(${pad - minX},${pad - minY + 12})`);
    out.appendChild(g);

    links.forEach((d) => {
      const path = document.createElementNS(ns, "path");
      path.setAttribute("d", linkPath(d));
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", "#6b7c90");
      path.setAttribute("stroke-width", "1.75");
      g.appendChild(path);
    });

    nodes.forEach((d) => {
      const gx = document.createElementNS(ns, "g");
      gx.setAttribute("transform", `translate(${d.x},${d.y})`);

      const rect = document.createElementNS(ns, "rect");
      rect.setAttribute("x", String(-NODE_W / 2));
      rect.setAttribute("y", String(-NODE_H / 2));
      rect.setAttribute("width", String(NODE_W));
      rect.setAttribute("height", String(NODE_H));
      rect.setAttribute("rx", "12");
      rect.setAttribute("ry", "12");
      rect.setAttribute("fill", d.data._synthetic ? "#0c2340" : "#ffffff");
      rect.setAttribute("stroke", d.data._synthetic ? "#b8923f" : "#9aa8b8");
      rect.setAttribute("stroke-width", "1.5");
      gx.appendChild(rect);

      const name = document.createElementNS(ns, "text");
      name.setAttribute("x", "0");
      name.setAttribute("y", "-14");
      name.setAttribute("text-anchor", "middle");
      name.setAttribute("fill", d.data._synthetic ? "#ffffff" : "#0a1f38");
      name.setAttribute("font-family", "Syne, Helvetica, Arial, sans-serif");
      name.setAttribute("font-size", "13");
      name.setAttribute("font-weight", "700");
      name.textContent = truncate(d.data.displayName || d.data.name, 24);
      gx.appendChild(name);

      const sub = document.createElementNS(ns, "text");
      sub.setAttribute("x", "0");
      sub.setAttribute("y", "6");
      sub.setAttribute("text-anchor", "middle");
      sub.setAttribute("fill", d.data._synthetic ? "rgba(255,255,255,0.8)" : "#3d536b");
      sub.setAttribute("font-family", "Figtree, Helvetica, Arial, sans-serif");
      sub.setAttribute("font-size", "11");
      sub.textContent = truncate(d.data.title || d.data.department || "—", 28);
      gx.appendChild(sub);

      const key = document.createElementNS(ns, "text");
      key.setAttribute("x", "0");
      key.setAttribute("y", "24");
      key.setAttribute("text-anchor", "middle");
      key.setAttribute("fill", d.data._synthetic ? "rgba(255,255,255,0.7)" : "#6b7c90");
      key.setAttribute("font-family", "IBM Plex Mono, Menlo, monospace");
      key.setAttribute("font-size", "10");
      key.textContent = truncate(d.data.userId || d.data.name, 22);
      gx.appendChild(key);

      g.appendChild(gx);
    });

    return out;
  }

  function printChart() {
    const host = document.getElementById("oc-print-root");
    if (!host) {
      window.print();
      return;
    }
    setStatus("Preparing print sheet…");
    const prevLayout = state.layout;
    let sheet = null;
    try {
      // Prefer top-down for print readability when currently on a dense layout
      if (state.layout === "tree-h" || state.layout === "radial") {
        state.layout = "tree";
      }
      sheet = buildPrintableSvg();
    } finally {
      state.layout = prevLayout;
    }
    if (!sheet) {
      setStatus("Nothing to print.", true);
      return;
    }
    host.innerHTML = "";
    host.appendChild(sheet);
    host.hidden = false;
    host.setAttribute("aria-hidden", "false");

    let cleaned = false;
    const cleanup = () => {
      if (cleaned) return;
      cleaned = true;
      host.innerHTML = "";
      host.hidden = true;
      host.setAttribute("aria-hidden", "true");
      window.removeEventListener("afterprint", cleanup);
      setStatus("Print finished — use Landscape + Save as PDF if needed.");
    };
    window.addEventListener("afterprint", cleanup);
    requestAnimationFrame(() => {
      window.print();
      // Fallback if afterprint never fires (some Chromium builds)
      setTimeout(cleanup, 12000);
    });
  }

  function exportSvg() {
    const sheet = buildPrintableSvg();
    if (!sheet) {
      setStatus("Nothing to export.", true);
      return;
    }
    const blob = new Blob([new XMLSerializer().serializeToString(sheet)], {
      type: "image/svg+xml;charset=utf-8",
    });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `mnb-orgchart-${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function exportPng() {
    const sheet = buildPrintableSvg();
    if (!sheet) {
      setStatus("Nothing to export.", true);
      return;
    }
    const xml = new XMLSerializer().serializeToString(sheet);
    const url = URL.createObjectURL(new Blob([xml], { type: "image/svg+xml;charset=utf-8" }));
    const img = new Image();
    img.onload = () => {
      const w = Number(sheet.getAttribute("width")) || img.width;
      const h = Number(sheet.getAttribute("height")) || img.height;
      const canvas = document.createElement("canvas");
      const scale = 2;
      canvas.width = w * scale;
      canvas.height = h * scale;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(scale, scale);
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (!blob) {
          setStatus("PNG export failed.", true);
          return;
        }
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = `mnb-orgchart-${Date.now()}.png`;
        a.click();
        URL.revokeObjectURL(a.href);
        setStatus("PNG downloaded.");
      }, "image/png");
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      setStatus("PNG export failed — try Export SVG or Print / PDF.", true);
    };
    img.src = url;
  }

  function truncate(s, n) {
    const t = String(s || "");
    return t.length > n ? `${t.slice(0, n - 1)}…` : t;
  }

  function initZoom() {
    state.zoom = d3
      .zoom()
      .scaleExtent([0.12, 2.5])
      .on("zoom", (event) => gRoot.attr("transform", event.transform));
    svg.call(state.zoom);
    svg.on("click", () => {
      state.selected = null;
      el.drawer.hidden = true;
      render();
    });
  }

  function bind() {
    const initial = qs();
    state.mode = initial.mode === "subtree" ? "subtree" : "company";
    // Prefer readable top-down unless URL forces another layout
    state.layout = ["tree", "cluster", "tree-h", "radial"].includes(initial.layout)
      ? initial.layout
      : "tree";
    el.mode.value = state.mode;
    el.layout.value = state.layout;
    el.root.value = initial.root || "MNB00002";
    el.rootField.hidden = state.mode !== "subtree";
    if (initial.q) el.search.value = initial.q;

    el.mode.addEventListener("change", () => {
      state.mode = el.mode.value;
      el.rootField.hidden = state.mode !== "subtree";
      writeUrl();
      fetchChart().catch((e) => setStatus(String(e.message || e), true));
    });
    el.layout.addEventListener("change", () => {
      state.layout = el.layout.value;
      writeUrl();
      render();
      fit();
    });
    document.getElementById("oc-reload").addEventListener("click", () => {
      writeUrl();
      fetchChart().catch((e) => setStatus(String(e.message || e), true));
    });
    document.getElementById("oc-fit").addEventListener("click", fit);
    document.getElementById("oc-expand").addEventListener("click", expandAll);
    document.getElementById("oc-collapse").addEventListener("click", collapseBelowRoots);
    document.getElementById("oc-print").addEventListener("click", () => printChart());
    document.getElementById("oc-svg-export").addEventListener("click", exportSvg);
    document.getElementById("oc-png").addEventListener("click", exportPng);
    document.getElementById("oc-drawer-close").addEventListener("click", () => {
      el.drawer.hidden = true;
    });
    document.getElementById("d-focus").addEventListener("click", () => {
      if (!state.selected) return;
      el.mode.value = "subtree";
      state.mode = "subtree";
      el.rootField.hidden = false;
      el.root.value = state.selected.name || state.selected.userId;
      writeUrl();
      fetchChart().catch((e) => setStatus(String(e.message || e), true));
    });
    document.getElementById("d-toggle").addEventListener("click", () => {
      if (!state.selected) return;
      const id = state.selected.id || state.selected.name;
      if (state.collapsed.has(id)) state.collapsed.delete(id);
      else state.collapsed.add(id);
      render();
    });

    let t = null;
    el.search.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => {
        writeUrl();
        runSearch(el.search.value.trim()).catch((e) => setStatus(String(e.message || e), true));
      }, 220);
    });
  }

  initZoom();
  bind();
  fetchChart()
    .then(() => {
      if (el.search.value.trim()) return runSearch(el.search.value.trim());
    })
    .catch((e) => setStatus(String(e.message || e), true));
})();
