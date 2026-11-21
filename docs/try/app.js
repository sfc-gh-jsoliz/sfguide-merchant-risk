/* Merchant Risk & Underwriting: hosted no-account example. Same data and logic as the
   Streamlit app's Sample mode (app/data.py). Always Sample mode; AI answers were captured
   from Live runs on Snowflake and are labeled "Sample AI response". No dependencies. */
(function () {
  "use strict";
  var D = window.MRU;
  var DEC = ["approve", "refer", "decline"];
  var FILL = { approve: "#2E8A5F", refer: "#D49A1F", decline: "#B02A1E" };
  var TIERS = ["A-Prime", "B-NearPrime", "C-Subprime", "D-HighRisk"];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MONL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  var VIEWS = [["portfolio", "Portfolio"], ["applications", "Applications"], ["segments", "Segments"], ["notes", "Underwriting notes"], ["ask", "Ask the agent"]];
  var SCOPES = { ALL: "Whole book", ELECTRONICS: "Electronics & Appliances", RESTAURANTS: "Restaurants & Food Service",
    FURNITURE: "Furniture & Home Furnishings", APPAREL: "Clothing & Accessories", HEALTH: "Health & Personal Care", GROCERY: "Food & Beverage Stores" };
  var FACTORS = [["f_category", "Category base risk"], ["f_chargebacks", "Chargeback history"], ["f_credit_tier", "Credit tier"],
    ["f_tenure", "Years trading"], ["f_prior_processor", "Switching from a prior processor"]];
  var ASK_STEPS = ["Sending the question to the Merchant Risk Agent (DATA_AGENT_RUN)", "Cortex Analyst writes SQL over the MERCHANT_RISK_SV semantic view",
    "Running the SQL on SNOWPACK_MERCHANT_RISK_WH", "Composing the answer from the result set"];

  // ---------------------------------------------------------------- data (same factors as MERCHANT_RISK_SCORE_FACTORS)
  var apps = D.apps.map(function (a) {
    return Object.assign({}, a, { f_category: a.base_risk, f_chargebacks: a.chargeback_history_bps / 10,
      f_credit_tier: TIERS.indexOf(a.credit_tier) * 8, f_tenure: -Math.min(a.years_in_business, 15) * 1.2, f_prior_processor: -a.prior_processor_flag * 5 });
  });
  var months = Array.from(new Set(apps.map(function (a) { return a.month_end; }))).sort();
  var cats = Array.from(new Set(apps.map(function (a) { return a.category_name; }))).sort();
  function rates(g) {
    var n = g.length, b = g.filter(function (a) { return a.decision !== "decline"; });
    function share(d) { return n ? g.filter(function (a) { return a.decision === d; }).length / n : 0; }
    return { n: n, approve: share("approve"), refer: share("refer"), decline: share("decline"),
      score: n ? sum(g, function (a) { return a.risk_score; }) / n : 0,
      reserve: b.length ? sum(b, function (a) { return a.reserve_pct; }) / b.length : 0,
      volume: sum(g, function (a) { return a.requested_monthly_volume; }) };
  }
  function sum(a, f) { return a.reduce(function (s, x) { return s + f(x); }, 0); }
  function byMonth() { return months.map(function (m) { var g = apps.filter(function (a) { return a.month_end === m; }); var r = rates(g); r.m = m; DEC.forEach(function (d) { r["c_" + d] = g.filter(function (a) { return a.decision === d; }).length; }); return r; }); }
  var MONTHLY = byMonth();

  // ---------------------------------------------------------------- format
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function pc(x, d) { return (x * 100).toFixed(d == null ? 1 : d) + "%"; }
  function usd(x) { var a = Math.abs(x); if (a >= 1e6) return "$" + (x / 1e6).toFixed(1) + "M"; if (a >= 1e3) return "$" + Math.round(x / 1e3) + "K"; return "$" + Math.round(x); }
  function ml(s) { var p = s.split("-"); return MON[+p[1] - 1] + " " + p[0].slice(2); }
  function mlong(s) { var p = s.split("-"); return MONL[+p[1] - 1] + " " + p[0]; }
  function cap1(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function pill(d) { return '<span class="pill ' + esc(d) + '">' + esc(cap1(d)) + "</span>"; }
  function verdict(s) { return s === "verified" ? '<span class="pill ok">✓ Verified</span>' : '<span class="pill warn">! Needs review</span>'; }
  function delta(x, t, goodUp) { if (Math.abs(x) < 1e-9) return '<span class="flat">● ' + esc(t) + "</span>"; var good = goodUp ? x > 0 : x < 0; return '<span class="' + (good ? "good" : "bad") + '">' + (x > 0 ? "▲ " : "▼ ") + esc(t) + "</span>"; }
  function head(t, s, c) { return '<div class="h"><div><h1>' + esc(t) + "</h1><p>" + esc(s) + '</p></div><div class="chips"><span class="chip sample"><i></i>Sample data</span><span class="cap">' + esc(c) + "</span></div></div>"; }
  function counter(el) { var to = +el.getAttribute("data-to"), dec = +el.getAttribute("data-dec") || 0, suf = el.getAttribute("data-suf") || "", t0 = null;
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { el.textContent = to.toFixed(dec) + suf; return; }
    function f(t) { if (!t0) t0 = t; var p = Math.min(1, (t - t0) / 650), e = 1 - Math.pow(1 - p, 3); el.textContent = (to * e).toFixed(dec) + suf; if (p < 1) requestAnimationFrame(f); }
    requestAnimationFrame(f); }
  function num(v, dec, suf) { return '<span class="cnt" data-to="' + v + '" data-dec="' + (dec || 0) + '" data-suf="' + esc(suf || "") + '">' + v.toFixed(dec || 0) + esc(suf || "") + "</span>"; }

  // ---------------------------------------------------------------- tooltip
  var tip = document.getElementById("tip");
  function bindTips(root) {
    root.querySelectorAll("[data-tip]").forEach(function (el) {
      el.addEventListener("mousemove", function (e) { tip.innerHTML = el.getAttribute("data-tip"); tip.hidden = false;
        var x = e.clientX + 14, y = e.clientY + 14, w = tip.offsetWidth, h = tip.offsetHeight;
        if (x + w > innerWidth - 8) x = e.clientX - w - 14; if (y + h > innerHeight - 8) y = e.clientY - h - 14;
        tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px"; });
      el.addEventListener("mouseleave", function () { tip.hidden = true; });
    });
  }

  // ---------------------------------------------------------------- charts (SVG)
  function spark(vals) { var w = 72, h = 24, lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), r = (hi - lo) || 1;
    return '<svg width="' + w + '" height="' + h + '" aria-hidden="true"><polyline fill="none" stroke="#7D2A3C" stroke-width="1.6" points="' +
      vals.map(function (v, i) { return (i * w / (vals.length - 1)).toFixed(1) + "," + (h - 2 - (v - lo) / r * (h - 4)).toFixed(1); }).join(" ") + '"/></svg>'; }
  function ticks(lo, hi, n) { var span = hi - lo || 1, st = Math.pow(10, Math.floor(Math.log10(span / n))), e = span / n / st;
    st *= e >= 7.5 ? 10 : e >= 3 ? 5 : e >= 1.5 ? 2 : 1; var t = [], s = Math.floor(lo / st) * st; for (var v = s; v <= hi + st * .01; v += st) t.push(+v.toFixed(10)); if (t[t.length - 1] < hi) t.push(+(t[t.length - 1] + st).toFixed(10)); return t; }
  function rail(scores, decs, marker, W, H) {
    W = W || 1000; H = H || 56; function x(v) { return 8 + v / 100 * (W - 16); }
    var g = '<rect x="' + x(0) + '" y="14" width="' + (x(40) - x(0)) + '" height="' + (H - 28) + '" fill="#DDF0E5"/><rect x="' + x(40) + '" y="14" width="' + (x(70) - x(40)) + '" height="' + (H - 28) + '" fill="#FBEBCB"/><rect x="' + x(70) + '" y="14" width="' + (x(100) - x(70)) + '" height="' + (H - 28) + '" fill="#F9E0DC"/>';
    scores.forEach(function (s, i) { g += '<line class="tick" x1="' + x(s).toFixed(1) + '" x2="' + x(s).toFixed(1) + '" y1="18" y2="' + (H - 18) + '" stroke="' + FILL[decs[i]] + '" stroke-opacity=".55" stroke-width="2"/>'; });
    if (marker != null) g += '<line x1="' + x(marker) + '" x2="' + x(marker) + '" y1="10" y2="' + (H - 14) + '" stroke="#1E1A1B" stroke-width="3"/><circle cx="' + x(marker) + '" cy="' + H / 2 + '" r="7" fill="#1E1A1B" stroke="#fff" stroke-width="2"/>';
    [0, 40, 70, 100].forEach(function (v) { g += '<text x="' + x(v) + '" y="' + (H - 2) + '" text-anchor="' + (v === 0 ? "start" : v === 100 ? "end" : "middle") + '" font-family="Red Hat Mono, monospace" font-size="12">' + v + "</text>"; });
    g += '<text x="' + x(20) + '" y="11" text-anchor="middle" font-size="12" font-weight="600" style="fill:#1D6B47">Approve</text><text x="' + x(55) + '" y="11" text-anchor="middle" font-size="12" font-weight="600" style="fill:#8A5A00">Refer</text><text x="' + x(85) + '" y="11" text-anchor="middle" font-size="12" font-weight="600" style="fill:#B02A1E">Decline</text>';
    return '<svg class="chart rail" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Risk scores on a 0 to 100 scale with approve, refer and decline bands">' + g + "</svg>";
  }
  function legendDec() { return '<div class="legend">' + DEC.map(function (d) { return '<span><i style="background:' + FILL[d] + '"></i>' + cap1(d) + "</span>"; }).join("") + "</div>"; }
  function stackedMonthly() {
    var W = 760, H = 290, max = 30, x0 = 40, bw = (W - x0 - 8) / months.length;
    function y(v) { return H - 24 - v / max * (H - 36); }
    var g = "";
    [0, 10, 20, 30].forEach(function (t) { g += '<line x1="' + x0 + '" x2="' + (W - 8) + '" y1="' + y(t) + '" y2="' + y(t) + '" stroke="#E7E1DA"/><text x="' + (x0 - 6) + '" y="' + (y(t) + 4) + '" text-anchor="end">' + t + "</text>"; });
    MONTHLY.forEach(function (r, i) {
      var base = 0, bx = x0 + i * bw + bw * .18, w = bw * .64;
      DEC.forEach(function (d) { var c = r["c_" + d]; g += '<rect x="' + bx.toFixed(1) + '" y="' + y(base + c).toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + (y(base) - y(base + c)).toFixed(1) + '" fill="' + FILL[d] + '"/>'; base += c; });
      g += '<rect x="' + (x0 + i * bw) + '" y="10" width="' + bw + '" height="' + (H - 34) + '" fill="transparent" data-tip="<b>' + mlong(r.m) + "</b><br>Approve: " + r.c_approve + "<br>Refer: " + r.c_refer + "<br>Decline: " + r.c_decline + '"/>';
      if (i % 3 === 1) g += '<text x="' + (x0 + i * bw + bw / 2) + '" y="' + (H - 6) + '" text-anchor="middle">' + ml(r.m) + "</text>";
    });
    return '<svg class="chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Applications per month by decision, stacked">' + g + "</svg>";
  }
  function backdrop() {
    var W = 760, H = 230, x0 = 44, x1 = W - 50, cf = D.cfpb;
    var dr = MONTHLY.map(function (r) { return r.decline * 100; }), cc = cf.map(function (r) { return r.complaint_count; });
    var t1 = ticks(0, Math.max.apply(null, dr), 4), t2 = ticks(Math.min.apply(null, cc), Math.max.apply(null, cc), 4);
    function x(i) { return x0 + i * (x1 - x0) / (months.length - 1); }
    function y1(v) { return H - 24 - (v - t1[0]) / (t1[t1.length - 1] - t1[0]) * (H - 36); }
    function y2(v) { return H - 24 - (v - t2[0]) / (t2[t2.length - 1] - t2[0]) * (H - 36); }
    var g = "";
    t1.forEach(function (t) { g += '<line x1="' + x0 + '" x2="' + x1 + '" y1="' + y1(t) + '" y2="' + y1(t) + '" stroke="#E7E1DA"/><text x="' + (x0 - 6) + '" y="' + (y1(t) + 4) + '" text-anchor="end" style="fill:#7D2A3C">' + t + "%</text>"; });
    t2.forEach(function (t) { g += '<text x="' + (x1 + 6) + '" y="' + (y2(t) + 4) + '" style="fill:#36587A">' + (t / 1000).toFixed(1) + "k</text>"; });
    g += '<polyline fill="none" stroke="#7D2A3C" stroke-width="2.2" points="' + dr.map(function (v, i) { return x(i) + "," + y1(v); }).join(" ") + '"/>';
    g += '<polyline fill="none" stroke="#36587A" stroke-width="2" stroke-dasharray="5 4" points="' + cc.map(function (v, i) { return x(i) + "," + y2(v); }).join(" ") + '"/>';
    var w = (x1 - x0) / (months.length - 1);
    months.forEach(function (m, i) {
      if (i % 3 === 1) g += '<text x="' + x(i) + '" y="' + (H - 6) + '" text-anchor="middle">' + ml(m) + "</text>";
      g += '<circle cx="' + x(i) + '" cy="' + y1(dr[i]) + '" r="2.6" fill="#7D2A3C"/>';
      g += '<rect x="' + (x(i) - w / 2) + '" y="10" width="' + w + '" height="' + (H - 34) + '" fill="transparent" data-tip="<b>' + mlong(m) + "</b><br>Decline rate: " + dr[i].toFixed(1) + "%<br>CFPB complaints: " + cc[i].toLocaleString("en-US") + "<br>% monetary relief: " + cf[i].pct_monetary_relief.toFixed(2) + '"/>';
    });
    return '<svg class="chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Decline rate of this book against monthly CFPB payment complaints">' + g + "</svg>";
  }

  // ---------------------------------------------------------------- views
  var main = document.getElementById("main");
  function portfolio() {
    var a = rates(apps.filter(function (x) { return x.month_end >= "2026-01"; })), b = rates(apps.filter(function (x) { return x.month_end >= "2025-07" && x.month_end < "2026-01"; }));
    function pp(x, y) { return ((x - y) * 100 >= 0 ? "+" : "") + ((x - y) * 100).toFixed(1) + " pp vs H2 2025"; }
    var tiles = [
      ["Applications, H1 2026", num(a.n), '<span class="flat">' + usd(a.volume) + " requested / month</span>", null],
      ["Approval rate", num(a.approve * 100, 1, "%"), delta(a.approve - b.approve, pp(a.approve, b.approve), true), MONTHLY.map(function (r) { return r.approve; })],
      ["Decline rate", num(a.decline * 100, 1, "%"), delta(a.decline - b.decline, pp(a.decline, b.decline), false), MONTHLY.map(function (r) { return r.decline; })],
      ["Average risk score", num(a.score, 1), delta(a.score - b.score, (a.score - b.score >= 0 ? "+" : "") + (a.score - b.score).toFixed(1) + " vs H2 2025", false), MONTHLY.map(function (r) { return r.score; })],
      ["Avg reserve, booked", num(a.reserve, 2, "%"), delta(a.reserve - b.reserve, (a.reserve - b.reserve >= 0 ? "+" : "") + (a.reserve - b.reserve).toFixed(2) + " pp vs H2 2025", false), MONTHLY.map(function (r) { return r.reserve; })]];
    var seg = cats.map(function (c) { var r = rates(apps.filter(function (x) { return x.category_name === c; })); r.c = c; return r; });
    var worst = seg.slice().sort(function (p, q) { return q.decline - p.decline; })[0], best = seg.slice().sort(function (p, q) { return q.approve - p.approve; })[0];
    var el = apps.filter(function (x) { return x.category_code === "ELECTRONICS"; });
    var ea = rates(el.filter(function (x) { return x.month_end >= "2026-01"; })), eb = rates(el.filter(function (x) { return x.month_end < "2026-01"; }));
    var reasons = {}; apps.filter(function (x) { return x.decision === "decline"; }).forEach(function (x) { reasons[x.decline_reason] = (reasons[x.decline_reason] || 0) + 1; });
    var rs = Object.keys(reasons).sort(function (p, q) { return reasons[q] - reasons[p]; }), top = reasons[rs[0]];
    var counts = {}; DEC.forEach(function (d) { counts[d] = apps.filter(function (x) { return x.decision === d; }).length; });
    main.innerHTML = head("Portfolio", apps.length + " new-merchant applications, July 2024 to June 2026, scored 0-100 and decided approve / refer / decline. Tiles compare Jan-Jun 2026 with Jul-Dec 2025.", "Sample data · MERCHANT_RISK_BOOK view") +
      '<div class="kpis">' + tiles.map(function (t, i) { return '<div class="kpi" style="animation-delay:' + i * .03 + 's"><div class="k">' + esc(t[0]) + '</div><div class="v">' + t[1] + '</div><div class="d">' + t[2] + "</div>" + (t[3] ? spark(t[3]) : "") + "</div>"; }).join("") + "</div>" +
      '<section class="card"><h2>Every application on the threshold rail</h2><p class="s">One tick per application at its risk score. Under 40 approves, 40 to 69.9 refers to an underwriter, 70 and over declines.</p>' +
      rail(apps.map(function (x) { return x.risk_score; }), apps.map(function (x) { return x.decision; })) +
      '<div class="legend">' + DEC.map(function (d) { return '<span><i style="background:' + FILL[d] + '"></i>' + cap1(d) + ' <b style="font-family:var(--mono)">' + counts[d] + "</b> (" + pc(counts[d] / apps.length) + ")</span>"; }).join("") + "</div></section>" +
      '<div class="insight"><b>On the desk.</b> ' + esc(worst.c) + " carries the highest decline rate (" + pc(worst.decline) + "); " + esc(best.c) + " the highest approval rate (" + pc(best.approve) + "). Electronics chargeback history has drifted up in 2026: its decline rate went from " + pc(eb.decline) + " (Jul 2024 to Dec 2025) to " + pc(ea.decline) + ' (Jan to Jun 2026). Open <a href="#applications">Applications</a> to see why any one merchant scored as it did, or <a href="#notes">Underwriting notes</a> for a verified write-up.</div>' +
      '<div class="grid2"><section class="card"><h2>Decision mix by month</h2><p class="s">Applications per month by decision. Hover for counts.</p>' + stackedMonthly() + legendDec() + "</section>" +
      '<section class="card"><h2>Why applications decline</h2><p class="s">First matching rule per declined application.</p><ul class="fx">' +
      rs.map(function (k) { return "<li><span>" + esc(k) + '</span><span class="bar"><i style="width:' + (reasons[k] / top * 100).toFixed(0) + '%;background:#B02A1E"></i></span><span class="n">' + reasons[k] + "</span></li>"; }).join("") +
      '</ul><p class="s" style="margin-top:.6rem">' + counts.decline + " declines in total.</p></section></div>" +
      '<section class="card"><h2>Industry backdrop: payment-product complaints</h2><p class="s">Monthly complaints (synthetic CFPB-style series, dashed) against this book\'s decline rate. The backdrop is an external, non-additive signal joined by month only; it is not this processor\'s complaints.</p>' + backdrop() +
      '<div class="legend"><span><i style="background:#7D2A3C"></i>Decline rate (this book)</span><span><i style="background:#36587A"></i>CFPB payment complaints (backdrop)</span></div></section>';
    main.querySelectorAll(".cnt").forEach(counter);
  }

  var Q = { q: "", dec: "", cat: "", tier: "", min: 0, sort: "risk_score", dir: -1 };
  var COLS = [["application_id", "ID", 0], ["merchant_name", "Merchant", 0], ["credit_tier", "Tier", 0], ["risk_score", "Score", 1], ["decision", "Decision", 0],
    ["reserve_pct", "Reserve %", 1], ["chargeback_history_bps", "CB bps", 1], ["years_in_business", "Years", 1], ["month_end", "Month", 0]];
  function filtered() {
    return apps.filter(function (a) {
      return (!Q.q || (a.merchant_name + " " + a.application_id).toLowerCase().indexOf(Q.q.toLowerCase()) >= 0) && (!Q.dec || a.decision === Q.dec) &&
        (!Q.cat || a.category_name === Q.cat) && (!Q.tier || a.credit_tier === Q.tier) && a.risk_score >= Q.min;
    }).sort(function (p, q) { var x = p[Q.sort], y = q[Q.sort]; if (x === y) return p.application_id < q.application_id ? -1 : 1; return (x < y ? -1 : 1) * Q.dir; });
  }
  function opt(v, l, cur) { return '<option value="' + esc(v) + '"' + (v === cur ? " selected" : "") + ">" + esc(l) + "</option>"; }
  function applications() {
    main.innerHTML = head("Applications", "The review queue. Filter and sort the book, then select a row to see how its score was built.", "Sample data · MERCHANT_RISK_BOOK view") +
      '<section class="card"><div class="filters">' +
      '<label>Search<input id="fq" type="search" placeholder="Merchant or application ID" value="' + esc(Q.q) + '"></label>' +
      '<label>Decision<select id="fd">' + opt("", "All decisions", Q.dec) + DEC.map(function (d) { return opt(d, cap1(d), Q.dec); }).join("") + "</select></label>" +
      '<label>Category<select id="fc">' + opt("", "All categories", Q.cat) + cats.map(function (c) { return opt(c, c, Q.cat); }).join("") + "</select></label>" +
      '<label>Credit tier<select id="ft">' + opt("", "All tiers", Q.tier) + TIERS.map(function (t) { return opt(t, t, Q.tier); }).join("") + "</select></label>" +
      '<label>Min score<select id="fm">' + [0, 40, 70, 90].map(function (v) { return opt(String(v), v ? v + "+" : "Any", String(Q.min)); }).join("") + "</select></label>" +
      '<label>&nbsp;<button type="button" class="btn" id="fr" style="width:100%;margin-top:.25rem">Reset</button></label></div></section><div id="qout"></div>';
    function upd() { Q.q = document.getElementById("fq").value; Q.dec = document.getElementById("fd").value; Q.cat = document.getElementById("fc").value; Q.tier = document.getElementById("ft").value; Q.min = +document.getElementById("fm").value; table(); }
    ["fq", "fd", "fc", "ft", "fm"].forEach(function (id) { document.getElementById(id).addEventListener(id === "fq" ? "input" : "change", upd); });
    document.getElementById("fr").addEventListener("click", function () { Q = { q: "", dec: "", cat: "", tier: "", min: 0, sort: "risk_score", dir: -1 }; applications(); });
    table();
  }
  function table() {
    var f = filtered(), out = document.getElementById("qout"), c = {};
    DEC.forEach(function (d) { c[d] = f.filter(function (a) { return a.decision === d; }).length; });
    var hdr = '<div class="count"><span><b>' + f.length + "</b> of " + apps.length + " applications</span>" + DEC.map(function (d) { return pill(d) + '<span class="m">' + c[d] + "</span>"; }).join("") + "</div>";
    if (!f.length) { out.innerHTML = hdr + '<div class="card empty"><b>No applications match</b>Clear a filter or lower the minimum score.</div>'; return; }
    out.innerHTML = hdr + '<div class="tw"><table><thead><tr>' + COLS.map(function (k) {
      var on = Q.sort === k[0]; return '<th class="' + (k[2] ? "num" : "") + '" aria-sort="' + (on ? (Q.dir > 0 ? "ascending" : "descending") : "none") + '"><button type="button" data-sort="' + k[0] + '">' + k[1] + (on ? (Q.dir > 0 ? " ▲" : " ▼") : "") + "</button></th>"; }).join("") +
      "</tr></thead><tbody>" + f.slice(0, 300).map(function (a) {
        return '<tr data-id="' + a.application_id + '" tabindex="0"><td><code>' + a.application_id + "</code></td><td>" + esc(a.merchant_name) + "</td><td>" + a.credit_tier + '</td><td class="num"><span class="sbar"><i style="width:' + a.risk_score + '%"></i></span>' + a.risk_score.toFixed(1) +
          "</td><td>" + pill(a.decision) + '</td><td class="num">' + a.reserve_pct.toFixed(2) + '</td><td class="num">' + a.chargeback_history_bps + '</td><td class="num">' + a.years_in_business + "</td><td>" + ml(a.month_end) + "</td></tr>"; }).join("") +
      "</tbody></table></div>" + (f.length > 300 ? '<p class="s" style="font-size:.8rem;color:var(--muted)">Showing the first 300 rows; filter to narrow.</p>' : "");
    out.querySelectorAll("th button").forEach(function (b) { b.addEventListener("click", function () { var k = b.getAttribute("data-sort"); if (Q.sort === k) Q.dir = -Q.dir; else { Q.sort = k; Q.dir = -1; } table(); }); });
    out.querySelectorAll("tbody tr").forEach(function (tr) {
      function open() { out.querySelectorAll("tr.sel").forEach(function (x) { x.classList.remove("sel"); }); tr.classList.add("sel"); drawer(tr.getAttribute("data-id")); }
      tr.addEventListener("click", open); tr.addEventListener("keydown", function (e) { if (e.key === "Enter") open(); });
    });
  }
  var dr = document.getElementById("drawer"), scrim = document.getElementById("scrim");
  function closeDrawer() { dr.setAttribute("aria-hidden", "true"); scrim.hidden = true; }
  scrim.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });
  function drawer(id) {
    var a = apps.find(function (x) { return x.application_id === id; });
    var reason = a.decline_reason || (a.decision === "approve" ? "Under the 40-point approval threshold" : "Between 40 and 70: an underwriter reviews before booking");
    var raw = sum(FACTORS, function (f) { return a[f[0]]; });
    document.getElementById("drawer-in").innerHTML = '<button type="button" class="x" id="dx">Close</button><p class="s" style="color:var(--muted);font-size:.8rem;margin:0">' + a.application_id + " · " + mlong(a.month_end) + "</p>" +
      '<h2 style="margin:.2rem 0 .4rem;font-size:1.1rem">' + esc(a.merchant_name) + "</h2><div class=\"chips\" style=\"margin:0 0 .5rem\">" + pill(a.decision) + '<span class="pill n">' + a.credit_tier + '</span><span class="pill n">MCC ' + a.mcc + "</span></div>" +
      rail([], [], a.risk_score, 420, 56) +
      '<div class="facts"><div><span>Requested volume / month</span><b>' + usd(a.requested_monthly_volume) + "</b></div><div><span>Chargebacks</span><b>" + a.chargeback_history_bps + " bps</b></div><div><span>Years trading</span><b>" + a.years_in_business +
      "</b></div><div><span>Prior processor</span><b>" + (a.prior_processor_flag ? "Yes" : "No") + "</b></div><div><span>Reserve</span><b>" + a.reserve_pct.toFixed(2) + '%</b></div><div><span>Category</span><b style="font-family:var(--sans);font-size:.82rem">' + esc(a.category_name) + "</b></div></div>" +
      '<h3 style="font-size:.9rem;margin:.4rem 0">Why it scored this way</h3><ul class="fx">' + FACTORS.map(function (f) { var v = a[f[0]];
        return "<li><span>" + f[1] + '</span><span class="bar"><i style="width:' + Math.min(Math.abs(v), 100) + "%;background:" + (v > 0 ? "#B02A1E" : "#1D6B47") + '"></i></span><span class="n">' + (v >= 0 ? "+" : "") + v.toFixed(1) + "</span></li>"; }).join("") +
      '<li style="border-bottom:0"><b>Risk score</b><span></span><span class="n"><b>' + a.risk_score.toFixed(1) + "</b></span></li></ul><p class=\"s\" style=\"font-size:.8rem;color:var(--muted)\">Red adds risk, green reduces it" + (raw < 0 || raw > 100 ? " (raw " + raw.toFixed(1) + ", clamped to 0-100)" : "") + ".</p>" +
      '<div class="insight"><b>' + cap1(a.decision) + ".</b> " + esc(reason) + ". " + (a.decision === "decline" ? "No reserve: declined." : a.reserve_pct.toFixed(2) + "% rolling reserve.") + '</div><div class="src">Source: <code>app/sample</code> · factors as in <code>MERCHANT_RISK_SCORE_FACTORS</code></div>';
    dr.setAttribute("aria-hidden", "false"); scrim.hidden = false; document.getElementById("dx").addEventListener("click", closeDrawer); document.getElementById("dx").focus();
  }

  var SEGM = { decline: ["Decline rate", "#B02A1E", 1], approve: ["Approval rate", "#1D6B47", 1], score: ["Average risk score", "#7D2A3C", 0], reserve: ["Avg reserve, booked (%)", "#36587A", 0] };
  var segMetric = "decline", segSort = ["decline", -1];
  function mix(c, t) { var a = parseInt(c.slice(1), 16), r = (a >> 16) & 255, g = (a >> 8) & 255, b = a & 255, s = [247, 244, 240];
    return "rgb(" + Math.round(s[0] + (r - s[0]) * t) + "," + Math.round(s[1] + (g - s[1]) * t) + "," + Math.round(s[2] + (b - s[2]) * t) + ")"; }
  function fmtM(k, v) { return SEGM[k][2] ? pc(v) : (k === "reserve" ? v.toFixed(2) : v.toFixed(1)); }
  function segments() {
    var cells = [];
    cats.forEach(function (c) { TIERS.forEach(function (t) { var r = rates(apps.filter(function (a) { return a.category_name === c && a.credit_tier === t; })); r.c = c; r.t = t; cells.push(r); }); });
    var vals = cells.map(function (r) { return r[segMetric]; }), lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var heat = '<div class="tw" style="max-height:none;border:0"><table><thead><tr><th>Category</th>' + TIERS.map(function (t) { return '<th class="num">' + t + "</th>"; }).join("") + "</tr></thead><tbody>" +
      cats.map(function (c) { return "<tr style=\"cursor:default\"><td>" + esc(c) + "</td>" + TIERS.map(function (t) { var r = cells.find(function (x) { return x.c === c && x.t === t; }), k = (r[segMetric] - lo) / ((hi - lo) || 1);
        return '<td class="num" style="background:' + mix(SEGM[segMetric][1], k) + ";color:" + (k > .6 ? "#fff" : "#1E1A1B") + ';font-weight:600" data-tip="<b>' + esc(c) + " · " + t + "</b><br>Applications: " + r.n + "<br>Approval: " + pc(r.approve) + "<br>Decline: " + pc(r.decline) + "<br>Avg score: " + r.score.toFixed(1) + "<br>Avg reserve, booked: " + r.reserve.toFixed(2) + '%">' + fmtM(segMetric, r[segMetric]) + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table></div>";
    // histogram
    var bins = []; for (var b = 0; b < 100; b += 5) bins.push(b);
    var W = 520, H = 260, x0 = 36, bw = (W - x0 - 8) / 20, hc = bins.map(function (b) { var o = {}; DEC.forEach(function (d) { o[d] = apps.filter(function (a) { return Math.min(Math.floor(a.risk_score / 5) * 5, 95) === b && a.decision === d; }).length; }); return o; });
    var hmax = Math.max.apply(null, hc.map(function (o) { return o.approve + o.refer + o.decline; })), ht = ticks(0, hmax, 4); hmax = ht[ht.length - 1];
    function hy(v) { return H - 24 - v / hmax * (H - 36); }
    var hg = ""; ht.forEach(function (t) { hg += '<line x1="' + x0 + '" x2="' + (W - 8) + '" y1="' + hy(t) + '" y2="' + hy(t) + '" stroke="#E7E1DA"/><text x="' + (x0 - 6) + '" y="' + (hy(t) + 4) + '" text-anchor="end">' + t + "</text>"; });
    bins.forEach(function (bn, i) { var base = 0; DEC.forEach(function (d) { var c = hc[i][d]; if (c) hg += '<rect x="' + (x0 + i * bw + 1) + '" y="' + hy(base + c) + '" width="' + (bw - 2) + '" height="' + (hy(base) - hy(base + c)) + '" fill="' + FILL[d] + '"/>'; base += c; });
      hg += '<rect x="' + (x0 + i * bw) + '" y="10" width="' + bw + '" height="' + (H - 34) + '" fill="transparent" data-tip="<b>Score ' + bn + "-" + (bn + 4.9) + "</b><br>Approve: " + hc[i].approve + "<br>Refer: " + hc[i].refer + "<br>Decline: " + hc[i].decline + '"/>';
      if (bn % 20 === 0) hg += '<text x="' + (x0 + i * bw) + '" y="' + (H - 6) + '" text-anchor="middle">' + bn + "</text>"; });
    [40, 70].forEach(function (v) { var xx = x0 + v / 5 * bw; hg += '<line x1="' + xx + '" x2="' + xx + '" y1="10" y2="' + (H - 24) + '" stroke="#1E1A1B" stroke-dasharray="4 3"/>'; });
    hg += '<text x="' + (W - 8) + '" y="' + (H - 6) + '" text-anchor="end">100</text>';
    // dumbbell
    var dd = cats.map(function (c) { var g = apps.filter(function (a) { return a.category_name === c; });
      return { c: c, a: rates(g.filter(function (a) { return a.month_end < "2025-01"; })).decline, b: rates(g.filter(function (a) { return a.month_end >= "2026-01"; })).decline }; }).sort(function (p, q) { return q.b - p.b; });
    var DW = 420, DH = 260, dx0 = 150, dx1 = DW - 16; function dxx(v) { return dx0 + v * (dx1 - dx0); }
    var dg = ""; [0, .25, .5, .75, 1].forEach(function (t) { dg += '<line x1="' + dxx(t) + '" x2="' + dxx(t) + '" y1="8" y2="' + (DH - 22) + '" stroke="#E7E1DA"/><text x="' + dxx(t) + '" y="' + (DH - 6) + '" text-anchor="middle">' + t * 100 + "%</text>"; });
    dd.forEach(function (r, i) { var yy = 22 + i * ((DH - 50) / (dd.length - 1));
      dg += '<text x="' + (dx0 - 8) + '" y="' + (yy + 4) + '" text-anchor="end" style="fill:#1E1A1B">' + esc(r.c.split(" & ")[0]) + '</text><line x1="' + dxx(r.a) + '" x2="' + dxx(r.b) + '" y1="' + yy + '" y2="' + yy + '" stroke="#C9C0B6" stroke-width="2"/>' +
        '<circle cx="' + dxx(r.a) + '" cy="' + yy + '" r="6" fill="#B8ADA3" data-tip="<b>' + esc(r.c) + "</b><br>Jul-Dec 2024: " + pc(r.a) + '"/><circle cx="' + dxx(r.b) + '" cy="' + yy + '" r="6" fill="#B02A1E" data-tip="<b>' + esc(r.c) + "</b><br>Jan-Jun 2026: " + pc(r.b) + '"/>'; });
    var srt = cells.slice().sort(function (p, q) { var x = p[segSort[0]], y = q[segSort[0]]; return (x < y ? -1 : x > y ? 1 : 0) * segSort[1]; });
    var SC = [["c", "Category", 0], ["t", "Credit tier", 0], ["n", "Apps", 1], ["approve", "Approve %", 1], ["refer", "Refer %", 1], ["decline", "Decline %", 1], ["score", "Avg score", 1], ["reserve", "Reserve % booked", 1]];
    main.innerHTML = head("Segments", "Where risk concentrates: merchant category against applicant credit tier, the full score distribution, and how each category moved between the first and last six months.", "Sample data · MERCHANT_RISK_BOOK view") +
      '<section class="card"><div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:flex-end"><div><h2>Category × credit tier</h2><p class="s">About 30 applications per cell. Hover a cell for the full figures.</p></div>' +
      '<label style="font-size:.8rem">Metric <select id="sm" style="padding:.35rem;border-radius:8px;border:1px solid var(--line)">' + Object.keys(SEGM).map(function (k) { return opt(k, SEGM[k][0], segMetric); }).join("") + "</select></label></div>" + heat + "</section>" +
      '<div class="grid2b"><section class="card"><h2>Risk score distribution</h2><p class="s">5-point bins, coloured by the decision each score produced. Thresholds at 40 and 70.</p><svg class="chart" viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="Histogram of risk scores by decision">' + hg + "</svg>" + legendDec() + "</section>" +
      '<section class="card"><h2>Decline rate: first vs last six months</h2><p class="s">Jul-Dec 2024 against Jan-Jun 2026, by category.</p><svg class="chart" viewBox="0 0 ' + DW + " " + DH + '" role="img" aria-label="Decline rate by category, first six months against last six months">' + dg + '</svg><div class="legend"><span><i style="background:#B8ADA3"></i>Jul-Dec 2024</span><span><i style="background:#B02A1E"></i>Jan-Jun 2026</span></div></section></div>' +
      '<section class="card"><h2>Segment table</h2><p class="s">Sortable. Same figures as the matrix.</p><div class="tw"><table><thead><tr>' + SC.map(function (k) { var on = segSort[0] === k[0];
        return '<th class="' + (k[2] ? "num" : "") + '" aria-sort="' + (on ? (segSort[1] > 0 ? "ascending" : "descending") : "none") + '"><button type="button" data-k="' + k[0] + '">' + k[1] + (on ? (segSort[1] > 0 ? " ▲" : " ▼") : "") + "</button></th>"; }).join("") +
      "</tr></thead><tbody>" + srt.map(function (r) { return '<tr style="cursor:default"><td>' + esc(r.c) + "</td><td>" + r.t + '</td><td class="num">' + r.n + '</td><td class="num">' + (r.approve * 100).toFixed(1) + '</td><td class="num">' + (r.refer * 100).toFixed(1) + '</td><td class="num">' + (r.decline * 100).toFixed(1) + '</td><td class="num">' + r.score.toFixed(1) + '</td><td class="num">' + r.reserve.toFixed(2) + "</td></tr>"; }).join("") + "</tbody></table></div></section>";
    document.getElementById("sm").addEventListener("change", function (e) { segMetric = e.target.value; segments(); });
    main.querySelectorAll("th button[data-k]").forEach(function (b) { b.addEventListener("click", function () { var k = b.getAttribute("data-k"); segSort = segSort[0] === k ? [k, -segSort[1]] : [k, -1]; segments(); }); });
    bindTips(main);
  }

  // ---------------------------------------------------------------- AI (replays captured Live runs)
  function mdInline(s) { return esc(s).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>"); }
  function md(src) {
    var lines = (src || "").split("\n"), out = [], i = 0;
    while (i < lines.length) {
      var l = lines[i];
      if (/^\|/.test(l)) { var rows = []; while (i < lines.length && /^\|/.test(lines[i])) { rows.push(lines[i]); i++; }
        var cells = rows.filter(function (r) { return !/^\|[\s:|-]+\|$/.test(r.trim()); }).map(function (r) { return r.trim().replace(/^\||\|$/g, "").split("|").map(function (c) { return c.trim(); }); });
        out.push("<table><thead><tr>" + cells[0].map(function (c) { return "<th>" + mdInline(c) + "</th>"; }).join("") + "</tr></thead><tbody>" + cells.slice(1).map(function (r) { return "<tr style=\"cursor:default\">" + r.map(function (c) { return "<td>" + mdInline(c) + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table>"); continue; }
      if (/^\s*[-*•] /.test(l)) { var it = []; while (i < lines.length && /^\s*[-*•] /.test(lines[i])) { it.push("<li>" + mdInline(lines[i].replace(/^\s*[-*•] /, "")) + "</li>"); i++; } out.push("<ul>" + it.join("") + "</ul>"); continue; }
      var h = l.match(/^(#{1,3}) (.*)/); if (h) out.push("<h" + h[1].length + ">" + mdInline(h[2]) + "</h" + h[1].length + ">");
      else if (l.trim() && !/^---+$/.test(l.trim())) out.push("<p>" + mdInline(l) + "</p>");
      i++;
    }
    return out.join("");
  }
  function steps(list, cur, done) { return '<ul class="steps">' + list.map(function (s, i) { return '<li class="' + (done || i < cur ? "done" : i === cur ? "now" : "") + '"><span class="ic"></span><span>' + esc(s) + "</span></li>"; }).join("") + "</ul>"; }
  function stage(el, list, cb) { var total = 4000 + Math.random() * 4000, i = 0;
    (function next() { el.innerHTML = steps(list, i, false); if (i++ < list.length) setTimeout(next, total / list.length); else { el.innerHTML = steps(list, 0, true); cb(); } })(); }
  function reveal(el, html, cb) {
    var words = el.ownerDocument.createElement("div"); words.innerHTML = html; var text = words.textContent.split(" "), n = 0, tmp = "";
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { el.innerHTML = html; if (cb) cb(); return; }
    var t = setInterval(function () { n += 6; tmp = text.slice(0, n).join(" "); el.textContent = tmp; if (n >= text.length) { clearInterval(t); el.innerHTML = html; if (cb) cb(); } }, 30);
  }
  function noteSteps(scope) { var n = scope === "ALL" ? 720 : 120, seg = scope === "ALL" ? "6 categories and 4 credit tiers" : "4 credit tiers";
    return ["Reading " + n + " applications from MERCHANT_RISK_BENCHMARK and grouping by " + seg, "Adding first-6-month vs last-6-month change, decline reasons and the CFPB backdrop",
      "Drafting the underwriting note with AI_COMPLETE (claude-sonnet-4-5) under the DATA RULES", "Fact-checking every number against the fact pack with a second AI_COMPLETE pass", "Saving the note and verdict to MERCHANT_RISK_REPORTS"]; }
  function noteHtml(n) {
    var fp = n.fact_pack || {}, rows = 0; Object.keys(fp).forEach(function (k) { if (Array.isArray(fp[k])) rows += fp[k].length; });
    return '<div class="chips" style="margin:0 0 .5rem">' + verdict(n.status) + '<span class="ai-cap">Sample AI response · captured from a Live run</span><span style="font-size:.8rem;color:var(--muted)">residual hedges: ' + esc(n.residual_hedges) + " · flagged: " + (n.edits || []).length + "</span></div>" +
      ((n.edits || []).length ? '<div class="insight" style="border-left-color:var(--dc)"><b>Verifier flagged</b><br>' + n.edits.map(function (e) { return "• " + esc(e); }).join("<br>") + "</div>" : "") +
      '<div class="md" id="mdout"></div><div class="src">Sources: ' + rows + " fact-pack rows from <code>MERCHANT_RISK_BENCHMARK</code>, <code>MERCHANT_RISK_DECISION</code> and <code>MERCHANT_RISK_CFPB_BENCHMARK</code> · scope " + esc(fp.scope) + " · window <code>" + esc(fp.window) + "</code> · model <code>" + esc(n.model) + "</code> · " + (n.latency_ms / 1000).toFixed(1) + " s measured in Live</div>";
  }
  var lastNote = null;
  function notes() {
    main.innerHTML = head("Underwriting notes", "A one-page underwriting note written only from a fact pack of allowed numbers, then fact-checked by a second model pass.", "Sample AI responses · Cortex AI_COMPLETE in Live") +
      '<div class="grid2" style="grid-template-columns:minmax(0,1fr) minmax(0,2.2fr)"><section class="card"><h2>Write a note</h2><p class="s">The whole book or one merchant category.</p><label style="font-size:.8rem">Scope<select id="ns" style="width:100%;margin:.25rem 0 .7rem;padding:.45rem;border-radius:8px;border:1px solid var(--line);background:var(--stone)">' +
      Object.keys(SCOPES).map(function (k) { return opt(k, SCOPES[k], "ALL"); }).join("") + '</select></label><button type="button" class="btn primary" id="nr">Run underwriting analysis</button><div id="nsteps" style="margin-top:.7rem"></div></section>' +
      '<div><section class="card" id="nprog" hidden></section><section class="card" id="nout"' + (lastNote ? "" : " hidden") + '></section></div></div><h2 style="font-size:.98rem;margin:.4rem 0 .6rem">Note library</h2><div class="lib" id="nlib"></div>';
    var ns = document.getElementById("ns"), nsteps = document.getElementById("nsteps");
    function idle() { nsteps.innerHTML = steps(noteSteps(ns.value), -1, false); }
    ns.addEventListener("change", idle); idle();
    function show(n, anim) { var o = document.getElementById("nout"); o.hidden = false; o.innerHTML = noteHtml(n); var m = document.getElementById("mdout"); if (anim) reveal(m, md(n.markdown)); else m.innerHTML = md(n.markdown); }
    if (lastNote) show(lastNote, false);
    document.getElementById("nr").addEventListener("click", function () {
      var b = this, n = D.ai.notes[ns.value], p = document.getElementById("nprog"); b.disabled = true; p.hidden = false; document.getElementById("nout").hidden = true;
      stage(p, noteSteps(ns.value), function () { b.disabled = false; lastNote = n; show(n, true); });
    });
    document.getElementById("nlib").innerHTML = Object.keys(D.ai.notes).map(function (k) { var n = D.ai.notes[k];
      return '<section class="card" tabindex="0" data-k="' + k + '">' + verdict(n.status) + '<h2 style="margin-top:.45rem">' + esc(n.subject) + '</h2><p class="s">' + esc((n.markdown || "").split("\n")[0].replace(/^#+\s*/, "")) + "</p></section>"; }).join("");
    document.querySelectorAll("#nlib .card").forEach(function (c) { function o() { lastNote = D.ai.notes[c.getAttribute("data-k")]; show(lastNote, false); document.getElementById("nout").scrollIntoView({ behavior: "smooth", block: "start" }); }
      c.addEventListener("click", o); c.addEventListener("keydown", function (e) { if (e.key === "Enter") o(); }); });
  }
  var lastQ = null;
  function ask() {
    var qs = Object.keys(D.ai.ask);
    main.innerHTML = head("Ask the agent", "Plain-English questions about the book. The agent writes SQL over the semantic view and answers only from the result.", "Sample AI responses · Cortex Agents in Live") +
      '<section class="card"><p class="s">Try a question</p><div class="qs">' + qs.map(function (q, i) { return '<button type="button" class="btn" data-i="' + i + '" aria-pressed="' + (q === lastQ) + '">' + esc(q) + "</button>"; }).join("") +
      '</div><p class="s" style="margin:.7rem 0 0">Sample mode replays these four questions. Run the app Live to ask your own.</p></section><section class="card" id="aprog" hidden></section><section class="card" id="aout" hidden></section>' +
      (lastQ ? "" : '<section class="card empty" id="aempty"><b>No question yet</b>Pick a suggested question to see the agent at work.</section>');
    function show(q, anim) {
      var a = D.ai.ask[q], o = document.getElementById("aout"), tb = a.table && a.table.rows && a.table.rows.length ?
        '<div class="tw" style="margin-top:.6rem"><table><thead><tr>' + a.table.columns.map(function (c) { return "<th>" + esc(c) + "</th>"; }).join("") + "</tr></thead><tbody>" + a.table.rows.map(function (r) { return '<tr style="cursor:default">' + r.map(function (c) { return "<td>" + esc(c) + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table></div>" : "";
      o.hidden = false; o.innerHTML = '<div class="chips" style="margin:0 0 .5rem"><b>' + esc(q) + '</b><span class="ai-cap">Sample AI response · captured from a Live run</span></div><div class="md" id="amd"></div>' + tb +
        (a.sql ? "<details><summary>SQL written by Cortex Analyst</summary><pre>" + esc(a.sql) + "</pre></details>" : "") +
        '<div class="src">Source: semantic view <code>MERCHANT_RISK_SV</code> via agent <code>MERCHANT_RISK_AGENT</code> · ' + (a.latency_ms / 1000).toFixed(1) + " s measured in Live</div>";
      var m = document.getElementById("amd"); if (anim) reveal(m, md(a.text)); else m.innerHTML = md(a.text);
    }
    if (lastQ) show(lastQ, false);
    main.querySelectorAll(".qs .btn").forEach(function (b) { b.addEventListener("click", function () {
      var q = qs[+b.getAttribute("data-i")], p = document.getElementById("aprog"), e = document.getElementById("aempty"); if (e) e.remove();
      main.querySelectorAll(".qs .btn").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); x.disabled = true; });
      document.getElementById("aout").hidden = true; p.hidden = false;
      stage(p, ASK_STEPS, function () { main.querySelectorAll(".qs .btn").forEach(function (x) { x.disabled = false; }); lastQ = q; show(q, true); });
    }); });
  }

  // ---------------------------------------------------------------- shell
  var R = { portfolio: portfolio, applications: applications, segments: segments, notes: notes, ask: ask };
  var nav = document.getElementById("nav"), side = document.getElementById("side"), menu = document.getElementById("menu");
  nav.innerHTML = VIEWS.map(function (v) { return '<a href="#' + v[0] + '">' + v[1] + "</a>"; }).join("");
  function route() {
    var k = (location.hash || "#portfolio").slice(1); if (!R[k]) k = "portfolio";
    nav.querySelectorAll("a").forEach(function (a) { if (a.getAttribute("href") === "#" + k) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    side.classList.remove("open"); menu.setAttribute("aria-expanded", "false"); closeDrawer(); tip.hidden = true;
    main.style.animation = "none"; void main.offsetWidth; main.style.animation = "";
    R[k](); bindTips(main); document.title = VIEWS.find(function (v) { return v[0] === k; })[1] + " · Merchant Risk & Underwriting (sample data)"; window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  menu.addEventListener("click", function () { var o = side.classList.toggle("open"); menu.setAttribute("aria-expanded", String(o)); });
  document.querySelectorAll(".seg button").forEach(function (b) { b.addEventListener("click", function () {
    if (b.getAttribute("data-mode") === "Sample") return;
    main.innerHTML = head("Connect Live mode", "This hosted example has no Snowflake connection, so it never pretends to be Live. Live mode runs the same Streamlit app on your account.", "Setup needed") +
      '<section class="card modal"><ol><li>Run <code>sql/setup.sql</code> in a Snowsight worksheet (about 17 s on an XSMALL warehouse).</li><li>Run the app locally with key-pair auth, or deploy it as Streamlit in Snowflake. Both are in the README.</li></ol><p><a href="https://github.com/sfc-gh-jsoliz/sfguide-merchant-risk#live-mode">Live mode instructions</a> · <a href="#portfolio" id="back">Back to Sample</a></p></section>';
    document.getElementById("back").addEventListener("click", function (e) { e.preventDefault(); location.hash = "#portfolio"; route(); });
    side.classList.remove("open");
  }); });
  route();
})();
