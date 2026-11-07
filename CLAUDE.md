# Shotclock: CLAUDE.md

You are helping a small team build **Shotclock**, an ADU fast-path checker, at the Claude Impact Lab hackathon
(UC Irvine, Affordable Housing, Orange County). Repo: github.com/KrishnaPatel1985/shotclock. **Lane 02: "Clear it": How do we turn four years into two?**
**Submissions close at 2:30 PM today.** Rough and working beats polished.

## Status right now (read first)
- ✅ **App built and running locally** (`app.py`, `deadlines.py`): both tabs, the shot clock, the download/copy
  buttons, the colored banners, problems sorted first. Page, sample loading and shot clock tested in the browser.
- ✅ **Real sources loaded:** `docs/state/hcd-adu-handbook.md` (HCD ADU Handbook, March 2026) and
  `docs/state/hcd-findings-dana-point-2025-08.md` (HCD Notice of Violation to Dana Point), both from official PDFs.
- ✅ **Demo files:** `demo/sample-comment-letter.md` and `demo/sample-project.md` (labeled FICTIONAL).
- ❌ **Not tested yet: the two Claude calls.** Needs an API key in `.streamlit/secrets.toml`.
- ❌ **Missing sources:** the San Clemente HCD letter (the "10 conflicts" proof), San Clemente's ADU checklist,
  Gov. Code statute text. See `docs/README.md`.
- ⚠️ **Only one `app.py` goes in the repo.** If a teammate already has one, compare and pick one before pushing.

## The idea (plain words)
An ADU is a small extra home on a lot (a backyard cottage or a garage conversion). California law says that if
an ADU meets the written rules, the city **must** approve it, with no hearings. That's the **fast path**.
In practice it's slow: each of OC's 34 cities has its own forms and checklists, applications bounce back
for fixes (each round costs weeks), and cities often ask for things state law doesn't allow.
**Proof:** in Oct 2025 the state housing department (HCD) found **10 conflicts with state law** in San Clemente's ADU
rules (TODO: add `docs/state/hcd-findings-san-clemente-2025-10.md`; until it's loaded, lead with the
Dana Point Notice of Violation, which is loaded).

**Name:** Shotclock: the clock is running on every housing project, and we help beat it (4 years → 2).

**Two tools, one Streamlit app (`app.py`):**
1. **Pre-check (Tab 1):** describe or upload an ADU project → list of ✅ pass / ⚠️ missing / ❌ problem,
   each with a fix and a cited source. Fix mistakes *before* the city sees them.
2. **"Is the city allowed to ask that?" (Tab 2):** paste a city comment letter → each request labeled
   🟢 matches law / 🔴 likely conflicts / 🟡 unclear, with the statute, plus a polite draft reply.
   Includes **the shot clock**: date the application was complete → the city's 60-day decision date
   (Gov. Code § 66317(a)(3): the city must approve or deny within 60 days; the loaded Handbook states
   "deemed approved" only for the coastal permit, § 66329(b)(5), so don't claim it for regular ADUs until the
   statute text is loaded) → "Z days left" or
   "Z days overdue". The draft reply cites the clock when it has run out. This is what the name promises.

Pitch line: *"The fast path exists on paper. We make it the normal path: we catch your mistakes before you
submit, and the city's mistakes after."*
Who it's for: a **Habitat / nonprofit project manager** first (a Habitat LA development director is judging),
then homeowners adding an ADU, small builders, and city permit techs.
**Habitat angle:** AB 587 lets qualified nonprofits build ADUs and sell them separately to low-income buyers
as ownership homes. So ADUs are a Habitat strategy, not just a homeowner project: *"Habitat can turn backyard
ADUs into for-sale family homes. The law says the city decides in 60 days. Shotclock makes sure it does."*
(Handbook: separate sale to a qualified buyer is Gov. Code § 66341(c)(3); owner-occupancy may only be required
for those ADUs, otherwise it is barred by § 66315.)

## Event data (`lanes/2-clear-it/` in the hackathon repo)
- `timeline.json`: 4-year baseline, labeled ASSUMPTION (say "organizers' estimate"). Hook: waiting costs $85k of a
  $535k home in its worked example.
- `oc-cities.json`: 34 OC cities with empty `permit_page` / `adu_checklist` / `fee_schedule` / `checked`. Copy into
  `docs/`, fill San Clemente (URLs + date checked). Feeds the scorecard and the Scale story.
- `scenarios.json`: C03, the permit tech who wants the right answer "even when our form is out of date", is our
  second demo user (city side).

## Judging (design every choice for these)
1. **Impact:** a nonprofit or city would use it next month
2. **Works:** live demo on REAL data, **sources shown**. Rough and working beats polished
3. **Scale:** believable path to the next 100 projects (add a city = drop its PDFs into `docs/city/`)
4. **Innovation:** a new way to see or solve the problem (checking the *city's* requests is our twist)

## Hard rules
- **Every finding cites a loaded source** (name + section + short quote). Claude must only use files in `docs/`.
  If not covered, say "not covered by loaded sources". Never invent statute numbers.
- Use cautious words: "likely", "appears to". Show the disclaimer: not legal advice, confirm with the city or an attorney.
- Current state ADU law is **Gov. Code §§ 66310–66342**. The old § 65852.2 was deleted by SB 477. Don't cite it as current.
- **Unverified, do not assert on stage** until checked against loaded statute text: AB 130 / SB 131 "shot clock"
  wording, the exact SB 543 deadline, the current section number for pre-approved ADU plans (was § 65852.27).
- The shot-clock date math is plain Python (`deadlines.py`), not Claude. Show it as "estimated"; tolling and
  completeness rules vary.
- Demo files in `demo/` are clearly labeled **SAMPLE / FICTIONAL**. Never present them as a real city's letter.
- No API keys in code or git. Key goes in `.streamlit/secrets.toml` (gitignored) or Streamlit Cloud Secrets.
- Keep it one simple app. No login, no database, no vector DB (documents are short; put them in context).

## Tech (already set up)
- `app.py`: Streamlit app, two tabs (Claude calls untested until a key is added)
- `deadlines.py`: 60-day shot clock, plain date math; `python deadlines.py` runs its self-test
- Claude via `anthropic` SDK with **structured outputs** (`client.messages.parse` + Pydantic models
  `PrecheckResult`, `LetterResult`). Do NOT use forced `tool_choice` (`any`/`tool`): it returns a 400 on
  Sonnet 5.5 / Opus 5.5. Sources are sent as a cached system block (prompt caching) for speed.
- Model from secret `CLAUDE_MODEL` (default `claude-sonnet-5-5`)
- `load_sources("state")` / `load_sources("city")` read every .md/.txt/.pdf in `docs/state/` and `docs/city/`
- Run:
  ```bash
  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
  cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste the key into it
  .venv/bin/streamlit run app.py                               # opens http://localhost:8501
  ```
- If the team is using the event's `habitat-streamlit` starter instead, port `app.py`'s logic into it; keep these rules.

## Files and owners
| Path | What | Owner agent |
| --- | --- | --- |
| `docs/state/*` | State law sources (Handbook + Dana Point done; add San Clemente findings + Gov Code text) | docs-agent |
| `docs/city/*` | Demo city's checklist/handout/code text | docs-agent |
| `demo/*` | Sample project + sample comment letter (fictional, labeled) | docs-agent |
| `app.py`, `deadlines.py`, `requirements.txt`, `.streamlit/config.toml` | The app + shot-clock math | builder |
| `docs/oc-cities.json` | Event's 34-city file; fill San Clemente (URLs + date checked); feeds the scorecard | docs-agent |
| `README.md`, `LICENSE` | Submission docs | builder (last) |

## Agents (multi-agent setup)
Optional: define these in `.claude/agents/` (not created yet). If babysitting agents slows you down, skip them
and work in one session. The main session is the **coordinator**: it plans, hands out work, and merges results.
**Two agents never edit the same file at the same time.**
- **docs-agent:** downloads/converts official sources into `docs/`, with the source URL at the top of each file. Only edits `docs/` and `demo/`.
- **builder:** improves `app.py` and ships. Never edits `docs/`.
- **tester:** runs the app's checks and the demo script; reports PASS/FAIL. Never edits files.

Example prompt: "Use docs-agent to do the TODOs in docs/README.md AND, in parallel, use builder for Phase 2. Then use tester."

## Build phases (do in order; tick when done)
- [ ] **Phase 1, now (15 min). Push + first real run.**
  - Commit and push this folder to the repo (check `git status` shows no `secrets.toml`).
  - Each teammate: clone, run the commands under Tech, add the key.
  - Tab 2 → "Load sample city letter" → "Check the letter". Expect 🔴 on items 2, 3, 4, 6, 🟡/🔴 on 5, and
    🟢 on 1, 7, 8. Tab 1 → "Load sample project" → "Run pre-check". Expect ⚠️ missing site plan / utility plan.
  - If results are off, tune the prompts in `ask_claude(...)` calls in `app.py`. Note how long each check takes.
- [ ] **Phase 2, until 12:00. Sources (docs-agent) + check quality (builder).**
  - docs-agent: San Clemente HCD letter (Oct 2025) → `docs/state/`; San Clemente ADU checklist + Municipal Code
    § 17.28.270 → `docs/city/`; Gov. Code §§ 66310–66342 text (copy from leginfo in a browser; it blocks curl).
    Source URL at the top of every file.
  - builder: spot-check every citation the app shows against the Handbook text. Tighten prompts if any quote isn't
    really in the source. If checks are slow, try `CLAUDE_MODEL` variants and keep the fastest that's accurate.
  - ✅ Done already: colored banner, problems sorted first, "Download report", `deadlines.py` + Tab 2 date input,
    overdue fed into the draft reply.
- [ ] **12:00-12:30 lunch** (keep docs-agent running).
- [ ] **Phase 3, 12:30-1:30. The backtest (+ scorecard if time).**
  - ✅ Done already: "X of Y requests likely conflict", editable draft reply with copy + download.
  - **High value: "Backtest" expander.** `ask_claude(..., exclude=("hcd-findings-san-clemente-2025-10.md",))`
    already supports hiding a source. Paste San Clemente's ordinance § 17.28.270 (docs-agent fetches it);
    the app checks it and shows how many of HCD's 10 real findings it caught: "Our checker found N of the 10 issues the
    state found." That's the "works on real data" proof. Hide HCD's findings file from Claude for this one run
    (pass sources without it) so it's a fair test. Caveat for the pitch: the model may have seen HCD's letter in
    training, so say "we withheld the findings file" and don't overclaim.
  - **Stretch, only after the backtest: City scorecard** (expander or Tab 3). One row per city from real HCD letters:
    ordinance void / state law governs? pre-approved plans? number of HCD findings, each linked to the letter.
    San Clemente + one more:
    Dana Point ADU NOV, Aug 2025 (already loaded): https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/dana-point-adu-nov-081325.pdf
    Irvine ADU TA, Mar 2025: https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/irvine-adu-ta-032725.pdf
    This is the visible "Scale" proof: adding a city = adding its letter + checklist.
- [ ] **Phase 4, 1:30-1:50. Ship.** tester runs the demo script. Fix blockers only. README (what, why, run, sources,
  disclaimer, MIT). Push to a **public** GitHub repo. Deploy on Streamlit Community Cloud (add the key in Secrets). Test the live URL.
- [ ] **1:50: STOP CODING.** Make the 30-second video, then submit at claudesocal.com/uci-impact-lab by 2:20.

## Demo script (tester uses it; it's also the pitch)
1. Problem: "In OC, land to keys takes ~4 years. The fast path exists, but 34 cities each do it differently, and
   the state just found 10 conflicts in San Clemente's ADU rules alone." (If the San Clemente letter isn't loaded,
   use: "the state issued Dana Point a Notice of Violation over its ADU rules.")
   User: "A Habitat project manager building for-sale ADUs under AB 587."
2. Tab 2 → Load sample city letter → Check. Show 🔴 owner occupancy (§ 66315), 🔴 parking with car share
   (§ 66322(a)(5)), 🔴 16 ft height near transit (§ 66321(b)(4)), 🔴 "match materials" (§ 66314(b)), 🔴 ADU deed
   restriction (§ 66315), while 🟢 the site plan / fee / utility plan items match. Show the shot clock
   ("city's 60-day decision date has passed") and the draft reply. Section numbers above are what we expect; say
   whatever the app actually cites, and only if the quote checks out.
   ⚠️ Before demo day, a mentor checks "match materials" and "deed restriction" against the statute text: an
   *objective* materials standard may be allowed, and deed-restriction rules differ for ADUs vs JADUs. If unsure,
   relabel those 🟡 in the sample letter rather than claim 🔴.
3. Tab 1 → Load sample project → Run. Show ⚠️ missing site plan / utility plan with fixes, ✅ passes with citations.
4. (If built) Backtest: "Our checker found N of the 10 issues the state found."
5. Scale: "Add a city by dropping in its checklist PDF." (If built) show the scorecard. Same engine for the next
   100 projects and for city permit techs. Next sources to add: SB 684 small-lot homeownership, SB 4, AB 2011.
6. Responsible AI: every flag quotes its source and says "likely". Not legal advice.

## Submission checklist (due 2:30)
- [ ] Public GitHub repo + README + MIT LICENSE, no keys, no private data
- [ ] 30-second video made with Claude (judges use it to pick the top 10)
- [ ] Form: claudesocal.com/uci-impact-lab
- [ ] Ready to demo live at 3:00 (laptop charged, live URL open, backup video)
