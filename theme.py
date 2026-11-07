"""Shared Shotclock styles (main app + Source watcher page)."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap');
:root{--ink:#111827;--muted:#6B7280;--line:#E7E5E4;--surface:#FAFAF9;--orange:#E8643A;
      --red:#DC2626;--amber:#D97706;--green:#16A34A;}
html, body, .stMarkdown, .stButton button, .stDownloadButton button, textarea, input, label, p {
  font-family:'Inter',system-ui,-apple-system,sans-serif;}
[data-testid="stHeader"]{background:transparent;}
h1, h2, h3, h4, [data-testid="stMetricValue"], [data-testid="stMetricLabel"] p{font-family:'Inter',system-ui,-apple-system,sans-serif!important;letter-spacing:-.02em;}
[data-testid="stToolbar"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]{display:none;}
.block-container{padding-top:1.4rem;max-width:1180px;}
.sc-logo{display:flex;align-items:center;gap:14px;margin-bottom:1.1rem;}
.sc-logo svg{flex:none;box-shadow:0 6px 16px rgba(232,100,58,.28);border-radius:12px;}
.sc-word{font-family:'Inter',sans-serif;font-weight:800;font-size:2.3rem;letter-spacing:-.035em;line-height:1;color:var(--ink);}
.sc-word span{color:var(--orange);}
.sc-tag{font-family:'JetBrains Mono',monospace;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:6px;}
[data-testid="stSelectbox"] label p{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700;}
.sc-label{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700;margin:.2rem 0 .45rem;}
.sc-score{display:flex;gap:10px;margin:.2rem 0 1rem;flex-wrap:wrap;}
.sc-chip{display:flex;align-items:baseline;gap:8px;border:1px solid var(--line);border-radius:12px;padding:10px 14px;background:#fff;}
.sc-chip b{font-family:'JetBrains Mono',monospace;font-size:1.6rem;line-height:1;}
.sc-chip.r b{color:var(--red);} .sc-chip.a b{color:var(--amber);} .sc-chip.g b{color:var(--green);}
.sc-chip span{color:var(--muted);font-size:.85rem;}
.sc-headline{font-size:1.15rem;font-weight:700;color:var(--ink);margin:.2rem 0 .3rem;}
.sc-cite{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.75rem;background:var(--surface);
  border:1px solid var(--line);border-radius:6px;padding:2px 8px;color:#374151;margin-top:.3rem;}
.sc-cite a{color:var(--orange);text-decoration:underline;text-underline-offset:2px;font-family:inherit;}
.sc-cite a:hover{color:var(--ink);}
.sc-quote{border-left:3px solid var(--orange);padding:2px 0 2px 12px;color:#374151;font-size:.9rem;margin:.6rem 0 .2rem;font-style:italic;}
.sc-fix{background:#FFF7F3;border-radius:10px;padding:10px 12px;font-size:.92rem;margin-top:.5rem;}
.sc-empty{border:1.5px dashed var(--line);border-radius:16px;padding:46px 22px;text-align:center;color:var(--muted);}
.sc-empty b{display:block;color:var(--ink);font-size:1.05rem;margin-bottom:6px;}
.sc-dots{display:grid;grid-template-columns:repeat(10,1fr);gap:8px;margin:14px 0 6px;}
.sc-dot{aspect-ratio:1;border-radius:10px;display:flex;align-items:center;justify-content:center;
  font-family:'JetBrains Mono',monospace;font-weight:700;font-size:.9rem;}
.sc-dot.y{background:var(--orange);color:#fff;} .sc-dot.n{background:#F3F4F6;color:#9CA3AF;}
.sc-bignum{font-family:'JetBrains Mono',monospace;font-weight:800;font-size:3.4rem;line-height:1;color:var(--ink);}
.sc-bignum span{color:var(--orange);}
[data-testid="stExpander"] details{border-radius:12px;border:1px solid var(--line);background:#fff;}
[data-testid="stExpander"] summary p{font-weight:600;font-size:.97rem;}
.sc-change{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:.5rem 0;background:#fff;}
.sc-change .t{font-weight:700;margin-bottom:8px;color:var(--ink);}
.sc-ba{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;}
.sc-before{background:#FEF2F2;border-radius:8px;padding:8px 10px;font-size:.88rem;color:#7F1D1D;}
.sc-after{background:#F0FDF4;border-radius:8px;padding:8px 10px;font-size:.88rem;color:#14532D;font-weight:500;}
.sc-arrow{align-self:center;color:var(--orange);font-weight:800;font-size:1.2rem;}
.sc-why{color:var(--muted);font-size:.85rem;margin-top:8px;}
.sc-todo{list-style:none;padding-left:0;margin:.2rem 0 1rem;} .sc-todo li{padding:3px 0;color:#374151;display:flex;gap:10px;align-items:baseline;}
.sc-box{width:13px;height:13px;border:1.5px solid #A1A1AA;border-radius:3px;flex:none;position:relative;top:1px;}
.sc-foot{color:#9CA3AF;font-size:.78rem;text-align:center;margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);}

/* ===== About popover: source watcher buttons ===== */
.st-key-about_actions{padding-bottom:14px;margin-bottom:4px;border-bottom:1px solid var(--line);}
.st-key-about_actions [data-testid="stElementContainer"]:has([data-testid="stPageLink"]),
.st-key-about_actions [data-testid="stPageLink"], .st-key-about_actions [data-testid="stPageLink"] > div{width:100%!important;}
.st-key-about_actions [data-testid="stPageLink"] a{width:100%;box-sizing:border-box;display:flex;justify-content:center;align-items:center;gap:6px;
  background:var(--orange);border:1px solid var(--orange);border-radius:10px;padding:.5rem .9rem;min-height:40px;
  box-shadow:0 4px 12px -4px rgba(232,100,58,.55);transition:filter .15s;text-decoration:none;}
.st-key-about_actions [data-testid="stPageLink"] a:hover{filter:brightness(1.06);background:var(--orange);}
.st-key-about_actions [data-testid="stPageLink"] a *{color:#fff!important;font-weight:600;}
.st-key-about_actions [data-testid="stLinkButton"] a{border-radius:10px;min-height:40px;font-weight:600;}

/* ===== tabs: spaced icon pills ===== */
[data-testid="stTabs"]{margin-top:1.6rem;}
[data-testid="stTabs"] [role="tablist"]{gap:12px;padding:6px;background:#F3F2EF;border-radius:16px;width:fit-content;
  max-width:100%;overflow-x:auto;}
[data-testid="stTabs"] [role="tab"]{padding:11px 22px!important;border-radius:12px;transition:background .2s,box-shadow .2s;}
[data-testid="stTabs"] [role="tab"]:hover{background:rgba(255,255,255,.6);}
[data-testid="stTabs"] [role="tab"] p{font-weight:600;font-size:.98rem;color:var(--muted);}
[data-testid="stTabs"] [role="tab"] [data-testid="stIconMaterial"]{color:var(--muted);font-size:1.2rem;margin-right:2px;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{background:#fff;
  box-shadow:0 1px 2px rgba(17,24,39,.06),0 6px 18px -6px rgba(232,100,58,.35);}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] p{color:var(--ink);}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] [data-testid="stIconMaterial"]{color:var(--orange);}
[data-testid="stTabs"] [role="tab"]:focus-visible{outline:2px solid var(--orange);outline-offset:2px;}
.react-aria-SelectionIndicator{display:none!important;}
[data-testid="stTabs"] [role="tabpanel"]{padding-top:1.8rem;}

/* ===== white card for the City Letter results column ===== */
.st-key-card_out2{background:#fff!important;border:1px solid var(--line)!important;border-radius:20px!important;
  box-shadow:0 1px 1px rgba(17,17,19,.03),0 6px 24px -8px rgba(17,17,19,.08);padding:28px!important;}

/* ===== shot clock: dial + timeline (light) ===== */
.sc-clock{display:flex;gap:28px;align-items:center;padding:0 0 8px;margin-bottom:.5rem;}
.sc-clock.div{border-bottom:1px solid var(--line);padding-bottom:24px;margin-bottom:12px;}
.sc-dial{position:relative;width:148px;height:148px;flex:none;}
.sc-dial svg{width:148px;height:148px;transform:rotate(-90deg);}
.sc-dial .c{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.sc-dial .n{font-weight:600;font-size:2.6rem;line-height:1;letter-spacing:-.05em;color:var(--ink);font-variant-numeric:tabular-nums;}
.sc-dial small{color:var(--muted);font-size:.78rem;margin-top:4px;}
.sc-clock .info{flex:1;min-width:0;}
.sc-clock .sc-label{font-weight:500;letter-spacing:.06em;}
.sc-tl{position:relative;margin:0 0 14px;}
.sc-tl .r{display:flex;align-items:center;gap:12px;padding:7px 0;position:relative;font-size:.92rem;}
.sc-tl .r::before{content:"";position:absolute;left:9px;top:0;bottom:0;width:2px;background:var(--line);}
.sc-tl .r:first-child::before{top:50%;} .sc-tl .r:last-child::before{bottom:50%;}
.sc-tl .d{width:20px;height:20px;border-radius:50%;background:#fff;border:2px solid var(--line);position:relative;z-index:1;
  display:flex;align-items:center;justify-content:center;flex:none;}
.sc-tl .d svg{width:11px;height:11px;}
.sc-tl .done .d{background:var(--green);border-color:var(--green);}
.sc-tl .now .d{background:var(--orange);border-color:var(--orange);box-shadow:0 0 0 4px rgba(232,100,58,.18);}
.sc-tl .late .d{background:var(--red);border-color:var(--red);}
.sc-tl b{font-weight:500;color:var(--ink);}
.sc-tl .dt{margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:.78rem;color:var(--muted);}
.sc-verdict{display:flex;align-items:center;gap:8px;border-radius:10px;padding:10px 12px;font-size:.9rem;font-weight:500;}
.sc-verdict svg{width:17px;height:17px;flex:none;}
.sc-verdict.ok{background:rgba(22,163,74,.09);color:#13803D;}
.sc-verdict.over{background:rgba(232,100,58,.1);color:#B8441F;}
.sc-clock .law{color:var(--muted);font-size:.74rem;margin-top:10px;font-family:'JetBrains Mono',monospace;}

/* ===== results ring ===== */
.sc-sum{display:flex;align-items:center;gap:24px;padding:4px 0 24px;margin-bottom:8px;border-bottom:1px solid var(--line);}
.sc-ring{position:relative;width:96px;height:96px;flex:none;}
.sc-ring svg{width:96px;height:96px;transform:rotate(-90deg);}
.sc-ring .v{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-weight:600;
  font-size:1.45rem;letter-spacing:-.03em;color:var(--ink);font-variant-numeric:tabular-nums;}
.sc-sum .t{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500;margin-bottom:10px;}
.sc-sum .sc-score{margin:0;}
.sc-sum .sc-chip{border-radius:999px;padding:6px 14px 6px 10px;align-items:center;}
.sc-sum .sc-chip b{font-family:inherit;font-size:1.05rem;font-weight:600;color:var(--ink);}
.sc-sum .sc-chip b::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:8px;
  vertical-align:middle;position:relative;top:-1px;}
.sc-sum .sc-chip.r b::before{background:var(--red);} .sc-sum .sc-chip.a b::before{background:var(--amber);}
.sc-sum .sc-chip.g b::before{background:var(--green);}
@media (max-width:700px){
  .sc-clock{flex-direction:column;align-items:stretch;}.sc-dial{margin:0 auto;}
  [data-testid="stTabs"] [role="tab"]{padding:9px 14px!important;}
  .sc-dots{grid-template-columns:repeat(5,1fr);}
  .sc-word{font-size:1.8rem;}
  .sc-ba{grid-template-columns:1fr;}.sc-arrow{display:none;}}
</style>
"""
