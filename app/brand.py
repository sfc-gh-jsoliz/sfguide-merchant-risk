"""Brand tokens from docs/DESIGN.md, global CSS and small HTML helpers."""
import base64
import html

T = {
    "ox900": "#3D1019", "ox700": "#5A1A28", "ox500": "#7D2A3C", "oxSoft": "#F4E6E8",
    "stone": "#F3F1EE", "surface": "#FFFFFF", "surface2": "#ECE8E3", "line": "#DCD6CF", "grid": "#E7E1DA",
    "ink": "#1E1A1B", "ink2": "#4A4245", "muted": "#655C5F", "steel": "#36587A",
    "approve": "#1D6B47", "approveSoft": "#DDF0E5", "refer": "#8A5A00", "referSoft": "#FBEBCB",
    "decline": "#B02A1E", "declineSoft": "#F9E0DC",
}
DEC_COLORS = {"approve": "#2E8A5F", "refer": "#D49A1F", "decline": "#B02A1E"}  # chart fills (non-text)

LOGO = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="30" height="30">'
        '<rect width="32" height="32" rx="7" fill="#5A1A28"/>'
        '<path d="M6 21 A10 10 0 0 1 11.1 12.3" stroke="#7FD1A8" stroke-width="3" fill="none"/>'
        '<path d="M12.9 11.4 A10 10 0 0 1 21.6 12.8" stroke="#F0C36A" stroke-width="3" fill="none"/>'
        '<path d="M23.2 14.3 A10 10 0 0 1 26 21" stroke="#F29A8E" stroke-width="3" fill="none"/>'
        '<path d="M16 21 L21 14.5" stroke="#FFF7F2" stroke-width="2" stroke-linecap="round"/>'
        '<circle cx="16" cy="21" r="2.2" fill="#FFF7F2"/></svg>')
LOGO_IMG = ('<img alt="Merchant Risk & Underwriting logo" width="34" height="34" src="data:image/svg+xml;base64,'
            + base64.b64encode(LOGO.encode()).decode() + '">')

_FONTS = "".join(
    f'@font-face{{font-family:"{fam}";src:url("app/static/fonts/{f}-latin-{w}-normal.woff2") format("woff2");font-weight:{w};font-display:swap}}'
    for fam, f, ws in (("Instrument Sans", "instrument-sans", (400, 500, 600, 700)), ("Red Hat Mono", "red-hat-mono", (400, 600)))
    for w in ws)

CSS = "<style>" + _FONTS + """
@property --n{syntax:"<integer>";initial-value:0;inherits:false}
:root{--ox900:#3D1019;--ox700:#5A1A28;--ox500:#7D2A3C;--oxSoft:#F4E6E8;--stone:#F3F1EE;--surface:#fff;--surface2:#ECE8E3;--line:#DCD6CF;--grid:#E7E1DA;
 --ink:#1E1A1B;--ink2:#4A4245;--muted:#655C5F;--steel:#36587A;--ap:#1D6B47;--apS:#DDF0E5;--rf:#8A5A00;--rfS:#FBEBCB;--dc:#B02A1E;--dcS:#F9E0DC;
 --sans:"Instrument Sans",ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"Red Hat Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
html{overflow-x:clip}
[data-testid="stIconMaterial"],.material-symbols-rounded{font-family:"Material Symbols Rounded"!important}
html,body,[class*="st-"],.stMarkdown,button,input,textarea,select{font-family:var(--sans)}
[data-testid="stToolbarActions"],[data-testid="stMainMenu"],[data-testid="stAppDeployButton"],[data-testid="stDecoration"],#MainMenu,footer{display:none}
[data-testid="stExpandSidebarButton"]{background:var(--ox700);border-radius:8px}[data-testid="stExpandSidebarButton"] svg{color:#FFF7F2}
[data-testid="stHeader"]{background:transparent;height:2.6rem}
.stApp{background:var(--stone)}
.block-container,[data-testid="stMainBlockContainer"]{padding-top:1.6rem!important;max-width:1240px;padding-left:1.4rem;padding-right:1.4rem}
/* sidebar shell */
[data-testid="stSidebar"]{background:var(--ox900);border-right:0}
[data-testid="stSidebar"] *{color:#F1E4E6}
[data-testid="stSidebarHeader"]{height:.6rem;padding:0}
[data-testid="stSidebarCollapseButton"] svg,[data-testid="stSidebarCollapsedControl"] svg{color:#C9AEB4}
.mr-brand{display:flex;gap:.65rem;align-items:center;padding:.2rem 0 .9rem;border-bottom:1px solid #5A2733;margin-bottom:.9rem}
.mr-brand b{display:block;font-size:1.02rem;font-weight:600;letter-spacing:-.01em;line-height:1.2;color:#FFF7F2}
.mr-brand span{display:block;font-size:.74rem;color:#C9AEB4;margin-top:.15rem}
.mr-label{font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:#C9AEB4!important;margin:.9rem 0 .35rem;font-weight:600}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button{background:transparent;border-color:#6E3441;min-height:2rem;font-size:.82rem}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button p{color:#E9D9DC}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[kind$="Active"]{background:#FFF7F2;border-color:#FFF7F2}
[data-testid="stSidebar"] [data-testid="stButtonGroup"] button[kind$="Active"] p{color:var(--ox900);font-weight:600}
.st-key-nav [role="radiogroup"]{gap:.15rem!important}
.st-key-nav label[data-baseweb="radio"]{margin:0!important;padding:.55rem .7rem;border-radius:8px;border-left:3px solid transparent;width:100%;cursor:pointer;transition:background .15s}
.st-key-nav label[data-baseweb="radio"]>div:first-child{display:none}
.st-key-nav label[data-baseweb="radio"] p{font-size:.92rem;font-weight:500;color:#E9D9DC}
.st-key-nav label[data-baseweb="radio"]:hover{background:#4E1A26}
.st-key-nav label[data-baseweb="radio"]:has(input:checked){background:#5A2030;border-left-color:#F29A8E}
.st-key-nav label[data-baseweb="radio"]:has(input:checked) p{color:#FFF7F2;font-weight:600}
.mr-chip{display:inline-flex;align-items:center;gap:.35rem;font-size:.74rem;border-radius:999px;padding:.22rem .6rem;border:1px solid var(--line);color:var(--ink2);background:var(--surface);white-space:nowrap;max-width:100%;font-weight:500}
.mr-chip.sample{background:var(--rfS);color:var(--rf)!important;border-color:#EDCF8E;font-weight:600}
.mr-chip.live{background:var(--apS);color:var(--ap)!important;border-color:#A9D8BE;font-weight:600}
[data-testid="stSidebar"] .mr-chip.role{white-space:normal;background:#4E1A26;border-color:#6E3441;color:#E9D9DC!important}
.mr-dot{width:7px;height:7px;border-radius:50%;background:currentColor}
.mr-side-foot{font-size:.72rem;color:#C9AEB4!important;margin-top:1.4rem;line-height:1.45}
/* page header */
.mr-h{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin:0 0 1rem}
.mr-h h1{font-size:1.7rem;line-height:1.15;margin:0;color:var(--ink);font-weight:600;letter-spacing:-.02em;padding:0}
.mr-h p{margin:.3rem 0 0;color:var(--muted);font-size:.9rem;max-width:64ch}
.mr-h .chips{display:flex;gap:.4rem;flex-wrap:wrap}
.mr-cap{display:inline-flex;gap:.35rem;align-items:center;font-size:.72rem;color:var(--ox500);background:var(--oxSoft);border:1px solid #E6CBD0;border-radius:6px;padding:.2rem .5rem;font-weight:500;max-width:100%;flex-wrap:wrap}
.mr-cap.sample{color:var(--rf);background:var(--rfS);border-color:#EDCF8E}
/* cards */
.mr-card,[class*="st-key-card"]{background:var(--surface);border:1px solid var(--line);border-radius:10px;min-width:0}
[class*="st-key-card"]{padding:1rem 1.1rem .6rem;animation:mrIn .16s ease-out backwards}
[class*="st-key-card"]:hover{border-color:#C9C0B6}
.mr-card{padding:1rem 1.1rem}
[data-testid="stMarkdownContainer"] p.mr-card-h,.mr-card-h{font-weight:600;font-size:.98rem;color:var(--ink);margin:0 0 .15rem}
[data-testid="stMarkdownContainer"] p.mr-card-s,.mr-card-s{font-size:.8rem;color:var(--muted);margin:0 0 .6rem}
@keyframes mrIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
/* kpis */
.mr-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.7rem;margin-bottom:1rem}
.mr-kpi{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:.8rem .9rem;position:relative;overflow:hidden;animation:mrIn .16s ease-out backwards;transition:transform .15s,border-color .15s}
.mr-kpi:hover{transform:translateY(-1px);border-color:#C9C0B6}
.mr-kpi:nth-child(2){animation-delay:.03s}.mr-kpi:nth-child(3){animation-delay:.06s}.mr-kpi:nth-child(4){animation-delay:.09s}.mr-kpi:nth-child(5){animation-delay:.12s}
.mr-kpi::before{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:var(--ox500)}
.mr-kpi .k{font-size:.75rem;color:var(--muted);font-weight:500}
.mr-kpi .v{font-family:var(--mono);font-size:1.6rem;font-weight:600;color:var(--ink);margin:.25rem 0 .1rem;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.mr-kpi .v .cnt{animation:mrCount .65s ease-out forwards;counter-reset:n var(--n)}
.mr-kpi .v .cnt::after{content:counter(n)}
@keyframes mrCount{from{--n:0}}
.mr-kpi .d{font-size:.74rem;color:var(--muted)}
.mr-kpi svg{position:absolute;right:.6rem;top:.7rem;opacity:.9}
.up-bad{color:var(--dc);font-weight:600}.down-good{color:var(--ap);font-weight:600}.up-good{color:var(--ap);font-weight:600}.down-bad{color:var(--dc);font-weight:600}.flat{color:var(--muted);font-weight:600}
/* pills */
.mr-pill{display:inline-flex;align-items:center;gap:.3rem;font-size:.72rem;font-weight:600;border-radius:999px;padding:.14rem .55rem;white-space:nowrap}
.mr-pill.approve{background:var(--apS);color:var(--ap)}.mr-pill.refer{background:var(--rfS);color:var(--rf)}.mr-pill.decline{background:var(--dcS);color:var(--dc)}
.mr-pill.ok{background:var(--apS);color:var(--ap)}.mr-pill.warn{background:var(--dcS);color:var(--dc)}.mr-pill.n{background:var(--surface2);color:var(--ink2)}
/* threshold rail */
.mr-rail{position:relative;margin:.2rem 0 .3rem}
.mr-rail svg{width:100%;height:auto;display:block}
.mr-rail .tick{animation:mrSlide .5s ease-out backwards}
@keyframes mrSlide{from{transform:translateX(-12px);opacity:0}}
.mr-legend{display:flex;gap:1rem;flex-wrap:wrap;font-size:.78rem;color:var(--ink2);margin:.2rem 0 .2rem}
.mr-legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:.35rem;vertical-align:-1px}
/* insight */
.mr-insight{border-left:3px solid var(--ox500);background:var(--surface);border-radius:0 10px 10px 0;padding:.7rem .9rem;font-size:.86rem;color:var(--ink2);margin:.2rem 0 1rem;border-top:1px solid var(--line);border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
.mr-insight b{color:var(--ink)}
/* factors */
.mr-fx{list-style:none;margin:.2rem 0 .4rem;padding:0}
.mr-fx li{display:grid;grid-template-columns:minmax(0,11rem) minmax(0,1fr) 3.6rem;gap:.6rem;align-items:center;padding:.32rem 0;font-size:.84rem;border-bottom:1px solid #EFEAE4}
.mr-fx .bar{position:relative;height:10px;background:var(--surface2);border-radius:3px}
.mr-fx .bar i{position:absolute;top:0;bottom:0;border-radius:3px}
.mr-fx .n{font-family:var(--mono);text-align:right;font-variant-numeric:tabular-nums}
.mr-facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem;margin:.4rem 0 .8rem}
.mr-facts div{background:var(--stone);border-radius:8px;padding:.5rem .6rem}
.mr-facts span{display:block;font-size:.7rem;color:var(--muted)}
.mr-facts b{font-family:var(--mono);font-size:.95rem;color:var(--ink)}
/* skeleton */
.mr-skel{border-radius:10px;background:linear-gradient(90deg,#ECE8E3 25%,#F7F5F2 37%,#ECE8E3 63%);background-size:400% 100%;animation:mrSh 1.3s ease infinite}
@keyframes mrSh{0%{background-position:100% 50%}100%{background-position:0 50%}}
/* ai */
.mr-steps{list-style:none;padding:0;margin:.2rem 0 .6rem}
.mr-steps li{display:flex;gap:.55rem;align-items:flex-start;font-size:.85rem;padding:.28rem 0;color:var(--muted)}
.mr-steps li.done{color:var(--ink2)}.mr-steps li.now{color:var(--ink);font-weight:500}
.mr-steps .ic{width:16px;height:16px;border-radius:50%;flex:none;margin-top:2px;border:2px solid var(--line)}
.mr-steps li.done .ic{background:var(--ox500);border-color:var(--ox500);box-shadow:inset 0 0 0 3px #fff}
.mr-steps li.now .ic{border-color:var(--ox500);border-top-color:transparent;animation:mrSpin .8s linear infinite}
@keyframes mrSpin{to{transform:rotate(360deg)}}
.mr-src{font-size:.78rem;color:var(--muted);border-top:1px dashed var(--line);margin-top:.6rem;padding-top:.5rem}
.mr-src code,.mr-card code{font-family:var(--mono);font-size:.74rem;background:var(--surface2);border-radius:4px;padding:.05rem .3rem;color:var(--ink2)}
[class*="st-key-note_body"] h1,[class*="st-key-card_answer"] h1{font-size:1.3rem!important;line-height:1.3!important;padding:.4rem 0!important}
[class*="st-key-note_body"] h2,[class*="st-key-card_answer"] h2{font-size:1.05rem!important;padding:.6rem 0 .2rem!important}
[data-testid="stMarkdownContainer"] table{font-size:.84rem}
[data-testid="stMarkdownContainer"] th{background:var(--surface2)}
.mr-empty{text-align:center;padding:2.2rem 1rem;color:var(--muted);font-size:.9rem}
.mr-empty b{display:block;color:var(--ink);font-size:1rem;margin-bottom:.25rem}
/* buttons */
.stButton>button[kind="primary"]{background:var(--ox700);border-color:var(--ox700);color:#fff;font-weight:600}
.stButton>button[kind="primary"]:hover{background:var(--ox500);border-color:var(--ox500)}
.stButton>button{border-radius:8px}
[data-testid="stDataFrame"]{border-radius:10px}
[data-testid="stExpander"] details{background:var(--surface);border-color:var(--line)}
@media (max-width:900px){.mr-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:640px){
 .mr-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
 .mr-kpi .v{font-size:1.25rem}
 .mr-kpi svg{display:none}
 .mr-h h1{font-size:1.35rem}
 .mr-fx li{grid-template-columns:minmax(0,8rem) minmax(0,1fr) 3.2rem}
 .mr-facts{grid-template-columns:repeat(2,minmax(0,1fr))}
 .block-container,[data-testid="stMainBlockContainer"]{padding-left:.9rem;padding-right:.9rem}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""


def esc(s):
    return html.escape(str(s))


def usd(x, d=1):
    x = float(x)
    if abs(x) >= 1e9:
        return f"${x / 1e9:.{d + 1}f}B"
    if abs(x) >= 1e6:
        return f"${x / 1e6:.{d}f}M"
    if abs(x) >= 1e3:
        return f"${x / 1e3:.0f}K"
    return f"${x:,.0f}"


def pc(x, d=1):
    return f"{x * 100:.{d}f}%"


def delta(x, text, good_when_up=True):
    if abs(x) < 1e-9:
        return f'<span class="flat">● {esc(text)}</span>'
    up = x > 0
    cls = ("up-good" if up else "down-bad") if good_when_up else ("up-bad" if up else "down-good")
    return f'<span class="{cls}">{"▲" if up else "▼"} {esc(text)}</span>'


def spark(values, color="#7D2A3C", w=72, h=24):
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1
    pts = " ".join(f"{i * w / (len(values) - 1):.1f},{h - 2 - (v - lo) / rng * (h - 4):.1f}" for i, v in enumerate(values))
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true"><polyline fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round" points="{pts}"/></svg>'


def kpi(label, value_html, delta_html, values=None):
    s = spark(values) if values else ""
    return f'<div class="mr-kpi"><div class="k">{esc(label)}</div><div class="v">{value_html}</div><div class="d">{delta_html}</div>{s}</div>'


def counter(prefix, number, suffix=""):
    """Animated integer count-up (CSS @property), with prefix/suffix text."""
    return f'{esc(prefix)}<span class="cnt" style="--n:{int(number)}"></span>{esc(suffix)}'


def num(value, decimals=0, prefix="", suffix=""):
    """Counter for a decimal figure: the integer part counts up, the rounded decimals follow."""
    txt = f"{value:.{decimals}f}"
    whole, _, frac = txt.partition(".")
    return counter(prefix, int(whole), ("." + frac if frac else "") + suffix)


def env_chip(mode):
    if mode == "Live":
        return '<span class="mr-chip live"><span class="mr-dot"></span>Live · Snowflake</span>'
    return '<span class="mr-chip sample"><span class="mr-dot"></span>Sample data</span>'


def header(title, sub, cap, mode):
    c = "mr-cap" if mode == "Live" else "mr-cap sample"
    return (f'<div class="mr-h"><div><h1>{esc(title)}</h1><p>{esc(sub)}</p></div>'
            f'<div class="chips">{env_chip(mode)}<span class="{c}">{cap}</span></div></div>')


def pill(decision):
    return f'<span class="mr-pill {esc(decision)}">{esc(decision.capitalize())}</span>'


def verdict(status):
    if status == "verified":
        return '<span class="mr-pill ok">✓ Verified</span>'
    return '<span class="mr-pill warn">! Needs review</span>'


def rail(scores, decisions, marker=None, h=56, W=1000):
    """The threshold rail: 0-100 split at 40 and 70, one tick per application."""
    x = lambda v: 8 + v / 100 * (W - 16)  # noqa: E731
    bands = (f'<rect x="{x(0)}" y="14" width="{x(40) - x(0)}" height="{h - 28}" fill="#DDF0E5"/>'
             f'<rect x="{x(40)}" y="14" width="{x(70) - x(40)}" height="{h - 28}" fill="#FBEBCB"/>'
             f'<rect x="{x(70)}" y="14" width="{x(100) - x(70)}" height="{h - 28}" fill="#F9E0DC"/>')
    ticks = "".join(f'<line class="tick" x1="{x(s):.1f}" x2="{x(s):.1f}" y1="18" y2="{h - 18}" stroke="{DEC_COLORS[d]}" stroke-opacity=".55" stroke-width="2"/>'
                    for s, d in zip(scores, decisions))
    labels = "".join(f'<text x="{x(v)}" y="{h - 2}" text-anchor="{ {0: "start", 100: "end"}.get(v, "middle") }" font-size="12" fill="#655C5F" font-family="Red Hat Mono, monospace">{v}</text>'
                     for v in (0, 40, 70, 100))
    names = (f'<text x="{x(20)}" y="11" text-anchor="middle" font-size="12" font-weight="600" fill="#1D6B47">Approve</text>'
             f'<text x="{x(55)}" y="11" text-anchor="middle" font-size="12" font-weight="600" fill="#8A5A00">Refer</text>'
             f'<text x="{x(85)}" y="11" text-anchor="middle" font-size="12" font-weight="600" fill="#B02A1E">Decline</text>')
    mk = ""
    if marker is not None:
        mk = (f'<line x1="{x(marker)}" x2="{x(marker)}" y1="10" y2="{h - 14}" stroke="#1E1A1B" stroke-width="3"/>'
              f'<circle cx="{x(marker)}" cy="{h / 2}" r="7" fill="#1E1A1B" stroke="#fff" stroke-width="2"/>')
    return (f'<div class="mr-rail"><svg viewBox="0 0 {W} {h}" role="img" aria-label="Risk scores on a 0 to 100 scale with approve, refer and decline bands">'
            f'{bands}{ticks}{mk}{labels}{names}</svg></div>')


def skeleton(rows=((5, 92), (1, 280))):
    out = []
    for n, h in rows:
        cells = "".join(f'<div class="mr-skel" style="height:{h}px"></div>' for _ in range(n))
        out.append(f'<div style="display:grid;grid-template-columns:repeat({n},minmax(0,1fr));gap:.7rem;margin-bottom:.9rem">{cells}</div>')
    return "".join(out)


def steps_html(steps, current, finished=False):
    items = []
    for i, s in enumerate(steps):
        cls = "done" if (i < current or finished) else ("now" if i == current else "")
        items.append(f'<li class="{cls}"><span class="ic"></span><span>{esc(s)}</span></li>')
    return f'<ul class="mr-steps">{"".join(items)}</ul>'


def md_safe(text):
    """Model markdown for st.markdown: dollar signs are not LaTeX, "•" lines become list items."""
    lines = []
    for ln in (text or "").replace("$", "\\$").split("\n"):
        s = ln.lstrip()
        lines.append("- " + s[1:].lstrip() if s.startswith("•") else ln)
    return "\n".join(lines)
