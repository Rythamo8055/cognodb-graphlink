/* GraphLink frontend — vanilla JS, one page, three domains.
   Every label and verb comes from the domain META served by the API;
   nothing here is domain-specific except generic UI words.
   All dynamic text is written with textContent — no innerHTML with data. */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const NS = "http://www.w3.org/2000/svg";

const state = { domain: "investors", node: null, hops: 2 };

let domains = [];
let meta = null;
let viewMode = "explore";

/* ---------- tiny DOM helpers ---------- */

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function setLoading(root, text) {
  root.replaceChildren(el("div", "loading", text || "Loading…"));
}

function setEmpty(root, text) {
  root.replaceChildren(el("div", "empty", text || "Nothing to show yet."));
}

/* ---------- API ---------- */

async function fetchJson(path) {
  try {
    const r = await fetch(path);
    let data = {};
    try { data = await r.json(); } catch (err) { /* non-JSON body */ }
    return { ok: r.ok, status: r.status, data };
  } catch (err) {
    return { ok: false, status: 0, data: { detail: "network error" } };
  }
}

function apiPath(base, params) {
  const p = new URLSearchParams({ domain: state.domain, ...(params || {}) });
  return base + "?" + p.toString();
}

function handleFail(res, container, text) {
  showBanner();
  setEmpty(container, text || (res.data && res.data.detail) || "Could not load this view.");
}

/* ---------- banner ---------- */

function showBanner() {
  const b = $("#banner");
  if (!b.textContent) {
    b.textContent = "Database unreachable — showing partial data where available.";
  }
  b.classList.remove("hidden");
}

function hideBanner() {
  $("#banner").classList.add("hidden");
}

/* ---------- domain state ---------- */

function verb(rel) {
  if (!rel) return "";
  return (meta.rel_labels && meta.rel_labels[rel]) ||
         String(rel).toLowerCase().replace(/_/g, " ");
}

function typeLabel(type) {
  return (meta.node_labels && meta.node_labels[type]) || type || "";
}

function selectDomain(id) {
  state.domain = id;
  state.node = null;
  meta = domains.find(d => d.id === id) || domains[0];
  document.documentElement.style.setProperty("--accent", meta.accent || "#E04F2F");
  $$("#tabs .tab").forEach(t => t.classList.toggle("active", t.dataset.id === id));
  $("#insights-title").textContent = meta.name + " — insights";
  renderSearchSetup();
  renderStats();
  renderInsights();
  renderWhy();
  resetExplorer();
  resetPath();
}

function renderTabs() {
  const tabs = $("#tabs");
  tabs.replaceChildren();
  for (const d of domains) {
    const b = el("button", "tab", d.name);
    b.type = "button";
    b.dataset.id = d.id;
    b.addEventListener("click", () => selectDomain(d.id));
    tabs.append(b);
  }
}

/* ---------- search ---------- */

function renderSearchSetup() {
  const input = $("#q");
  const samples = (meta.sample_searches || []).slice(0, 2);
  input.placeholder = samples.length
    ? 'Try "' + samples.join('" or "') + '"'
    : "Search this network";
  const chips = $("#chips");
  chips.replaceChildren();
  for (const s of meta.sample_searches || []) {
    const c = el("button", "chip", s);
    c.type = "button";
    c.addEventListener("click", () => { input.value = s; doSearch(s); });
    chips.append(c);
  }
}

async function doSearch(q) {
  const term = (q !== undefined ? q : $("#q").value).trim();
  if (!term) return;
  const box = $("#search-results");
  setLoading(box, "Searching…");
  const res = await fetchJson(apiPath("/api/search", { q: term }));
  if (!res.ok) { handleFail(res, box, "Search is unavailable right now."); return; }
  const results = res.data.results || [];
  box.replaceChildren();
  if (!results.length) {
    setEmpty(box, 'No matches for "' + term + '" in this network.');
    return;
  }
  box.append(el("div", "results-title",
    results.length + " match" + (results.length === 1 ? "" : "es") + ' for "' + term + '"'));
  const grid = el("div", "results-grid");
  for (const r of results) {
    const card = el("div", "result-card");
    const name = el("span", "result-name", r.name);
    name.dataset.node = r.name;
    card.append(name, el("span", "badge", typeLabel(r.type)));
    if (r.city) card.append(el("span", "result-meta", r.city));
    grid.append(card);
  }
  box.append(grid);
}

/* ---------- stats ---------- */

function statCard(num, label) {
  const c = el("div", "stat-card");
  c.append(el("span", "num", String(num)), el("span", "lbl", label));
  return c;
}

async function renderStats() {
  const box = $("#stats");
  setLoading(box, "Loading stats…");
  const res = await fetchJson(apiPath("/api/stats"));
  if (!res.ok) { handleFail(res, box, "Stats are unavailable right now."); return; }
  paintStats(box, res.data.nodes || {}, res.data.edges ?? 0);
}

function paintStats(box, nodes, edges) {
  box.replaceChildren();
  for (const [type, count] of Object.entries(nodes || {})) {
    box.append(statCard(count, typeLabel(type)));
  }
  box.append(statCard(edges, "relationships"));
}

/* ---------- insights ---------- */

async function renderInsights() {
  const boxes = {
    pairs: $("#block-pairs"),
    interlocks: $("#block-interlocks"),
    alumni: $("#block-alumni"),
    hubs: $("#block-hubs"),
  };
  Object.values(boxes).forEach(b => setLoading(b, "Loading…"));
  const res = await fetchJson(apiPath("/api/insights"));
  if (!res.ok) {
    Object.values(boxes).forEach(b => handleFail(res, b, "Insights are unavailable right now."));
    return;
  }
  paintInsights(res.data);
}

function paintInsights(data) {
  renderPairs($("#block-pairs"), (data.pairs || []).slice(0, 8));
  renderInterlocks($("#block-interlocks"), (data.interlocks || []).slice(0, 8));
  renderAlumni($("#block-alumni"), data.alumni || []);
  renderHubs($("#block-hubs"), (data.hubs || []).slice(0, 6));
}

function nodeSpan(name, cls) {
  const s = el("span", cls || "name", name);
  s.dataset.node = name;
  return s;
}

function renderPairs(box, rows) {
  box.replaceChildren();
  box.append(el("h3", "card-title", "Top pairs — shared via " + verb(meta.pairs_rel)));
  box.append(el("p", "card-sub", "Nodes that keep sharing a common target in this network."));
  if (!rows.length) { box.append(el("div", "empty", "No shared pairs in this dataset yet.")); return; }
  const list = el("div", "insight-list");
  for (const r of rows) {
    const row = el("div", "insight-row");
    row.append(nodeSpan(r.left, "pair-name"), el("span", "pair-sep", "↔"),
               nodeSpan(r.right, "pair-name"),
               el("span", "row-meta", "(" + r.shared + " shared)"));
    list.append(row);
  }
  box.append(list);
}

function renderInterlocks(box, rows) {
  box.replaceChildren();
  box.append(el("h3", "card-title", "Interlocks via " + verb(meta.interlock_rel)));
  box.append(el("p", "card-sub",
    "People linked to more than one " + typeLabel(meta.org_type).toLowerCase() +
    " through " + verb(meta.interlock_rel) + "."));
  if (!rows.length) { box.append(el("div", "empty", "No interlocks in this dataset yet.")); return; }
  const list = el("div", "insight-list");
  for (const r of rows) {
    const row = el("div", "insight-row");
    row.append(nodeSpan(r.person), el("span", "row-meta", "→"));
    [r.org_a, r.org_b].forEach((org, i) => {
      if (i > 0) row.append(el("span", "row-meta", "&"));
      row.append(nodeSpan(org));
    });
    list.append(row);
  }
  box.append(list);
}

function renderAlumni(box, rows) {
  box.replaceChildren();
  box.append(el("h3", "card-title", "Alumni & pathways"));
  box.append(el("p", "card-sub",
    "Where members of each " + typeLabel(meta.institution_type).toLowerCase() + " go next."));
  if (!rows.length) { box.append(el("div", "empty", "No alumni pathways in this dataset yet.")); return; }
  const grid = el("div", "alumni-grid");
  for (const inst of rows) {
    const card = el("div", "alumni-card");
    const head = el("div", "alumni-head");
    head.append(nodeSpan(inst.institution),
                el("span", "alumni-count",
                   inst.count + " member" + (inst.count === 1 ? "" : "s")));
    card.append(head);
    const members = el("ul", "alumni-members");
    for (const m of inst.members || []) {
      const li = el("li");
      li.append(nodeSpan(m));
      members.append(li);
    }
    card.append(members);
    grid.append(card);
  }
  box.append(grid);
}

function renderHubs(box, rows) {
  box.replaceChildren();
  box.append(el("h3", "card-title", "Most connected"));
  box.append(el("p", "card-sub", "The hubs of this network, by number of relationships."));
  if (!rows.length) { box.append(el("div", "empty", "No hubs in this dataset yet.")); return; }
  const list = el("div", "insight-list");
  for (const r of rows) {
    const row = el("div", "insight-row");
    row.append(nodeSpan(r.name), el("span", "badge", typeLabel(r.type)),
               el("span", "row-meta", r.degree + " connection" + (r.degree === 1 ? "" : "s")));
    list.append(row);
  }
  box.append(list);
}

/* ---------- node explorer ---------- */

function resetExplorer() {
  setEmpty($("#node-panel"),
    "Click any node name — in search results, insights or paths — to open it here.");
}

function selectNode(name) {
  state.node = name;
  switchView("explore");
  renderExplorer();
}

function switchView(mode) {
  viewMode = mode;
  $("#btn-explore").classList.toggle("active", mode === "explore");
  $("#btn-path").classList.toggle("active", mode === "path");
  $("#main").classList.toggle("path-mode", mode === "path");
}

async function renderExplorer() {
  const panel = $("#node-panel");
  setLoading(panel, "Loading node…");
  const [nres, hres] = await Promise.all([
    fetchJson(apiPath("/api/node", { name: state.node })),
    fetchJson(apiPath("/api/neighborhood", { name: state.node, hops: state.hops })),
  ]);
  panel.replaceChildren();
  if (nres.status === 404 || hres.status === 404) {
    setEmpty(panel, '"' + state.node + '" is not in this network.');
    return;
  }
  if (!nres.ok || !hres.ok) {
    handleFail(nres.ok ? hres : nres, panel, "Node explorer is unavailable right now.");
    return;
  }
  paintExplorer(panel, nres.data.props || {}, nres.data.links || [],
                { nodes: hres.data.nodes || [], edges: hres.data.edges || [] });
}

function paintExplorer(panel, props, links, hood) {
  panel.replaceChildren();

  const close = el("button", "panel-close", "Close");
  close.type = "button";
  close.addEventListener("click", resetExplorer);
  panel.append(close);

  const head = el("div", "node-head");
  head.append(el("h2", "node-title", props.name || state.node),
              el("span", "badge", typeLabel(props.type)));
  panel.append(head);

  const propGrid = el("div", "props-grid");
  let anyProps = false;
  for (const [k, v] of Object.entries(props)) {
    if (k === "name" || k === "type" || v === null || v === undefined) continue;
    anyProps = true;
    const cell = el("div", "prop-cell");
    cell.append(el("span", "prop-label", k.replace(/_/g, " ")),
                el("span", "prop-val", fmtProp(k, v)));
    propGrid.append(cell);
  }
  if (anyProps) panel.append(propGrid);

  if (links.length) {
    const box = el("div", "links-box");
    box.append(el("h3", "card-title", "One-hop connections"));
    const groups = {};
    for (const l of links) (groups[l.rel] = groups[l.rel] || []).push(l);
    for (const [rel, rows] of Object.entries(groups)) {
      box.append(el("div", "links-group", verb(rel)));
      for (const l of rows) {
        const row = el("div", "link-row");
        row.append(nodeSpan(l.name), el("span", "badge", typeLabel(l.type)));
        const extra = fmtProps(l.props);
        if (extra) row.append(el("span", "link-meta", extra));
        box.append(row);
      }
    }
    panel.append(box);
  }

  const hoodBox = el("div", "hood-box");
  hoodBox.append(el("h3", "card-title", "Two-hop neighborhood"));
  if (hood && hood.nodes && hood.nodes.length > 1) {
    renderNeighborhood(hoodBox, hood.nodes, hood.edges || []);
  } else {
    hoodBox.append(el("div", "empty", "No further connections to draw."));
  }
  panel.append(hoodBox);
}

/* ---------- 2-hop SVG neighborhood (circle layout, plain SVG) ---------- */

function renderNeighborhood(box, nodes, edges) {
  const size = 440, cx = size / 2, cy = size / 2;
  const start = nodes.find(n => n.hop === 0);
  const rings = { 1: [], 2: [] };
  for (const n of nodes) {
    if (n.hop === 1 || n.hop === 2) rings[n.hop].push(n);
  }
  const pos = {};
  for (const [hop, list] of Object.entries(rings)) {
    const r = hop === "1" ? 82 : 172;
    list.forEach((n, i) => {
      const a = (i / Math.max(list.length, 1)) * Math.PI * 2 - Math.PI / 2;
      pos[n.name] = { x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r };
    });
  }
  if (start) pos[start.name] = { x: cx, y: cy };

  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 " + size + " " + size);
  svg.setAttribute("class", "hood-svg");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Two-hop neighborhood around " + (start ? start.name : ""));

  for (const e of edges) {
    const a = pos[e.from], b = pos[e.to];
    if (!a || !b) continue;
    const line = document.createElementNS(NS, "line");
    line.setAttribute("x1", a.x); line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
    line.setAttribute("class", "hood-edge");
    svg.append(line);
    const t = document.createElementNS(NS, "text");
    t.setAttribute("x", (a.x + b.x) / 2);
    t.setAttribute("y", (a.y + b.y) / 2 - 3);
    t.setAttribute("class", "hood-edge-label");
    t.setAttribute("text-anchor", "middle");
    t.textContent = verb(e.rel);
    svg.append(t);
  }

  for (const n of nodes) {
    const p = pos[n.name];
    if (!p) continue;
    const g = document.createElementNS(NS, "g");
    g.setAttribute("class", "hood-node" +
      (n.hop === 0 ? " start" : "") + (n.hop === 2 ? " faded" : ""));
    const circ = document.createElementNS(NS, "circle");
    circ.setAttribute("cx", p.x); circ.setAttribute("cy", p.y);
    circ.setAttribute("r", n.hop === 0 ? 11 : 7);
    g.append(circ);
    const label = document.createElementNS(NS, "text");
    label.setAttribute("x", p.x);
    label.setAttribute("y", p.y + (n.hop === 0 ? 27 : 22));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("class", "hood-label");
    label.textContent = n.name;
    g.append(label);
    const tip = document.createElementNS(NS, "title");
    tip.textContent = typeLabel(n.type) + (n.hop ? " · hop " + n.hop : " · selected");
    g.append(tip);
    g.addEventListener("click", () => selectNode(n.name));
    svg.append(g);
  }
  box.append(svg);
}

/* ---------- props formatting ---------- */

function money(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v);
  if (n >= 1e6) return "$" + (n / 1e6).toFixed(n % 1e6 === 0 ? 0 : 1) + "M";
  if (n >= 1e3) return "$" + Math.round(n / 1e3) + "K";
  return "$" + n;
}

function fmtProp(k, v) {
  if (k === "amount_usd") return money(v);
  if (k === "round") return String(v).replace(/_/g, " ").toLowerCase();
  if (k === "year" || k === "since" || k === "founded_year") return String(v);
  return String(v);
}

function fmtProps(props) {
  return Object.entries(props || {})
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([k, v]) => fmtProp(k, v))
    .join(" · ");
}

/* ---------- pathfinder ---------- */

function resetPath() {
  $("#pf-a").value = "";
  $("#pf-b").value = "";
  $("#sug-a").classList.add("hidden");
  $("#sug-b").classList.add("hidden");
  $("#pf-result").replaceChildren();
}

function wireSuggestions() {
  const pairs = [["pf-a", "sug-a"], ["pf-b", "sug-b"]];
  for (const [inpId, sugId] of pairs) {
    const input = $("#" + inpId);
    const box = $("#" + sugId);
    input.addEventListener("input", async () => {
      const q = input.value.trim();
      if (q.length < 2) { box.classList.add("hidden"); box.replaceChildren(); return; }
      const res = await fetchJson(apiPath("/api/search", { q }));
      box.replaceChildren();
      if (!res.ok || !(res.data.results || []).length) {
        box.classList.add("hidden");
        return;
      }
      for (const r of res.data.results.slice(0, 8)) {
        const item = el("div", "suggest-item", r.name);
        item.addEventListener("mousedown", () => {
          input.value = r.name;
          box.classList.add("hidden");
          box.replaceChildren();
        });
        box.append(item);
      }
      box.classList.remove("hidden");
    });
    input.addEventListener("blur", () => setTimeout(() => box.classList.add("hidden"), 150));
    input.addEventListener("keydown", e => { if (e.key === "Enter") findPath(); });
  }
}

async function findPath() {
  const a = $("#pf-a").value.trim();
  const b = $("#pf-b").value.trim();
  const out = $("#pf-result");
  if (!a || !b) { setEmpty(out, "Type two node names first."); return; }
  if (a === b) { setEmpty(out, "Pick two different nodes."); return; }
  setLoading(out, "Finding the shortest path…");
  const [na, nb, pathRes] = await Promise.all([
    fetchJson(apiPath("/api/node", { name: a })),
    fetchJson(apiPath("/api/node", { name: b })),
    fetchJson(apiPath("/api/path", { from: a, to: b })),
  ]);
  if (na.status === 404 || nb.status === 404) {
    setEmpty(out, '"' + (na.status === 404 ? a : b) +
      '" is not in this network — node not found.');
    return;
  }
  if (!na.ok || !nb.ok || !pathRes.ok) {
    handleFail(pathRes, out, "Pathfinder is unavailable right now.");
    return;
  }
  if (!pathRes.data.found) {
    setEmpty(out, 'No path up to 6 hops between "' + a + '" and "' + b + '".');
    return;
  }
  const steps = pathRes.data.steps || [];
  paintPath(out, steps, a, b);
}

function paintPath(out, steps, a, b) {
  out.replaceChildren();
  out.append(el("div", "path-summary",
    steps.length + " hop" + (steps.length === 1 ? "" : "s") + " · " + a + " → " + b));
  const chain = el("div", "path-chain");
  steps.forEach((s, i) => {
    const step = el("div", "path-step");
    step.append(el("span", "step-n", String(i + 1)));
    step.append(nodeSpan(s.from));
    step.append(el("span", "step-verb", verb(s.rel)));
    step.append(nodeSpan(s.to));
    const extra = fmtProps(s.props);
    if (extra) step.append(el("span", "step-props", "(" + extra + ")"));
    chain.append(step);
  });
  out.append(chain);
}

async function renderPath() {
  if (state.from) $("#pf-a").value = state.from;
  if (state.to) $("#pf-b").value = state.to;
  await findPath();
}

/* ---------- why a graph ---------- */

const WHY = {
  investors: "In a relational schema, an investment forces a choice between two tables — one for people and one for firms — and \"who else backed this startup\" becomes a UNION across both. As edges, investments keep one shape whether the investor is a person or a firm, so shared targets, reachability and shortest paths are a handful of Cypher lines instead of recursive CTEs.",
  education: "Alumni pipelines are defined by their paths: a student studied at a campus, was mentored by an alum, and landed at a company. In tables, tracking who shares a campus and where alumni end up means several joins at a fixed depth; in a graph the same question is a variable-length walk and every hop stays one edge.",
  healthcare: "Care networks only make sense as connections: doctors share patients, refer to one another, and work across hospitals. In tables, \"which doctors share a patient\" is a self-join on the patient key that grows with every new table; in a graph the patient is one shared node and the answer is a two-hop pattern that reads like the domain.",
};

function renderWhy() {
  const body = $("#why-body");
  body.replaceChildren();
  for (const d of domains) {
    const p = el("p", "why-para");
    p.append(el("strong", "why-head", d.name + ". "));
    p.append(WHY[d.id] || "Connections are the data — a graph stores them directly.");
    body.append(p);
  }
}

/* ---------- static wiring & boot ---------- */

function wireStaticEvents() {
  $("#go").addEventListener("click", () => doSearch());
  $("#q").addEventListener("keydown", e => { if (e.key === "Enter") doSearch(); });
  $("#btn-explore").addEventListener("click", () => switchView("explore"));
  $("#btn-path").addEventListener("click", () => { switchView("path"); resetPath(); });
  $("#why-link").addEventListener("click", e => {
    e.preventDefault();
    const d = $("#why");
    d.open = true;
    d.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  wireSuggestions();
  $("#pf-go").addEventListener("click", findPath);

  document.addEventListener("click", e => {
    const t = e.target.closest("[data-node]");
    if (t) selectNode(t.dataset.node);
  });
}

async function checkHealth() {
  const res = await fetchJson("/health");
  if (res.ok && res.data.db === false) $("#mode-tag").classList.remove("hidden");
}

function applyDeepLink() {
  const q = new URLSearchParams(location.search);
  const d = q.get("domain");
  const n = q.get("node");
  const v = q.get("view");
  const f = q.get("from");
  const t = q.get("to");
  if (d) state.domain = d;
  if (v === "path") viewMode = "path";
  else if (v === "explore") viewMode = "explore";
  if (n) state.node = n;
  state.from = f || "";
  state.to = t || "";
}

async function init() {
  applyDeepLink();
  wireStaticEvents();
  const snap = window.__SNAP__;
  if (snap) { snapInit(snap); return; }
  const res = await fetchJson("/api/domains");
  if (!res.ok) {
    showBanner();
    setEmpty($("#node-panel"), "Could not load domains — is the server running?");
    return;
  }
  domains = res.data.domains || [];
  if (!domains.length) {
    setEmpty($("#node-panel"), "No domains are configured yet.");
    return;
  }
  if (!domains.find(d => d.id === state.domain)) state.domain = domains[0].id;
  renderTabs();
  selectDomain(state.domain);
  if (state.node) { switchView("explore"); renderExplorer(); }
  if (viewMode === "path") { switchView("path"); if (state.from) renderPath(); }
  checkHealth();
}

function snapInit(snap) {
  const v = snap.view || { kind: "home", domain: "investors" };
  domains = snap.domains || [];
  state.domain = v.domain || domains[0].id;
  state.node = null;
  meta = domains.find(d => d.id === state.domain) || domains[0];
  document.documentElement.style.setProperty("--accent", meta.accent || "#E04F2F");
  renderTabs();
  renderSearchSetup();
  renderWhy();
  if (v.kind === "node") {
    switchView("explore");
    state.node = v.node;
    paintExplorer($("#node-panel"), v.props || {}, v.links || [], v.hood || null);
  } else if (v.kind === "path") {
    switchView("path");
    paintPath($("#pf-result"), v.steps || [], v.from, v.to);
    $("#pf-a").value = v.from || "";
    $("#pf-b").value = v.to || "";
  } else {
    paintStats($("#stats"), (v.stats || {}).nodes || {}, (v.stats || {}).edges ?? 0);
    paintInsights(v.insights || {});
  }
}

init();
