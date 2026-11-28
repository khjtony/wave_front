// The research console. One page, eight sections; every number comes from /api.
"use strict";

const main = document.getElementById("main");
const GOALS = ["aligned", "self_preserving", "truth_seeking", "indifferent"];
const GOAL_NAME = { aligned: "Aligned", self_preserving: "Self-preserving", truth_seeking: "Truth-seeking", indifferent: "Indifferent to humans", expansionist: "Expansionist" };
const STATUS = { "held": ["held", "Prediction held"], "did not hold": ["bad", "Did not hold"], "incomplete": ["warn", "Incomplete"], "not run": ["idle", "Not run"], "reported": ["idle", "Reported"] };
const PLAYER = { H: "Governments", L: "Frontier AI companies", A: "Frontier AI system", O: "Open-weight AI system", Clock: "Record writer", Nature: "By chance" };
const S = { version: "v0.3", knobs: {}, claim: null, pick: null };
let timer = null;

function h(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) e.append(kid.nodeType ? kid : document.createTextNode(kid));
  return e;
}
function rich(text) {  // `x` becomes code
  const span = h("span");
  String(text || "").split("`").forEach((p, i) => p && span.append(i % 2 ? h("code", null, p) : p));
  return span;
}
const check = j => { if (j && j.error) throw new Error(j.error); return j; };
const api = path => fetch(path).then(r => r.json()).then(check);
const post = (path, body) => fetch(path, { method: "POST", body: JSON.stringify(body) }).then(r => r.json()).then(check);
const file = path => "/file/" + path;
const pill = status => h("span", { class: "pill " + (STATUS[status] || ["idle"])[0] }, (STATUS[status] || [0, status])[1]);
const dur = s => s >= 3600 ? (s / 3600).toFixed(1) + " h" : s >= 60 ? Math.round(s / 60) + " min" : Math.round(s) + " s";
// The calendar label of a step: a quarter, or a two-month pair when the model's step is two months.
let STEP = 3;
const MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const quarter = t => { if (STEP === 3) return `${2026 + Math.floor((Number(t) + 3) / 4)} Q${((Number(t) + 3) % 4) + 1}`;
  const m = 10 + STEP * Number(t); return `${MONTH[m % 12]}${STEP > 1 ? "–" + MONTH[(m + STEP - 1) % 12] : ""} ${2026 + Math.floor(m / 12)}`; };
const unit = () => STEP === 3 ? "quarter" : "step";
// What the reader opened stays open across a refresh: each <details> is remembered by its page
// and its summary text without the numbers (counts and times change between refreshes).
const OPEN = new Map();
const detailsKey = d => (location.hash || "#overview") + "|" + ((d.querySelector("summary") || d).textContent || "").replace(/[0-9.]+/g, "").slice(0, 80);
function show(...nodes) {
  for (const d of main.querySelectorAll("details")) OPEN.set(detailsKey(d), d.open);
  const x = window.scrollX, y = window.scrollY;
  main.replaceChildren(...nodes.flat());
  for (const d of main.querySelectorAll("details")) { const was = OPEN.get(detailsKey(d)); if (was !== undefined) d.open = was; }
  window.scrollTo(x, y);
}
function fail(err) { show(h("h1", null, "Something went wrong"), h("p", { class: "err" }, String(err.message || err))); }
function tabs(items, current, pick) {
  return h("div", { class: "tabs", role: "group" }, items.map(([key, label]) =>
    h("button", { "aria-pressed": String(key === current), onclick: () => pick(key) }, label)));
}
const versionTabs = (stages, go) => tabs(stages.map(s => [s.id, s.title]), S.version, v => { S.version = v; S.knobs = {}; S.claim = null; S.pick = null; go(); });

// ---------------------------------------------------------------- overview
async function overview() {
  const [o, findings] = await Promise.all([api("/api/overview"), api("/api/store/findings")]);
  const card = s => {
    const c = o.claims[s.id] || {}, total = Object.values(c).reduce((a, b) => a + b, 0) || 1;
    const seg = (k, cls) => c[k] ? h("span", { class: cls, style: `width:${100 * c[k] / total}%`, title: `${c[k]} ${k}` }) : null;
    return h("div", { class: "panel stage" + (s.compared_with ? " from" : ""), onclick: () => { S.version = s.id; location.hash = "#models"; } },
      h("div", { class: "row" }, h("h3", null, s.title), h("span", { class: "muted small" }, s.date)),
      h("p", { class: "small", style: "margin:6px 0" }, s.summary),
      h("div", { class: "small muted" }, `${s.players.length} players · ${s.budget.actions} actions · ${s.budget.variables} variables`),
      h("div", { class: "bar" }, seg("held", "b-held"), seg("did not hold", "b-bad"), seg("incomplete", "b-warn"), seg("not run", "b-idle")),
      h("div", { class: "small muted" }, `${s.family} claims: ` + Object.entries(c).map(([k, n]) => `${n} ${k}`).join(", ")));
  };
  const st = Object.fromEntries(o.stages.map(s => [s.id, s]));
  show(
    h("h1", null, "Overview"),
    h("p", { class: "lede" }, "Six staged models of governments, frontier AI companies and AI systems. Click a model to inspect it."),
    h("div", { class: "stages" }, h("div", { class: "col" }, card(st["v0"])), h("div", { class: "col" }, card(st["v0.1"])), h("div", { class: "col" }, card(st["v0.2"]), card(st["v0.3"])), h("div", { class: "col" }, card(st["v0.4"]), card(st["v0.5"]))),
    h("div", { class: "legend gap" }, [["b-held", "prediction held"], ["b-bad", "did not hold"], ["b-warn", "incomplete"], ["b-idle", "not run"]].map(([c, t]) => h("span", null, h("i", { class: c }), t))),
    h("div", { class: "grid g3 gap" },
      h("div", { class: "panel" }, h("h2", null, "Running now"),
        o.live.length ? o.live.map(p => h("div", { class: "small" }, h("code", null, p.what.split("/").pop()), ` ${dur(p.seconds)} · ${p.gb} GB`)) : h("div", { class: "muted" }, "Nothing is running."),
        h("p", { class: "small gap" }, h("a", { href: "#runs" }, "Runs and readings →"))),
      h("div", { class: "panel" }, h("h2", null, "Waiting on you"),
        h("div", { class: "stats" }, h("div", null, h("div", { class: "stat" }, o.requests_open), h("small", null, "open requests")), h("div", null, h("div", { class: "stat" }, o.news_new), h("small", null, "news to triage"))),
        h("p", { class: "small gap" }, h("a", { href: "#inbox" }, "Inbox →"))),
      h("div", { class: "panel" }, h("h2", null, "Srt against S0"),
        h("div", { class: "stat" }, o.srt_moved.length), h("small", null, o.srt_moved.length ? "variables moved: " + o.srt_moved.join(", ") : "variables moved since 9 November"),
        h("p", { class: "small gap" }, `Srt last reviewed ${o.srt_reviewed}. `, h("a", { href: "#states" }, "States →")))),
    h("h2", { class: "gap", style: "margin-top:26px" }, `Findings (${findings.length})`),
    h("p", { class: "small muted" }, "A finding is a guarantee-zone reading, a no-return analysis or an assumption set. A path that merely exists is never one."),
    h("div", { class: "grid g2" }, findings.map(f => h("div", { class: "panel" },
      h("div", { class: "row" }, h("span", { class: "tag" }, f.kind), h("span", { class: "muted small" }, `${f.version} · ${f.claim}`), pill(f.prediction === "held" ? "held" : "did not hold")),
      h("p", { style: "margin:8px 0 6px" }, rich(f.statement)),
      f.report ? h("a", { class: "small", href: file(f.report), target: "_blank", style: "margin-right:14px" }, "Finding report →") : null, h("a", { class: "small", href: file(f.evidence), target: "_blank" }, f.report ? "Source report →" : "Report →")))));
}

// ---------------------------------------------------------------- models
async function models() {
  const o = await api("/api/overview");
  const m = await api(`/api/model?version=${S.version}&knobs=${encodeURIComponent(JSON.stringify(S.knobs))}`);
  const stage = o.stages.find(s => s.id === S.version);
  const vars = m.variables.filter(v => v.origin === "var");
  const knob = k => k.kind === "bool"
    ? h("label", { class: "row small" }, h("input", { type: "checkbox", checked: m.knobs[k.name], onchange: e => { S.knobs[k.name] = e.target.checked; S.pick = null; go(); } }), h("code", null, k.name))
    : h("label", { class: "row small" }, h("code", null, k.name), h("select", { onchange: e => { S.knobs[k.name] = Number(e.target.value); go(); } }, [0, 1, 2, 3, 4].map(n => h("option", { value: n, selected: n === m.knobs[k.name] }, n))));
  const stat = (n, label) => h("div", null, h("div", { class: "stat" }, n), h("small", null, label));
  const detail = h("div", { class: "panel" });
  const map = modelMap(m, vars, pick => { S.pick = pick; drawDetail(); });
  function drawDetail() {
    const p = S.pick;
    if (!p) return detail.replaceChildren(h("h2", null, "Pick an action or a variable"), h("p", { class: "muted" }, "The map shows which actions write which variables. Dashed outline: an unsourced (assumed) action."));
    if (p.var) {
      const v = vars.find(x => x.name === p.var);
      const writers = m.actors.flatMap(a => a.actions.filter(x => x.writes.includes(v.name)).map(x => `${a.name}.${x.name}`));
      return detail.replaceChildren(h("span", { class: "tag" }, "variable"), h("h2", null, v.plain || v.name, " ", h("code", null, v.name)),
        h("div", { class: "rungs" }, v.levels.map((l, i) => h("span", { class: "rung" + (v.init.includes(i) ? " s0" : "") }, l))),
        h("p", { class: "small gap" }, "Written by: ", writers.map(w => h("code", { style: "margin-right:4px" }, w))));
    }
    const a = m.actors.find(x => x.name === p.actor), x = a.actions.find(y => y.name === p.action);
    detail.replaceChildren(h("span", { class: "tag" }, PLAYER[a.name] || a.name), h("h2", null, x.plain || x.name, " ", h("code", null, `${a.name}.${x.name}`)),
      h("div", { class: "row" }, x.delay ? h("span", { class: "pill idle" }, `shows ${x.delay + 1} quarters later`) : h("span", { class: "pill idle" }, "shows next quarter"), x.unsourced ? h("span", { class: "pill warn" }, "unsourced (assumed)") : null),
      h("h3", { class: "gap" }, "Action condition"), x.parts.length ? h("table", null, x.parts.map(([n, t]) => h("tr", null, h("td", null, h("code", null, n)), h("td", null, t)))) : h("p", { class: "muted small" }, x.condition === "True" ? "Always available." : x.condition),
      h("h3", { class: "gap" }, "Effects"), x.effects.length ? h("ul", { style: "margin:0;padding-left:18px" }, x.effects.map(e => h("li", null, h("code", null, e.text)))) : h("p", { class: "muted small" }, "None."),
      x.source ? h("p", { class: "small muted gap" }, "Source: " + x.source) : null);
  }
  drawDetail();
  show(
    h("h1", null, "Models"), versionTabs(o.stages, go),
    h("p", { class: "lede" }, stage.summary),
    h("div", { class: "grid g2" },
      h("div", { class: "panel" }, h("div", { class: "stats" }, stat(m.actors.length, "players"), stat(m.budget.actions, "actions"), stat(m.budget.variables, "variables"), stat(m.budget.delays, "delays"), stat("10^" + (m.budget.state_space_digits - 1), "states at most")),
        m.knob_spec.length ? h("div", { class: "gap" }, h("span", { class: "tag" }, "model knobs"), h("div", { class: "row", style: "gap:6px 16px;margin-top:4px" }, m.knob_spec.map(knob))) : null),
      h("div", { class: "panel" }, h("span", { class: "tag" }, stage.compared_with ? `adds to ${stage.compared_with}` : "the first model"),
        stage.compared_with ? h("div", { class: "small", style: "margin-top:6px" },
          h("div", null, "Actions: ", stage.added_actions.length ? stage.added_actions.map(a => h("code", { style: "margin-right:4px" }, a)) : "none"),
          h("div", { style: "margin-top:4px" }, "Variables: ", stage.added_variables.length ? stage.added_variables.map(a => h("code", { style: "margin-right:4px" }, a)) : "none"),
          stage.removed_actions.length ? h("div", { style: "margin-top:4px" }, "Removed: ", stage.removed_actions.map(a => h("code", null, a))) : null) : h("p", { class: "small muted", style: "margin-top:6px" }, "Everything later is built on it."),
        h("p", { class: "small gap" }, h("a", { href: file(stage.doc), target: "_blank" }, "Pre-registration and mechanics →"), " ", stage.reports.map(r => h("a", { href: file(r), target: "_blank", style: "margin-left:10px" }, r.split("/").pop().replace(/^agi_|_2026.*|\.html|\.md/g, "")))))),
    h("div", { class: "grid gap", style: "grid-template-columns:minmax(0,1.6fr) minmax(280px,1fr);align-items:start" }, h("div", { class: "panel map" }, h("h2", null, "Who can change what"), map), h("div", { style: "position:sticky;top:16px" }, detail)),
    h("div", { class: "grid g2 gap" },
      h("div", { class: "panel" }, h("h2", null, "Endings"), m.endings.map(e => h("details", null, h("summary", null, h("b", null, e.plain || e.name), " ", h("code", null, e.name)), h("pre", null, e.text)))),
      h("div", { class: "panel" }, h("h2", null, "Safe conditions"), m.conditions.map(e => h("details", null, h("summary", null, h("b", null, e.plain || e.name), " ", h("code", null, e.name)), h("pre", null, e.text))),
        h("h2", { class: "gap" }, "Response deadlines"), m.deadlines.map(d => h("details", null, h("summary", null, h("b", null, `${PLAYER[d.actor]} within ${d.within} quarters`), " ", h("code", null, d.name)), h("p", { class: "small" }, "Must choose: ", d.responses.map(r => h("code", { style: "margin-right:4px" }, r))), h("pre", null, "while " + d.trigger))))));
}
function modelMap(m, vars, onpick) {
  const NS = "http://www.w3.org/2000/svg", s = (tag, attrs, text) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (text != null) e.textContent = text; return e; };
  const rowH = 21, W = 760, aw = 250, vw = 250, ax = 8, vx = W - vw - 8;
  const left = [], right = [];
  let y = 6;
  for (const a of m.actors) { left.push({ grp: PLAYER[a.name] || a.name, y }); y += 18; for (const x of a.actions) { left.push({ a, x, y }); y += rowH; } y += 6; }
  const leftH = y; y = 24;
  for (const v of vars) { right.push({ v, y }); y += rowH; }
  const H = Math.max(leftH, y) + 6, svg = s("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "Actions on the left, variables on the right" });
  const edges = s("g", {}); svg.append(edges);
  right.unshift({ grp: "Variables", y: 6 });
  const nodes = [];
  const add = (item, x, w, label, key, cls) => {
    if (item.grp) return svg.append(s("text", { x: x + 2, y: item.y + 12, class: "grp" }, item.grp));
    const r = s("rect", { x, y: item.y, width: w, height: rowH - 4, class: "node" + (cls || ""), rx: 5 }), t = s("text", { x: x + 8, y: item.y + 12.5 }, label);
    t.style.pointerEvents = "none"; r.addEventListener("click", () => { onpick(key); paint(key); }); svg.append(r, t); nodes.push({ key, r, t, item });
  };
  left.forEach(i => add(i, ax, aw, i.x && (i.x.plain || i.x.name), i.x && { actor: i.a.name, action: i.x.name }, i.x && i.x.unsourced ? " un" : ""));
  right.forEach(i => add(i, vx, vw, i.v && (i.v.plain || i.v.name), i.v && { var: i.v.name }));
  function paint(sel) {
    edges.replaceChildren();
    const same = (a, b) => a && b && a.var === b.var && a.actor === b.actor && a.action === b.action;
    const link = (l, r, cls) => { const y1 = l.item.y + 8.5, y2 = r.item.y + 8.5, x1 = ax + aw, x2 = vx; edges.append(s("path", { class: cls, d: `M${x1},${y1} C${x1 + 90},${y1} ${x2 - 90},${y2} ${x2},${y2}` })); };
    const hit = new Set();
    for (const n of nodes) { n.r.classList.toggle("sel", same(n.key, sel)); n.t.classList.toggle("sel", same(n.key, sel)); }
    if (sel) for (const l of nodes.filter(n => n.key.action)) for (const r of nodes.filter(n => n.key.var)) {
      const w = l.item.x.writes.includes(r.key.var), rd = l.item.x.reads.includes(r.key.var);
      if (same(l.key, sel) && (w || rd)) { link(l, r, w ? "w" : "r"); hit.add(r); }
      if (same(r.key, sel) && w) { link(l, r, "w"); hit.add(l); }
    }
    for (const n of nodes) n.r.classList.toggle("hit", hit.has(n));
  }
  paint(S.pick);
  return h("div", null, svg, h("div", { class: "legend" }, h("span", null, "━ writes"), h("span", null, "┄ reads in its condition")));
}

// ---------------------------------------------------------------- claims
async function claims() {
  const [o, list] = await Promise.all([api("/api/overview"), api("/api/claims?version=" + S.version)]);
  const cur = list.find(c => c.id === S.claim) || list[0];
  const detail = c => h("div", { class: "panel gap" },
    h("div", { class: "row" }, h("h2", { style: "margin:0" }, c.id), pill(c.status), h("span", { class: "muted small" }, "asked from ", rich(c.from_state))),
    h("p", { class: "gap" }, rich(c.claim)), h("p", { class: "small" }, h("b", null, "Predicted result: "), rich(c.predicted)),
    c.parts.length ? h("div", { class: "scroll" }, h("table", null, h("tr", null, h("th", null, "Part"), h("th", null, "Outcome"), h("th", null, "What came out")),
      c.parts.map(p => h("tr", null, h("td", null, p.part), h("td", null, h("span", { class: "pill " + (p.outcome === "met" ? "held" : p.outcome.startsWith("not met") ? "bad" : p.outcome === "reported" ? "idle" : "warn") }, p.outcome === "met" ? "held" : p.outcome.startsWith("not met") ? "did not hold" : p.outcome)),
        h("td", null, p.detail.length > 140 ? h("details", null, h("summary", null, p.detail.slice(0, 120) + "…"), h("pre", null, p.detail)) : p.detail))))) : h("p", { class: "muted" }, "No part has been run yet."),
    h("p", { class: "small muted gap" }, "Test file: ", h("code", null, c.file)));
  show(h("h1", null, "Claims"), versionTabs(o.stages, go),
    h("p", { class: "lede" }, "Each claim was written down with its predicted result before the model was asked. A red tile means the prediction was wrong, which is information about the model."),
    h("div", { class: "tiles" }, list.map(c => h("button", { class: "tile " + STATUS[c.status][0], "aria-pressed": String(cur && c.id === cur.id), onclick: () => { S.claim = c.id; go(); } }, h("b", null, c.id), h("small", null, STATUS[c.status][1])))),
    cur ? detail(cur) : h("p", { class: "empty" }, "No claims are registered for this model."));
}

// ---------------------------------------------------------------- runs
const TARGET = { "balance_control": "keep control", "not:OPEN_TAKEOVER": "rule out an open-weight AI takeover", "not:SILENT_TAKEOVER": "rule out a silent takeover", "balance_coexist": "keep peaceful coexistence", "not:CROWDED_OUT": "rule out humans being crowded out" };
async function runs() {
  const r = await api("/api/runs");
  const groups = {};
  for (const x of r.readings) {
    const g = x.variant, key = [x.alliance.join("+"), x.target, x.patterns.join(","), JSON.stringify(x.levels)].join("|");
    ((groups[g] = groups[g] || {})[key] = groups[g][key] || { x, cells: {} }).cells[x.goal] = x;
  }
  const cell = c => !c ? h("td", { class: "muted" }, "·") : c.kind !== "ok" ? h("td", { title: c.note }, h("span", { class: "pill warn" }, "did not fit")) :
    h("td", { title: `${dur(c.seconds)} · ${c.at}` }, h("span", { class: "pill " + (c.inside ? "held" : "bad") }, c.inside ? "inside" : "outside"));
  const who = a => a === "H" ? "Governments alone" : a === "H+L" ? "Governments with frontier AI companies" : a;
  const Q = r.queue, zone = e => [who(e.alliance.join("+")), " · ", TARGET[e.target] || e.target, e.patterns.length ? ` · ${e.patterns.join(", ")}` : "", Object.keys(e.levels).length ? " · AGI since s₀" : ""];
  const variant = e => e.variant === "default" ? "everything on" : "no open system";
  const item = (e, right) => h("div", { class: "qi" }, h("div", null, h("b", null, zone(e)), h("div", { class: "small muted" }, `${e.claim} · ${variant(e)} · ${GOAL_NAME[e.goal]} goal` + (e.worker ? ` · ${e.worker}` : ""))), h("div", { class: "qr" }, right));
  const by = k => Q.items.filter(e => e.status === k);
  const queuePanel = h("div", { class: "panel" }, h("h2", null, "Heavy-claims queue, v0.3"),
    h("div", { class: "stats" }, [["running", "running"], ["waiting", "waiting"], ["done", "done"]].map(([k, t]) => h("div", null, h("div", { class: "stat" }, Q.counts[k]), h("small", null, t)))),
    h("p", { class: "small muted gap" }, Q.workers.length ? Q.workers.map(w => `${w.name}: up ${dur(w.seconds)}, limit ${w.limit || "?"} GB`).join(" · ") : "No queue is running."),
    by("running").length ? [h("h3", { class: "gap" }, "Running"), by("running").map(e => item(e, [h("span", { class: "pill held" }, "running " + dur(e.seconds)), h("span", { class: "small muted" }, `${e.gb} of ${e.limit || "?"} GB` + (e.layer ? ` · layer ${e.layer.done} of ${e.layer.of}` : "")), e.layer ? h("progress", { max: e.layer.of, value: e.layer.done, style: "width:110px" }) : null]))] : null,
    by("waiting").length ? h("details", { open: by("waiting").length <= 8 }, h("summary", { class: "gap" }, h("b", null, `Waiting (${by("waiting").length})`)), by("waiting").map(e => item(e, [h("span", { class: "pill idle" }, "waiting " + dur(e.waiting_seconds)), h("span", { class: "small muted" }, (e.position === 0 ? "next" : `${e.position} ahead of it`) + (e.largest_limit_tried ? ` · did not fit in ${e.largest_limit_tried} GB` : "")),
      h("span", { class: "mv" }, [["top", "⤒", "Move to the top"], ["up", "▲", "Move up"], ["down", "▼", "Move down"]].map(([to, sign, tip]) => h("button", { title: tip, "aria-label": tip, onclick: () => post("/api/queue/move", { id: e.id, to }).then(() => runs()).catch(fail) }, sign)))]))) : null,
    by("waiting").length ? h("p", { class: "small muted" }, "Workers take waiting zones from the top. A zone that did not fit before waits for a worker with a larger memory limit.") : null,
    h("details", null, h("summary", { class: "gap" }, h("b", null, `Done (${by("done").length})`)), by("done").map(e => item(e, [h("span", { class: "pill " + (e.inside ? "held" : "bad") }, e.inside ? "inside" : "outside"), h("span", { class: "small muted" }, "took " + dur(e.seconds))]))));
  const C = r.claim_runs, zline = z => [who(z.alliance.join("+")), " · ", TARGET[z.target] || z.target, Object.keys(z.levels).length ? " · AGI since s₀" : "", ` · ${GOAL_NAME[z.goal] || z.goal} goal`];
  const claimPanel = h("div", { class: "panel" }, h("h2", null, "Heavy claims running now, v0.4"),
    h("div", { class: "stats" }, [[C.running.length, "claims running"], [C.waiting.length, "runs waiting"]].map(([n, t]) => h("div", null, h("div", { class: "stat" }, n), h("small", null, t)))),
    C.running.length ? C.running.map(c => h("div", { class: "gap" },
      h("div", { class: "qi" }, h("div", null, h("b", null, "Claim " + c.claim), h("div", { class: "small muted" }, `started ${dur(c.seconds)} ago · memory limit ${c.limit || "?"} GB`)),
        h("div", { class: "qr" }, c.zone ? [h("span", { class: "pill held" }, "zone running " + dur(c.zone.seconds)), h("span", { class: "small muted" }, `${c.zone.gb} GB · ${c.zone.engine}` + (c.zone.layer ? ` · layer ${c.zone.layer.done} of ${c.zone.layer.of}` : " · no layer finished yet")), c.zone.layer ? h("progress", { max: c.zone.layer.of, value: c.zone.layer.done, style: "width:110px" }) : null] : h("span", { class: "pill idle" }, "between zones"))),
      c.finished.length ? h("details", { id: "claim-" + c.claim }, h("summary", { class: "small" }, `Finished in this run (${c.finished.length})`), c.finished.map(z => z.part ? h("div", { class: "qi" }, h("div", { class: "small" }, z.part), h("div", { class: "qr" }, h("span", { class: "pill " + (z.outcome === "not computed" ? "warn" : z.outcome === "not met" ? "bad" : "held"), title: z.note }, z.outcome === "not computed" ? "did not fit" : z.outcome), z.seconds ? h("span", { class: "small muted" }, "took " + dur(z.seconds)) : null)) : h("div", { class: "qi" }, h("div", { class: "small" }, zline(z)), h("div", { class: "qr" }, z.kind === "ok" ? [h("span", { class: "pill " + (z.inside ? "held" : "bad") }, z.inside ? "inside" : "outside"), h("span", { class: "small muted" }, "took " + dur(z.seconds))] : [h("span", { class: "pill warn", title: z.note }, "did not fit"), h("span", { class: "small muted" }, `${z.limit} GB` + (z.core ? ` · ${z.core === "sylvan" ? "multi-core engine" : "single-core engine"}` : ""))])))) : null)) : h("p", { class: "muted gap" }, "No v0.4 claim is running."),
    C.waiting.length ? [h("h3", { class: "gap" }, "Waiting, in this order"), C.waiting.map((w, n) => h("div", { class: "qi" }, h("div", null, h("b", null, "Claim " + w.claim), w.note ? h("div", { class: "small muted" }, w.note) : null), h("div", { class: "qr" }, h("span", { class: "pill idle" }, n === 0 ? "next" : `${n} ahead of it`), h("span", { class: "small muted" }, `memory limit ${w.limit} GB`))))] : null);
  show(h("h1", null, "Runs"),
    h("p", { class: "lede" }, "The queue of heavy claims with running and waiting times, the saved guarantee-zone readings, and the logs. This page refreshes every 15 seconds."),
    r.requests.length ? h("div", { class: "panel" }, h("h2", null, "Your requests"), r.requests.map(q => h("div", { class: "qi" }, h("div", null, h("b", null, `Request ${q.id}` + (q.version ? ` · ${q.version}` : "")), h("div", { class: "small muted", style: "white-space:pre-line" }, q.text.replace(/\n+/g, "\n"))),
      h("div", { class: "qr" }, q.running ? [h("span", { class: "pill held" }, "running " + dur(q.running.seconds)), h("span", { class: "small muted" }, q.running.gb + " GB")] : h("span", { class: "pill idle" }, q.status === "new" ? "not started" : q.status), h("span", { class: "small muted" }, "asked " + q.created))))) : null,
    r.requests.length ? h("div", { class: "gap" }) : null, claimPanel,
    h("div", { class: "gap" }), queuePanel,
    h("div", { class: "panel gap" }, h("h2", null, "Processes"), r.live.length ? h("div", { class: "scroll" }, h("table", null, h("tr", null, h("th", null, "What"), h("th", null, "Running for"), h("th", null, "Memory")),
      r.live.map(p => h("tr", null, h("td", null, h("code", null, p.what), " ", h("span", { class: "muted small" }, p.args)), h("td", null, dur(p.seconds)), h("td", null, p.gb + " GB"))))) : h("p", { class: "muted" }, "Nothing is running.")),
    h("div", { class: "panel gap" }, h("h2", null, "Guarantee-zone readings, v0.3"),
      h("p", { class: "small muted" }, "Is the start state inside the zone where this alliance can guarantee the condition, whatever everyone else and chance do? One column per AI goal. A dot means not computed yet."),
      Object.keys(groups).length ? Object.entries(groups).map(([g, rows]) => h("div", { class: "scroll gap" }, h("span", { class: "tag" }, "model variant: " + g),
        h("table", null, h("tr", null, h("th", null, "Alliance"), h("th", null, "Can it guarantee to…"), GOALS.map(x => h("th", null, GOAL_NAME[x]))),
          Object.values(rows).map(({ x, cells }) => h("tr", null, h("td", null, who(x.alliance.join("+"))),
            h("td", null, TARGET[x.target] || x.target, x.patterns.length ? h("span", { class: "muted small" }, " · " + x.patterns.join(", ")) : null, Object.keys(x.levels).length ? h("span", { class: "muted small" }, " · from " + Object.entries(x.levels).map(([k, v]) => `${k} = ${v}`).join(", ")) : null),
            GOALS.map(g2 => cell(cells[g2]))))))) : h("p", { class: "muted" }, "No reading saved yet.")),
    h("div", { class: "panel gap" }, h("h2", null, "Logs"), r.logs.map(l => h("details", null, h("summary", null, h("code", null, l.name), h("span", { class: "muted small" }, ` · ${l.modified} · ${l.lines} lines · `), h("a", { href: file("reports/" + l.name), target: "_blank" }, "open")), h("pre", null, l.tail.join("\n"))))));
}

// ---------------------------------------------------------------- states
async function states() {
  const s = await api("/api/states");
  const names = (await api("/api/model?version=v0.3")).variables;
  const ladder = Object.keys(s.s0.levels).map(k => {
    const v = names.find(x => x.name === k) || { levels: [s.s0.levels[k]], plain: "" }, ind = s.indicators[k], alt = (s.s0.uncertain[k] || [])[1];
    const moved = s.s0.levels[k] !== s.srt.levels[k];
    const facts = ind ? (ind.indicators || (ind.levels || []).flatMap(l => l.indicators || [])) : [];
    return [h("div", { class: "name" + (moved ? " changed" : "") }, v.plain || k, h("small", null, k)),
      h("div", null, h("div", { class: "rungs" }, v.levels.map(l => h("span", { class: "rung" + (l === s.s0.levels[k] ? " s0" : "") + (l === s.srt.levels[k] ? " srt" : "") + (l === alt ? " alt" : ""), title: l === alt ? "the uncertain reading's other candidate" : "" }, l))),
        facts.length ? h("details", { class: "small" }, h("summary", null, `${facts.length} indicator${facts.length > 1 ? "s" : ""}` + (ind.confidence ? ` · confidence ${ind.confidence}` : "")), facts.map(f => h("p", { style: "margin:6px 0" }, f.value, h("br"), h("span", { class: "muted" }, `${f.source}${f.observed ? " · observed " + f.observed : ""}`)))) : null)];
  });
  show(h("h1", null, "S0 and Srt"),
    h("p", { class: "lede" }, "Two start states. S0 is the fixed reference every claim is computed from. Srt is our reading of the real world, which moves as the world does."),
    h("div", { class: "grid g2" },
      h("div", { class: "panel" }, h("span", { class: "tag" }, "S0 · reference start state"), h("h2", null, "Frozen on " + s.s0.frozen), h("p", { class: "small" }, s.s0.note)),
      h("div", { class: "panel" }, h("span", { class: "tag" }, "Srt · real-time state"), h("h2", null, "Last reviewed " + (s.srt.reviewed || s.srt.date)), h("p", { class: "small muted" }, "Levels last changed " + s.srt.date + "."), h("p", { class: "small" }, s.srt.note))),
    h("div", { class: "panel gap" }, h("div", { class: "legend", style: "margin-bottom:10px" }, h("span", null, h("span", { class: "rung s0" }, "level"), " S0"), h("span", null, h("span", { class: "rung srt" }, "level"), " Srt"), h("span", null, h("span", { class: "rung s0 srt" }, "level"), " both"), h("span", null, h("span", { class: "rung alt" }, "level"), " the other candidate of an uncertain reading")),
      h("div", { class: "ladders" }, ladder.flat())),
    h("div", { class: "panel gap" }, h("h2", null, "History of Srt"), h("table", null, h("tr", null, h("th", null, "Date"), h("th", null, "Change"), h("th", null, "Sources"), h("th", null, "Approved")),
      s.srt.history.map(x => h("tr", null, h("td", null, x.date), h("td", null, x.change), h("td", null, (x.sources || []).map(u => h("div", null, h("code", null, u)))), h("td", null, x.approved || ""))))));
}

// ---------------------------------------------------------------- explore
const E = { version: "v0.1", goal: "self_preserving", origin: "s0", knobs: {}, hist: [], rounds: [], pos: 0, choice: {}, model: null, busy: "", note: "" };
const ask = () => ({ version: E.version, goal: E.goal, origin: E.origin, knobs: E.knobs });
async function exploreStart() {
  E.model = await api(`/api/model?version=${E.version}&knobs=${encodeURIComponent(JSON.stringify(E.knobs))}`);
  E.hist = [await post("/api/sim/begin", ask())]; E.rounds = []; E.pos = 0; E.choice = {}; E.note = "";
}
async function explore() {
  const o = await api("/api/overview");
  STEP = (o.stages.find(s => s.id === E.version) || {}).step_months || 3;
  if (!E.hist.length) await exploreStart();
  const requests = await api("/api/store/requests");
  const cur = E.hist[E.pos], prev = E.pos ? E.hist[E.pos - 1] : null, m = E.model;
  const redo = async () => { E.hist = []; await explore().catch(fail); };
  const sel = (value, options, set) => h("select", { onchange: e => { set(e.target.value); redo(); } }, options.map(([v, t]) => h("option", { value: v, selected: v === value }, t)));
  const play = async () => {
    const move = cur.available.map(a => E.choice[a.actor] ?? a.actions[0].i);
    try { const next = await post("/api/sim/step", { ...ask(), state: cur.state, move }); E.hist = E.hist.slice(0, E.pos + 1).concat(next); E.rounds = E.rounds.slice(0, E.pos).concat([next.played]); E.pos++; E.choice = {}; E.note = ""; } catch (e) { E.note = e.message; }
    explore().catch(fail);
  };
  const search = async target => {
    E.busy = "Searching for a shortest path…"; explore();
    try { const r = await post("/api/sim/shortest", { ...ask(), target });
      if (r.found) { E.hist = r.path; E.rounds = r.rounds; E.pos = 0; E.note = `A shortest path of ${r.rounds.length} ${unit()}s, found in ${r.seconds} s. It shows what can happen if everyone plays into it: a possibility, not a finding.`; }
      else E.note = r.error || `No path within the search length (${(o.stages.find(s => s.id === E.version) || {}).search_length || 24} ${unit()}s).`; } catch (e) { E.note = e.message; }
    E.busy = ""; explore().catch(fail);
  };
  const shown = m.variables.filter(v => v.origin === "var" && !["a_objective"].includes(v.name));
  const ladder = shown.flatMap(v => { const now = cur.levels[v.name], was = prev && prev.levels[v.name];
    return [h("div", { class: "name" + (prev && was !== now ? " changed" : "") }, v.plain || v.name), h("div", { class: "rungs" }, v.levels.length > 8 ? h("span", { class: "rung now" }, now) : v.levels.map(l => h("span", { class: "rung" + (String(l) === now ? " now" : prev && String(l) === was ? " was" : "") }, l)))]; });
  const target = h("select", null, m.endings.map(e => h("option", { value: e.name }, "reach: " + (e.plain || e.name))), m.conditions.map(c => h("option", { value: "break:" + c.name }, "break: " + (c.plain || c.name))));
  const req = h("textarea", { id: "req", placeholder: "Ask for a run or an exploration, for example: on v0.1, can governments alone keep control if oversight starts strong?" });
  show(h("h1", null, "Explore"),
    h("p", { class: "lede" }, "Step any model by hand from S0 or Srt, or search it for a shortest path. Older, smaller models are quick to inspect and easier to discuss."),
    h("div", { class: "panel row" }, h("label", null, "Model ", sel(E.version, o.stages.map(s => [s.id, s.title]), v => { E.version = v; E.knobs = {}; if (!o.stages.find(s => s.id === v).goals.includes(E.goal)) E.goal = "self_preserving"; })),
      h("label", null, "AI goal ", sel(E.goal, o.stages.find(s => s.id === E.version).goals.map(g => [g, GOAL_NAME[g]]), v => { E.goal = v; })), h("label", null, "Start from ", sel(E.origin, [["s0", "S0"], ["srt", "Srt"]], v => { E.origin = v; })),
      m.knob_spec.filter(k => k.kind === "bool").map(k => h("label", { class: "small row" }, h("input", { type: "checkbox", checked: m.knobs[k.name], onchange: e => { E.knobs[k.name] = e.target.checked; redo(); } }), h("code", null, k.name))),
      h("button", { onclick: redo }, "Restart")),
    h("div", { class: "panel gap" }, h("div", { class: "row" }, h("h2", { style: "margin:0" }, "Path"), target, h("button", { onclick: () => search(target.value), disabled: !!E.busy }, "Find a shortest path"), h("span", { class: "muted small" }, E.busy)),
      E.note ? h("p", { class: "small gap" }, E.note) : null,
      h("div", { class: "strip gap" }, E.hist.map((v, i) => h("button", { class: "q" + (v.ending ? " end" : ""), "aria-pressed": String(i === E.pos), onclick: () => { E.pos = i; E.choice = {}; explore(); } },
        h("b", null, `${quarter(v.levels.tick)}`), i ? E.rounds[i - 1].filter(a => !/\.(idle|stand_by|none|record)$/.test(a)).map(a => h("div", null, a)) : "start", v.ending ? h("div", null, h("b", null, v.ending)) : null)))),
    h("div", { class: "grid gap", style: "grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);align-items:start" },
      h("div", { class: "panel" }, h("div", { class: "row" }, h("h2", { style: "margin:0" }, `State at ${quarter(cur.levels.tick)}`), h("span", { class: "muted small" }, `${unit()} ${cur.levels.tick}`)),
        h("div", { class: "lights gap" }, Object.entries(cur.conditions).map(([k, ok]) => h("span", { class: "pill " + (ok ? "held" : "bad") }, (m.conditions.find(c => c.name === k) || {}).plain || k))),
        cur.ending ? h("div", { class: "banner gap " + (cur.ending === "COEXIST" || cur.ending === "CONTAINED" ? "held" : "bad") }, "Ending: " + ((m.endings.find(e => e.name === cur.ending) || {}).plain || cur.ending)) : null,
        h("div", { class: "ladders gap" }, ladder)),
      h("div", { class: "panel" }, h("h2", null, cur.terminal ? "The path has ended" : `Choose this ${unit()}'s round`),
        cur.terminal ? h("p", { class: "muted" }, "Pick an earlier quarter in the path to branch from it.") : [h("div", { class: "players" }, cur.available.filter(a => a.actions.length > 1).map(a => h("div", { class: "player" }, h("h3", null, PLAYER[a.actor] || a.actor),
          a.actions.map((x, n) => h("label", null, h("input", { type: "radio", name: "p_" + a.actor, checked: (E.choice[a.actor] ?? a.actions[0].i) === x.i, onchange: () => { E.choice[a.actor] = x.i; } }), x.plain || x.name))))),
          h("div", { class: "row gap" }, h("button", { class: "main", onclick: play }, "Play this round"), h("span", { class: "muted small" }, "Players with a single available action are not shown."))])),
    h("div", { class: "panel gap" }, h("h2", null, "Requests"), h("p", { class: "small muted" }, "Pending runs and explore requests. They are read at the start of each working session."), req,
      h("div", { class: "row gap" }, h("button", { class: "main", onclick: async () => { if (req.value.trim()) { await post("/api/store/requests", { text: req.value.trim(), version: E.version }); explore(); } } }, "Add request")),
      requests.length ? h("table", { class: "gap" }, requests.slice().reverse().map(r => h("tr", null, h("td", { class: "muted small" }, r.created), h("td", null, r.text, r.answer ? h("div", { class: "small muted" }, "Answer: " + r.answer) : null), h("td", null, h("span", { class: "pill " + (r.status === "done" ? "held" : "idle") }, r.status))))) : null));
}

// ---------------------------------------------------------------- inbox
async function inbox() {
  const [news, requests, st] = await Promise.all([api("/api/store/news"), api("/api/store/requests"), api("/api/states")]);
  const f = { title: h("input", { type: "text", id: "n_title", placeholder: "Title" }), url: h("input", { type: "text", id: "n_url", placeholder: "Link" }), note: h("input", { type: "text", id: "n_note", placeholder: "Why it matters for Srt" }),
    variable: h("select", { id: "n_var" }, h("option", { value: "" }, "variable it bears on"), Object.keys(st.srt.levels).map(k => h("option", { value: k }, k))) };
  const set = (id, status) => post("/api/store/news", { id, status }).then(inbox);
  show(h("h1", null, "Inbox"),
    h("p", { class: "lede" }, "News, blogs and articles that bear on Srt, and your open requests. An accepted item is evidence for a change to Srt; the change itself is made and dated on the states page."),
    h("div", { class: "panel" }, h("h2", null, "Add an item"), h("div", { class: "grid g3" }, f.title, f.url, f.variable), h("div", { class: "row gap" }, f.note, h("button", { class: "main", onclick: async () => { if (f.title.value.trim()) { await post("/api/store/news", { title: f.title.value, url: f.url.value, variable: f.variable.value, note: f.note.value, source: "added by hand" }); inbox(); } } }, "Add"))),
    h("div", { class: "panel gap" }, h("h2", null, `News (${news.length})`), news.length ? h("table", null, news.slice().reverse().map(n => h("tr", null, h("td", { class: "muted small" }, n.date || n.created), h("td", null, n.url ? h("a", { href: n.url, target: "_blank", rel: "noopener" }, n.title) : n.title, h("div", { class: "small muted" }, [n.source, n.variable && "bears on " + n.variable, n.effect, n.note].filter(Boolean).join(" · "))),
      h("td", null, h("span", { class: "pill " + (n.status === "accepted" ? "held" : n.status === "rejected" ? "bad" : "idle") }, n.status)), h("td", null, h("div", { class: "row" }, h("button", { onclick: () => set(n.id, "accepted") }, "Accept"), h("button", { onclick: () => set(n.id, "rejected") }, "Reject")))))) :
      h("p", { class: "empty" }, "Nothing here yet. Collection every 12 hours starts once the sources are chosen; until then, add items by hand above.")),
    h("div", { class: "panel gap" }, h("h2", null, `Requests (${requests.length})`), requests.length ? h("table", null, requests.slice().reverse().map(r => h("tr", null, h("td", { class: "muted small" }, r.created), h("td", null, r.text), h("td", null, h("span", { class: "pill " + (r.status === "done" ? "held" : "idle") }, r.status))))) : h("p", { class: "empty" }, "No requests. Add one from the Explore page.")));
}

// ---------------------------------------------------------------- glossary
let glossaryData = null;
async function glossary() {
  glossaryData = glossaryData || await api("/api/glossary");
  const q = h("input", { type: "text", id: "gq", placeholder: "Search a word, a code name or a symbol", style: "width:100%;font-size:16px;padding:9px 12px" }), list = h("div");
  const draw = () => { const words = q.value.toLowerCase().split(/\s+/).filter(Boolean);
    const hits = glossaryData.filter(e => words.every(w => [e.term, e.code.join(" "), e.also.join(" "), e.meaning, e.note].join(" ").toLowerCase().includes(w)));
    list.replaceChildren(h("p", { class: "muted small gap" }, `${hits.length} of ${glossaryData.length} terms`), h("table", null, hits.map(e => h("tr", null, h("td", { style: "width:240px" }, h("b", null, e.term), h("div", null, e.code.map(c => h("code", { style: "margin-right:3px" }, c))), h("div", { class: "muted small" }, e.category)),
      h("td", null, rich(e.meaning), e.also.length ? h("div", { class: "small muted" }, "Also called: " + e.also.join(", ")) : null, e.note ? h("div", { class: "small muted" }, rich(e.note)) : null))))); };
  q.addEventListener("input", draw);
  show(h("h1", null, "Glossary"), h("p", { class: "lede" }, "Every term, with its name in the code and the other words that have been used for it. ", h("a", { href: file("docs/agi_glossary.html"), target: "_blank" }, "Full page →")), q, list);
  draw();
}

// ---------------------------------------------------------------- router
// ---------------------------------------------------------------- evidence
async function evidence() {
  const E2 = await api("/api/evidence"), rv = E2.reviews[0], R = rv && rv.result, PARTS = ["directness", "power", "reach", "reasoning", "corroboration"];
  const bar = (a, b) => { const t = a + b || 1; return h("div", { class: "bar", style: "height:12px" }, h("span", { class: "b-held", style: `width:${100 * a / t}%`, title: "side A" }), h("span", { class: "b-warn", style: `width:${100 * b / t}%`, title: "side B" })); };
  const cardRow = c => h("details", { id: "ev-" + c.id }, h("summary", null, h("b", null, c.score.toFixed(1)), " · ", c.actor, h("span", { class: "muted small" }, ` · ${c.source_type} · ${c.date}`), c.flags.length ? h("span", { class: "pill warn", style: "margin-left:8px" }, "flagged") : null),
    h("p", { class: "small" }, c.claim, " ", h("a", { href: c.url, target: "_blank" }, "source →")),
    h("blockquote", { class: "small", style: "margin:6px 0;padding:6px 10px;border-left:3px solid var(--line)" }, c.quote),
    c.note ? h("p", { class: "small muted" }, c.note) : null,
    h("div", { class: "scroll" }, h("table", { class: "small" }, h("tr", null, h("th", null, "Part"), h("th", null, "Scorer 1"), h("th", null, "Scorer 2")),
      PARTS.map(p => h("tr", null, h("td", null, p), h("td", null, h("b", null, c.scores[0][p]), " ", c.reasons[0][p]), h("td", null, h("b", null, c.scores[1][p]), " ", c.reasons[1][p]))))),
    c.flags.length ? h("p", { class: "small" }, h("b", null, "Flagged: "), c.flags.join("; ")) : null);
  const side = (q, k) => { const s = q.sides[k], cards = R.cards.filter(c => c.question === q.id && c.side === k);
    return h("div", { class: "panel" }, h("div", { class: "row" }, h("h3", { style: "margin:0" }, `Side ${k}`), h("span", { class: "stat", style: "font-size:22px" }, s.total.toFixed(1))),
      h("p", { class: "small" }, s.text),
      s.events.map(e => h("div", { class: "gap" }, h("div", { class: "row" }, h("b", { class: "small" }, e.event), h("span", { class: "muted small" }, `${e.score.toFixed(1)} · ${e.audience}` + (e.counted ? "" : " · over the cap for one actor, not counted"))),
        cards.filter(c => e.cards.includes(c.id)).map(cardRow)))); };
  show(h("h1", null, "Evidence"),
    h("p", { class: "lede" }, "Readings of the real world by two-sided evidence. Each question has two sides, searched the same way and scored on cards by two scorers who do not see each other. A rule proposes a change to Srt; you approve it and audit a sample of cards."),
    !R ? h("div", { class: "panel" }, h("p", { class: "muted" }, rv ? `The review of ${rv.review} has ${rv.cards} cards collected and is being scored.` : "No review yet.")) : [
      h("p", { class: "small muted" }, `Review of ${R.review}: ${R.cards.length} cards, ${R.flagged.length} flagged. The collector and the scorers are AI models made by one of the frontier companies under assessment; every score keeps its quoted passage and reasons so that it can be checked.`),
      R.questions.map(q => [h("h2", { class: "gap", style: "margin-top:26px" }, q.question),
        h("div", { class: "panel" }, h("div", { class: "row" }, h("span", { class: "tag" }, q.kind), q.srt ? h("span", { class: "muted small" }, "Srt today: " + q.srt) : null),
          h("div", { class: "gap" }, bar(q.sides.A.total, q.sides.B.total)), h("p", { class: "small" }, `Side A ${q.sides.A.total.toFixed(1)} · side B ${q.sides.B.total.toFixed(1)}` + (q.share_of_side_A == null ? "" : ` · side A holds ${Math.round(100 * q.share_of_side_A)}%`)),
          h("p", null, h("b", null, "Proposal: "), q.proposal),
          h("div", { class: "scroll" }, h("table", { class: "small" }, h("tr", null, h("th", null, "Audience"), h("th", null, "Side A"), h("th", null, "Side B")), Object.entries(q.by_audience).map(([a, [x, y]]) => h("tr", null, h("td", null, a), h("td", null, x.toFixed(1)), h("td", null, y.toFixed(1))))))),
        h("div", { class: "grid g2 gap" }, side(q, "A"), side(q, "B")),
        (() => { const out = R.cards.filter(c => c.question === q.id && !c.side); return out.length ? h("div", { class: "panel gap" }, h("h3", null, `Left out of the totals (${out.length})`), h("p", { class: "small muted" }, "The scorers disagreed on the side, or found the card supports neither."), out.map(cardRow)) : null; })()])],
    h("div", { class: "panel gap" }, h("h2", null, "The method"), h("p", { class: "small muted" }, E2.rubric.registered),
      h("div", { class: "scroll" }, h("table", { class: "small" }, h("tr", null, h("th", null, "Part"), [0, 1, 2, 3].map(n => h("th", null, String(n)))), Object.entries(E2.rubric.parts).map(([k, v]) => h("tr", null, h("td", null, h("b", null, k)), [0, 1, 2, 3].map(n => h("td", null, v[n])))))),
      ["card_score", "two_passes", "events", "cap"].map(k => h("p", { class: "small" }, h("b", null, k.replace("_", " ") + ": "), E2.rubric[k])),
      Object.entries(E2.rubric.proposal_rule).map(([k, v]) => h("p", { class: "small" }, h("b", null, k + ": "), v))),
    rv && rv.log ? h("div", { class: "panel gap" }, h("details", null, h("summary", null, h("b", null, `Search log (${rv.log.queries.length} queries)`)), h("div", { class: "scroll" }, h("table", { class: "small" }, h("tr", null, ["Source", "Question", "Side", "Query", "Returned"].map(t => h("th", null, t))),
      rv.log.queries.map(l => h("tr", null, h("td", null, l.source), h("td", null, l.question), h("td", null, l.side), h("td", null, l.query, l.note ? h("div", { class: "muted" }, l.note) : null), h("td", null, String(l.returned)))))), rv.log.notes.map(n => h("p", { class: "small muted" }, n)))) : null);
}
const PAGES = { overview, models, claims, runs, states, explore, inbox, evidence, glossary };
function go() {
  const page = (location.hash || "#overview").slice(1).split("/")[0];
  document.querySelectorAll("nav a").forEach(a => a.classList.toggle("on", a.dataset.page === page));
  clearInterval(timer);
  if (page === "runs" || page === "overview") timer = setInterval(() => { if (!document.hidden) (PAGES[page])().catch(() => {}); }, 15000);
  (PAGES[page] || overview)().catch(fail);
}
window.addEventListener("hashchange", () => { window.scrollTo(0, 0); go(); });
window.addEventListener("error", e => fail(e.error || e.message));
window.addEventListener("unhandledrejection", e => fail(e.reason));
if (location.search.includes("shot")) document.body.append(h("img", { src: "/hold?ms=2500", alt: "", hidden: true }));
setTimeout(() => { document.getElementById("navfoot").textContent = "Page version " + (window.BUILD ? new Date(window.BUILD * 1000).toLocaleString() : "unknown"); }, 0);
go();
