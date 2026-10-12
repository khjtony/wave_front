/* Visualizer page script. Plain functions, no framework. The embedded bundle is the only
   data source and the filter state S is the only view state: every view is re-rendered
   from (B, S). Model strings are inserted with textContent / createTextNode only. */
(function () {
  'use strict';

  const B = JSON.parse(document.getElementById('bundle').textContent);
  // The SVG namespace, taken from an inline <svg> so the page holds no URL at all.
  const SVGNS = document.getElementById('svg-ns').namespaceURI;

  const STATUS = ['kept', 'contested', 'lost', 'failed'];
  const STATUS_MEANING = [
    'inside the kernel: the coalition can keep the property whatever the others do',
    'contested: neither the coalition nor the rest can force the outcome',
    'lost: the rest can force the property false',
    'failed: the property is false in this state',
  ];
  const DECISION = ['safe', 'risky', 'losing', 'ends'];
  const DECISION_MEANING = [
    'every completion stays inside the kernel',
    'some completion leaves the kernel',
    'every completion leaves the kernel',
    'every completion ends the game',
  ];
  const TICK = B.meta.timed ? 'tick' : 'step';
  const NA = B.actors.length;
  const NC = B.coalitions.length;
  const H = B.hypotheses.items;
  const FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif';
  const PENDING = pendingIndex();

  // ---------------------------------------------------------------- view state
  const S = {
    hyp: B.meta.default.hypothesis,
    coal: B.meta.default.coalition,
    ending: B.meta.default.ending,
    prop: 'auto',
    trace: 'ref',
    tick: 0,
    cf: null,
    choice: {},
    compare: null,
    lvar: defaultLandscapeVar(),
    lmode: 'status',
    lby: NC,
    lfocus: 0,
    builtins: false,
    tables: {},
    allTables: false,
    isoStatus: null,
    isoActor: null,
    theme: loadTheme(),
  };
  readHash();
  let C = null; // resolved colors for the current theme

  // ---------------------------------------------------------------- small helpers
  function $(id) { return document.getElementById(id); }

  function append(node, kids) {
    if (kids == null) return node;
    if (!Array.isArray(kids)) kids = [kids];
    for (const k of kids) {
      if (k == null || k === false) continue;
      node.appendChild(typeof k === 'object' ? k : document.createTextNode(String(k)));
    }
    return node;
  }

  function h(tag, props, kids) {
    const e = document.createElement(tag);
    if (props) {
      for (const k of Object.keys(props)) {
        const v = props[k];
        if (v == null || v === false) continue;
        if (k === 'text') e.textContent = String(v);
        else if (k === 'cls') e.className = v;
        else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), v);
        else e.setAttribute(k, v === true ? '' : String(v));
      }
    }
    return append(e, kids);
  }

  function sv(tag, attrs, kids) {
    const e = document.createElementNS(SVGNS, tag);
    if (attrs) {
      for (const k of Object.keys(attrs)) {
        const v = attrs[k];
        if (v == null || v === false) continue;
        if (k === 'text') e.textContent = String(v);
        else if (k.slice(0, 2) === 'on') e.addEventListener(k.slice(2), v);
        else e.setAttribute(k, String(v));
      }
    }
    return append(e, kids);
  }

  function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); return node; }

  function fmtInt(n) { return Number(n).toLocaleString('en-US'); }

  function plural(n, word) { return n + ' ' + word + (n === 1 ? '' : 's'); }

  const MCTX = document.createElement('canvas').getContext('2d');
  function textWidth(text, size, weight) {
    MCTX.font = (weight || 400) + ' ' + (size || 11) + 'px ' + FONT;
    return MCTX.measureText(text).width;
  }
  // Shorten with an ellipsis to fit; never crop a glyph. Returns '' when nothing fits.
  function fitText(text, width, size, weight) {
    if (textWidth(text, size, weight) <= width) return text;
    let lo = 0;
    let hi = text.length;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (textWidth(text.slice(0, mid) + '…', size, weight) <= width) lo = mid;
      else hi = mid - 1;
    }
    return lo >= 2 ? text.slice(0, lo) + '…' : '';
  }

  // ---------------------------------------------------------------- colors
  function readColors() {
    const cs = getComputedStyle(document.documentElement);
    const v = (n) => cs.getPropertyValue(n).trim();
    const range = (n, f) => Array.from({ length: n }, (_, i) => f(i));
    return {
      page: v('--page'), surface: v('--surface'), chip: v('--chip'), ink: v('--ink'),
      ink2: v('--ink-2'), muted: v('--muted'), grid: v('--grid'), axis: v('--axis'),
      wash: v('--wash'), nature: v('--nature'),
      st: range(4, (i) => v('--st' + i)),
      slot: range(8, (i) => v('--s' + (i + 1))),
      ramp: range(10, (i) => v('--r' + i)),
    };
  }

  function rgb(hex) {
    const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
    if (!m) return [128, 128, 128];
    const n = parseInt(m[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function luminance(hex) {
    const c = rgb(hex).map((x) => {
      const s = x / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }

  // Ink or white on a fill, whichever contrasts more.
  function onFill(hex) {
    const L = luminance(hex);
    return (L + 0.05) / 0.05 >= 1.05 / (L + 0.05) ? '#0b0b0b' : '#ffffff';
  }

  function actorColor(i) {
    const a = B.actors[i];
    if (a.is_nature || a.color_slot == null || a.color_slot > 8) return C.nature;
    return C.slot[a.color_slot - 1];
  }

  // Ordinal ramp: n levels spread over the ten validated steps (light end first).
  function rampColor(i, n) {
    if (n <= 1) return C.ramp[4];
    return C.ramp[Math.round((i * 9) / (n - 1))];
  }

  function seqColor(v, max) {
    if (max <= 0) return C.ramp[0];
    return C.ramp[Math.max(0, Math.min(9, Math.round((v / max) * 9)))];
  }

  // ---------------------------------------------------------------- bundle accessors
  function pendingIndex() {
    // per actor: [{action, var}] for delayed actions
    const out = B.actors.map(() => []);
    B.actors.forEach((a, i) => a.actions.forEach((x, j) => {
      if (x.delay > 0) {
        const name = 'pending_' + a.name + '_' + x.name;
        const v = B.variables.findIndex((w) => w.name === name);
        if (v >= 0) out[i].push({ action: j, v: v });
      }
    }));
    return out;
  }

  function defaultLandscapeVar() {
    const vars = B.variables;
    let i = vars.findIndex((v) => !v.builtin && !v.swept && v.origin === 'var' && v.levels.length > 2);
    if (i < 0) i = vars.findIndex((v) => !v.builtin && !v.swept);
    if (i < 0) i = vars.findIndex((v) => !v.swept);
    return Math.max(0, i);
  }

  function propIndex() {
    if (S.prop !== 'auto') return Number(S.prop);
    const e = B.endings[S.ending];
    let i = B.properties.findIndex((p) => p.kind === 'avoid' && p.name === e);
    if (i < 0) i = B.properties.findIndex((p) => p.kind === 'invariant');
    if (i < 0) i = B.properties.length ? 0 : -1;
    return i;
  }

  function propLabel(p) { return p >= 0 ? B.properties[p].label : 'no property'; }

  function status(s, c, p) {
    if (c == null) c = S.coal;
    if (p == null) p = propIndex();
    if (p < 0) return -1;
    return B.states.status[p][c].charCodeAt(s) - 48;
  }

  function value(v, s) { return B.states.values[v][s]; }

  function level(v, x) {
    const L = B.variables[v].levels;
    return x >= 0 && x < L.length ? L[x] : String(x);
  }

  function endingOf(s) {
    const k = B.states.ending[s];
    return k >= 0 ? B.all_endings[k] : null;
  }

  function tickOf(s) { return B.states.tick[s]; }

  function rankOf(e, c, s) {
    const per = B.states.rank[e];
    return per ? per[c][s] : -1;
  }

  function actionName(i, j) { return B.actors[i].actions[j].name; }

  function coalName(c) { return B.coalitions[c].name; }

  function hypLabel(h) { return H[h].label; }

  function shownVars() {
    return B.variables.map((v, i) => i).filter((i) => S.builtins || !B.variables[i].builtin);
  }

  function refEntry(hyp, e) {
    const name = B.endings[e];
    return B.traces.find((t) => t.hypothesis === hyp && t.ending === name) || null;
  }

  function traceOptions() {
    const out = [];
    const e = B.endings[S.ending];
    const ref = refEntry(S.hyp, S.ending);
    if (ref && ref.states) out.push({ key: 'ref', label: 'Shortest trace to ' + e });
    H.forEach((_, other) => {
      if (other === S.hyp) return;
      const t = refEntry(other, S.ending);
      if (t && t.states && t.replays.some((r) => r.hypothesis === S.hyp)) {
        out.push({ key: 'replay:' + other, label: 'Moves of the ' + hypLabel(other) + ' trace, replayed here' });
      }
    });
    return out;
  }

  // A trace object: {key, label, short, hyp, states, moves, stop}
  function getTrace(key) {
    if (key === 'ref') {
      const t = refEntry(S.hyp, S.ending);
      if (!t || !t.states) return null;
      return {
        key: 'ref', hyp: S.hyp, states: t.states, moves: t.moves, stop: null,
        label: 'shortest trace from ' + hypLabel(S.hyp) + ' to ' + B.endings[S.ending],
        short: 'shortest trace to ' + B.endings[S.ending],
      };
    }
    if (key && key.indexOf('replay:') === 0) {
      const other = Number(key.slice(7));
      const t = refEntry(other, S.ending);
      if (!t || !t.states) return null;
      const r = t.replays.find((x) => x.hypothesis === S.hyp);
      if (!r) return null;
      return {
        key: key, hyp: S.hyp, states: r.states, moves: r.moves, stop: r.stop,
        label: 'moves of the ' + hypLabel(other) + ' trace to ' + B.endings[S.ending] + ', replayed under ' + hypLabel(S.hyp),
        short: 'replay of the ' + hypLabel(other) + ' trace',
      };
    }
    return null;
  }

  function noTraceText() {
    if (!B.endings.length) return 'The model offers no ending, so there is no reference trace; the decision tree below starts from the initial state.';
    return 'No play reaches ' + B.endings[S.ending] + ' from ' + hypLabel(S.hyp) + '. Choose another hypothesis or ending.';
  }

  function currentTrace() {
    let t = getTrace(S.trace);
    if (!t && S.trace !== 'ref') { S.trace = 'ref'; t = getTrace('ref'); }
    return t;
  }

  // ---------------------------------------------------------------- moves and classes
  function movesAt(s) {
    const k = B.moves.avail[s];
    if (k == null || k < 0) return null;
    return { avail: B.moves.avail_table[k], off: B.moves.offset[s] };
  }

  function forEachJoint(avail, fn) {
    const n = avail.map((a) => a.length);
    const total = n.reduce((a, b) => a * b, 1);
    const pos = new Array(n.length).fill(0);
    for (let k = 0; k < total; k++) {
      fn(k, pos);
      for (let i = n.length - 1; i >= 0; i--) {
        pos[i]++;
        if (pos[i] < n[i]) break;
        pos[i] = 0;
      }
    }
  }

  function successor(s, move) {
    const m = movesAt(s);
    if (!m) return null;
    let k = 0;
    for (let i = 0; i < m.avail.length; i++) {
      const p = m.avail[i].indexOf(move[i]);
      if (p < 0) return null;
      k = k * m.avail[i].length + p;
    }
    return B.moves.succ[m.off + k];
  }

  // Per actor, per available action: successor status counts and the decision class.
  function stepStats(s, c, p) {
    const m = movesAt(s);
    if (!m || p < 0) return null;
    const rows = m.avail.map((acts) => acts.map((a) => ({
      action: a, counts: [0, 0, 0, 0], succ: [], allTerminal: true, cls: 0,
    })));
    forEachJoint(m.avail, (k, pos) => {
      const t = B.moves.succ[m.off + k];
      const code = status(t, c, p);
      const term = B.states.terminal[t] === 1;
      for (let i = 0; i < pos.length; i++) {
        const r = rows[i][pos[i]];
        r.counts[code]++;
        r.succ.push(t);
        if (!term) r.allTerminal = false;
      }
    });
    for (const per of rows) {
      for (const r of per) {
        const total = r.succ.length;
        if (r.counts[0] === total) r.cls = 0;
        else if (r.allTerminal) r.cls = 3;
        else if (r.counts[0] === 0) r.cls = 2;
        else r.cls = 1;
      }
    }
    return rows;
  }

  function availAt(s) {
    const m = movesAt(s);
    return m ? m.avail : null;
  }

  function phases(states, c, p) {
    const out = { tK: null, tL: null, tPhi: null };
    if (p < 0) return out;
    states.forEach((s, k) => {
      const code = status(s, c, p);
      if (out.tK == null && code !== 0) out.tK = k;
      if (out.tL == null && code >= 2) out.tL = k;
      if (out.tPhi == null && code === 3) out.tPhi = k;
    });
    return out;
  }

  function firstFalse(states, q) {
    for (let k = 0; k < states.length; k++) if (status(states[k], 0, q) === 3) return k;
    return null;
  }

  function forkIndex(cf, tr, c, p) {
    if (!cf || !tr || p < 0) return null;
    for (let k = 0; k < cf.states.length && k < tr.states.length; k++) {
      if (status(cf.states[k], c, p) !== status(tr.states[k], c, p)) return k;
    }
    return null;
  }

  // ---------------------------------------------------------------- shared marks
  // Status icons drawn as shapes (font glyphs for half and quarter circles render
  // unreliably): kept a dot, contested a half-filled ring, lost a quarter-filled ring,
  // failed a cross.
  function iconInto(g, cx, cy, r, code, color) {
    if (code === 0) { g.appendChild(sv('circle', { cx: cx, cy: cy, r: r * 0.72, fill: color })); return; }
    if (code === 3) {
      const d = r * 0.72;
      g.appendChild(sv('path', { d: 'M' + (cx - d) + ' ' + (cy - d) + 'L' + (cx + d) + ' ' + (cy + d) + 'M' + (cx + d) + ' ' + (cy - d) + 'L' + (cx - d) + ' ' + (cy + d), stroke: color, 'stroke-width': 1.7, 'stroke-linecap': 'round', fill: 'none' }));
      return;
    }
    g.appendChild(sv('circle', { cx: cx, cy: cy, r: r - 0.6, fill: 'none', stroke: color, 'stroke-width': 1.2 }));
    const d = code === 1
      ? 'M' + cx + ' ' + (cy - r) + 'A' + r + ' ' + r + ' 0 0 0 ' + cx + ' ' + (cy + r) + 'Z'
      : 'M' + cx + ' ' + cy + 'L' + cx + ' ' + (cy - r) + 'A' + r + ' ' + r + ' 0 0 1 ' + (cx + r) + ' ' + cy + 'Z';
    g.appendChild(sv('path', { d: d, fill: color }));
  }

  function badge(code, label) {
    const col = C.st[code];
    const svg = sv('svg', { width: 16, height: 16, viewBox: '0 0 16 16', class: 'badge', 'aria-hidden': 'true' });
    svg.appendChild(sv('circle', { cx: 8, cy: 8, r: 8, fill: col }));
    iconInto(svg, 8, 8, 4.4, code, onFill(col));
    if (label) svg.appendChild(sv('title', { text: label }));
    return svg;
  }

  // A status cell: the fill, the icon and (when it fits) the label, in ink or white by fill.
  function statusCell(svg, x, y, w, hh, code, opacity, data) {
    const fill = C.st[code];
    const ink = onFill(fill);
    const g = sv('g', Object.assign({ opacity: opacity, 'data-status': code }, data || {}));
    g.appendChild(sv('rect', { x: x, y: y, width: w, height: hh, rx: 3, fill: fill }));
    const tw = textWidth(STATUS[code], 11, 600);
    const withText = w >= tw + 30;
    const cx = withText ? x + w / 2 - (tw + 14) / 2 + 5 : x + w / 2;
    iconInto(g, cx, y + hh / 2, 4.6, code, ink);
    if (withText) g.appendChild(sv('text', { x: cx + 9, y: y + hh / 2 + 4, 'font-size': 11, 'font-weight': 600, fill: ink, text: STATUS[code], 'pointer-events': 'none' }));
    svg.appendChild(g);
  }

  function statusText(code) {
    if (code < 0) return h('span', { cls: 'muted', text: 'n/a' });
    return h('span', { style: 'display:inline-flex;align-items:center;gap:5px' }, [badge(code), STATUS[code]]);
  }

  function decisionText(cls) {
    return h('span', { style: 'display:inline-flex;align-items:center;gap:5px' }, [badge(cls), DECISION[cls]]);
  }

  function svgBadge(g, cx, cy, code, r) {
    const col = C.st[code];
    g.appendChild(sv('circle', { cx: cx, cy: cy, r: r || 6.5, fill: col }));
    iconInto(g, cx, cy, (r || 6.5) * 0.62, code, onFill(col));
  }

  function lineKey(color) { return h('span', { cls: 'key-line', style: 'background:' + color }); }

  function statusLegend(extra) {
    const items = STATUS.map((name, code) => h('span', { cls: 'item', title: STATUS_MEANING[code] }, [badge(code), name]));
    return h('div', { cls: 'legend', 'aria-label': 'Status legend' }, items.concat(extra || []));
  }

  function actorLegend() {
    return h('div', { cls: 'legend', 'aria-label': 'Actors (click to isolate)' }, B.actors.map((a, i) => h('button', {
      type: 'button', cls: 'item' + (S.isoActor != null && S.isoActor !== i ? ' off' : ''),
      'aria-pressed': String(S.isoActor === i),
      onclick: () => { S.isoActor = S.isoActor === i ? null : i; render(); },
    }, [lineKey(actorColor(i)), a.name + (a.is_nature ? ' (events)' : '')])));
  }

  // ---------------------------------------------------------------- tooltips
  function tipShow(tip, body, x, y) {
    tip.style.display = 'block';
    const bw = body.clientWidth;
    const tw = tip.offsetWidth;
    const th = tip.offsetHeight;
    let left = x + 14;
    if (left + tw > bw) left = Math.max(0, x - tw - 14);
    let top = y + 14;
    const bh = Math.max(body.clientHeight, th);
    if (top + th > bh + 40) top = Math.max(0, y - th - 10);
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }

  function tipHide(tip) { if (tip) tip.style.display = 'none'; }

  function tipRow(tip, key, val, keyNode) {
    tip.appendChild(h('div', { cls: 't-row' }, [h('span', { cls: 'k' }, [keyNode, key]), h('span', { cls: 'v' }, val)]));
  }

  function tipSep(tip) { tip.appendChild(h('div', { cls: 't-sep' })); }

  function relPos(ev, body) {
    const r = body.getBoundingClientRect();
    return [ev.clientX - r.left, ev.clientY - r.top];
  }

  // The state tooltip shared by the board, the compare view and the landscape.
  function stateTip(tip, sid, move, title, extraRows) {
    clear(tip);
    tip.appendChild(h('div', { cls: 't-head', text: title }));
    const e = endingOf(sid);
    if (e) tip.appendChild(h('div', { cls: 't-note' }, ['⚑ terminal: ' + e]));
    const p = propIndex();
    for (let c = 0; c < NC; c++) {
      const code = status(sid, c, p);
      tipRow(tip, coalName(c), code >= 0 ? STATUS[code] : 'n/a', code >= 0 ? badge(code) : null);
    }
    if (extraRows) extraRows(tip);
    if (move) {
      tipSep(tip);
      const stats = stepStats(sid, S.coal, p);
      move.forEach((j, i) => {
        let cls = null;
        if (stats) { const r = stats[i].find((x) => x.action === j); if (r) cls = r.cls; }
        tipRow(tip, B.actors[i].name, actionName(i, j) + (cls != null ? ' (' + DECISION[cls] + ')' : ''), lineKey(actorColor(i)));
      });
    }
    tipSep(tip);
    B.variables.forEach((v, i) => {
      if (v.builtin && !S.builtins) return;
      tipRow(tip, v.name, level(i, value(i, sid)));
    });
    if (!S.builtins) tip.appendChild(h('div', { cls: 't-note muted', text: 'built-in variables hidden (toggle on the board)' }));
  }

  // ---------------------------------------------------------------- figure frame
  function figure(sec, id, title, sub, tools, drawChart, drawTable) {
    clear(sec);
    const tableOn = S.tables[id] != null ? S.tables[id] : S.allTables;
    const btn = h('button', {
      type: 'button', id: 'tbtn-' + id, 'aria-pressed': String(tableOn),
      title: 'Swap the chart for its table twin',
      onclick: () => { S.tables[id] = !tableOn; render(); },
    }, 'Table view');
    sec.appendChild(h('div', { cls: 'fig-head' }, [
      h('h2', { id: 'h-' + id.replace(/^sec-/, ''), text: title }),
      h('div', { cls: 'tools' }, (tools || []).concat([btn])),
    ]));
    if (sub) sec.appendChild(h('p', { cls: 'fig-sub' }, sub));
    const body = h('div', { cls: 'fig-body' });
    sec.appendChild(body);
    const tip = h('div', { cls: 'tip', role: 'tooltip' });
    if (tableOn) drawTable(body);
    else drawChart(body, tip);
    body.appendChild(tip);
    return body;
  }

  function table(head, rows, opts) {
    const t = h('table', null, [
      opts && opts.caption ? h('caption', { text: opts.caption }) : null,
      h('thead', null, h('tr', null, head.map((x, i) => h('th', { cls: opts && opts.num && opts.num[i] ? 'num' : null, scope: 'col' }, x)))),
      h('tbody', null, rows.map((r) => h('tr', null, r.map((x, i) => h('td', { cls: opts && opts.num && opts.num[i] ? 'num' : null }, x))))),
    ]);
    return h('div', { cls: 'tbl-wrap' }, t);
  }

  function notice(text) { return h('p', { cls: 'notice', text: text }); }

  // ---------------------------------------------------------------- header and footer
  function renderHeader() {
    const m = B.meta;
    const hdr = $('hdr');
    clear(hdr);
    const profile = m.profile || 'none';
    const horizon = m.timed ? 'horizon ' + m.horizon : 'untimed';
    const src = { model: 'the model’s initial states', explicit: 'explicit initial states', snapshot: 'a snapshot' }[m.initial_source] || m.initial_source;
    hdr.appendChild(h('h1', { text: m.name }));
    hdr.appendChild(h('div', { cls: 'meta' }, [
      h('span', null, ['fingerprint ', h('code', { text: m.fingerprint })]),
      h('span', { text: horizon }),
      h('span', { text: 'profile: ' + profile }),
      h('span', { text: fmtInt(m.counts.states) + ' reachable states' }),
      h('span', { text: 'starts from ' + src }),
    ]));
    if (m.description) hdr.appendChild(h('p', { cls: 'desc', text: m.description }));
    hdr.appendChild(h('p', { cls: 'caveat' }, [h('strong', { text: 'Caveat. ' }), m.caveat]));
    if (!B.moves.complete) {
      hdr.appendChild(notice('The full move table has ' + fmtInt(m.counts.moves) + ' joint moves, more than the ' + fmtInt(m.counts.max_moves) +
        ' kept in this page. Successor data is included only around the shown traces (their states, successors and successors’ successors); the decision tree says so where it stops.'));
    }
  }

  function renderFooter() {
    const f = $('ftr');
    clear(f);
    const themes = [['light', 'Light'], ['dark', 'Dark'], ['system', 'System']];
    f.appendChild(h('div', { cls: 'controls' }, [
      h('span', { cls: 'check' }, ['Theme ', h('span', { cls: 'seg', role: 'group', 'aria-label': 'Theme' }, themes.map((t) => h('button', {
        type: 'button', id: 'theme-' + t[0], 'aria-pressed': String(S.theme === t[0]),
        onclick: () => { S.theme = t[0]; saveTheme(); applyTheme(); render(); },
      }, t[1])))]),
      h('label', { cls: 'check' }, [h('input', {
        type: 'checkbox', id: 'all-tables', checked: S.allTables ? true : null,
        onchange: (ev) => { S.allTables = ev.target.checked; S.tables = {}; render(); },
      }), 'Show every figure as its table']),
    ]));
    f.appendChild(h('h2', { text: 'How to read this page' }));
    f.appendChild(h('ul', null, [
      h('li', { text: 'The filter row scopes everything below it. The hypothesis picks the initial state; the coalition and the property pick every status color; the ending picks the reference trace and the backward wavefront.' }),
      h('li', { text: 'Status is relative to the selected coalition’s kernel for the selected property: kept (the coalition can keep it), contested (neither side can force), lost (the rest can force it false), failed (it is false). Icons and labels always accompany the colors.' }),
      h('li', { text: 't_K is the point of no return (first state outside the kernel), t_L the first state from which the rest can force failure, t_φ the first state where the property is false. The silent phase is [t_K, t_φ): the outcome is decided but nothing is visible yet.' }),
      h('li', { text: 'Decision classes rate each available action against the selected coalition’s kernel over all completions by the other actors and Nature: safe (all stay kept), risky (some leave), losing (none stay kept), ends (all end the game).' }),
      h('li', { text: 'Strategies are perfect-information: for coalitions with hidden variables a keeping or forcing result is an upper bound (see the uniformity notes). Every number is conditional on the model version (fingerprint) and the initial state.' }),
      h('li', { text: 'Every chart has a table twin (Table view). Hover or focus a mark for details; the same values are in the tables.' }),
    ]));
  }

  // ---------------------------------------------------------------- filter row
  function select(id, label, options, current, onchange, title) {
    const sel = h('select', { id: id, title: title || null, onchange: (ev) => onchange(ev.target.value) },
      options.map((o) => h('option', { value: String(o[0]), selected: String(o[0]) === String(current) ? true : null }, o[1])));
    return h('label', { for: id }, [label, sel]);
  }

  function resetBranch() { S.cf = null; S.choice = {}; }

  function renderFilters() {
    const f = $('filters');
    clear(f);
    const hv = B.hypotheses.variables;
    if (hv.length) {
      hv.forEach((name, vi) => {
        const cur = H[S.hyp].values[name];
        f.appendChild(select('f-hyp-' + vi, 'Hypothesis: ' + name, B.hypotheses.values[name].map((x) => [x, x]), cur, (val) => {
          const want = Object.assign({}, H[S.hyp].values, { [name]: val });
          let k = H.findIndex((it) => hv.every((n) => it.values[n] === want[n]));
          if (k < 0) k = H.findIndex((it) => it.values[name] === val);
          if (k >= 0) { S.hyp = k; S.trace = 'ref'; S.tick = 0; S.compare = null; resetBranch(); }
          render();
        }, 'Swept variable: one initial state per value'));
      });
    } else {
      f.appendChild(h('label', null, ['Hypothesis', h('span', { cls: 'sub', style: 'min-height:30px;display:flex;align-items:center', text: H[S.hyp].label })]));
    }
    f.appendChild(select('f-coal', 'Coalition', B.coalitions.map((c, i) => [i, c.name]), S.coal, (v) => { S.coal = Number(v); render(); }));
    if (B.endings.length) {
      f.appendChild(select('f-ending', 'Ending', B.endings.map((e, i) => [i, e]), S.ending, (v) => {
        S.ending = Number(v); S.trace = 'ref'; S.tick = 0; S.compare = null; resetBranch(); render();
      }));
    } else {
      f.appendChild(h('label', null, ['Ending', h('span', { cls: 'sub', style: 'min-height:30px;display:flex;align-items:center', text: 'none offered' })]));
    }
    const autoName = B.properties.some((p) => p.kind === 'avoid' && p.name === B.endings[S.ending]) ? 'not ' + B.endings[S.ending] : propLabel(propIndex());
    const props = [['auto', autoName + ' (follows the ending)']].concat(B.properties.map((p, i) => [i, p.label]));
    f.appendChild(select('f-prop', 'Property kept', props, S.prop, (v) => { S.prop = v; render(); }, 'The predicate statuses are computed against'));
    const opts = traceOptions();
    if (!B.endings.length) {
      // no ending, no trace: nothing to choose
    } else if (opts.length) {
      f.appendChild(select('f-trace', 'Trace', opts.map((o) => [o.key, o.label]), S.trace, (v) => {
        S.trace = v; S.tick = 0; resetBranch(); render();
      }));
    } else {
      f.appendChild(h('label', null, ['Trace', h('span', { cls: 'sub', style: 'min-height:30px;display:flex;align-items:center', text: 'none reaches ' + B.endings[S.ending] })]));
    }
  }

  // ---------------------------------------------------------------- stat tiles
  function tile(label, value, note) {
    return h('div', { cls: 'tile' }, [h('div', { cls: 'label', text: label }), h('div', { cls: 'value' }, value), h('div', { cls: 'note' }, note)]);
  }

  function renderTiles() {
    const t = $('tiles');
    clear(t);
    const item = H[S.hyp];
    const p = propIndex();
    const c = S.coal;
    const code = p >= 0 ? item.card.status[p][c] : -1;
    const short = p >= 0 ? item.card.shortest[p][c] : null;
    const tr = currentTrace();
    const ph = tr && p >= 0 ? phases(tr.states, c, p) : null;
    const e = B.endings[S.ending];
    const rel = item.tables.relaxations.find((r) => r.ending === e);
    t.appendChild(tile('Reachable states', fmtInt(item.reachable), 'from ' + item.label + ' (' + fmtInt(B.states.count) + ' in the explored graph)'));
    t.appendChild(tile('Kernel membership of s₀', code >= 0 ? [badge(code), STATUS[code]] : 'n/a', coalName(c) + ', property ' + propLabel(p)));
    let shortText = 'n/a';
    if (code === 0) shortText = short == null ? 'never' : plural(short, TICK);
    else if (code > 0) shortText = 'outside';
    t.appendChild(tile('Shortest distance', shortText, code === 0 ? 'fewest ' + TICK + 's of some play that leave the kernel' : 'the initial state is not in the kernel'));
    let pnr = 'no trace';
    if (ph) pnr = ph.tK == null ? 'never' : TICK + ' ' + tickOf(tr.states[ph.tK]);
    t.appendChild(tile('Point of no return', pnr, tr ? 'on the ' + tr.short : (e ? 'no play reaches ' + e + ' from ' + item.label : 'no ending is offered')));
    let relText = 'n/a';
    if (rel) relText = rel.minimum_size == null ? 'none ≤ ' + rel.max_size : String(rel.minimum_size);
    t.appendChild(tile('Minimum relaxation', relText, rel ? (rel.minimum_size === 0 ? e + ' is reachable as declared' : 'named assumptions to relax so that ' + e + ' is reachable') + ' from ' + item.label : e));
  }

  // ---------------------------------------------------------------- 1. initial state
  function levelScale(v, x) {
    const n = B.variables[v].levels.length;
    const w = 84;
    const step = n > 1 ? (w - 12) / (n - 1) : 0;
    const svg = sv('svg', { width: w, height: 14, class: 'levelscale', 'aria-hidden': 'true' });
    svg.appendChild(sv('line', { x1: 6, x2: w - 6, y1: 7, y2: 7, stroke: C.axis, 'stroke-width': 1 }));
    for (let i = 0; i < n; i++) svg.appendChild(sv('circle', { cx: 6 + i * step, cy: 7, r: 2, fill: C.axis }));
    const col = rampColor(x, n);
    svg.appendChild(sv('circle', { cx: 6 + x * step, cy: 7, r: 5, fill: col, stroke: C.surface, 'stroke-width': 2 }));
    return svg;
  }

  function renderInitial() {
    const sec = $('sec-initial');
    const item = H[S.hyp];
    const sid = item.state;
    const snap = B.snapshot;
    const p = propIndex();
    const tools = [h('button', {
      type: 'button', id: 'init-builtins', 'aria-pressed': String(S.builtins),
      onclick: () => { S.builtins = !S.builtins; render(); },
    }, 'Built-in variables')];
    const sub = 'State #' + sid + ' (' + item.label + '). Status chips use the property ' + propLabel(p) + '.';
    figure(sec, 'initial', '1. Initial state', sub, tools, (body) => {
      const grid = h('div', { cls: 'init-grid' });
      grid.appendChild(varTable(sid, snap, true));
      const right = h('div');
      right.appendChild(h('h3', { text: 'Kernel membership', style: 'margin-top:0' }));
      const chips = h('div', { cls: 'chips' });
      for (let c = 0; c < NC; c++) {
        const code = p >= 0 ? item.card.status[p][c] : -1;
        const sh = p >= 0 ? item.card.shortest[p][c] : null;
        const mg = p >= 0 ? item.card.margin[p][c] : null;
        let detail = '';
        if (code === 0) detail = 'shortest ' + (sh == null ? 'never' : plural(sh, TICK)) + ' · margin ' + (mg == null ? '-' : mg);
        else if (code > 0) detail = STATUS_MEANING[code];
        chips.appendChild(h('div', { cls: 'chip-status' }, [code >= 0 ? badge(code) : null,
          h('div', null, [h('span', { cls: 'name', text: coalName(c) }), ' ', code >= 0 ? STATUS[code] : 'n/a', h('div', { cls: 'detail', text: detail })])]));
      }
      right.appendChild(chips);
      right.appendChild(h('h3', { text: 'Endings reachable from here' }));
      const ul = h('ul', { cls: 'endings-list' });
      const ends = Object.keys(item.card.endings).filter((e) => item.card.endings[e] != null);
      ends.sort((a, b) => item.card.endings[a] - item.card.endings[b]);
      ends.forEach((e) => ul.appendChild(h('li', { text: e + ': at least ' + plural(item.card.endings[e], TICK) })));
      Object.keys(item.card.endings).filter((e) => item.card.endings[e] == null).forEach((e) => ul.appendChild(h('li', { cls: 'muted', text: e + ': not reachable' })));
      if (!Object.keys(item.card.endings).length) ul.appendChild(h('li', { cls: 'muted', text: 'the model offers no ending' }));
      right.appendChild(ul);
      if (item.identical_to.length && H.length > 1) {
        const hidden = B.hypotheses.variables.join(', ');
        right.appendChild(h('p', { cls: 'sub small', text: 'To ' + item.identical_to.join(', ') + ' the initial states of every hypothesis look identical: ' +
          (item.identical_to.length === 1 ? 'it does' : 'they do') + ' not observe ' + hidden + '. ' +
          (item.identical_to.length === 1 ? 'It has' : 'They have') + ' to choose without knowing which hypothesis holds.' }));
      }
      grid.appendChild(right);
      body.appendChild(grid);
    }, (body) => {
      body.appendChild(varTable(sid, snap, false));
      const head = ['property'].concat(B.coalitions.map((c) => c.name));
      const rows = B.properties.map((pp, pi) => [pp.label].concat(B.coalitions.map((_, c) => {
        const code = item.card.status[pi][c];
        const sh = item.card.shortest[pi][c];
        const mg = item.card.margin[pi][c];
        return h('span', null, [statusText(code), code === 0 ? ' (shortest ' + (sh == null ? 'never' : sh) + ', margin ' + (mg == null ? '-' : mg) + ')' : '']);
      })));
      body.appendChild(table(head, rows, { caption: 'Kernel membership of the initial state, every property and coalition' }));
      body.appendChild(table(['ending', 'minimum ' + TICK + 's'], Object.keys(item.card.endings).map((e) => [e, item.card.endings[e] == null ? 'not reachable' : String(item.card.endings[e])]), { num: [false, true] }));
    });
  }

  function varTable(sid, snap, withScale) {
    const head = ['variable', 'level'];
    if (B.hypotheses.variables.length) head.push('hidden from');
    if (snap) head.push('confidence', 'indicators (source, observed, rule)');
    const rows = [];
    B.variables.forEach((v, i) => {
      if (v.builtin && !S.builtins) return;
      const x = value(i, sid);
      const lv = h('span', { style: 'display:inline-flex;align-items:center;gap:8px;white-space:nowrap' }, [withScale ? levelScale(i, x) : null, h('span', { text: level(i, x) })]);
      const row = [h('span', null, [v.name, v.swept ? h('span', { cls: 'tag', style: 'margin-left:6px', text: 'hypothesis' }) : null]), lv];
      if (B.hypotheses.variables.length) row.push(v.hidden_from.join(', ') || '-');
      if (snap) {
        const e = snap.variables[v.name];
        row.push(e ? String(e.confidence) : '-');
        row.push(e ? h('div', null, (e.indicators || []).map((ind) => h('div', { cls: 'small' }, [
          h('strong', { text: String(ind.id) }), ': ' + String(ind.value) + ' · ', h('span', { cls: 'mono', text: String(ind.source) }),
          ' · observed ' + String(ind.observed) + ' · rule: ' + String(ind.rule)]))) : '-');
      }
      rows.push(row);
    });
    const cap = snap ? 'Variables, with the snapshot of ' + snap.date + ' as provenance' : 'Variables';
    return table(head, rows, { caption: cap });
  }

  // ---------------------------------------------------------------- 2. trajectory board
  function boardMarkers(tr, c, p, cf) {
    const out = [];
    const n = tr.states.length;
    const t = (k) => tickOf(tr.states[Math.min(k, n - 1)]);
    if (p >= 0) {
      const ph = phases(tr.states, c, p);
      const pl = propLabel(p);
      if (ph.tK != null) out.push({ k: ph.tK, label: 't_K ' + t(ph.tK), text: 't_K = ' + TICK + ' ' + t(ph.tK) + ': point of no return, ' + coalName(c) + ' can no longer guarantee ' + pl });
      const prop = B.properties[p];
      const failure = prop.kind === 'avoid' ? prop.name : prop.name + ' false';
      if (ph.tL != null) out.push({ k: ph.tL, label: 't_L ' + t(ph.tL), text: 't_L = ' + TICK + ' ' + t(ph.tL) + ': the rest (every actor outside ' + coalName(c) + ', Nature included) can now force ' + failure });
      if (ph.tPhi != null) out.push({ k: ph.tPhi, label: 't_φ ' + t(ph.tPhi), text: 't_φ = ' + TICK + ' ' + t(ph.tPhi) + ': the failure is visible (' + (prop.kind === 'avoid' ? prop.name + ' holds' : prop.name + ' is false') + ')' });
      B.properties.forEach((q, qi) => {
        if (qi === p || q.kind !== 'invariant') return;
        const k = firstFalse(tr.states, qi);
        if (k != null) out.push({ k: k, label: q.name + ' false ' + t(k), text: 'invariant ' + q.name + ' is false from ' + TICK + ' ' + t(k), soft: true });
      });
    }
    const last = tr.states[n - 1];
    const e = endingOf(last);
    if (e) out.push({ k: n - 1, label: '⚑ ' + e + ' ' + t(n - 1), text: 'ending ' + e + ' at ' + TICK + ' ' + t(n - 1), flag: true });
    if (tr.stop) {
      const s = tr.stop;
      const why = s.reason === 'unavailable' ? actionName(s.actor, s.action) + ' is not available to ' + B.actors[s.actor].name : s.reason;
      out.push({ k: s.index, label: '⊘ stops ' + t(s.index), text: 'the replay stops at ' + TICK + ' ' + t(s.index) + ': ' + why });
    }
    if (cf) {
      const f = forkIndex(cf, tr, c, p);
      if (f != null) out.push({ k: f, label: 'fork ' + t(f), text: 'fork at ' + TICK + ' ' + t(f) + ': your branch’s status first differs from the trace' });
    }
    return out;
  }

  // Place marker labels in rows: a label may not overlap another label in its row, may not
  // cover the line of a marker placed in an earlier row, and its own line (which runs from its
  // row down) may not cross a label placed in a later row. Preference: right of the line in
  // any row, then left of it, then the short label (without the tick) in the same order.
  function layoutLabels(markers, colX, width) {
    const placed = []; // {row, x0, x1, line}
    const fits = (x, w, line, r) => placed.every((q) => {
      if (q.row === r && !(x + w < q.x0 - 4 || x > q.x1 + 4)) return false;
      if (q.row < r && q.line > x - 3 && q.line < x + w + 3) return false;
      if (q.row > r && line > q.x0 - 3 && line < q.x1 + 3) return false;
      return true;
    });
    markers.sort((a, b) => a.k - b.k);
    for (const m of markers) {
      const line = colX(m.k);
      const short = m.label.replace(/ \d+$/, '');
      const tries = [];
      for (const text of short !== m.label ? [m.label, short] : [m.label]) {
        const w = textWidth(text, 11, 600) + 10;
        for (const side of ['right', 'left']) {
          const x = side === 'right' ? line + 4 : line - 4 - w;
          if (x < 0 || x + w > width - 2) continue;
          for (let r = 0; r < 6; r++) tries.push([text, x, w, r]);
        }
      }
      const pick = tries.find((t) => fits(t[1], t[2], line, t[3]));
      if (pick) {
        m.label = pick[0];
        m.x = pick[1];
        m.row = pick[3];
        placed.push({ row: pick[3], x0: pick[1], x1: pick[1] + pick[2], line: line });
      } else {
        const w = textWidth(short, 11, 600) + 10;
        const r = placed.reduce((a, q) => Math.max(a, q.row + 1), 0);
        m.label = short;
        m.x = Math.max(0, Math.min(width - w - 2, line + 4));
        m.row = r;
        placed.push({ row: r, x0: m.x, x1: m.x + w, line: line });
      }
    }
    return placed.reduce((a, q) => Math.max(a, q.row + 1), 0);
  }

  function drawChip(g, x, y, w, i, j, opts) {
    const a = B.actors[i];
    const act = a.actions[j];
    const ghost = opts.ghost;
    const idle = act.is_idle;
    g.appendChild(sv('rect', {
      x: x, y: y, width: w, height: 20, rx: 3,
      fill: ghost ? 'none' : C.chip, stroke: ghost ? C.axis : 'none', 'stroke-width': 1,
    }));
    if (!ghost) g.appendChild(sv('rect', { x: x, y: y, width: 2, height: 20, fill: actorColor(i) }));
    let right = 4;
    if (opts.cls != null) { svgBadge(g, x + w - 11, y + 10, opts.cls, 6.5); right = 21; }
    if (opts.pending) {
      g.appendChild(sv('text', { x: x + w - right - 2, y: y + 14, 'text-anchor': 'end', 'font-size': 11, fill: C.muted, text: '⧗' }));
      right += 12;
    }
    if (opts.diff) {
      g.appendChild(sv('text', { x: x + w - right - 2, y: y + 14, 'text-anchor': 'end', 'font-size': 10, fill: C.muted, text: '◆' }));
      right += 11;
    }
    const label = fitText(act.name, w - 8 - right, 11.5, ghost ? 400 : 500);
    if (label) {
      g.appendChild(sv('text', {
        x: x + 7, y: y + 14, 'font-size': 11.5, 'font-weight': ghost ? 400 : 500,
        'font-style': idle ? 'italic' : null,
        fill: idle ? C.muted : ghost ? C.ink2 : C.ink, text: label,
      }));
    }
  }

  function pendingAt(i, s) {
    return PENDING[i].filter((d) => value(d.v, s) > 0);
  }

  function renderBoard() {
    const sec = $('sec-board');
    const tr = currentTrace();
    const p = propIndex();
    const tools = [h('button', {
      type: 'button', id: 'board-builtins', 'aria-pressed': String(S.builtins),
      onclick: () => { S.builtins = !S.builtins; render(); },
    }, 'Built-in variables')];
    const sub = tr
      ? 'The ' + tr.label + ' (' + plural(tr.states.length - 1, 'step') + '). Status against ' + propLabel(p) + '; markers and decision classes for ' + coalName(S.coal) +
        '. Click a ' + TICK + ' (or focus the board and use the arrow keys) to open its decision tree below.'
      : null;
    figure(sec, 'board', '2. Trajectory board', sub, tools, (body, tip) => {
      if (!tr) { body.appendChild(notice(noTraceText())); return; }
      drawBoard(body, tip, tr, p);
    }, (body) => {
      if (!tr) { body.appendChild(notice('No trace to show.')); return; }
      boardTable(body, tr, p);
    });
  }

  function drawBoard(body, tip, tr, p) {
    const c = S.coal;
    const cf = S.cf;
    const n = Math.max(tr.states.length, cf ? cf.states.length : 0);
    S.tick = Math.min(S.tick, tr.states.length - 1);
    const W = Math.max(300, body.clientWidth || 300);
    const narrow = W < 560;
    const LW = narrow ? 0 : 132; // label column (wide screens)
    const LA = narrow ? 15 : 0; // label line above each row (narrow screens)
    const cw = Math.max(narrow ? 60 : 64, Math.min(180, Math.floor((W - LW - 6) / n)));
    const PW = LW + cw * n + 6;
    const colX = (k) => LW + k * cw;
    const markers = boardMarkers(tr, c, p, cf);
    const nRows = layoutLabels(markers, colX, PW);
    const ph = p >= 0 ? phases(tr.states, c, p) : null;
    const silent = ph && ph.tK != null ? [ph.tK, ph.tPhi == null ? tr.states.length - 1 : ph.tPhi] : null;
    const rowH = 24;
    const heatH = 22;

    // vertical layout
    const axisY = 12;
    let y = 20;
    const labelTop = y; y += nRows * 15 + 2;
    const bracketTop = y; if (silent) y += 24;
    const statusTop = y; y += NC * (rowH + LA);
    const cfTop = y; if (cf) y += 8 + NC * (rowH + LA);
    const statusBottom = y;
    y += 14;
    const laneH = B.actors.map((a, i) => {
      let maxAlt = 0;
      tr.states.slice(0, -1).forEach((s) => { const av = availAt(s); if (av) maxAlt = Math.max(maxAlt, av[i].length - 1); });
      return LA + 26 + 20 * maxAlt;
    });
    const laneY = [];
    B.actors.forEach((a, i) => { laneY.push(y); y += laneH[i]; });
    y += 12;
    const heatTop = y;
    const vars = shownVars();
    y += vars.length * (heatH + LA);
    const PH = y + 6;

    const wrap = h('div', { cls: 'scroll-x chart' });
    const svg = sv('svg', {
      width: PW, height: PH, viewBox: '0 0 ' + PW + ' ' + PH, id: 'board-svg', tabindex: 0, role: 'img',
      'aria-label': 'Trajectory board: status band, decision lanes and variable heatmap along the ' + tr.label + '. Arrow keys select a ' + TICK + '.',
      'font-family': FONT,
    });
    wrap.appendChild(svg);
    body.appendChild(wrap);

    const gBack = sv('g'); svg.appendChild(gBack);
    gBack.appendChild(sv('rect', { x: colX(S.tick), y: statusTop - 4, width: cw, height: PH - statusTop, fill: C.wash }));
    if (silent) {
      const x0 = colX(silent[0]);
      const x1 = colX(silent[1]);
      if (x1 > x0) {
        gBack.appendChild(sv('rect', { x: x0, y: statusTop - 2, width: x1 - x0, height: statusBottom - statusTop + 2, fill: C.wash }));
        gBack.appendChild(sv('path', { d: 'M' + (x0 + 1) + ' ' + (bracketTop + 21) + 'V' + (bracketTop + 15) + 'H' + (x1 - 1) + 'V' + (bracketTop + 21), fill: 'none', stroke: C.ink2, 'stroke-width': 1 }));
        const lbl = fitText('silent phase [t_K, t_\u03c6)', x1 - x0 - 8, 11, 400) || fitText('silent', x1 - x0 - 4, 11, 400);
        if (lbl) gBack.appendChild(sv('text', { x: (x0 + x1) / 2, y: bracketTop + 11, 'text-anchor': 'middle', 'font-size': 11, fill: C.ink2, text: lbl }));
      }
    }
    for (let k = 0; k < n; k++) {
      const s = k < tr.states.length ? tr.states[k] : cf.states[k];
      svg.appendChild(sv('text', { x: colX(k) + cw / 2, y: axisY, 'text-anchor': 'middle', 'font-size': 11, fill: k === S.tick ? C.ink : C.muted, 'font-weight': k === S.tick ? 600 : 400, text: String(tickOf(s)) }));
    }
    svg.appendChild(sv('text', { x: 0, y: axisY, 'font-size': 11, fill: C.muted, text: TICK }));
    // a row label: in the label column, or on a line above the row on narrow screens
    const rowLabel = (top, height, text, bold, color) => {
      const base = LA ? top + 11 : top + height / 2 + 4;
      const room = LA ? PW : LW;
      let x = 0;
      if (color) { svg.appendChild(sv('rect', { x: 0, y: base - 10, width: 3, height: 12, rx: 1, fill: color })); x = 7; }
      const t = fitText(text, room - x - 6, 11.5, bold ? 600 : 400);
      svg.appendChild(sv('text', { x: x, y: base, 'font-size': 11.5, 'font-weight': bold ? 600 : 400, fill: bold ? C.ink : C.ink2, text: t }));
    };
    const statusRow = (states, top, cc, prefix) => {
      rowLabel(top, rowH, prefix + coalName(cc), cc === c && !prefix, null);
      states.forEach((s, k) => {
        const code = status(s, cc, p);
        if (code >= 0) statusCell(svg, colX(k) + 1, top + LA + 2, cw - 2, rowH - 4, code, cc === c ? 1 : 0.8, { 'data-row': prefix ? 'branch' : 'trace', 'data-coalition': cc });
      });
    };
    for (let cc = 0; cc < NC; cc++) statusRow(tr.states, statusTop + cc * (rowH + LA), cc, '');
    if (cf) {
      svg.appendChild(sv('line', { x1: 0, x2: PW, y1: cfTop + 3, y2: cfTop + 3, stroke: C.grid }));
      for (let cc = 0; cc < NC; cc++) statusRow(cf.states, cfTop + 8 + cc * (rowH + LA), cc, 'branch ');
    }
    for (const m of markers) {
      const x = colX(m.k);
      svg.appendChild(sv('line', { x1: x, x2: x, y1: labelTop + m.row * 15 + 2, y2: statusBottom, stroke: m.soft ? C.muted : C.ink, 'stroke-width': 1, 'stroke-opacity': m.soft ? 0.8 : 0.9 }));
      const tt = sv('text', { x: m.x, y: labelTop + m.row * 15 + 11, 'font-size': 11, 'font-weight': 600, fill: m.soft ? C.ink2 : C.ink, text: m.label, 'data-marker': m.label });
      tt.appendChild(sv('title', { text: m.text }));
      svg.appendChild(tt);
    }
    // decision lanes
    const gLanes = sv('g');
    svg.appendChild(gLanes);
    const gGhost = sv('g');
    svg.appendChild(gGhost);
    const statsCache = {};
    const ref = tr.key === 'ref' ? refEntry(S.hyp, S.ending) : null;
    const statsAt = (k) => {
      if (!(k in statsCache)) {
        let st = k < tr.moves.length ? stepStats(tr.states[k], c, p) : null;
        if (!st && ref && ref.classes && p >= 0 && k < tr.moves.length) {
          st = ref.classes[p][c][k].map((per) => per.map((x) => ({ action: x[0], cls: x[1], counts: null, succ: [] })));
        }
        statsCache[k] = st;
      }
      return statsCache[k];
    };
    const chipTop = (i) => laneY[i] + LA;
    B.actors.forEach((a, i) => {
      const top = laneY[i];
      const g = sv('g', { opacity: S.isoActor != null && S.isoActor !== i ? 0.25 : 1 });
      gLanes.appendChild(g);
      g.appendChild(sv('line', { x1: 0, x2: PW, y1: top - 3, y2: top - 3, stroke: C.grid }));
      const base = LA ? top + 11 : top + 14;
      g.appendChild(sv('rect', { x: 0, y: base - 10, width: 3, height: 12, rx: 1, fill: actorColor(i) }));
      g.appendChild(sv('text', { x: 7, y: base, 'font-size': 11.5, 'font-weight': 600, fill: C.ink, text: fitText(a.name, (LA ? PW : LW) - 12, 11.5, 600) }));
      tr.moves.forEach((mv, k) => {
        const st = statsAt(k);
        const j = mv[i];
        let cls = null;
        if (st) { const r = st[i].find((x) => x.action === j); if (r) cls = r.cls; }
        drawChip(g, colX(k) + 3, chipTop(i), cw - 6, i, j, { cls: cls, pending: pendingAt(i, tr.states[k]).length > 0 });
      });
    });
    const drawGhosts = (k) => {
      clear(gGhost);
      if (k == null || k >= tr.moves.length) return;
      const st = statsAt(k);
      if (!st) return;
      B.actors.forEach((a, i) => {
        if (S.isoActor != null && S.isoActor !== i) return;
        const chosen = tr.moves[k][i];
        let row = 0;
        st[i].forEach((r) => {
          if (r.action === chosen) return;
          row++;
          drawChip(gGhost, colX(k) + 3, chipTop(i) + row * 20 + 4, cw - 6, i, r.action, { ghost: true, cls: r.cls });
        });
      });
    };
    drawGhosts(S.tick);
    // variable heatmap
    vars.forEach((v, r) => {
      const top = heatTop + r * (heatH + LA);
      const spec = B.variables[v];
      rowLabel(top, heatH, spec.name, false, null);
      const nl = spec.levels.length;
      let prev = null;
      tr.states.forEach((s, k) => {
        const x = value(v, s);
        const fill = rampColor(x, nl);
        svg.appendChild(sv('rect', { x: colX(k) + 1, y: top + LA + 2, width: cw - 2, height: heatH - 4, rx: 2, fill: fill }));
        if (k === 0 || x !== prev) {
          const name = level(v, x);
          if (textWidth(name, 11, 500) <= cw - 12) {
            svg.appendChild(sv('text', { x: colX(k) + 6, y: top + LA + heatH / 2 + 4, 'font-size': 11, 'font-weight': 500, fill: onFill(fill), text: name, 'pointer-events': 'none' }));
          }
        }
        if (spec.origin === 'latch' && k > 0 && prev === 0 && x > 0) {
          svg.appendChild(sv('line', { x1: colX(k) + 0.5, x2: colX(k) + 0.5, y1: top + LA, y2: top + LA + heatH, stroke: C.ink, 'stroke-width': 1.5 }));
        }
        prev = x;
      });
    });
    // crosshair, hit area, one tooltip
    const cross = sv('line', { x1: 0, x2: 0, y1: statusTop - 4, y2: PH, stroke: C.ink2, 'stroke-width': 1, visibility: 'hidden', 'pointer-events': 'none' });
    svg.appendChild(cross);
    const hit = sv('rect', { x: LW, y: 0, width: cw * n, height: PH, fill: 'transparent' });
    svg.appendChild(hit);
    const colAt = (ev) => {
      const r = svg.getBoundingClientRect();
      return Math.max(0, Math.min(n - 1, Math.floor((ev.clientX - r.left - LW) / cw)));
    };
    const chipAt = (k, ysvg) => {
      if (k >= tr.moves.length) return null;
      for (let i = 0; i < NA; i++) {
        if (ysvg < chipTop(i) || ysvg >= laneY[i] + laneH[i]) continue;
        const chosen = tr.moves[k][i];
        if (ysvg < chipTop(i) + 22) return { i: i, j: chosen, chosen: true };
        const st = statsAt(k);
        if (!st) return null;
        const alts = st[i].filter((r) => r.action !== chosen);
        const row = Math.floor((ysvg - chipTop(i) - 4) / 20) - 1;
        return row >= 0 && row < alts.length ? { i: i, j: alts[row].action, chosen: false } : null;
      }
      return null;
    };
    const chipTip = (k, hit2) => {
      const i = hit2.i;
      const act = B.actors[i].actions[hit2.j];
      const st = statsAt(k);
      const r = st ? st[i].find((x) => x.action === hit2.j) : null;
      clear(tip);
      tip.appendChild(h('div', { cls: 't-head', text: B.actors[i].name + '.' + act.name + (hit2.chosen ? ' (chosen)' : ' (alternative)') + ' \u00b7 ' + TICK + ' ' + tickOf(tr.states[k]) }));
      if (r) {
        tipRow(tip, 'decision class', DECISION[r.cls], badge(r.cls));
        tip.appendChild(h('div', { cls: 't-note', text: DECISION_MEANING[r.cls] + ' (' + coalName(c) + ', ' + propLabel(p) + ')' }));
        if (r.counts) r.counts.forEach((n2, code) => { if (n2) tipRow(tip, STATUS[code], n2 + ' of ' + r.succ.length + ' completions', badge(code)); });
      }
      tipSep(tip);
      tipRow(tip, 'guard', act.guard_text || 'True');
      tip.appendChild(h('div', { cls: 't-note', text: 'source: ' + (act.source || (act.is_idle ? 'built-in action' : '-')) }));
      tipRow(tip, 'speculative', act.speculative ? 'yes' : 'no');
      if (act.delay) tipRow(tip, 'delay', 'effect visible ' + plural(act.delay + 1, TICK) + ' after it is chosen');
      pendingAt(i, tr.states[k]).forEach((d) => tipRow(tip, 'pending', actionName(i, d.action) + ' lands in ' + plural(value(d.v, tr.states[k]), TICK)));
    };
    const showAt = (k, px, py, ysvg) => {
      cross.setAttribute('x1', colX(k) + cw / 2);
      cross.setAttribute('x2', colX(k) + cw / 2);
      cross.setAttribute('visibility', 'visible');
      drawGhosts(k);
      const onChip = ysvg != null && k < tr.states.length ? chipAt(k, ysvg) : null;
      if (onChip) { chipTip(k, onChip); tipShow(tip, body, px, py); return; }
      const onRef = k < tr.states.length;
      const sid = onRef ? tr.states[k] : cf.states[k];
      const move = onRef ? (k < tr.moves.length ? tr.moves[k] : null) : (k < cf.moves.length ? cf.moves[k] : null);
      stateTip(tip, sid, move, TICK + ' ' + tickOf(sid) + ' \u00b7 state #' + sid + (onRef ? '' : ' (branch)'), (t) => {
        PENDING.forEach((list, i) => list.forEach((d) => {
          const left = value(d.v, sid);
          if (left > 0) tipRow(t, B.actors[i].name + ' pending', actionName(i, d.action) + ' lands in ' + plural(left, TICK));
        }));
        markers.filter((m) => m.k === k).forEach((m) => t.appendChild(h('div', { cls: 't-note', text: m.text })));
      });
      tipShow(tip, body, px, py);
    };
    hit.addEventListener('pointermove', (ev) => {
      const pos = relPos(ev, body);
      showAt(colAt(ev), pos[0], pos[1], ev.clientY - svg.getBoundingClientRect().top);
    });
    hit.addEventListener('pointerleave', () => { cross.setAttribute('visibility', 'hidden'); tipHide(tip); drawGhosts(S.tick); });
    hit.addEventListener('click', (ev) => {
      const k = colAt(ev);
      if (k < tr.states.length) { S.tick = k; resetBranch(); render(); }
    });
    svg.addEventListener('focus', () => showAt(S.tick, colX(S.tick) + cw / 2 - wrap.scrollLeft, statusTop));
    svg.addEventListener('blur', () => { cross.setAttribute('visibility', 'hidden'); tipHide(tip); });
    svg.addEventListener('keydown', (ev) => {
      let k = S.tick;
      if (ev.key === 'ArrowRight') k = Math.min(tr.states.length - 1, k + 1);
      else if (ev.key === 'ArrowLeft') k = Math.max(0, k - 1);
      else if (ev.key === 'Home') k = 0;
      else if (ev.key === 'End') k = tr.states.length - 1;
      else return;
      ev.preventDefault();
      if (k !== S.tick) { S.tick = k; resetBranch(); render(); }
    });

    body.appendChild(statusLegend([h('span', { cls: 'item' }, ['\u29d7 pending delayed action']), h('span', { cls: 'item' }, ['\u2691 ending'])]));
    body.appendChild(actorLegend());
    body.appendChild(h('div', { cls: 'legend', 'aria-label': 'Decision classes' }, [h('span', { text: 'Decision classes:' })].concat(DECISION.map((d, i) => h('span', { cls: 'item', title: DECISION_MEANING[i] }, [badge(i), d])))));
    if (markers.length) {
      body.appendChild(h('ul', { cls: 'small sub', style: 'margin:4px 0 0;padding-left:18px' }, markers.map((m) => h('li', { text: m.text }))));
    }
  }

  function boardTable(body, tr, p) {
    const c = S.coal;
    const head = [TICK, 'state'].concat(B.coalitions.map((x) => x.name)).concat(B.actors.map((a) => a.name)).concat(shownVars().map((v) => B.variables[v].name));
    const rows = tr.states.map((s, k) => {
      const st = k < tr.moves.length ? stepStats(s, c, p) : null;
      const row = [String(tickOf(s)), '#' + s + (endingOf(s) ? ' ⚑ ' + endingOf(s) : '')];
      for (let cc = 0; cc < NC; cc++) row.push(statusText(status(s, cc, p)));
      B.actors.forEach((a, i) => {
        if (k >= tr.moves.length) { row.push('-'); return; }
        const j = tr.moves[k][i];
        const r = st ? st[i].find((x) => x.action === j) : null;
        const alts = st ? st[i].filter((x) => x.action !== j).map((x) => actionName(i, x.action) + ' ' + DECISION[x.cls]).join(', ') : '';
        row.push(h('span', null, [r ? badge(r.cls) : null, actionName(i, j) + (r ? ' (' + DECISION[r.cls] + ')' : ''), alts ? h('div', { cls: 'small muted', text: 'alternatives: ' + alts }) : null]));
      });
      shownVars().forEach((v) => row.push(level(v, value(v, s))));
      return row;
    });
    body.appendChild(table(head, rows, { caption: 'The ' + tr.label + '; statuses against ' + propLabel(p) + ', decision classes for ' + coalName(c) }));
    const markers = boardMarkers(tr, c, p, S.cf);
    if (markers.length) body.appendChild(table(['marker', 'meaning'], markers.map((m) => [m.label, m.text])));
  }

  // ---------------------------------------------------------------- 3. decision tree
  function treeOrigin(tr) {
    if (S.cf) {
      const k = S.cf.states.length - 1;
      return { sid: S.cf.states[k], k: k, branch: true };
    }
    if (tr) return { sid: tr.states[S.tick], k: S.tick, branch: false };
    return { sid: H[S.hyp].state, k: 0, branch: false };
  }

  function defaultChoice(tr, origin, i, avail) {
    if (tr && origin.k < tr.moves.length) {
      const j = tr.moves[origin.k][i];
      if (avail.indexOf(j) >= 0) return j;
    }
    if (avail.indexOf(0) >= 0) return 0;
    return avail[0];
  }

  function choiceNote(tr, origin, i, chosen) {
    if (S.choice[i] != null) return '';
    const j = tr && origin.k < tr.moves.length ? tr.moves[origin.k][i] : null;
    if (j == null) return ' (default)';
    if (j === chosen) return ' (as in the trace)';
    return ' (the trace\u2019s ' + actionName(i, j) + ' is not available here)';
  }

  function bestWorst(r) {
    let best = null;
    let worst = null;
    for (const t of r.succ) {
      const code = status(t);
      if (best == null || code < status(best)) best = t;
      if (worst == null || code > status(worst)) worst = t;
    }
    return [best, worst];
  }

  function endingsFrom(t, limit) {
    const last = NC; // the all-actors entry
    const out = [];
    B.endings.forEach((e, k) => {
      const r = rankOf(k, last, t);
      if (r >= 0) out.push([e, r]);
    });
    out.sort((a, b) => a[1] - b[1]);
    return limit ? out.slice(0, limit) : out;
  }

  function endingsText(t, limit) {
    const list = endingsFrom(t, limit);
    if (!list.length) return 'no offered ending';
    return list.map((x) => x[0] + ' in ' + x[1]).join(', ');
  }

  function renderTree() {
    const sec = $('sec-tree');
    const tr = currentTrace();
    const p = propIndex();
    const c = S.coal;
    const origin = treeOrigin(tr);
    const sid = origin.sid;
    const where = origin.branch
      ? 'the last state of your branch (' + plural(S.cf.moves.length - S.cf.start, 'step') + ' from ' + TICK + ' ' + tickOf(S.cf.states[S.cf.start]) + ')'
      : tr ? 'the ' + tr.short : 'the initial state (' + (B.endings.length ? 'no trace reaches ' + B.endings[S.ending] : 'no ending is offered') + ')';
    const sub = 'From ' + TICK + ' ' + tickOf(sid) + ', state #' + sid + ', on ' + where + '. Each row is one available action; the bar counts the successor statuses over all completions by the other actors and Nature, against ' +
      propLabel(p) + ' for ' + coalName(c) + '. Choose an action per actor and step to build a branch by hand.';
    const stats = stepStats(sid, c, p);
    const m = movesAt(sid);
    figure(sec, 'tree', '3. Decision tree', sub, [], (body, tip) => {
      if (B.states.terminal[sid]) { body.appendChild(notice('This state is terminal' + (endingOf(sid) ? ' (' + endingOf(sid) + ')' : '') + ': no decisions remain.')); treeBranchBar(body, tr, p, null); return; }
      if (!m || !stats) { body.appendChild(notice('Successor data for state #' + sid + ' is not in this page (the move table was limited to the neighborhood of the shown traces), so the tree cannot expand here.')); treeBranchBar(body, tr, p, null); return; }
      B.actors.forEach((a, i) => {
        const chosen = S.choice[i] != null && m.avail[i].indexOf(S.choice[i]) >= 0 ? S.choice[i] : defaultChoice(tr, origin, i, m.avail[i]);
        const traceAct = tr && !origin.branch && origin.k < tr.moves.length ? tr.moves[origin.k][i] : null;
        body.appendChild(h('div', { cls: 'tree-actor' }, [h('span', { cls: 'bar', style: 'background:' + actorColor(i) }), h('strong', { text: a.name }),
          h('span', { cls: 'sub small', text: 'chosen: ' + actionName(i, chosen) + choiceNote(tr, origin, i, chosen) })]));
        stats[i].forEach((r) => {
          const act = a.actions[r.action];
          const bw = bestWorst(r);
          const total = r.succ.length;
          const bar = h('div', { style: 'display:flex;gap:2px;height:10px;min-width:60px', 'aria-hidden': 'true' },
            r.counts.map((n, code) => n ? h('div', { style: 'flex:' + n + ' 1 0;background:' + C.st[code] + ';border-radius:2px;min-width:2px' }) : null));
          const row = h('button', {
            type: 'button', cls: 'tree-row' + (r.action === chosen ? ' chosen' : ''), 'aria-pressed': String(r.action === chosen),
            id: 'tree-' + i + '-' + r.action,
            onclick: () => { S.choice[i] = r.action; render(); },
          }, [
            h('span', { cls: 'act' }, [badge(r.cls), h('span', { cls: 'nm' + (act.is_idle ? ' idle' : ''), text: act.name }),
              h('span', { cls: 'sr-only', text: ' ' + DECISION[r.cls] }),
              act.speculative ? h('span', { cls: 'tag', text: 'speculative' }) : null,
              traceAct === r.action ? h('span', { cls: 'tag', text: 'trace' }) : null]),
            bar,
            h('span', { cls: 'outc' }, ['best ', badge(status(bw[0])), STATUS[status(bw[0])], ' · worst ', badge(status(bw[1])), STATUS[status(bw[1])]]),
            h('span', { cls: 'ends', text: 'best → ' + endingsText(bw[0], 2) + '; worst → ' + endingsText(bw[1], 2) }),
          ]);
          const show = (x, y) => {
            clear(tip);
            tip.appendChild(h('div', { cls: 't-head', text: a.name + '.' + act.name + ' · ' + DECISION[r.cls] }));
            tip.appendChild(h('div', { cls: 't-note', text: DECISION_MEANING[r.cls] }));
            tipSep(tip);
            r.counts.forEach((n, code) => tipRow(tip, STATUS[code], n + ' of ' + total, badge(code)));
            tipSep(tip);
            tipRow(tip, 'guard', act.guard_text || 'True');
            if (act.source) tip.appendChild(h('div', { cls: 't-note', text: 'source: ' + act.source }));
            tipRow(tip, 'speculative', act.speculative ? 'yes' : 'no');
            if (act.delay) tipRow(tip, 'delay', plural(act.delay, TICK));
            tipRow(tip, 'endings (best)', endingsText(bw[0]));
            tipRow(tip, 'endings (worst)', endingsText(bw[1]));
            tipShow(tip, body, x, y);
          };
          row.addEventListener('pointermove', (ev) => { const pos = relPos(ev, body); show(pos[0], pos[1]); });
          row.addEventListener('pointerleave', () => tipHide(tip));
          row.addEventListener('focus', () => show(row.offsetLeft + 40, row.offsetTop + row.offsetHeight - 6));
          row.addEventListener('blur', () => tipHide(tip));
          body.appendChild(row);
        });
      });
      body.appendChild(statusLegend([h('span', { cls: 'item', text: 'bar: successor statuses over all completions' })]));
      treeBranchBar(body, tr, p, m);
    }, (body) => {
      if (!stats) { body.appendChild(notice('No decisions at this state.')); treeBranchBar(body, tr, p, m); return; }
      const rows = [];
      B.actors.forEach((a, i) => stats[i].forEach((r) => {
        const bw = bestWorst(r);
        rows.push([a.name, a.actions[r.action].name, decisionText(r.cls)].concat(r.counts.map(String)).concat([STATUS[status(bw[0])], STATUS[status(bw[1])], endingsText(bw[0]), endingsText(bw[1]), a.actions[r.action].guard_text]));
      }));
      body.appendChild(table(['actor', 'action', 'class', 'kept', 'contested', 'lost', 'failed', 'best', 'worst', 'endings from best', 'endings from worst', 'guard'], rows,
        { num: [false, false, false, true, true, true, true], caption: 'Successor statuses over all completions, state #' + sid }));
      treeBranchBar(body, tr, p, m);
    });
  }

  function treeBranchBar(body, tr, p, m) {
    const bar = h('div', { cls: 'cf-bar' });
    const origin = treeOrigin(tr);
    const canStep = m && !B.states.terminal[origin.sid];
    bar.appendChild(h('button', { type: 'button', id: 'tree-step', disabled: canStep ? null : true, onclick: () => stepBranch(tr) }, 'Step one ' + TICK));
    if (S.cf) {
      bar.appendChild(h('button', { type: 'button', id: 'tree-back', onclick: () => {
        S.cf.states.pop(); S.cf.moves.pop(); S.choice = {};
        if (S.cf.moves.length <= S.cf.start) S.cf = null;
        render();
      } }, 'Back one step'));
      bar.appendChild(h('button', { type: 'button', id: 'tree-reset', onclick: () => { resetBranch(); render(); } }, 'Reset branch'));
      const f = forkIndex(S.cf, tr, S.coal, p);
      const last = S.cf.states[S.cf.states.length - 1];
      let text = 'Branch: ' + plural(S.cf.moves.length - S.cf.start, 'step') + ' from ' + TICK + ' ' + tickOf(S.cf.states[S.cf.start]) + ', now at state #' + last + ' (' + STATUS[status(last)] + (endingOf(last) ? ', ending ' + endingOf(last) : '') + '). ';
      if (f != null) text += 'Fork at ' + TICK + ' ' + tickOf(S.cf.states[f]) + ': ' + STATUS[status(tr.states[f])] + ' on the trace, ' + STATUS[status(S.cf.states[f])] + ' on the branch.';
      else text += 'No status difference from the trace yet.';
      bar.appendChild(h('span', { cls: 'sub', text: text }));
    } else {
      bar.appendChild(h('span', { cls: 'sub small', text: 'Stepping starts a branch from the selected ' + TICK + '; it is drawn on the board and can be compared below.' }));
    }
    body.appendChild(bar);
  }

  function stepBranch(tr) {
    const origin = treeOrigin(tr);
    const m = movesAt(origin.sid);
    if (!m) return;
    const move = m.avail.map((acts, i) => (S.choice[i] != null && acts.indexOf(S.choice[i]) >= 0 ? S.choice[i] : defaultChoice(tr, origin, i, acts)));
    const t = successor(origin.sid, move);
    if (t == null) return;
    if (!S.cf) {
      const base = tr ? tr.states.slice(0, S.tick + 1) : [origin.sid];
      const moves = tr ? tr.moves.slice(0, S.tick) : [];
      S.cf = { start: moves.length, states: base, moves: moves };
    }
    S.cf.moves.push(move);
    S.cf.states.push(t);
    S.choice = {};
    if (S.compare == null || S.compare.indexOf('cf') !== 0) S.compare = 'cf';
    render();
  }

  // ---------------------------------------------------------------- 4. compare
  function compareOptions(trA) {
    const out = [];
    if (S.cf) out.push({ key: 'cf', label: 'your branch from the decision tree' });
    const ref = refEntry(S.hyp, S.ending);
    if (ref && ref.states && (!trA || trA.key === 'ref')) {
      ref.replays.forEach((r) => out.push({ key: 'replay:' + r.hypothesis, label: 'the same moves replayed under ' + hypLabel(r.hypothesis) }));
    }
    B.endings.forEach((e, k) => {
      if (k === S.ending) return;
      const t = refEntry(S.hyp, k);
      if (t && t.states) out.push({ key: 'ending:' + k, label: 'the shortest trace to ' + e });
    });
    return out;
  }

  function compareTrace(key) {
    if (key === 'cf' && S.cf) return { states: S.cf.states, moves: S.cf.moves, stop: null, hyp: S.hyp, label: 'your branch' };
    if (key.indexOf('replay:') === 0) {
      const other = Number(key.slice(7));
      const ref = refEntry(S.hyp, S.ending);
      const r = ref && ref.replays.find((x) => x.hypothesis === other);
      if (!r) return null;
      return { states: r.states, moves: r.moves, stop: r.stop, hyp: other, label: 'replay under ' + hypLabel(other) };
    }
    if (key.indexOf('ending:') === 0) {
      const k = Number(key.slice(7));
      const t = refEntry(S.hyp, k);
      if (!t || !t.states) return null;
      return { states: t.states, moves: t.moves, stop: null, hyp: S.hyp, label: 'shortest trace to ' + B.endings[k] };
    }
    return null;
  }

  function compareVars() {
    // Hypothesis variables differ by construction between hypotheses; built-ins mirror moves.
    return B.variables.map((v, i) => i).filter((i) => !B.variables[i].swept && !B.variables[i].builtin);
  }

  function firstDifference(A, Bt) {
    const vars = compareVars();
    const n = Math.max(A.states.length, Bt.states.length);
    for (let k = 0; k < n; k++) {
      if (k >= A.states.length || k >= Bt.states.length) {
        const shorter = k >= A.states.length ? 'A' : 'B';
        return { k: k, what: 'trace ' + shorter + ' has ended', tickState: (k < A.states.length ? A : Bt).states[k] };
      }
      const sa = A.states[k];
      const sb = Bt.states[k];
      const dv = vars.filter((v) => value(v, sa) !== value(v, sb));
      if (dv.length) {
        return { k: k, tickState: sa, what: dv.map((v) => B.variables[v].name + ' ' + level(v, value(v, sa)) + ' vs ' + level(v, value(v, sb))).join(', ') };
      }
      if (Bt.stop && Bt.stop.index === k && k >= Bt.moves.length) {
        const s = Bt.stop;
        const why = s.reason === 'unavailable' ? actionName(s.actor, s.action) + ' is not available to ' + B.actors[s.actor].name + ' under ' + hypLabel(Bt.hyp) + '; the replay stops' : 'the replay stops (' + s.reason + ')';
        return { k: k, tickState: sa, what: why };
      }
      if (k < A.moves.length && k < Bt.moves.length) {
        const diffs = [];
        A.moves[k].forEach((j, i) => {
          const jb = Bt.moves[k][i];
          if (j !== jb) diffs.push((B.actors[i].is_nature ? 'a Nature event: ' : B.actors[i].name + ' plays ') + actionName(i, j) + ' in A, ' + actionName(i, jb) + ' in B');
        });
        if (diffs.length) return { k: k, tickState: sa, what: diffs.join('; ') };
      }
    }
    return null;
  }

  function hiddenNote(A, Bt) {
    if (A.hyp === Bt.hyp) return null;
    const vars = B.hypotheses.variables;
    const parts = vars.filter((n) => H[A.hyp].values[n] !== H[Bt.hyp].values[n]).map((n) => {
      const v = B.variables.find((x) => x.name === n);
      return n + ' (' + H[A.hyp].values[n] + ' vs ' + H[Bt.hyp].values[n] + (v && v.hidden_from.length ? ', hidden from ' + v.hidden_from.join(', ') : '') + ')';
    });
    return parts.length ? 'The hidden variable differs throughout: ' + parts.join(', ') + '.' : null;
  }

  function renderCompare() {
    const sec = $('sec-compare');
    const A = currentTrace();
    const opts = compareOptions(A);
    if (S.compare == null || !opts.some((o) => o.key === S.compare)) S.compare = opts.length ? (opts.find((o) => o.key.indexOf('replay:') === 0) || opts[0]).key : null;
    const Bt = S.compare ? compareTrace(S.compare) : null;
    const tools = opts.length ? [select('f-compare', 'Trace B', opts.map((o) => [o.key, o.label]), S.compare, (v) => { S.compare = v; render(); })] : [];
    const p = propIndex();
    const diff = A && Bt ? firstDifference(A, Bt) : null;
    const line = A && Bt ? h('p', { cls: 'line-above' }, [h('strong', { text: diff ? 'First difference at ' + TICK + ' ' + tickOf(diff.tickState) + ': ' : 'No difference: ' }),
      diff ? diff.what + '.' : 'the two traces agree at every ' + TICK + '.', ' ', hiddenNote(A, Bt) || '']) : null;
    const sub = A && Bt ? 'A: the ' + A.label + '. B: ' + Bt.label + '. Statuses for ' + coalName(S.coal) + ' against ' + propLabel(p) + '; ◆ marks a cell where B differs (hover for B’s value).' : null;
    figure(sec, 'compare', '4. Compare', sub, tools, (body, tip) => {
      if (!A) { body.appendChild(notice('There is no reference trace to compare.')); return; }
      if (!Bt) { body.appendChild(notice('Nothing to compare with: build a branch in the decision tree, or choose an ending or hypothesis with a trace.')); return; }
      body.appendChild(line);
      drawCompare(body, tip, A, Bt, p, diff);
    }, (body) => {
      if (!A || !Bt) { body.appendChild(notice('Nothing to compare.')); return; }
      body.appendChild(line);
      compareTable(body, A, Bt, p);
    });
  }

  function drawCompare(body, tip, A, Bt, p, diff) {
    const c = S.coal;
    const n = Math.max(A.states.length, Bt.states.length);
    const W = Math.max(300, body.clientWidth || 300);
    const narrow = W < 560;
    const LW = narrow ? 0 : 132;
    const LA = narrow ? 15 : 0;
    const cw = Math.max(narrow ? 60 : 96, Math.min(200, Math.floor((W - LW - 6) / n)));
    const PW = LW + cw * n + 6;
    const colX = (k) => LW + k * cw;
    const stack = (cw - 8) / 2 < 72; // A and B chips one above the other when side by side is too tight
    const vars = compareVars().concat(B.variables.map((v, i) => i).filter((i) => B.variables[i].swept));
    const rowH = 24;
    const heatH = 22;
    const laneH = LA + (stack ? 50 : 28);
    let y = 20;
    const markTop = y; y += 16;
    const stTop = y; y += 2 * (rowH + LA) + 10;
    const laneTop = y; y += NA * laneH + 10;
    const heatTop = y; y += vars.length * (heatH + LA);
    const PH = y + 6;
    const wrap = h('div', { cls: 'scroll-x chart' });
    const svg = sv('svg', { width: PW, height: PH, viewBox: '0 0 ' + PW + ' ' + PH, id: 'compare-svg', tabindex: 0, role: 'img', 'aria-label': 'Compare trace A with trace B on one ' + TICK + ' axis', 'font-family': FONT });
    wrap.appendChild(svg);
    body.appendChild(wrap);
    const colA = C.slot[0];
    const colB = C.slot[1];
    for (let k = 0; k < n; k++) {
      const s = k < A.states.length ? A.states[k] : Bt.states[k];
      svg.appendChild(sv('text', { x: colX(k) + cw / 2, y: 12, 'text-anchor': 'middle', 'font-size': 11, fill: C.muted, text: String(tickOf(s)) }));
    }
    svg.appendChild(sv('text', { x: 0, y: 12, 'font-size': 11, fill: C.muted, text: TICK }));
    const label = (top, height, text, color, bold) => {
      const base = LA ? top + 11 : top + height / 2 + 4;
      const room = LA ? PW : LW;
      if (color) svg.appendChild(sv('rect', { x: 0, y: base - 5, width: 12, height: 2, rx: 1, fill: color }));
      svg.appendChild(sv('text', { x: color ? 16 : 0, y: base, 'font-size': 11.5, 'font-weight': bold ? 600 : 400, fill: bold ? C.ink : C.ink2, text: fitText(text, room - (color ? 20 : 4), 11.5, bold ? 600 : 400) }));
    };
    // markers: the first difference and the replay stop (merged when they coincide)
    const marks = {};
    if (diff) marks[diff.k] = ['\u25c6 first difference'];
    if (Bt.stop) (marks[Bt.stop.index] = marks[Bt.stop.index] || []).push('\u2298 B stops');
    let lastEnd = -Infinity;
    Object.keys(marks).map(Number).sort((a, b) => a - b).forEach((k) => {
      const x = colX(k);
      svg.appendChild(sv('line', { x1: x, x2: x, y1: markTop + 4, y2: stTop + 2 * (rowH + LA), stroke: C.ink, 'stroke-width': 1 }));
      const text = marks[k].join(' \u00b7 ');
      const w = textWidth(text, 11, 600);
      let tx = x + 4;
      if (tx + w > PW) tx = x - 4 - w;
      if (tx < lastEnd + 6) return; // the line still marks it; the sentence above names it
      svg.appendChild(sv('text', { x: tx, y: markTop + 8, 'font-size': 11, 'font-weight': 600, fill: C.ink, text: text }));
      lastEnd = tx + w;
    });
    [[A, 'A', colA], [Bt, 'B', colB]].forEach((pair, r) => {
      const t = pair[0];
      const top = stTop + r * (rowH + LA);
      label(top, rowH, pair[1] + ': ' + coalName(c), pair[2], r === 0);
      t.states.forEach((s, k) => {
        const code = status(s, c, p);
        if (code >= 0) statusCell(svg, colX(k) + 1, top + LA + 2, cw - 2, rowH - 4, code, 1, { 'data-row': pair[1] });
      });
    });
    // decision lanes: A and B chips (side by side, or stacked when narrow); a 2px trace key under each
    B.actors.forEach((a, i) => {
      const top = laneTop + i * laneH;
      svg.appendChild(sv('line', { x1: 0, x2: PW, y1: top - 2, y2: top - 2, stroke: C.grid }));
      const base = LA ? top + 11 : top + 15;
      svg.appendChild(sv('rect', { x: 0, y: base - 10, width: 3, height: 12, rx: 1, fill: actorColor(i) }));
      svg.appendChild(sv('text', { x: 7, y: base, 'font-size': 11.5, 'font-weight': 600, fill: C.ink, text: fitText(a.name, (LA ? PW : LW) - 12, 11.5, 600) }));
      const w = stack ? cw - 6 : (cw - 8) / 2;
      for (let k = 0; k < n; k++) {
        const ja = k < A.moves.length ? A.moves[k][i] : null;
        const jb = k < Bt.moves.length ? Bt.moves[k][i] : null;
        const xa = colX(k) + 3;
        const ya = top + LA + 1;
        const xb = stack ? xa : colX(k) + 5 + w;
        const yb = stack ? ya + 23 : ya;
        if (ja != null) {
          drawChip(svg, xa, ya, w, i, ja, {});
          svg.appendChild(sv('rect', { x: xa + 2, y: ya + 19, width: w - 2, height: 2, fill: colA }));
        }
        if (jb != null) {
          drawChip(svg, xb, yb, w, i, jb, { diff: ja != null && ja !== jb });
          svg.appendChild(sv('rect', { x: xb + 2, y: yb + 19, width: w - 2, height: 2, fill: colB }));
        } else if (Bt.stop && k === Bt.stop.index && ja != null) {
          svg.appendChild(sv('text', { x: xb + 6, y: yb + 14, 'font-size': 11, fill: C.ink2, text: fitText('\u2298 stops', w - 8, 11, 400) }));
        }
      }
    });
    vars.forEach((v, r) => {
      const top = heatTop + r * (heatH + LA);
      const spec = B.variables[v];
      label(top, heatH, spec.name + (spec.swept ? ' (hypothesis)' : ''), null, false);
      let prev = null;
      A.states.forEach((s, k) => {
        const x = value(v, s);
        const fill = rampColor(x, spec.levels.length);
        svg.appendChild(sv('rect', { x: colX(k) + 1, y: top + LA + 2, width: cw - 2, height: heatH - 4, rx: 2, fill: fill }));
        let right = 4;
        if (k < Bt.states.length && value(v, Bt.states[k]) !== x) {
          svg.appendChild(sv('text', { x: colX(k) + cw - 6, y: top + LA + heatH / 2 + 4, 'text-anchor': 'end', 'font-size': 10, fill: onFill(fill), opacity: 0.75, text: '\u25c6' }));
          right = 16;
        }
        const name = level(v, x);
        if ((k === 0 || x !== prev) && textWidth(name, 11, 500) <= cw - 6 - right - 6) {
          svg.appendChild(sv('text', { x: colX(k) + 6, y: top + LA + heatH / 2 + 4, 'font-size': 11, 'font-weight': 500, fill: onFill(fill), text: name }));
        }
        prev = x;
      });
    });
    const cross = sv('line', { x1: 0, x2: 0, y1: stTop, y2: PH, stroke: C.ink2, 'stroke-width': 1, visibility: 'hidden', 'pointer-events': 'none' });
    svg.appendChild(cross);
    const hit = sv('rect', { x: LW, y: 0, width: cw * n, height: PH, fill: 'transparent' });
    svg.appendChild(hit);
    let focusK = 0;
    const showAt = (k, px, py) => {
      cross.setAttribute('x1', colX(k) + cw / 2);
      cross.setAttribute('x2', colX(k) + cw / 2);
      cross.setAttribute('visibility', 'visible');
      clear(tip);
      const sa = k < A.states.length ? A.states[k] : null;
      const sb = k < Bt.states.length ? Bt.states[k] : null;
      tip.appendChild(h('div', { cls: 't-head', text: TICK + ' ' + tickOf(sa != null ? sa : sb) }));
      tipRow(tip, 'A status', sa != null ? STATUS[status(sa, c, p)] : 'ended', lineKey(colA));
      tipRow(tip, 'B status', sb != null ? STATUS[status(sb, c, p)] : (Bt.stop ? 'stopped' : 'ended'), lineKey(colB));
      tipSep(tip);
      B.actors.forEach((a, i) => {
        const ja = k < A.moves.length ? actionName(i, A.moves[k][i]) : '-';
        const jb = k < Bt.moves.length ? actionName(i, Bt.moves[k][i]) : '-';
        tipRow(tip, a.name, ja === jb ? ja : ja + ' / ' + jb + ' \u25c6', lineKey(actorColor(i)));
      });
      tipSep(tip);
      vars.forEach((v) => {
        const va = sa != null ? level(v, value(v, sa)) : '-';
        const vb = sb != null ? level(v, value(v, sb)) : '-';
        tipRow(tip, B.variables[v].name, va === vb ? va : va + ' / ' + vb + ' \u25c6');
      });
      tip.appendChild(h('div', { cls: 't-note muted', text: 'values: A / B' }));
      tipShow(tip, body, px, py);
    };
    const colAt = (ev) => { const r = svg.getBoundingClientRect(); return Math.max(0, Math.min(n - 1, Math.floor((ev.clientX - r.left - LW) / cw))); };
    hit.addEventListener('pointermove', (ev) => { const pos = relPos(ev, body); showAt(colAt(ev), pos[0], pos[1]); });
    hit.addEventListener('pointerleave', () => { cross.setAttribute('visibility', 'hidden'); tipHide(tip); });
    svg.addEventListener('focus', () => showAt(focusK, colX(focusK) + cw / 2 - wrap.scrollLeft, stTop + 40));
    svg.addEventListener('blur', () => { cross.setAttribute('visibility', 'hidden'); tipHide(tip); });
    svg.addEventListener('keydown', (ev) => {
      if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      ev.preventDefault();
      focusK = Math.max(0, Math.min(n - 1, focusK + (ev.key === 'ArrowRight' ? 1 : -1)));
      showAt(focusK, colX(focusK) + cw / 2 - wrap.scrollLeft, stTop + 40);
    });
    body.appendChild(h('div', { cls: 'legend' }, [h('span', { cls: 'item' }, [lineKey(colA), 'A: ' + A.label]), h('span', { cls: 'item' }, [lineKey(colB), 'B: ' + Bt.label]),
      h('span', { cls: 'item' }, ['\u25c6 B differs']), h('span', { cls: 'item' }, ['\u2298 replay stops (an action is not available)'])]));
    body.appendChild(statusLegend());
  }

  function compareTable(body, A, Bt, p) {
    const c = S.coal;
    const n = Math.max(A.states.length, Bt.states.length);
    const vars = compareVars().concat(B.variables.map((v, i) => i).filter((i) => B.variables[i].swept));
    const head = [TICK, 'A status', 'B status'].concat(B.actors.map((a) => a.name + ' (A / B)')).concat(['variables that differ (A vs B)']);
    const rows = [];
    for (let k = 0; k < n; k++) {
      const sa = k < A.states.length ? A.states[k] : null;
      const sb = k < Bt.states.length ? Bt.states[k] : null;
      const row = [String(tickOf(sa != null ? sa : sb)), sa != null ? statusText(status(sa, c, p)) : 'ended', sb != null ? statusText(status(sb, c, p)) : (Bt.stop ? 'stopped' : 'ended')];
      B.actors.forEach((a, i) => {
        const ja = k < A.moves.length ? actionName(i, A.moves[k][i]) : '-';
        const jb = k < Bt.moves.length ? actionName(i, Bt.moves[k][i]) : '-';
        row.push(ja === jb ? ja : ja + ' / ' + jb + ' ◆');
      });
      const dv = sa != null && sb != null ? vars.filter((v) => value(v, sa) !== value(v, sb)).map((v) => B.variables[v].name + ': ' + level(v, value(v, sa)) + ' vs ' + level(v, value(v, sb))) : [];
      row.push(dv.join('; ') || '-');
      rows.push(row);
    }
    body.appendChild(table(head, rows, { caption: 'A: ' + A.label + '. B: ' + Bt.label + '.' }));
  }

  // ---------------------------------------------------------------- 5. landscape
  function hash01(x) {
    let v = (x + 0x9e3779b9) | 0;
    v = Math.imul(v ^ (v >>> 16), 0x85ebca6b);
    v = Math.imul(v ^ (v >>> 13), 0xc2b2ae35);
    v ^= v >>> 16;
    return (v >>> 0) / 4294967296;
  }

  function landscapePoints() {
    const depth = B.states.depth[S.hyp];
    const pts = [];
    for (let s = 0; s < B.states.count; s++) if (depth[s] >= 0) pts.push(s);
    return pts;
  }

  function renderLandscape() {
    const sec = $('sec-landscape');
    const p = propIndex();
    const varOpts = B.variables.map((v, i) => [i, v.name + (v.builtin ? ' (built-in)' : '')]);
    const tools = [
      select('f-lvar', 'y: variable', varOpts, S.lvar, (v) => { S.lvar = Number(v); render(); }),
      h('span', { cls: 'seg', role: 'group', 'aria-label': 'Landscape mode' }, [['status', 'Status'], ['forward', 'Forward'], ['backward', 'Backward']].filter((m) => m[0] !== 'backward' || B.endings.length).map((m) => h('button', {
        type: 'button', id: 'lmode-' + m[0], 'aria-pressed': String(S.lmode === m[0]), onclick: () => { S.lmode = m[0]; render(); },
      }, m[1]))),
    ];
    if (S.lmode === 'backward') {
      tools.splice(1, 0, select('f-lby', 'forced by', [[NC, 'any play (every actor and Nature)']].concat(B.coalitions.map((c, i) => [i, c.name])), S.lby, (v) => { S.lby = Number(v); render(); }));
    }
    const pts = landscapePoints();
    const e = B.endings[S.ending];
    const what = {
      status: 'colored by status for ' + coalName(S.coal) + ' against ' + propLabel(p),
      forward: 'colored by breadth-first depth from the initial state (the forward wavefront)',
      backward: 'colored by attractor rank to ' + e + ' for ' + (S.lby === NC ? 'any play' : coalName(S.lby)) + ' (the backward wavefront)',
    }[S.lmode];
    const sub = fmtInt(pts.length) + ' states reachable from ' + hypLabel(S.hyp) + ': x = ' + TICK + ', y = ' + B.variables[S.lvar].name + ' (jittered inside the level band), ' + what + '. Terminal states are flags; the line is the ' + ((currentTrace() || {}).short || 'trace') + '.';
    figure(sec, 'landscape', '5. Landscape', sub, tools, (body, tip) => drawLandscape(body, tip, pts, p), (body) => landscapeTable(body, pts, p));
  }

  function landscapeColor(s, p) {
    if (S.lmode === 'status') return C.st[status(s, S.coal, p)];
    if (S.lmode === 'forward') return seqColor(B.states.depth[S.hyp][s], LSCALE.max);
    const r = rankOf(S.ending, S.lby, s);
    return r < 0 ? C.axis : seqColor(r, LSCALE.max);
  }

  const LSCALE = { max: 0 };

  function drawLandscape(body, tip, pts, p) {
    const v = S.lvar;
    const spec = B.variables[v];
    const nL = spec.levels.length;
    const tr = currentTrace();
    const W = Math.max(300, body.clientWidth || 300);
    const LM = Math.min(W < 560 ? 70 : 120, Math.max(...spec.levels.map((l) => textWidth(l, 11))) + 14);
    const RM = 14;
    const TM = 22;
    const BM = 34;
    const plotW = W - LM - RM;
    const plotH = Math.max(220, Math.min(460, nL * 64));
    const PW = W;
    const PH = TM + plotH + BM;
    let maxX = 0;
    for (const s of pts) if (tickOf(s) > maxX) maxX = tickOf(s);
    const bandW = plotW / (maxX + 1);
    const bandH = plotH / nL;
    const xOf = (s) => LM + (tickOf(s) + 0.5 + (hash01(s) - 0.5) * 0.72) * bandW;
    const yOf = (s) => TM + (nL - 1 - value(v, s) + 0.5 + (hash01(s * 7 + 3) - 0.5) * 0.74) * bandH;
    LSCALE.max = 0;
    for (const s of pts) {
      const x = S.lmode === 'forward' ? B.states.depth[S.hyp][s] : S.lmode === 'backward' ? rankOf(S.ending, S.lby, s) : 0;
      if (x > LSCALE.max) LSCALE.max = x;
    }

    const box = h('div', { cls: 'chart', style: 'position:relative;width:' + PW + 'px;height:' + PH + 'px;max-width:100%' });
    body.appendChild(box);
    // gridlines and axes (SVG underlay)
    const under = sv('svg', { width: PW, height: PH, style: 'position:absolute;left:0;top:0', 'aria-hidden': 'true', 'font-family': FONT });
    box.appendChild(under);
    for (let l = 0; l <= nL; l++) under.appendChild(sv('line', { x1: LM, x2: LM + plotW, y1: TM + l * bandH, y2: TM + l * bandH, stroke: C.grid, 'stroke-width': 1 }));
    under.appendChild(sv('line', { x1: LM, x2: LM + plotW, y1: TM + plotH, y2: TM + plotH, stroke: C.axis, 'stroke-width': 1 }));
    for (let l = 0; l < nL; l++) {
      const t = fitText(spec.levels[l], LM - 10, 11, 400);
      under.appendChild(sv('text', { x: LM - 6, y: TM + (nL - 1 - l + 0.5) * bandH + 4, 'text-anchor': 'end', 'font-size': 11, fill: C.ink2, text: t }));
    }
    const every = Math.max(1, Math.ceil(26 / bandW));
    for (let x = 0; x <= maxX; x += every) {
      under.appendChild(sv('text', { x: LM + (x + 0.5) * bandW, y: TM + plotH + 14, 'text-anchor': 'middle', 'font-size': 11, fill: C.muted, text: String(x) }));
    }
    under.appendChild(sv('text', { x: LM + plotW / 2, y: TM + plotH + 30, 'text-anchor': 'middle', 'font-size': 11, fill: C.ink2, text: B.meta.timed ? 'tick' : 'depth' }));
    under.appendChild(sv('text', { x: 0, y: 12, 'font-size': 11, fill: C.ink2, text: spec.name }));

    // points: canvas above 5,000 points, SVG otherwise
    const useCanvas = pts.length > 5000;
    const order = pts.slice();
    if (S.lmode === 'status') {
      const counts = [0, 0, 0, 0];
      for (const s of order) counts[status(s, S.coal, p)]++;
      order.sort((a, b) => counts[status(b, S.coal, p)] - counts[status(a, S.coal, p)]);
    }
    const dim = (s) => S.lmode === 'status' && S.isoStatus != null && status(s, S.coal, p) !== S.isoStatus;
    const terminal = B.states.terminal;
    const flagPath = (x, y) => 'M' + x + ' ' + (y + 2) + 'V' + (y - 5) + 'L' + (x + 4) + ' ' + (y - 3.2) + 'L' + x + ' ' + (y - 1.5) + 'Z';
    if (useCanvas) {
      const dpr = window.devicePixelRatio || 1;
      const cv = h('canvas', { width: Math.round(PW * dpr), height: Math.round(PH * dpr), style: 'position:absolute;left:0;top:0;width:' + PW + 'px;height:' + PH + 'px', 'aria-hidden': 'true' });
      box.appendChild(cv);
      const ctx = cv.getContext('2d');
      ctx.scale(dpr, dpr);
      for (const s of order) {
        const x = xOf(s);
        const y = yOf(s);
        ctx.globalAlpha = dim(s) ? 0.1 : 0.9;
        ctx.fillStyle = landscapeColor(s, p);
        if (terminal[s]) {
          ctx.strokeStyle = ctx.fillStyle;
          ctx.lineWidth = 1;
          ctx.fill(new Path2D(flagPath(x, y)));
          ctx.beginPath(); ctx.moveTo(x, y + 2); ctx.lineTo(x, y - 5); ctx.stroke();
        } else {
          ctx.beginPath();
          ctx.arc(x, y, 2.2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
    }
    const over = sv('svg', { width: PW, height: PH, style: 'position:absolute;left:0;top:0', id: 'landscape-svg', tabindex: 0, role: 'img', 'font-family': FONT,
      'aria-label': 'Landscape of ' + pts.length + ' reachable states; focus and use the arrow keys to walk the trace' });
    box.appendChild(over);
    if (!useCanvas) {
      const g = sv('g');
      over.appendChild(g);
      for (const s of order) {
        const x = xOf(s);
        const y = yOf(s);
        const fill = landscapeColor(s, p);
        const op = dim(s) ? 0.1 : 0.9;
        if (terminal[s]) g.appendChild(sv('path', { d: flagPath(x, y), fill: fill, stroke: fill, 'stroke-width': 1, opacity: op }));
        else g.appendChild(sv('circle', { cx: x.toFixed(1), cy: y.toFixed(1), r: 2.6, fill: fill, opacity: op }));
      }
    }
    // ending labels, one per ending at its densest cell, skipped on collision
    const placed = [];
    const byEnding = {};
    for (const s of pts) {
      if (!terminal[s]) continue;
      const e = endingOf(s) || 'terminal';
      const key = tickOf(s) + ':' + value(v, s);
      const m = byEnding[e] || (byEnding[e] = {});
      m[key] = (m[key] || 0) + 1;
    }
    const halo = { stroke: C.surface, 'stroke-width': 3, 'paint-order': 'stroke', 'stroke-linejoin': 'round' };
    Object.keys(byEnding).forEach((e) => {
      const cells = byEnding[e];
      const best = Object.keys(cells).sort((a, b) => cells[b] - cells[a])[0];
      const parts = best.split(':').map(Number);
      const text = '⚑ ' + e;
      const w = textWidth(text, 11, 600);
      let x = LM + (parts[0] + 0.5) * bandW - w / 2;
      x = Math.max(LM + 2, Math.min(LM + plotW - w - 2, x));
      let y = TM + (nL - 1 - parts[1]) * bandH + 12;
      for (let tries = 0; tries < 4; tries++) {
        const bx = [x - 2, y - 11, x + w + 2, y + 3];
        if (!placed.some((p2) => !(bx[2] < p2[0] || bx[0] > p2[2] || bx[3] < p2[1] || bx[1] > p2[3]))) {
          placed.push(bx);
          over.appendChild(sv('text', Object.assign({ x: x, y: y, 'font-size': 11, 'font-weight': 600, fill: C.ink, text: text, 'pointer-events': 'none' }, halo)));
          return;
        }
        y += 14;
      }
    });
    // reference trace: 2px line, 8px markers with surface rings
    if (tr) {
      const d = tr.states.map((s, k) => (k ? 'L' : 'M') + xOf(s).toFixed(1) + ' ' + yOf(s).toFixed(1)).join('');
      over.appendChild(sv('path', { d: d, fill: 'none', stroke: C.ink, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', 'pointer-events': 'none' }));
      tr.states.forEach((s) => over.appendChild(sv('circle', { cx: xOf(s), cy: yOf(s), r: 4, fill: landscapeColor(s, p), stroke: C.surface, 'stroke-width': 2, 'pointer-events': 'none' })));
    }
    // nearest-point hover with a 24px hit area
    const cell = 24;
    const grid = new Map();
    for (const s of pts) {
      const key = Math.floor(xOf(s) / cell) + ',' + Math.floor(yOf(s) / cell);
      if (!grid.has(key)) grid.set(key, []);
      grid.get(key).push(s);
    }
    const nearest = (x, y) => {
      let best = null;
      let bd = 12 * 12;
      const gx = Math.floor(x / cell);
      const gy = Math.floor(y / cell);
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
        const list = grid.get((gx + dx) + ',' + (gy + dy));
        if (!list) continue;
        for (const s of list) {
          const ddx = xOf(s) - x;
          const ddy = yOf(s) - y;
          const dd = ddx * ddx + ddy * ddy;
          if (dd <= bd) { bd = dd; best = s; }
        }
      }
      return best;
    };
    const ring = sv('circle', { r: 6, fill: 'none', stroke: C.ink, 'stroke-width': 1.5, visibility: 'hidden', 'pointer-events': 'none' });
    over.appendChild(ring);
    const show = (s, px, py) => {
      ring.setAttribute('cx', xOf(s));
      ring.setAttribute('cy', yOf(s));
      ring.setAttribute('visibility', 'visible');
      stateTip(tip, s, null, TICK + ' ' + tickOf(s) + ' · state #' + s, (t) => {
        tipRow(t, 'depth from s₀', String(B.states.depth[S.hyp][s]));
        if (B.endings.length) {
          const r = rankOf(S.ending, S.lby, s);
          tipRow(t, 'rank to ' + B.endings[S.ending], r < 0 ? 'cannot force' : String(r));
        }
      });
      tipShow(tip, body, px, py);
    };
    over.addEventListener('pointermove', (ev) => {
      const r = over.getBoundingClientRect();
      const s = nearest(ev.clientX - r.left, ev.clientY - r.top);
      if (s == null) { ring.setAttribute('visibility', 'hidden'); tipHide(tip); return; }
      const pos = relPos(ev, body);
      show(s, pos[0], pos[1]);
    });
    over.addEventListener('pointerleave', () => { ring.setAttribute('visibility', 'hidden'); tipHide(tip); });
    const walk = tr ? tr.states : [H[S.hyp].state];
    over.addEventListener('focus', () => { S.lfocus = Math.min(S.lfocus, walk.length - 1); const s = walk[S.lfocus]; show(s, xOf(s), yOf(s)); });
    over.addEventListener('blur', () => { ring.setAttribute('visibility', 'hidden'); tipHide(tip); });
    over.addEventListener('keydown', (ev) => {
      if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
      ev.preventDefault();
      S.lfocus = Math.max(0, Math.min(walk.length - 1, S.lfocus + (ev.key === 'ArrowRight' ? 1 : -1)));
      const s = walk[S.lfocus];
      show(s, xOf(s), yOf(s));
    });
    // legend
    if (S.lmode === 'status') {
      body.appendChild(h('div', { cls: 'legend', 'aria-label': 'Status (click to isolate)' }, STATUS.map((name, code) => h('button', {
        type: 'button', cls: 'item' + (S.isoStatus != null && S.isoStatus !== code ? ' off' : ''), 'aria-pressed': String(S.isoStatus === code), title: STATUS_MEANING[code],
        onclick: () => { S.isoStatus = S.isoStatus === code ? null : code; render(); },
      }, [badge(code), name])).concat([h('span', { cls: 'item' }, ['⚑ terminal state']), h('span', { cls: 'item' }, [lineKey(C.ink), 'trace'])])));
    } else {
      const ramp = 'linear-gradient(90deg,' + C.ramp.join(',') + ')';
      const label = S.lmode === 'forward' ? 'depth from the initial state' : 'rank to ' + B.endings[S.ending] + ' (' + TICK + 's to force it)';
      body.appendChild(h('div', { cls: 'legend' }, [h('span', { cls: 'item' }, ['0 ', h('span', { cls: 'scale-bar', style: 'background:' + ramp }), ' ' + LSCALE.max]), h('span', { cls: 'item', text: label }),
        S.lmode === 'backward' ? h('span', { cls: 'item' }, [h('span', { cls: 'key-dot', style: 'background:' + C.axis }), 'cannot force']) : null,
        h('span', { cls: 'item' }, ['⚑ terminal state']), h('span', { cls: 'item' }, [lineKey(C.ink), 'trace'])]));
    }
  }

  function landscapeTable(body, pts, p) {
    const c = S.coal;
    const v = S.lvar;
    const byTick = {};
    const byLevel = {};
    for (const s of pts) {
      const t = tickOf(s);
      const code = status(s, c, p);
      const row = byTick[t] || (byTick[t] = [0, 0, 0, 0, 0]);
      row[code]++;
      if (B.states.terminal[s]) row[4]++;
      const lv = value(v, s);
      const lr = byLevel[lv] || (byLevel[lv] = [0, 0, 0, 0, 0]);
      lr[code]++;
      if (B.states.terminal[s]) lr[4]++;
    }
    const num = [false, true, true, true, true, true, true];
    const mk = (r) => r.slice(0, 4).map(String).concat([String(r[4]), String(r[0] + r[1] + r[2] + r[3])]);
    body.appendChild(table([TICK].concat(STATUS).concat(['terminal', 'total']), Object.keys(byTick).map(Number).sort((a, b) => a - b).map((t) => [String(t)].concat(mk(byTick[t]))),
      { num: num, caption: 'Reachable states per ' + TICK + ' and status (' + coalName(c) + ', ' + propLabel(p) + ')' }));
    body.appendChild(table([B.variables[v].name].concat(STATUS).concat(['terminal', 'total']), Object.keys(byLevel).map(Number).sort((a, b) => a - b).map((l) => [level(v, l)].concat(mk(byLevel[l]))),
      { num: num, caption: 'Reachable states per level of ' + B.variables[v].name + ' and status' }));
  }

  // ---------------------------------------------------------------- 6. tables
  function renderTables() {
    const sec = $('sec-tables');
    clear(sec);
    const item = H[S.hyp];
    const T = item.tables;
    sec.appendChild(h('div', { cls: 'fig-head' }, h('h2', { id: 'h-tables', text: '6. Tables' })));
    sec.appendChild(h('p', { cls: 'fig-sub', text: 'The numbers the Markdown report prints, computed from the initial state of ' + item.label + '.' }));
    const fmtSet = (s) => (s.length ? '{' + s.join(', ') + '}' : '{} (no relaxation)');
    sec.appendChild(h('h3', { text: 'Minimal relaxation sets' }));
    sec.appendChild(h('p', { cls: 'sub small', text: 'Smallest sets of named assumptions (guards, fairness constraints, selected profiles, assume restrictions) whose relaxation makes each ending reachable from some initial state of ' + item.label + ', searched up to size ' + T.max_relax + '.' }));
    sec.appendChild(table(['ending', 'minimum size', 'minimal sets', 'not counted'], T.relaxations.map((r) => [r.ending, r.minimum_size == null ? '> ' + r.max_size : String(r.minimum_size),
      r.sets.length ? r.sets.map(fmtSet).join('; ') : 'none found',
      (r.ill_formed.length || r.undecided.length) ? h('details', { cls: 'small' }, [
        h('summary', { text: [r.ill_formed.length ? r.ill_formed.length + ' ill-formed' : null, r.undecided.length ? r.undecided.length + ' undecided' : null].filter(Boolean).join(', ') }),
      ].concat(r.ill_formed.map((x) => h('div', { text: fmtSet(x.set) + ' ill-formed: ' + x.message }))).concat(r.undecided.map((x) => h('div', { text: fmtSet(x.set) + ' undecided: ' + x.message })))) : '-']), { num: [false, true] }));
    sec.appendChild(h('p', { cls: 'sub small', text: 'Not counted: relaxations whose model raised an error (ill-formed) or passed the exploration budget (undecided). From an explicit initial state, relaxing a fairness constraint removes its counter from the state, so those relaxations are reported as ill-formed.' }));
    sec.appendChild(h('h3', { text: 'Pivotal coalitions' }));
    sec.appendChild(h('p', { cls: 'sub small', text: 'Minimal coalitions of declared actors (Nature always adversarial) that can force, or block, each ending from the initial state of ' + item.label + '.' }));
    const fmtC = (cs) => (cs.length ? cs.map((c) => '{' + c.join(', ') + '}').join('; ') : 'none');
    sec.appendChild(table(['ending', 'forcing', 'blocking'], T.pivotal.map((r) => [r.ending, fmtC(r.forcing), fmtC(r.blocking)])));
    sec.appendChild(h('h3', { text: 'Sensitivity' }));
    if (!T.sensitivity.length) sec.appendChild(h('p', { cls: 'sub small', text: 'No invariant is declared, so there is nothing to perturb against.' }));
    T.sensitivity.forEach((g) => {
      const rows = g.rows.slice(0, 25).map((r) => r.error ? [r.variable, r.from + ' → ' + r.to, String(r.states), 'error', '-', r.error] : [r.variable, r.from + ' → ' + r.to, String(r.states),
        r.base_in_kernel + ' → ' + r.new_in_kernel, String(r.flips), (r.base_shortest == null ? 'never' : r.base_shortest) + ' → ' + (r.new_shortest == null ? 'never' : r.new_shortest)]);
      sec.appendChild(table(['variable', 'initial value', 'states', 'in kernel', 'flips', 'min shortest'], rows,
        { caption: 'Invariant ' + g.invariant + ' for {' + g.coalition.join(', ') + '}' + (g.rows.length > 25 ? ' (first 25 of ' + g.rows.length + ' rows)' : ''), num: [false, false, true, false, true] }));
    });
    sec.appendChild(h('h3', { text: 'Speculative actions used by the shown traces' }));
    const spec = B.tables.speculative;
    if (!spec.length) sec.appendChild(h('p', { cls: 'sub small', text: 'None of the shown traces uses a speculative action.' }));
    else {
      const rows = spec.map((name) => {
        const dot = name.indexOf('.');
        const a = B.actors.find((x) => x.name === name.slice(0, dot));
        const act = a && a.actions.find((x) => x.name === name.slice(dot + 1));
        return [name, act ? act.source : '', act ? act.guard_text : ''];
      });
      sec.appendChild(table(['action', 'source', 'guard'], rows));
    }
    sec.appendChild(h('h3', { text: 'Strategy uniformity' }));
    if (!T.uniformity.length) sec.appendChild(h('p', { cls: 'sub small', text: 'No forcing or keeping result holds from this initial state.' }));
    else {
      sec.appendChild(table(['result', 'coalition', 'uniform per member', 'uniform on pooled observations', 'conflicts'], T.uniformity.map((u) => [
        (u.kind === 'keep' ? 'keeping ' : 'forcing ') + u.subject, '{' + u.coalition.join(', ') + '}', u.uniform ? 'yes' : 'no (upper bound)', u.jointly_uniform ? 'yes' : 'no',
        u.example ? u.conflicts + ', e.g. ' + u.example[0] + ' cannot tell #' + u.example[1] + ' from #' + u.example[2] : '0']), { num: [false, false, false, false, false] }));
    }
    sec.appendChild(h('h3', { text: 'Parameter budget' }));
    sec.appendChild(table(['quantity', 'count'], Object.keys(B.meta.budget).map((k) => [k.replace(/_/g, ' '), fmtInt(B.meta.budget[k])]), { num: [false, true] }));
  }

  // ---------------------------------------------------------------- theme, hash, render
  function loadTheme() {
    try { const t = window.localStorage.getItem('wf-viz-theme'); if (t === 'light' || t === 'dark' || t === 'system') return t; } catch (e) { /* storage unavailable */ }
    return 'system';
  }

  function saveTheme() {
    try { window.localStorage.setItem('wf-viz-theme', S.theme); } catch (e) { /* storage unavailable */ }
  }

  function applyTheme() {
    if (S.theme === 'light' || S.theme === 'dark') document.documentElement.setAttribute('data-theme', S.theme);
    else document.documentElement.removeAttribute('data-theme');
  }

  function readHash() {
    try {
      const q = new URLSearchParams(window.location.hash.slice(1));
      const num = (k, max) => { const v = q.get(k); if (v == null) return null; const n = Number(v); return Number.isInteger(n) && n >= 0 && n < max ? n : null; };
      const hyp = num('h', H.length); if (hyp != null) S.hyp = hyp;
      const c = num('c', NC); if (c != null) S.coal = c;
      const e = num('e', B.endings.length); if (e != null) S.ending = e;
      const p = q.get('p'); if (p === 'auto' || (p != null && Number(p) >= 0 && Number(p) < B.properties.length)) S.prop = p;
      const t = q.get('theme'); if (t === 'light' || t === 'dark' || t === 'system') S.theme = t;
    } catch (e) { /* ignore a malformed hash */ }
  }

  function writeHash() {
    try {
      const q = 'h=' + S.hyp + '&c=' + S.coal + '&e=' + S.ending + '&p=' + S.prop;
      if (window.location.hash.slice(1) !== q) window.history.replaceState(null, '', '#' + q);
    } catch (e) { /* not available in this context */ }
  }

  function render() {
    const active = document.activeElement && document.activeElement.id;
    C = readColors();
    renderFilters();
    renderTiles();
    renderInitial();
    renderBoard();
    renderTree();
    renderCompare();
    renderLandscape();
    renderTables();
    renderFooter();
    writeHash();
    if (active) {
      const e = document.getElementById(active);
      if (e && e !== document.activeElement) e.focus({ preventScroll: true });
    }
  }

  applyTheme();
  C = readColors();
  renderHeader();
  render();
  let lastW = document.documentElement.clientWidth;
  let timer = null;
  window.addEventListener('resize', () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const w = document.documentElement.clientWidth;
      if (w !== lastW) { lastW = w; render(); }
    }, 120);
  });
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => { if (S.theme === 'system') render(); });
  } catch (e) { /* older engines */ }
})();
