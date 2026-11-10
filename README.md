# Shotclock

> For Habitat-style nonprofit project managers building ADUs (backyard homes) in Orange County: Shotclock checks
> an ADU application before it goes to the city, and checks the city's correction letter against state law after,
> so the legal 60-day fast path becomes the normal path.

**Team:** Shotclock
**Members:** Krishna Patel, Lakshi VS
**Lane:** 2 Clear it
**Built at:** Claude Impact Lab: UCI × SoCal Affordable Housing, November 7, 2026

## The real user

A Habitat for Humanity–style nonprofit project manager building ADUs to sell at cost to low-income families
(possible under AB 587, Gov. Code § 66341). State law says a city must approve or deny a complete ADU application
within 60 days, ministerially, but each of Orange County's 34 cities has its own forms, and applications bounce back
for corrections, sometimes for things state law doesn't allow. Each correction round costs weeks.

**Before:** the project manager reads the city checklist, submits, waits, gets a correction letter, and has to work
out alone (or pay someone) which requests are lawful. Nobody tracks whether the city's 60-day deadline has passed.

**After:** they paste the project into Shotclock and fix gaps before submitting. When a letter comes back, Shotclock
marks each request as lawful, likely in conflict with state law, or unclear, quotes the law, counts the 60-day
deadline, and drafts a polite reply that cites the statutes.

## What we built

**Live demo:** https://shotclock-adu.vercel.app (web version) · https://shotclock.streamlit.app (Streamlit)
**Demo video:** uploaded on the hub (30 seconds)

| Tab | What it does |
| --- | --- |
| **Application Pre-Check** | Describe or upload a project. Each requirement is marked pass / missing / problem, with a fix and a quote from the law. **"Fix it for me"** drafts the corrected application (before → after) and lists what only a person can do. |
| **City Letter Review** | Paste the city's letter. Each request is marked matches law / likely conflicts / unclear, with the statute, plus a **draft reply**. The **shot clock** counts the 60-day deadline; past it, Gov. Code § 66317(a)(3) says the application "shall be deemed approved". |
| **Accuracy Test** | Reviews San Clemente's real ordinance with HCD's findings hidden, then compares with HCD's 10 findings. |
| **Source watcher** | Re-downloads the official sources and flags any that changed, moved or disappeared. A person approves each update. |

Our twist: most tools only check the applicant. Shotclock also checks the **city**.

## How Claude is used

- **Built with Claude:** Claude Code wrote and reviewed the app with us, gathered and verified the official sources,
  ran code and security reviews, tested the live site end to end in a browser, and made the demo video and slides.
- **Inside the tool:** Claude (`claude-sonnet-5-5`, structured outputs) reads only the loaded official sources in
  `docs/` and returns, for each item, a status, reason, fix, source, section and a short exact quote. The shot-clock
  date math is plain Python (`deadlines.py`), not Claude.
- **What a person checks:** every flag shows its quote and a link to the official document, so a person can verify
  it. Results say "likely"; the draft reply is a draft to edit before sending. Source updates need human approval.

## Try it

```bash
git clone https://github.com/KrishnaPatel1985/shotclock.git && cd shotclock
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your Anthropic API key into it
.venv/bin/streamlit run app.py                               # opens http://localhost:8501
```

Needs Python 3.10+ and an Anthropic API key in `ANTHROPIC_API_KEY` (in `.streamlit/secrets.toml`, which is
gitignored, or Streamlit Cloud Secrets). Optional `CLAUDE_MODEL` (default `claude-sonnet-5-5`). No keys in the repo.
Self-test of the shot clock: `python3 deadlines.py`.

### Web version (Next.js on Vercel)

`web/` is the same tool as a Next.js site: Pre-Check with "Fix it for me", City Letter Review with the shot clock,
the Accuracy Test result, and linked sources. Claude runs in Vercel serverless functions with the same prompts and
sources as `app.py` (`web/scripts/sync-content.mjs` copies `docs/`, `demo/` and `backtest/` in at build time).

Deploy: on vercel.com, **Add New → Project → Import** `KrishnaPatel1985/shotclock`, set **Root Directory** to `web`,
add the environment variable `ANTHROPIC_API_KEY` (optional `CLAUDE_MODEL`), then **Deploy**.

Run locally:

```bash
cd web && npm install
ANTHROPIC_API_KEY=sk-ant-... npm run dev   # opens http://localhost:3000
```

## Sources and assumptions

| Item | Source or assumption | Date checked |
|---|---|---|
| State ADU law (60-day decision, "deemed approved", owner occupancy, parking, height, separate sale) | Cal. Gov. Code §§ 66310–66342, [leginfo](https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?tocCode=GOV&division=1.&title=7.&part=&chapter=13.&article=) → `docs/state/gov-code-66310-66342.md` | 2026-11-07 |
| HCD ADU Handbook | [hcd.ca.gov](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/adu-handbook-update.pdf) → `docs/state/hcd-adu-handbook.md` | 2026-11-07 |
| 10 conflicts in San Clemente's ADU rules | HCD findings letter, Oct 14, 2025, [hcd.ca.gov](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/san-clemente-adu-findings-101425.pdf) | 2026-11-07 |
| Dana Point Notice of Violation | HCD, Aug 13, 2025, [hcd.ca.gov](https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/dana-point-adu-nov-081325.pdf) | 2026-11-07 |
| San Clemente's current ADU ordinance | Muni. Code § 17.28.270 (Ord. 1810, June 2026), [Municode](https://library.municode.com/ca/san_clemente/codes/code_of_ordinances?nodeId=TIT17ZO_CH17.28SPUS_17.28.270ACDWUN) | 2026-11-07 |
| San Clemente ADU checklist and packet | [Checklist](https://www.sanclemente.gov/DocumentCenter/View/694/ADU-Application-Packet-PDF), [packet](https://www.sanclemente.gov/DocumentCenter/View/1295) | 2026-11-07 |
| 34 OC cities | Organizers' `lanes/2-clear-it/data/oc-cities.json` → `docs/oc-cities.json` (San Clemente filled) | 2026-11-07 |
| ~4 years land to keys; $85k of a $535k home lost to waiting | **ASSUMPTION** (organizers' estimate, `timeline.json`), labelled as such in the app | 2026-11-07 |
| Sample project and sample city letter | **FICTIONAL**, written for the demo and labelled "SAMPLE / FICTIONAL" in `demo/` | — |
| Application completion date Aug 1, 2026 in the demo | **ASSUMPTION** (sample date set by "Use sample letter") | — |
| Shot clock dates | Computed in Python from the date you enter; shown as an **estimate** (tolling and completeness rules vary) | — |

## What is real and what is mocked

| Part | Status |
|---|---|
| Pre-check, "Fix it for me", City Letter Review, draft reply (live Claude calls on real sources) | working |
| Shot clock (60-day date math) | working (estimate) |
| Accuracy Test on San Clemente's real ordinance vs HCD's 10 findings: **7/10** | working (saved result; can re-run live) |
| Source watcher | partly working: some official sites (Municode, leginfo) block automated checks, so those show "unreachable" and need a browser check |
| City rules | San Clemente only; other cities get state law only and are told city rules are "not covered" |
| Sample project and city letter | mocked (fictional demo inputs) |

## Where it gets things wrong

- The Accuracy Test missed 3 of HCD's 10 findings, and the model may have seen public reports in training, so 7/10
  is a sanity check, not proof.
- Results can vary between runs (counts of problems or missing items shift a little).
- It knows only the documents loaded in `docs/`; anything else is "not covered by loaded sources". It does not know
  each city's fees, local amendments outside § 17.28.270, coastal-zone details, or tolling disputes.
- We would not trust it to file anything or to replace an attorney or the city: it is a first read with citations.

## Next steps

For a nonprofit or city to use it next month: load the checklist and ordinance for the other OC cities (same format,
no code changes), run the Source watcher weekly with a named reviewer, add a city-staff view for permit techs, and
have a land-use attorney spot-check flags across a few real letters. With one more week: upload the full
application packet (PDF drawings), track each application's clock over time, and add SB 684 / SB 4 / AB 2011.

## Data and privacy

This project uses only public or provided data. It contains no personal information about real tenants, buyers or
residents. It does not file applications or contact any city or person. The demo project and letter are fictional.
Usage limits protect the shared API credit on the public site.

> **Not legal advice.** Shotclock is an automated reading of the loaded sources. Confirm with the city or an
> attorney before acting.

## License

MIT, see the [LICENSE](LICENSE) file.
