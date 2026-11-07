"""Shotclock: ADU fast-path checker (Claude Impact Lab, Lane 02 "Clear it").

Application Pre-Check: check an ADU project before submitting.
City Letter Review: check a city corrections letter against state law, with the 60-day shot clock and a draft reply.
Accuracy Test: blind review of San Clemente's ordinance vs HCD's 10 findings.
Every finding must cite a loaded source in docs/. Not legal advice.
"""
import html
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Literal

import anthropic
import streamlit as st
from pydantic import BaseModel, Field, ValidationError

from deadlines import shot_clock

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
DEMO = ROOT / "demo"

# Backtest: review San Clemente's rules blind, then compare with HCD's 10 real findings.
# The backtest input is the version HCD reviewed (Ord. 1742), kept in docs/historical/ so Tabs 1-2 never cite it.
# San Clemente amended § 17.28.270 on June 16, 2026 (Ord. 1810); that current text lives in docs/city/.
ORDINANCE_FILE = DOCS / "historical" / "san-clemente-muni-code-17-28-270.md"
CURRENT_ORDINANCE_FILE = DOCS / "city" / "san-clemente-muni-code-17-28-270-2026.md"
PACKET_FILE = DOCS / "city" / "san-clemente-adu-info-packet-2024-08.md"
HCD_SC_SUMMARY = DOCS / "state" / "hcd-findings-san-clemente-2025-10.md"
BACKTEST_HIDE = ("hcd-findings-san-clemente-2025-10.md", "hcd-findings-san-clemente-2025-10-fulltext.md",
                 PACKET_FILE.name, ORDINANCE_FILE.name,  # the answer key + the input itself
                 CURRENT_ORDINANCE_FILE.name)  # the city's 2026 fix would give the answers away
BACKTEST_SAVED = ROOT / "backtest" / "last-result.json"
GRADER_RULES = ("You grade a backtest strictly. A finding counts as caught only if a checker issue names the same "
                "city rule (or clearly the same requirement) AND the same legal problem. Related but different "
                "issues do not count. Do not give partial credit.")

DISCLAIMER = ("Not legal advice. Results say \"likely\" because they are an automated reading of the loaded "
              "sources. Confirm with the city or an attorney before acting.")


# ---------- config ----------
def secret(name: str, default: str | None = None) -> str | None:
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # no secrets.toml
        pass
    return os.environ.get(name, default)


MODEL = secret("CLAUDE_MODEL", "claude-sonnet-5-5")


# ---------- sources ----------
@st.cache_data(show_spinner=False)
def load_sources(kind: str, exclude: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    """Read every .md/.txt/.pdf in docs/<kind>/ -> [(filename, text)]."""
    out = []
    folder = DOCS / kind
    if not folder.exists():
        return out
    for p in sorted(folder.iterdir()):
        if p.name in exclude or p.name.lower() == "readme.md":
            continue
        if p.suffix.lower() in (".md", ".txt"):
            out.append((p.name, p.read_text(errors="ignore")))
        elif p.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            text = "\n".join((pg.extract_text() or "") for pg in PdfReader(p).pages)
            out.append((p.name, text))
    return out


def sources_block(exclude: tuple[str, ...] = ()) -> str:
    parts = []
    for kind in ("state", "city"):
        for name, text in load_sources(kind, exclude):
            parts.append(f'<source name="{kind}/{name}">\n{text}\n</source>')
    return "\n\n".join(parts)


SYSTEM_RULES = """You are Shotclock, an assistant that checks California ADU (accessory dwelling unit) permit
matters against the loaded sources below. Users are Habitat for Humanity / nonprofit project managers,
homeowners, small builders, and city permit techs in Orange County.

Hard rules:
- Use ONLY the loaded sources. Every finding cites a source: its name (e.g. "state/hcd-adu-handbook.md"),
  the section (e.g. "Gov. Code § 66315"), and a SHORT exact quote from that source (under 30 words).
- If the sources do not cover an item, say "not covered by loaded sources" and mark it unclear / missing.
- Never invent statute numbers. Current state ADU law is Gov. Code §§ 66310-66342; § 65852.2 was repealed
  by SB 477 and must not be cited as current.
- Use cautious words ("likely", "appears to"). You are not giving legal advice.
- Deadlines: say only what the sources state. § 66317(a)(3) (state/gov-code-66310-66342.md) requires the agency to
  approve or deny a completed application within 60 days, and says that if it has not, "the application shall be
  deemed approved." When the shot clock shows the deadline has passed, you may say the application "appears to be
  deemed approved under Gov. Code § 66317(a)(3)", quoting the statute, and note that the 60 days are tolled if the
  applicant requested a delay and only start once the application is complete.
- Be concise and practical: each reason and fix is one or two plain-English sentences."""


@st.cache_resource
def get_client() -> anthropic.Anthropic | None:
    key = secret("ANTHROPIC_API_KEY")
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


# ---------- structured outputs ----------
class PrecheckItem(BaseModel):
    item: str = Field(description="Short title of the requirement, at most 6 words, e.g. 'Site plan' or 'Impact fees'")
    status: Literal["pass", "missing", "problem"]
    reason: str
    fix: str = Field(description="What to do; empty if status is pass")
    source: str = Field(description="Loaded source file name")
    citation: str = Field(description="Section, e.g. Gov. Code § 66321(b)")
    quote: str = Field(description="Short exact quote from the source")


class PrecheckResult(BaseModel):
    summary: str
    items: list[PrecheckItem]


class Correction(BaseModel):
    item: str = Field(description="Short title, at most 6 words")
    before: str = Field(description="Exact wording in the application now, or '(not in application)'")
    after: str = Field(description="Exact replacement wording or text to add; use [CONFIRM: ...] for unknown facts")
    why: str = Field(description="One sentence")
    citation: str


class CorrectedApplication(BaseModel):
    corrections: list[Correction]
    corrected_text: str = Field(description="Full revised application / project description with all corrections "
                                            "applied, ready to edit and resubmit")
    human_todo: list[str] = Field(description="Things only a person can produce: drawings, reports, signatures, "
                                              "fees, confirmations")
    cover_note: str = Field(description="Short note to the city listing what changed in this resubmittal")


class LetterItem(BaseModel):
    request: str = Field(description="Short title of the city's request, at most 8 words, e.g. 'Owner-occupancy covenant'")
    status: Literal["matches_law", "likely_conflicts", "unclear"]
    reason: str
    source: str
    citation: str
    quote: str


class LetterResult(BaseModel):
    summary: str
    items: list[LetterItem]
    draft_reply: str = Field(description="Polite reply letter to the city, citing statutes for conflicts")


class BacktestIssue(BaseModel):
    rule: str = Field(description="The ordinance provision, e.g. § 17.28.270(E)(2)(a), and what it says")
    conflict: str = Field(description="Why it likely conflicts with state ADU law")
    citation: str
    quote: str = Field(description="Short exact quote from a loaded state source")


class BacktestResult(BaseModel):
    summary: str
    issues: list[BacktestIssue]


class FindingMatch(BaseModel):
    finding_number: int
    finding: str = Field(description="HCD's finding in a few words")
    caught: bool
    matched_issue: str = Field(description="The checker issue that matches it, or empty")


class BacktestGrade(BaseModel):
    matches: list[FindingMatch]
    extra_issues: list[str] = Field(description="Checker issues that match no HCD finding")


# Resolve nested model types explicitly (needed on Python < 3.14 when Streamlit runs the script).
for _m in (PrecheckItem, PrecheckResult, Correction, CorrectedApplication, LetterItem, LetterResult,
           BacktestIssue, BacktestResult, FindingMatch, BacktestGrade):
    _m.model_rebuild(force=True, _types_namespace=globals())


def ask_claude(task: str, output_model: type[BaseModel], exclude: tuple[str, ...] = (),
               system_override: str | None = None, effort: str | None = None, max_tokens: int = 16000):
    client = get_client()
    if client is None:
        st.error("No API key. Add ANTHROPIC_API_KEY to .streamlit/secrets.toml (see secrets.toml.example).")
        return None
    if system_override is not None:
        system = system_override
    else:
        system = [
            {"type": "text", "text": SYSTEM_RULES},
            # Sources are identical across calls -> cache them so repeat checks are fast and cheap.
            {"type": "text", "text": "LOADED SOURCES:\n\n" + sources_block(exclude),
             "cache_control": {"type": "ephemeral"}},
        ]
    # Attempt 1 as requested. If the JSON reply is cut off or malformed (the SDK raises ValidationError while
    # parsing, before we can check stop_reason), retry once with low effort (less thinking, more room for the
    # answer) and the most tokens a non-streaming call allows.
    attempts = [(effort, max_tokens), ("low", max(max_tokens, 21000))]
    try:
        for i, (eff, mt) in enumerate(attempts):
            try:
                resp = client.messages.parse(
                    model=MODEL,
                    max_tokens=mt,
                    system=system,
                    **({"output_config": {"effort": eff}} if eff else {}),
                    messages=[{"role": "user", "content": task}],
                    output_format=output_model,
                )
                if resp.stop_reason == "max_tokens" and i == 0:
                    continue
                break
            except (ValidationError, ValueError):
                if i == len(attempts) - 1:
                    st.error("Claude's answer was cut off or malformed twice. Please click the button again, "
                             "or shorten the input.")
                    return None
    except anthropic.AuthenticationError:
        st.error("The API key was rejected. Check ANTHROPIC_API_KEY.")
        return None
    except anthropic.RateLimitError:
        st.error("Rate limited. Wait a few seconds and try again.")
        return None
    except anthropic.APIStatusError as e:
        st.error(f"Claude API error {e.status_code}: {e.message}")
        return None
    except anthropic.APIConnectionError:
        st.error("Could not reach the Claude API. Check the internet connection.")
        return None
    if resp.stop_reason == "refusal":
        st.error("Claude declined this request. Try rephrasing.")
        return None
    if resp.stop_reason == "max_tokens" or resp.parsed_output is None:
        st.error("The answer was cut off. Try a shorter input.")
        return None
    return resp.parsed_output


# ---------- UI helpers ----------
STATUS_STYLE = {
    "problem": ("❌", "Problem"), "missing": ("⚠️", "Missing"), "pass": ("✅", "Passes"),
    "likely_conflicts": ("🔴", "Likely conflicts with state law"),
    "unclear": ("🟡", "Unclear: not covered by loaded sources"), "matches_law": ("🟢", "Matches law"),
}
ORDER = ["problem", "likely_conflicts", "missing", "unclear", "pass", "matches_law"]
CITIES = ["San Clemente", "Dana Point", "Irvine", "Santa Ana", "Anaheim", "Other OC city"]
# Shotclock is tuned for Habitat-style nonprofits (the sponsor); this line goes into every check.
APPLICANT = ("a Habitat for Humanity-style nonprofit building an ADU to sell at cost (0% markup) to a low-income "
             "family, possibly as a separate sale under Gov. Code § 66341. Prioritize what keeps the project on the "
             "60-day ministerial path and keeps the affordable sale possible.")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700;800&display=swap');
:root{--ink:#111827;--muted:#6B7280;--line:#E7E5E4;--surface:#FAFAF9;--orange:#E8643A;
      --red:#DC2626;--amber:#D97706;--green:#16A34A;}
html, body, .stMarkdown, .stButton button, .stDownloadButton button, textarea, input, label, p {
  font-family:'Inter',system-ui,-apple-system,sans-serif;}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stToolbar"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]{display:none;}
.block-container{padding-top:1.4rem;max-width:1180px;}
.sc-logo{display:flex;align-items:center;gap:14px;margin-bottom:1.1rem;}
[data-testid="stTabs"]{margin-top:.9rem;}
.sc-logo svg{flex:none;box-shadow:0 6px 16px rgba(232,100,58,.28);border-radius:12px;}
.sc-word{font-family:'Inter',sans-serif;font-weight:800;font-size:2.3rem;letter-spacing:-.035em;line-height:1;color:var(--ink);}
.sc-word span{color:var(--orange);}
.sc-tag{font-family:'JetBrains Mono',monospace;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-top:6px;}
[data-testid="stSelectbox"] label p{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700;}
.sc-label{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700;margin:.2rem 0 .45rem;}
.sc-clock{border-radius:18px;padding:22px 24px;background:#111827;color:#fff;margin-bottom:1rem;}
.sc-clock .big{font-family:'JetBrains Mono',monospace;font-weight:800;font-size:3.1rem;line-height:1;color:var(--orange);}
.sc-clock .big.ok{color:#4ADE80;}
.sc-clock .sub{color:#E5E7EB;font-size:.95rem;margin-top:8px;}
.sc-clock .law{color:#9CA3AF;font-size:.78rem;margin-top:10px;font-family:'JetBrains Mono',monospace;}
.sc-bar{height:8px;border-radius:99px;background:#374151;margin-top:14px;overflow:hidden;}
.sc-bar>div{height:100%;background:var(--orange);}
.sc-bar>div.ok{background:#4ADE80;}
.sc-score{display:flex;gap:10px;margin:.2rem 0 1rem;flex-wrap:wrap;}
.sc-chip{display:flex;align-items:baseline;gap:8px;border:1px solid var(--line);border-radius:12px;padding:10px 14px;background:#fff;}
.sc-chip b{font-family:'JetBrains Mono',monospace;font-size:1.6rem;line-height:1;}
.sc-chip.r b{color:var(--red);} .sc-chip.a b{color:var(--amber);} .sc-chip.g b{color:var(--green);}
.sc-chip span{color:var(--muted);font-size:.85rem;}
.sc-headline{font-size:1.15rem;font-weight:700;color:var(--ink);margin:.2rem 0 .3rem;}
.sc-cite{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:.75rem;background:var(--surface);
  border:1px solid var(--line);border-radius:6px;padding:2px 8px;color:#374151;margin-top:.3rem;}
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
[data-testid="stTabs"] [role="tab"] p{font-weight:700;font-size:1rem;}
.sc-change{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:.5rem 0;background:#fff;}
.sc-change .t{font-weight:700;margin-bottom:8px;color:var(--ink);}
.sc-ba{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;}
.sc-before{background:#FEF2F2;border-radius:8px;padding:8px 10px;font-size:.88rem;color:#7F1D1D;}
.sc-after{background:#F0FDF4;border-radius:8px;padding:8px 10px;font-size:.88rem;color:#14532D;font-weight:500;}
.sc-arrow{align-self:center;color:var(--orange);font-weight:800;font-size:1.2rem;}
.sc-why{color:var(--muted);font-size:.85rem;margin-top:8px;}
.sc-todo{list-style:none;padding-left:0;margin:.2rem 0 1rem;} .sc-todo li{padding:3px 0;color:#374151;}
.sc-foot{color:#9CA3AF;font-size:.78rem;text-align:center;margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);}
@media (max-width:700px){.sc-dots{grid-template-columns:repeat(5,1fr);}
  .sc-word{font-size:1.8rem;}.sc-clock .big{font-size:2.4rem;}
  .sc-ba{grid-template-columns:1fr;}.sc-arrow{display:none;}}
</style>
"""


def h(text) -> str:
    return html.escape(str(text or ""))


def html_block(markup: str):
    st.markdown(markup, unsafe_allow_html=True)


def label(text: str):
    html_block(f'<div class="sc-label">{h(text)}</div>')


def empty_state(title: str, body: str):
    html_block(f'<div class="sc-empty"><b>{h(title)}</b>{h(body)}</div>')


def score_chips(chips: list[tuple[str, int, str]]):
    html_block('<div class="sc-score">' + "".join(
        f'<div class="sc-chip {cls}"><b>{n}</b><span>{h(lbl)}</span></div>' for cls, n, lbl in chips) + "</div>")


def render_rows(items, title_attr: str, fix_attr: str | None = None):
    for it in sorted(items, key=lambda x: ORDER.index(x.status)):
        icon, status_label = STATUS_STYLE[it.status]
        with st.expander(f"{icon}  {getattr(it, title_attr)}"):
            label(status_label)
            st.write(it.reason)
            fix = getattr(it, fix_attr, "") if fix_attr else ""
            if fix:
                html_block(f'<div class="sc-fix"><b>Fix</b> · {h(fix)}</div>')
            html_block(f'<div class="sc-quote">“{h(it.quote)}”</div>'
                       f'<span class="sc-cite">{h(it.citation)} · {h(it.source)}</span>')


def clock_card(clock):
    pct = min(100, max(0, round((60 - clock.days_left) / 60 * 100)))
    if clock.overdue:
        big, cls, sub = (f"−{-clock.days_left} DAYS", "", f"past the 60-day deadline ({clock.due_date:%b %d, %Y}): the application appears deemed approved")
    else:
        big, cls, sub = f"{clock.days_left} DAYS LEFT", "ok", f"until the city must decide ({clock.due_date:%b %d, %Y})"
    html_block(f'<div class="sc-clock"><div class="sc-label" style="color:#9CA3AF">Shot clock</div>'
               f'<div class="big {cls}">{big}</div><div class="sub">{h(sub)}</div>'
               f'<div class="sc-bar"><div class="{cls}" style="width:{pct}%"></div></div>'
               f'<div class="law">Gov. Code § 66317(a)(3) · complete {clock.complete_date:%b %d} · estimate; tolled if you asked for a delay</div></div>')


def read_upload(f) -> str:
    if f is None:
        return ""
    if f.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(f).pages)
    return f.read().decode(errors="ignore")


def report_md(title: str, summary: str, items, title_attr: str, extra: str = "") -> str:
    lines = [f"# {title}", "", summary, ""]
    for it in sorted(items, key=lambda x: ORDER.index(x.status)):
        icon, lbl = STATUS_STYLE[it.status]
        lines += [f"## {icon} {getattr(it, title_attr)} ({lbl})", it.reason,
                  f"Source: {it.citation}, {it.source}: \"{it.quote}\"", ""]
    if extra:
        lines += [extra, ""]
    lines += ["---", DISCLAIMER]
    return "\n".join(lines)


# ---------- page ----------
st.set_page_config(page_title="Shotclock · ADU fast-path checker", page_icon="⏱️", layout="wide",
                   initial_sidebar_state="collapsed")
html_block(CSS)

# Header: logo · about & sources, then labeled settings
LOGO_SVG = (
    '<svg width="46" height="46" viewBox="0 0 46 46" aria-hidden="true">'
    '<rect width="46" height="46" rx="12" fill="#E8643A"/>'
    '<rect x="19" y="7" width="8" height="4" rx="1.5" fill="#fff"/>'
    '<circle cx="23" cy="25" r="12" fill="none" stroke="#fff" stroke-width="3.2"/>'
    '<path d="M23 25 L23 17.5" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/>'
    '<path d="M23 25 L28.5 28.5" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/>'
    '<circle cx="23" cy="25" r="2" fill="#fff"/></svg>')
hc = st.columns([5, 1.6], vertical_alignment="center")
hc[0].markdown(f'<div class="sc-logo">{LOGO_SVG}<div><div class="sc-word">Shot<span>clock</span></div>'
               '<div class="sc-tag">ADU permit checker · California</div></div></div>', unsafe_allow_html=True)
with hc[1].popover("About & sources", icon=":material/info:", width="stretch"):
    st.markdown("**What is Shotclock?** It checks ADU permit applications and city correction letters against "
                "California law, so the 60-day fast path becomes the normal path. Built at the Claude Impact Lab "
                "(UCI × Habitat OC), Lane 02 *Clear it*.")
    st.markdown("**Loaded sources.** Every flag quotes one of these.")
    for kind in ("state", "city"):
        for name, text in load_sources(kind):
            st.caption(f"`{kind}/{name}` · {len(text) // 1000}k chars")
    st.caption(f"Model `{MODEL}` · API key {'✅' if get_client() else '❌ missing'} · Python {sys.version.split()[0]}")
    st.caption(DISCLAIMER)

sc = st.columns([1, 3])
city = sc[0].selectbox("City", CITIES, help="The city whose rules apply. San Clemente has full city sources loaded.")
WHO = f"Applicant: {APPLICANT}\n"

tab1, tab2, tab3 = st.tabs(["Application Pre-Check", "City Letter Review", "Accuracy Test"])

# ----- Tab 1: pre-check -----
with tab1:
    left, right = st.columns([5, 7], gap="large")
    with left:
        label("Your ADU project")
        if st.button("Use sample project", key="s1", icon=":material/description:"):
            st.session_state["project"] = (DEMO / "sample-project.md").read_text()
        project = st.text_area("Project", key="project", height=230, label_visibility="collapsed",
                               placeholder="Lot, existing home, ADU type and size, height, setbacks, parking, "
                                           "distance to transit, documents ready…")
        up = st.file_uploader("Or upload the application", type=["pdf", "txt", "md"], key="up1")
        run1 = st.button("Run pre-check", type="primary", key="run1", width="stretch")
    with right:
        if run1:
            text = (project + "\n\n" + read_upload(up)).strip()
            if not text:
                st.warning("Describe the project or upload a file first.")
            else:
                st.session_state.pop("fix", None)
                st.session_state["pre_text"] = text
                st.session_state.pop("corrected", None)  # keyed text area would keep the old run's text
                with st.spinner("Checking against state law and city rules… (about a minute)"):
                    st.session_state["pre"] = ask_claude(
                        f"City: {city}\n{WHO}\nPre-check this ADU project BEFORE submission. List each relevant "
                        f"requirement as pass / missing (document or info not provided) / problem (conflicts "
                        f"with a rule). Give a concrete fix for each non-pass item.\n\n<project>\n{text}\n</project>",
                        PrecheckResult)
        res = st.session_state.get("pre")
        if not res:
            empty_state("Results appear here", "Each flag says what's wrong, how to fix it, and quotes the law.")
        else:
            c = {s: sum(i.status == s for i in res.items) for s in ("problem", "missing", "pass")}
            label("Result")
            score_chips([("r", c["problem"], "problems"), ("a", c["missing"], "missing"), ("g", c["pass"], "pass")])
            with st.expander("Summary", icon=":material/notes:"):
                st.write(res.summary)
            render_rows(res.items, "item", "fix")
            st.download_button("Download fix list", report_md("Shotclock pre-check", res.summary, res.items, "item"),
                               file_name="shotclock-precheck.md", icon=":material/download:")

            # ----- Fix it for me: draft the corrected application -----
            html_block('<div class="sc-headline" style="margin-top:1.4rem">Fix it for me</div>')
            st.caption("Claude drafts the corrected application: every change before → after, with the law behind "
                       "it. Anything only a person can do (drawings, reports, signatures) is listed separately.")
            if st.button("Draft the corrected application", type="primary", key="fix1", icon=":material/auto_fix_high:"):
                flagged = "\n".join(f"- [{i.status}] {i.item}: {i.reason} Fix: {i.fix} ({i.citation})"
                                    for i in res.items if i.status != "pass")
                st.session_state.pop("corrected", None)
                with st.spinner("Drafting the corrected application… (about a minute)"):
                    st.session_state["fix"] = ask_claude(
                        f"City: {city}\n{WHO}\nDraft the corrected version of this ADU application so it can be "
                        f"submitted without a correction round. Use the pre-check findings below. For each problem "
                        f"or missing item give 'before' (exact wording from the application, or '(not in "
                        f"application)') and 'after' (the exact replacement wording or text to add, with the "
                        f"specific numbers the law sets). Never invent facts about the property: use a bracketed "
                        f"placeholder like [CONFIRM: walking distance to the transit stop]. Put drawings, reports, "
                        f"signatures and fees in human_todo. Then write corrected_text (the full revised "
                        f"application) and a short cover_note to the city listing what changed.\n\n"
                        f"<application>\n{st.session_state.get('pre_text', '')}\n</application>\n\n"
                        f"<precheck_findings>\n{flagged}\n</precheck_findings>",
                        CorrectedApplication, effort="medium", max_tokens=20000)
            fix = st.session_state.get("fix")
            if fix:
                score_chips([("r", len(fix.corrections), "changes"), ("a", len(fix.human_todo), "for a person")])
                for c in fix.corrections:
                    html_block(f'<div class="sc-change"><div class="t">{h(c.item)}</div><div class="sc-ba">'
                               f'<div class="sc-before">{h(c.before)}</div><div class="sc-arrow">→</div>'
                               f'<div class="sc-after">{h(c.after)}</div></div>'
                               f'<div class="sc-why">{h(c.why)} <span class="sc-cite">{h(c.citation)}</span></div>'
                               f'</div>')
                if fix.human_todo:
                    label("Still needs a person")
                    html_block("<ul class='sc-todo'>" + "".join(f"<li>☐ {h(t)}</li>" for t in fix.human_todo)
                               + "</ul>")
                label("Corrected application (edit before submitting)")
                corrected = st.text_area("Corrected", fix.corrected_text, height=320, key="corrected",
                                         label_visibility="collapsed")
                with st.expander("Cover note to the city", icon=":material/mail:"):
                    st.write(fix.cover_note)
                package = "\n".join(
                    ["# Corrected ADU application (draft by Shotclock)", "", corrected, "", "## Changes made", ""]
                    + [f"- **{c.item}**: {c.before} → {c.after} ({c.citation})" for c in fix.corrections]
                    + ["", "## Still needs a person", ""] + [f"- [ ] {t}" for t in fix.human_todo]
                    + ["", "## Cover note to the city", "", fix.cover_note, "", "---", DISCLAIMER])
                st.download_button("Download corrected application", package, file_name="shotclock-corrected.md",
                                   type="primary", icon=":material/download:")

# ----- Tab 2: city letter -----
with tab2:
    left, right = st.columns([5, 7], gap="large")
    with left:
        label("The city's comment letter")
        if st.button("Use sample letter", key="s2", icon=":material/mail:"):
            st.session_state["letter"] = (DEMO / "sample-comment-letter.md").read_text()
        letter = st.text_area("Letter", key="letter", height=230, label_visibility="collapsed",
                              placeholder="Paste the corrections letter the city sent you…")
        d1, d2 = st.columns([3, 2], vertical_alignment="bottom")
        complete = d1.date_input("Application complete on", value=date(2026, 8, 1))
        use_clock = d2.toggle("Shot clock", value=True)
        run2 = st.button("Check the letter", type="primary", key="run2", width="stretch")
    clock = shot_clock(complete) if use_clock else None
    with right:
        if clock:
            clock_card(clock)
        if run2:
            if not letter.strip():
                st.warning("Paste a letter first.")
            else:
                clock_fact = f"\nShot clock (computed, not by you): {clock.summary()}\n" if clock else ""
                st.session_state.pop("reply", None)  # keyed text area would keep the old run's text
                with st.spinner("Checking each request against state law… (about a minute)"):
                    st.session_state["let"] = ask_claude(
                        f"City: {city}\n{WHO}{clock_fact}\nSplit this city comment letter into its individual requests. "
                        f"For each, decide: matches_law (the city may ask this), likely_conflicts (state ADU law "
                        f"appears to prohibit it), or unclear (not covered by loaded sources). Then draft a short, "
                        f"polite reply from the applicant: agree to the lawful items, ask the city to withdraw the "
                        f"conflicting ones citing the statute, and if the 60-day decision deadline has passed, note "
                        f"that, quote § 66317(a)(3) that the application appears to be deemed approved, and ask the city to confirm the approval in writing. "
                        f"Sign it [Applicant name].\n\n<letter>\n{letter}\n</letter>",
                        LetterResult)
        res2 = st.session_state.get("let")
        if not res2:
            if not clock:
                empty_state("Results appear here", "Each request is checked against state law, with a draft reply.")
        else:
            c = {s: sum(i.status == s for i in res2.items) for s in ("likely_conflicts", "unclear", "matches_law")}
            html_block(f'<div class="sc-headline">{c["likely_conflicts"]} of {len(res2.items)} requests likely '
                       f'conflict with state law</div>')
            score_chips([("r", c["likely_conflicts"], "conflict"), ("a", c["unclear"], "unclear"),
                         ("g", c["matches_law"], "lawful")])
            with st.expander("Summary", icon=":material/notes:"):
                st.write(res2.summary)
            render_rows(res2.items, "request")
            label("Draft reply to the city")
            reply = st.text_area("Reply", res2.draft_reply, height=300, key="reply", label_visibility="collapsed")
            b1, b2 = st.columns(2)
            b1.download_button("Download reply", report_md("Shotclock letter check", res2.summary, res2.items,
                               "request", "## Draft reply\n\n" + reply), file_name="shotclock-reply.md",
                               icon=":material/download:", width="stretch")
            with b2.popover("Copy reply", icon=":material/content_copy:", width="stretch"):
                st.code(reply, language=None, wrap_lines=True)

# ----- Tab 3: backtest -----
with tab3:
    if "bt" not in st.session_state and BACKTEST_SAVED.exists():
        st.session_state["bt"] = json.loads(BACKTEST_SAVED.read_text())
    html_block('<div class="sc-headline">Would Shotclock have caught what the state caught?</div>')
    st.caption("HCD found 10 conflicts in San Clemente's ADU ordinance. Shotclock reviews the ordinance with "
               "HCD's letter hidden, then a strict second pass compares its list with HCD's 10 findings.")
    bt = st.session_state.get("bt")
    if bt:
        matches = sorted(bt["grade"]["matches"], key=lambda m: m["finding_number"])
        n = sum(m["caught"] for m in matches)
        c1, c2 = st.columns([1, 3], vertical_alignment="center")
        c1.markdown(f'<div class="sc-bignum"><span>{n}</span>/{len(matches)}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="sc-dots">' + "".join(
            f'<div class="sc-dot {"y" if m["caught"] else "n"}" title="{h(m["finding"])}">{m["finding_number"]}</div>'
            for m in matches) + "</div>", unsafe_allow_html=True)
        st.caption(f"Input: {bt['input']}. The model may have seen public reports in training, so treat this as a "
                   "sanity check, not proof.")
        for m in matches:
            with st.expander(f"{'✅' if m['caught'] else '⬜'}  HCD #{m['finding_number']} · {m['finding']}"):
                st.write(f"**Shotclock:** {m['matched_issue']}" if m["caught"] else "Not caught in this run.")
        if bt["grade"]["extra_issues"]:
            with st.expander(f"➕  {len(bt['grade']['extra_issues'])} more issues Shotclock flagged (not in HCD's letter)"):
                for e in bt["grade"]["extra_issues"]:
                    st.markdown(f"- {e}")
    else:
        empty_state("No backtest yet", "Run it below. It takes about two minutes.")

    with st.expander("Run it live", icon=":material/science:"):
        if ORDINANCE_FILE.exists():
            default_input, input_label = ORDINANCE_FILE.read_text(), f"`{ORDINANCE_FILE.name}` (full ordinance)"
        elif PACKET_FILE.exists():
            # Strip the packet's note that names HCD's findings, so the test stays blind.
            default_input = "\n".join(l for l in PACKET_FILE.read_text().splitlines()
                                      if "hcd" not in l.lower() and "conflict with state law" not in l)
            input_label = f"`{PACKET_FILE.name}` (city's rule summary; full ordinance text not loaded yet)"
        else:
            default_input, input_label = "", "nothing loaded: paste the ordinance"
        st.caption(f"Input: {input_label}. Hidden from the checker: " + ", ".join(f"`{x}`" for x in BACKTEST_HIDE))
        ordinance = st.text_area("City ADU rules to review", default_input, height=180, key="ordinance")
        if st.button("Run backtest (~2 min)", key="run_bt", icon=":material/play_arrow:") and ordinance.strip():
            with st.spinner("Step 1/2: reviewing the city's rules against state law (HCD letter hidden)…"):
                review = ask_claude(
                    "Review this city ADU ordinance against state ADU law. List every provision that likely "
                    "conflicts with state law, one issue per provision.\n\n<ordinance>\n" + ordinance +
                    "\n</ordinance>", BacktestResult, exclude=BACKTEST_HIDE)
            grade = None
            if review:
                with st.spinner("Step 2/2: comparing with HCD's 10 findings…"):
                    grade = ask_claude(
                        "HCD's findings:\n<hcd>\n" + HCD_SC_SUMMARY.read_text() + "\n</hcd>\n\nChecker issues:\n"
                        "<checker>\n" + "\n".join(f"- {i.rule}: {i.conflict}" for i in review.issues) +
                        "\n</checker>\n\nFor each of HCD's numbered findings, say whether the checker caught it.",
                        BacktestGrade, system_override=GRADER_RULES)
            if review and grade:
                st.session_state["bt"] = {"review": review.model_dump(), "grade": grade.model_dump(),
                                          "input": input_label}
                BACKTEST_SAVED.parent.mkdir(exist_ok=True)
                BACKTEST_SAVED.write_text(json.dumps(st.session_state["bt"], indent=2))
                st.rerun()

html_block(f'<div class="sc-foot">Shotclock · Claude Impact Lab: UCI × Habitat OC · {h(DISCLAIMER)}</div>')
