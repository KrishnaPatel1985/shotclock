"""Shotclock: ADU fast-path checker (Claude Impact Lab, Lane 02 "Clear it").

Tab 1: pre-check an ADU project before submitting.
Tab 2: check a city comment letter against state law, with the 60-day shot clock and a draft reply.
Every finding must cite a loaded source in docs/. Not legal advice.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Literal

import anthropic
import streamlit as st
from pydantic import BaseModel, Field

from deadlines import shot_clock

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
DEMO = ROOT / "demo"

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
- Deadlines: say only what the sources state. § 66317(a)(3) requires the agency to approve or deny within 60 days.
  Do NOT say an ordinary ADU application is "deemed approved" unless a loaded source states that rule for it (the
  loaded Handbook states "deemed approved" only for coastal development permits, § 66329(b)(5)).
- Be concise and practical: each reason and fix is one or two plain-English sentences."""


@st.cache_resource
def get_client() -> anthropic.Anthropic | None:
    key = secret("ANTHROPIC_API_KEY")
    if not key:
        return None
    return anthropic.Anthropic(api_key=key)


# ---------- structured outputs ----------
class PrecheckItem(BaseModel):
    item: str = Field(description="Short name of the requirement checked")
    status: Literal["pass", "missing", "problem"]
    reason: str
    fix: str = Field(description="What to do; empty if status is pass")
    source: str = Field(description="Loaded source file name")
    citation: str = Field(description="Section, e.g. Gov. Code § 66321(b)")
    quote: str = Field(description="Short exact quote from the source")


class PrecheckResult(BaseModel):
    summary: str
    items: list[PrecheckItem]


class LetterItem(BaseModel):
    request: str = Field(description="The city's request, paraphrased in one line")
    status: Literal["matches_law", "likely_conflicts", "unclear"]
    reason: str
    source: str
    citation: str
    quote: str


class LetterResult(BaseModel):
    summary: str
    items: list[LetterItem]
    draft_reply: str = Field(description="Polite reply letter to the city, citing statutes for conflicts")


def ask_claude(task: str, output_model: type[BaseModel], exclude: tuple[str, ...] = ()):
    client = get_client()
    if client is None:
        st.error("No API key. Add ANTHROPIC_API_KEY to .streamlit/secrets.toml (see secrets.toml.example).")
        return None
    system = [
        {"type": "text", "text": SYSTEM_RULES},
        # Sources are identical across calls -> cache them so repeat checks are fast and cheap.
        {"type": "text", "text": "LOADED SOURCES:\n\n" + sources_block(exclude),
         "cache_control": {"type": "ephemeral"}},
    ]
    try:
        resp = client.messages.parse(
            model=MODEL,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": task}],
            output_format=output_model,
        )
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
    "problem": ("❌", "Problem"), "missing": ("⚠️", "Missing"), "pass": ("✅", "Pass"),
    "likely_conflicts": ("🔴", "Likely conflicts with state law"),
    "unclear": ("🟡", "Unclear"), "matches_law": ("🟢", "Matches law"),
}
ORDER = ["problem", "likely_conflicts", "missing", "unclear", "pass", "matches_law"]


def render_items(items, title_attr: str, extra_attr: str | None = None):
    for it in sorted(items, key=lambda x: ORDER.index(x.status)):
        icon, label = STATUS_STYLE[it.status]
        with st.container(border=True):
            st.markdown(f"**{icon} {getattr(it, title_attr)}**  \n*{label}*")
            st.write(it.reason)
            if extra_attr and getattr(it, extra_attr):
                st.markdown(f"**Fix:** {getattr(it, extra_attr)}")
            st.caption(f"📎 {it.citation} · `{it.source}` — “{it.quote}”")


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
        icon, label = STATUS_STYLE[it.status]
        lines += [f"## {icon} {getattr(it, title_attr)} ({label})", it.reason,
                  f"Source: {it.citation}, {it.source}: \"{it.quote}\"", ""]
    if extra:
        lines += [extra, ""]
    lines += ["---", DISCLAIMER]
    return "\n".join(lines)


# ---------- page ----------
st.set_page_config(page_title="Shotclock: ADU fast-path checker", page_icon="⏱️", layout="wide")
st.title("⏱️ Shotclock")
st.markdown("**The fast path exists on paper. We make it the normal path:** we catch your mistakes before you "
            "submit, and the city's mistakes after. *Lane 02: turn 4 years into 2.*")

with st.sidebar:
    st.header("Setup")
    city = st.text_input("City", "San Clemente")
    st.caption(f"Model: `{MODEL}`")
    st.caption("API key: " + ("✅ loaded" if get_client() else "❌ missing"))
    st.subheader("Loaded sources")
    for kind in ("state", "city"):
        srcs = load_sources(kind)
        st.markdown(f"**{kind}/** ({len(srcs)})")
        for name, text in srcs:
            st.caption(f"• {name} ({len(text)//1000}k chars)")
        if not srcs:
            st.caption("• none yet")
    st.info(DISCLAIMER)

tab1, tab2 = st.tabs(["① Pre-check my project", "② Is the city allowed to ask that?"])

# ----- Tab 1 -----
with tab1:
    st.subheader("Check your ADU project before the city sees it")
    st.caption("Each round of city corrections costs weeks. Fix problems before you submit.")
    if st.button("Load sample project (fictional)", key="s1"):
        st.session_state["project"] = (DEMO / "sample-project.md").read_text()
    project = st.text_area("Describe the ADU project", key="project", height=260,
                           placeholder="Lot size, existing house, ADU type and size, height, setbacks, "
                                       "parking, distance to transit, documents you have ready...")
    up = st.file_uploader("…or upload the application (PDF or text)", type=["pdf", "txt", "md"], key="up1")
    if st.button("Run pre-check", type="primary", key="run1"):
        text = (project + "\n\n" + read_upload(up)).strip()
        if not text:
            st.warning("Describe the project or upload a file first.")
        else:
            with st.spinner("Checking against state ADU law and city sources…"):
                st.session_state["pre"] = ask_claude(
                    f"City: {city}\n\nPre-check this ADU project BEFORE submission. List each relevant "
                    f"requirement as pass / missing (document or info not provided) / problem (conflicts "
                    f"with a rule). Give a concrete fix for each non-pass item.\n\n<project>\n{text}\n</project>",
                    PrecheckResult)
    res = st.session_state.get("pre")
    if res:
        n_bad = sum(i.status != "pass" for i in res.items)
        (st.error if any(i.status == "problem" for i in res.items) else
         st.warning if n_bad else st.success)(f"{n_bad} of {len(res.items)} items need attention. {res.summary}")
        render_items(res.items, "item", "fix")
        st.download_button("Download report (.md)", report_md("Shotclock pre-check", res.summary, res.items, "item"),
                           file_name="shotclock-precheck.md")

# ----- Tab 2 -----
with tab2:
    st.subheader("Paste the city's comment letter")
    st.caption("Cities sometimes ask for things state law doesn't allow. Each extra round costs weeks.")
    if st.button("Load sample city letter (fictional)", key="s2"):
        st.session_state["letter"] = (DEMO / "sample-comment-letter.md").read_text()
    letter = st.text_area("City comment letter", key="letter", height=260)
    c1, c2 = st.columns([1, 2])
    with c1:
        use_clock = st.checkbox("Start the shot clock", value=True)
        complete = st.date_input("Date the application was complete", value=date(2026, 8, 1),
                                 disabled=not use_clock)
    clock = shot_clock(complete) if use_clock else None
    with c2:
        if clock:
            (st.error if clock.overdue else st.info)("⏱️ " + clock.summary() + "  \n*Estimate: completeness "
                                                     "and tolling rules vary.*")
    if st.button("Check the letter", type="primary", key="run2"):
        if not letter.strip():
            st.warning("Paste a letter first.")
        else:
            clock_fact = f"\nShot clock (computed, not by you): {clock.summary()}\n" if clock else ""
            with st.spinner("Checking each request against state law…"):
                st.session_state["let"] = ask_claude(
                    f"City: {city}\n{clock_fact}\nSplit this city comment letter into its individual requests. "
                    f"For each, decide: matches_law (the city may ask this), likely_conflicts (state ADU law "
                    f"appears to prohibit it), or unclear (not covered by loaded sources). Then draft a short, "
                    f"polite reply from the applicant: agree to the lawful items, ask the city to withdraw the "
                    f"conflicting ones citing the statute, and if the 60-day decision deadline has passed, note "
                    f"that and ask the city to approve or deny promptly (do not claim it is deemed approved). "
                    f"Sign it [Applicant name].\n\n<letter>\n{letter}\n</letter>",
                    LetterResult)
    res2 = st.session_state.get("let")
    if res2:
        n_conf = sum(i.status == "likely_conflicts" for i in res2.items)
        (st.error if n_conf else st.success)(
            f"**{n_conf} of {len(res2.items)} requests likely conflict with state law.** {res2.summary}")
        render_items(res2.items, "request")
        st.subheader("Draft reply to the city")
        reply = st.text_area("Edit before sending", res2.draft_reply, height=320, key="reply")
        st.code(reply, language=None)  # has a built-in copy button
        st.download_button("Download reply (.md)",
                           report_md("Shotclock letter check", res2.summary, res2.items, "request",
                                     "## Draft reply\n\n" + reply), file_name="shotclock-reply.md")

st.divider()
st.caption("Shotclock · Claude Impact Lab: UCI × Habitat OC · " + DISCLAIMER)
