# ⏱️ Shotclock: ADU fast-path checker

**Live app:** https://shotclock.streamlit.app

> *The fast path exists on paper. We make it the normal path: we catch your mistakes before you submit,
> and the city's mistakes after.*

Built at the **Claude Impact Lab** (UC Irvine × Habitat for Humanity OC), Lane 02 *"Clear it": how do we turn
four years into two?*

---

## The problem

An **ADU** (accessory dwelling unit) is a small extra home on a lot: a backyard cottage or a garage conversion.
California law gives ADUs a **fast path**. If an ADU meets the written rules, the city must approve it
**ministerially** (no hearings) and must decide within **60 days** of a complete application. If it hasn't, the law
says *"the application shall be deemed approved"* (Gov. Code § 66317(a)(3)).

In practice it's slow:

- Each of Orange County's **34 cities** has its own forms and checklists.
- Applications bounce back for corrections, and every round costs weeks.
- Cities often ask for things state law doesn't allow. In October 2025 the state housing department (HCD) found
  **10 conflicts with state law** in San Clemente's ADU ordinance alone.

The organizers estimate land-to-keys at about 4 years.

## What Shotclock does

| Tab | For | What it does |
| --- | --- | --- |
| **Application Pre-Check** | Before you submit | Describe or upload an ADU project. Each requirement is marked ✅ pass / ⚠️ missing / ❌ problem, with a fix and a quote from the law. **"Fix it for me"** drafts the corrected application (before → after for every change) and lists what only a person can do. |
| **City Letter Review** | After the city replies | Paste the city's correction letter. Each request is marked 🟢 matches law / 🔴 likely conflicts / 🟡 unclear, with the statute, plus a polite **draft reply**. The **shot clock** counts the city's 60-day deadline (plain Python date math, not AI). |
| **Accuracy Test** | Proof it works on real data | Shotclock reviews San Clemente's real ordinance with HCD's findings **hidden**, then a strict second pass compares its list with HCD's 10 findings. |

A **Source watcher** page (linked under *About & sources*) re-downloads the official sources and flags any that
changed, moved or disappeared. A person approves each update.

**Our twist:** most tools only check the applicant. Shotclock also checks the **city**.

### Who it's for
1. **Habitat for Humanity and other nonprofits.** Under AB 587 (Gov. Code § 66341), a qualified nonprofit can build
   an ADU and sell it **separately** to a low-income buyer. Backyard ADUs can become for-sale family homes.
2. Homeowners adding an ADU, small builders, and city permit technicians.

## Results so far

- **Accuracy Test:** with HCD's San Clemente letter withheld, Shotclock found **7 of HCD's 10 findings** in
  Ordinance No. 1742, plus 9 other likely issues. The model may have seen public reports in training, so treat this
  as a sanity check, not proof.
- **Sample city letter** (fictional): it flags owner occupancy (§ 66315), parking near a car share (§ 66322(a)(5)),
  a 16 ft height cap near transit (§ 66321(b)(4)(B)), discretionary design review (§§ 66316, 66317(a)(1)) and a
  no-rental deed restriction (§§ 66314(d)(1), 66315). Lawful requests (site plan, utility plan, plan-check fees) are
  marked as such.

## Responsible AI

- **Every finding cites a loaded source** (file, section and a short exact quote). Claude may use only the files
  in `docs/`. If they don't cover something, it says *"not covered by loaded sources"*. It never invents statute
  numbers.
- Results use cautious words ("likely", "appears to").
- Shot-clock dates are computed in plain Python (`deadlines.py`) and shown as an **estimate**. Tolling and
  completeness rules vary.
- Pasted letters and uploads are treated as **data, never instructions**.
- Demo files in `demo/` are clearly labeled **SAMPLE / FICTIONAL**.
- Usage limits protect the shared API credit on the public URL (calls per session, input size, upload size).

> **Not legal advice.** Shotclock is an automated reading of the loaded sources. Confirm with the city or an
> attorney before acting.

## Sources (all official, in `docs/`)

| File | Source |
| --- | --- |
| `state/gov-code-66310-66342.md` | California Gov. Code §§ 66310–66342 (ADU law, as amended through Jan 1, 2026): [leginfo.legislature.ca.gov](https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?tocCode=GOV&division=1.&title=7.&part=&chapter=13.&article=) |
| `state/hcd-adu-handbook.md` | HCD ADU Handbook: [hcd.ca.gov](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/adu-handbook-update.pdf) |
| `state/hcd-findings-dana-point-2025-08.md` | HCD Notice of Violation, Dana Point (Aug 13, 2025): [hcd.ca.gov](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/dana-point-adu-nov-081325.pdf) |
| `state/hcd-findings-san-clemente-2025-10*.md` | HCD findings, San Clemente (Oct 14, 2025): [hcd.ca.gov](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/san-clemente-adu-findings-101425.pdf) |
| `city/san-clemente-muni-code-17-28-270-2026.md` | San Clemente Muni. Code § 17.28.270, **current** (Ord. 1810, June 2026): [Municode](https://library.municode.com/ca/san_clemente/codes/code_of_ordinances?nodeId=TIT17ZO_CH17.28SPUS_17.28.270ACDWUN) |
| `city/san-clemente-adu-checklist-2023-03.md` | San Clemente ADU Submittal Checklist (Mar 2023): [sanclemente.gov](https://www.sanclemente.gov/DocumentCenter/View/694/ADU-Application-Packet-PDF) |
| `city/san-clemente-adu-info-packet-2024-08.md` | San Clemente ADU Information Packet (Aug 2024 summary; current June 2026 packet: [sanclemente.gov](https://www.sanclemente.gov/DocumentCenter/View/1295)) |
| `historical/san-clemente-muni-code-17-28-270.md` | § 17.28.270 as HCD reviewed it (Ord. 1742). Used only as the Accuracy Test input. |
| `oc-cities.json` | The organizers' 34-city list. San Clemente is filled in; the rest use the same format. |

**Scaling up:** adding a city means adding its checklist and ordinance to `docs/city/`. The same engine then
handles the next 100 projects.

## Run it yourself

Requires Python 3.10+ and an [Anthropic API key](https://platform.claude.com/settings/keys).

```bash
git clone https://github.com/KrishnaPatel1985/shotclock.git && cd shotclock
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your key into it
.venv/bin/streamlit run app.py                               # opens http://localhost:8501
```

`.streamlit/secrets.toml` is gitignored. Never commit a key. On Streamlit Community Cloud, put
`ANTHROPIC_API_KEY` (and optionally `CLAUDE_MODEL`, default `claude-sonnet-5-5`) under **App settings → Secrets**.

Shot-clock self-test: `python3 deadlines.py`

## How it works

- **One Streamlit app** (`app.py`), no login, no database, no vector DB. The sources are short enough to send in
  full as a **cached** system block (prompt caching), which keeps repeat checks fast and cheap.
- **Claude** through the `anthropic` SDK with **structured outputs** (`client.messages.parse` with Pydantic models),
  so every result has a status, reason, fix, source, citation and quote.
- If a reply is cut off, the app retries once automatically.
- `deadlines.py`: the 60-day shot clock (plain date math).
- `watcher/`, `pages/2_Source_watcher.py`: the Source watcher.

## Team

Krishna Patel and Lakshi VS, Claude Impact Lab at UC Irvine, November 2026.

## License

[MIT](LICENSE)
