import Checker from "./Checker";
import Nav from "./Nav";
import { BACKTEST, DEMO, SOURCES } from "@/lib/generated/content";
import { DISCLAIMER, sourceInfo } from "@/lib/shared";

const REPO = "https://github.com/KrishnaPatel1985/shotclock";

function Logo({ size = 34 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 46 46" aria-hidden>
      <rect width="46" height="46" rx="12" fill="#E8643A" />
      <rect x="19" y="7" width="8" height="4" rx="1.5" fill="#fff" />
      <circle cx="23" cy="25" r="12" fill="none" stroke="#fff" strokeWidth="3.2" />
      <path d="M23 25 L23 17.5 M23 25 L28.5 28.5" stroke="#fff" strokeWidth="3.2" strokeLinecap="round" />
    </svg>
  );
}

const FEATURES = [
  {
    t: "Application Pre-Check",
    d: "Every requirement marked pass, missing or problem, with a concrete fix and the exact law quoted. “Fix it for me” drafts the corrected application.",
    i: "M9 12l2 2 4-4M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z",
  },
  {
    t: "City Letter Review",
    d: "Paste the city’s correction letter. Each request is marked lawful, likely in conflict with state law, or unclear, with a polite reply that cites the statutes.",
    i: "M4 4h16v16H4zM4 6l8 7 8-7",
  },
  {
    t: "The shot clock",
    d: "Counts the city’s 60-day deadline in plain date math. Past it, Gov. Code § 66317(a)(3) says the application “shall be deemed approved.”",
    i: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2",
    dark: true,
  },
];

export default function Page() {
  const caught = BACKTEST?.grade?.matches?.filter((m: { caught: boolean }) => m.caught).length ?? 7;
  const total = BACKTEST?.grade?.matches?.length ?? 10;
  const seen = new Set<string>();
  const sources = SOURCES.map((s) => ({ kind: s.kind, ...sourceInfo(s.name) })).filter((s) => {
    if (seen.has(s.name)) return false;
    seen.add(s.name);
    return true;
  });

  return (
    <>
      <Nav logo={<Logo />} repo={REPO} />

      <header className="hero">
        <div className="wrap">
          <span className="eyebrow">ADU permits · California · Orange County</span>
          <h1>The law says <em>60 days</em>. Shotclock makes sure it happens.</h1>
          <p className="lead">
            California gives backyard homes (ADUs) a fast path: a complete application must be approved or denied in
            60 days. Shotclock catches your mistakes before you submit, and the city’s mistakes after, with every flag
            quoting the law.
          </p>
          <div className="ctas">
            <a className="btn primary" href="#try">Try the checker</a>
            <a className="btn" href="#results">See the accuracy test</a>
          </div>
          <div className="stats">
            <div className="stat"><b className="o">60</b><span>days for the city to decide a complete ADU application</span></div>
            <div className="stat"><b>~4 yrs</b><span>land to keys in Orange County today</span><small>ASSUMPTION · organizers’ estimate</small></div>
            <div className="stat"><b>34</b><span>OC cities, each with its own forms and checklists</span></div>
            <div className="stat dark"><b className="o">10</b><span>conflicts with state law the state found in San Clemente’s ADU rules (Oct 2025)</span></div>
          </div>
        </div>
      </header>

      <section className="block" id="how">
        <div className="wrap">
          <div className="sec-head">
            <div className="kicker">How it works</div>
            <h2>Check the applicant and the city.</h2>
            <p>Most tools only check the applicant. Shotclock also checks the city’s requests against state law, and keeps the 60-day clock running.</p>
          </div>
          <div className="features">
            {FEATURES.map((f) => (
              <div key={f.t} className={`feature ${f.dark ? "dark" : ""}`}>
                <div className="ico">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d={f.i} /></svg>
                </div>
                <h3>{f.t}</h3>
                <p>{f.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="block" style={{ paddingTop: 16 }}>
        <div className="wrap">
          <div className="sec-head">
            <div className="kicker">Try it</div>
            <h2>Run a check</h2>
            <p>Use the fictional sample project or letter, or paste your own. Each check takes about 20–60 seconds.</p>
          </div>
          <Checker demo={DEMO} backtest={BACKTEST} />
        </div>
      </section>

      <section className="block" id="results">
        <div className="wrap">
          <div className="cta-band">
            <h2>On real data, with the state’s letter hidden, Shotclock found <em>{caught} of {total}</em> conflicts the state found in San Clemente’s ADU ordinance.</h2>
            <a className="btn primary" href="#try">Open the accuracy test</a>
          </div>
        </div>
      </section>

      <section className="block" id="sources">
        <div className="wrap">
          <div className="sec-head">
            <div className="kicker">Sources</div>
            <h2>Every answer comes from official documents.</h2>
            <p>Shotclock reads only these files. If they don’t cover something, it says “not covered by loaded sources.”</p>
          </div>
          <div className="sources">
            {sources.map((s) => (
              <a key={s.name} className="source" href={s.url ?? REPO} target="_blank" rel="noopener noreferrer">
                <span className={`tag ${s.kind}`}>{s.kind}</span>
                <div><b>{s.name}</b><span>{s.url ? new URL(s.url).hostname.replace(/^www\./, "") : "github.com"}</span></div>
              </a>
            ))}
          </div>
        </div>
      </section>

      <footer>
        <div className="wrap">
          <p>
            <b>Shotclock</b> · Built with Claude at the Claude Impact Lab: UCI × SoCal Affordable Housing, Nov 2026.{" "}
            {DISCLAIMER} Sample project and letter are fictional.
          </p>
          <a href={REPO} target="_blank" rel="noopener noreferrer">GitHub ↗</a>
        </div>
      </footer>
    </>
  );
}
