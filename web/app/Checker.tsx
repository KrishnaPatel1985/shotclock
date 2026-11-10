"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { CorrectedApplicationT, LetterResultT, PrecheckResultT } from "@/lib/schemas";
import { CITIES, City, DISCLAIMER, MAX_INPUT_CHARS, fmtDate, shotClock, sourceInfo } from "@/lib/shared";

type Tab = "pre" | "letter" | "acc";
type Status = "pass" | "missing" | "problem" | "matches_law" | "likely_conflicts" | "unclear";

const LABEL: Record<Status, string> = {
  problem: "Problem",
  missing: "Missing",
  pass: "Passes",
  likely_conflicts: "Likely conflicts",
  unclear: "Unclear",
  matches_law: "Matches law",
};
const ORDER: Status[] = ["problem", "likely_conflicts", "missing", "unclear", "pass", "matches_law"];
const SAMPLE_DATE = "2026-08-01"; // fictional sample date, set by "Use sample letter"

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Backtest = any;

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({ error: `Request failed (${r.status}).` }));
  if (!r.ok || data.error) throw new Error(data.error || `Request failed (${r.status}).`);
  return data as T;
}

function useElapsed(on: boolean) {
  const [s, setS] = useState(0);
  useEffect(() => {
    if (!on) return setS(0);
    const t0 = Date.now();
    const id = setInterval(() => setS(Math.round((Date.now() - t0) / 1000)), 500);
    return () => clearInterval(id);
  }, [on]);
  return s;
}

function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/markdown;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/* ---------- small UI pieces ---------- */
function Icon({ d, size = 22 }: { d: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  );
}
const ICONS = {
  check: "M9 12l2 2 4-4M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z",
  mail: "M4 4h16v16H4zM4 6l8 7 8-7",
  chart: "M4 20V10M10 20V4M16 20v-8M22 20H2",
  chev: "M9 6l6 6-6 6",
  dl: "M12 3v12M7 10l5 5 5-5M5 21h14",
  copy: "M9 9h11v11H9zM5 15H4V4h11v1",
  wand: "M15 4V2M15 10V8M11 6H9M21 6h-2M19.5 8.5l-1-1M5 21l11-11-2-2L3 19z",
  file: "M14 3H6v18h12V7zM14 3v4h4",
  upload: "M12 21V9M7 14l5-5 5 5M5 3h14",
};

function Cite({ citation, source }: { citation: string; source: string }) {
  const s = sourceInfo(source);
  return (
    <span className="cite">
      {citation}
      {s.name ? <> · {s.url ? <a href={s.url} target="_blank" rel="noopener noreferrer">{s.name}</a> : s.name}</> : null}
    </span>
  );
}

function Loading({ label, seconds }: { label: string; seconds: number }) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <div className="spinner" />
      <div>
        <div className="t">{label}</div>
        <div className="s">{seconds}s · usually 20–60 seconds. Every answer is checked against the loaded official sources.</div>
      </div>
    </div>
  );
}

type Row = { title: string; status: Status; reason: string; fix?: string; quote: string; citation: string; source: string };

function Rows({ rows }: { rows: Row[] }) {
  const [open, setOpen] = useState<number | null>(null);
  const sorted = useMemo(() => [...rows].sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status)), [rows]);
  return (
    <div className="items">
      {sorted.map((r, i) => (
        <div key={i} className={`item ${open === i ? "open" : ""}`}>
          <button onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i}>
            <span className={`badge ${r.status}`}>{LABEL[r.status]}</span>
            <span className="title">{r.title}</span>
            <span className="chev"><Icon d={ICONS.chev} size={18} /></span>
          </button>
          {open === i && (
            <div className="body">
              <p>{r.reason}</p>
              {r.fix ? <div className="fixbox"><b>Fix</b> · {r.fix}</div> : null}
              {r.quote ? <div className="quote">“{r.quote}”</div> : null}
              <Cite citation={r.citation} source={r.source} />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function reportMd(title: string, summary: string, rows: Row[], extra = "") {
  const lines = [`# ${title}`, "", summary, ""];
  for (const r of [...rows].sort((a, b) => ORDER.indexOf(a.status) - ORDER.indexOf(b.status))) {
    const s = sourceInfo(r.source);
    lines.push(`## ${r.title} (${LABEL[r.status]})`, r.reason);
    if (r.fix) lines.push(`Fix: ${r.fix}`);
    lines.push(`Source: ${r.citation}, ${s.url ? `[${s.name}](${s.url})` : s.name}: "${r.quote}"`, "");
  }
  if (extra) lines.push(extra, "");
  lines.push("---", DISCLAIMER);
  return lines.join("\n");
}

/** Corrected application with [CHANGE n] ... [/CHANGE n] passages highlighted. */
function MarkedText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const re = /\[CHANGE (\d+)\]([\s\S]*?)\[\/CHANGE \1\]/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(<mark key={m.index}>{m[2]}<sup>{m[1]}</sup></mark>);
    last = m.index + m[0].length;
  }
  parts.push(text.slice(last));
  return <div className="doc">{parts}</div>;
}
const stripMarks = (t: string) => t.replace(/\[\/?CHANGE \d+\]/g, "");

/* ---------- shot clock card ---------- */
function ClockCard({ complete }: { complete: string }) {
  const c = shotClock(complete);
  if (!c) return null;
  const pct = Math.min(1, Math.max(0, (60 - c.daysLeft) / 60));
  const color = c.overdue ? "var(--red)" : "var(--orange)";
  const R = 62, C = 2 * Math.PI * R;
  return (
    <div className="clock">
      <div className="dial">
        <svg viewBox="0 0 150 150">
          <circle cx="75" cy="75" r={R} fill="none" stroke="#f1efec" strokeWidth="12" />
          <circle cx="75" cy="75" r={R} fill="none" stroke={color} strokeWidth="12" strokeLinecap="round" strokeDasharray={C} strokeDashoffset={C * (1 - pct)} />
        </svg>
        <div className="v">
          <b style={{ color }}>{Math.abs(c.daysLeft)}</b>
          <small>{c.overdue ? "days overdue" : "days left"}</small>
        </div>
      </div>
      <div>
        <div className="kick">Shot clock · 60-day review</div>
        <ul className="timeline">
          <li><span className="dot" style={{ background: "var(--green)" }} /><span className="lbl">Application complete</span><span className="d">{fmtDate(c.complete)}</span></li>
          <li><span className="dot" style={{ background: c.overdue ? "var(--red)" : "#d6d3d1" }} /><span className="lbl">{c.overdue ? "City deadline passed" : "City must decide by"}</span><span className="d">{fmtDate(c.due)}</span></li>
          <li><span className="dot" style={{ background: "var(--orange)" }} /><span className="lbl">Today</span><span className="d">{fmtDate(new Date())}</span></li>
        </ul>
        <div className={`verdict ${c.overdue ? "over" : "ok"}`}>
          {c.overdue ? "Appears deemed approved" : `${c.daysLeft} days left for the city to approve or deny`}
        </div>
        <div className="law">Gov. Code § 66317(a)(3) · estimate; tolled if you asked for a delay</div>
      </div>
    </div>
  );
}

/* ---------- main component ---------- */
export default function Checker({ demo, backtest }: { demo: { project: string; letter: string }; backtest: Backtest }) {
  const [tab, setTab] = useState<Tab>("pre");
  const [city, setCity] = useState<City>("San Clemente");

  // pre-check
  const [project, setProject] = useState("");
  const [pre, setPre] = useState<PrecheckResultT | null>(null);
  const [preText, setPreText] = useState("");
  const [fix, setFix] = useState<CorrectedApplicationT | null>(null);
  // letter
  const [letter, setLetter] = useState("");
  const [complete, setComplete] = useState("");
  const [useClock, setUseClock] = useState(true);
  const [let_, setLet] = useState<LetterResultT | null>(null);
  const [reply, setReply] = useState("");

  const [busy, setBusy] = useState<null | "pre" | "fix" | "letter">(null);
  const [error, setError] = useState<{ where: Tab; msg: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const seconds = useElapsed(busy !== null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function run<T>(kind: "pre" | "fix" | "letter", where: Tab, fn: () => Promise<T>, done: (r: T) => void) {
    setBusy(kind);
    setError(null);
    try {
      done(await fn());
    } catch (e) {
      setError({ where, msg: e instanceof Error ? e.message : "Something went wrong." });
    } finally {
      setBusy(null);
    }
  }

  const runPre = () => {
    const text = project.trim();
    if (!text) return setError({ where: "pre", msg: "Describe the project or upload a .txt/.md file first." });
    setFix(null);
    run("pre", "pre", () => post<PrecheckResultT>("/api/precheck", { city, project: text }), (r) => { setPre(r); setPreText(text); });
  };
  const runFix = () => {
    if (!pre) return;
    const findings = pre.items.filter((i) => i.status !== "pass").map((i) => `- [${i.status}] ${i.item}: ${i.reason} Fix: ${i.fix} (${i.citation})`).join("\n");
    run("fix", "pre", () => post<CorrectedApplicationT>("/api/fix", { city, application: preText, findings: findings || "- none" }), setFix);
  };
  const runLetter = () => {
    const text = letter.trim();
    if (!text) return setError({ where: "letter", msg: "Paste the city's letter first." });
    run("letter", "letter", () => post<LetterResultT>("/api/letter", { city, letter: text, complete: useClock ? complete : "" }), (r) => { setLet(r); setReply(r.draft_reply); });
  };

  const onFile = (f?: File) => {
    if (!f) return;
    if (!/\.(txt|md)$/i.test(f.name)) return setError({ where: "pre", msg: "Upload a .txt or .md file, or paste the text." });
    f.text().then((t) => setProject((t.length > MAX_INPUT_CHARS ? t.slice(0, MAX_INPUT_CHARS) : t)));
  };

  const preRows: Row[] = pre ? pre.items.map((i) => ({ title: i.item, status: i.status, reason: i.reason, fix: i.fix, quote: i.quote, citation: i.citation, source: i.source })) : [];
  const letRows: Row[] = let_ ? let_.items.map((i) => ({ title: i.request, status: i.status, reason: i.reason, quote: i.quote, citation: i.citation, source: i.source })) : [];
  const count = (rows: Row[], s: Status) => rows.filter((r) => r.status === s).length;

  return (
    <div className="app" id="try">
      <div className="app-top">
        <div className="tabs" role="tablist" aria-label="Shotclock tools">
          <button role="tab" aria-selected={tab === "pre"} className={`tab ${tab === "pre" ? "on" : ""}`} onClick={() => setTab("pre")}><Icon d={ICONS.check} size={18} />Application Pre-Check</button>
          <button role="tab" aria-selected={tab === "letter"} className={`tab ${tab === "letter" ? "on" : ""}`} onClick={() => setTab("letter")}><Icon d={ICONS.mail} size={18} />City Letter Review</button>
          <button role="tab" aria-selected={tab === "acc"} className={`tab ${tab === "acc" ? "on" : ""}`} onClick={() => setTab("acc")}><Icon d={ICONS.chart} size={18} />Accuracy Test</button>
        </div>
        {tab !== "acc" && (
          <label>
            <span className="field-label">City</span>
            <select className="city" value={city} onChange={(e) => setCity(e.target.value as City)}>
              {CITIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </label>
        )}
      </div>

      {/* ---------- Pre-check ---------- */}
      {tab === "pre" && (
        <div>
          <div className="input-row">
            <span className="field-label" style={{ margin: 0 }}>Your ADU project</span>
            <div className="actions" style={{ margin: 0 }}>
              <button className="btn sm" onClick={() => setProject(demo.project)}><Icon d={ICONS.file} size={16} />Use sample project</button>
              <button className="btn sm" onClick={() => fileRef.current?.click()}><Icon d={ICONS.upload} size={16} />Upload .txt / .md</button>
              <input ref={fileRef} type="file" accept=".txt,.md,text/plain,text/markdown" hidden onChange={(e) => onFile(e.target.files?.[0])} />
            </div>
          </div>
          <textarea className="input" value={project} maxLength={MAX_INPUT_CHARS} onChange={(e) => setProject(e.target.value)}
            placeholder="Lot size, existing home, ADU type and size, height, setbacks, parking, distance to transit, documents ready…" />
          <div className="char">{project.length.toLocaleString()} / {MAX_INPUT_CHARS.toLocaleString()}</div>
          <div style={{ marginTop: 14 }}>
            <button className="btn primary block" onClick={runPre} disabled={busy !== null}>{busy === "pre" ? "Checking…" : "Run pre-check"}</button>
          </div>
          {error?.where === "pre" && <div className="error">{error.msg}</div>}

          <div className="results">
            {busy === "pre" ? <Loading label="Checking against state law and city rules…" seconds={seconds} /> : !pre ? (
              <div className="empty"><b>Results appear here</b>Each flag says what’s wrong, how to fix it, and quotes the law.</div>
            ) : (
              <>
                <div className="summary-bar">
                  <div className="chips">
                    <div className="chip r"><b>{count(preRows, "problem")}</b><span>problems</span></div>
                    <div className="chip a"><b>{count(preRows, "missing")}</b><span>missing</span></div>
                    <div className="chip g"><b>{count(preRows, "pass")}</b><span>pass</span></div>
                  </div>
                  <button className="btn sm" onClick={() => download("shotclock-precheck.md", reportMd("Shotclock pre-check", pre.summary, preRows))}><Icon d={ICONS.dl} size={16} />Download fix list</button>
                </div>
                <div className="summary">{pre.summary}</div>
                <Rows rows={preRows} />

                <h3 className="subhead">Fix it for me</h3>
                <p className="subnote">Claude drafts the corrected application: every change before → after, with the law behind it. Anything only a person can do is listed separately.</p>
                <button className="btn dark" onClick={runFix} disabled={busy !== null}><Icon d={ICONS.wand} size={18} />{busy === "fix" ? "Drafting…" : "Draft the corrected application"}</button>
                <div style={{ marginTop: 16 }}>
                  {busy === "fix" ? <Loading label="Drafting the corrected application…" seconds={seconds} /> : fix && (
                    <>
                      <div className="chips" style={{ marginBottom: 14 }}>
                        <div className="chip r"><b>{fix.corrections.length}</b><span>changes</span></div>
                        <div className="chip a"><b>{fix.human_todo.length}</b><span>for a person</span></div>
                      </div>
                      {fix.corrections.map((c, n) => (
                        <div className="change" key={n}>
                          <div className="t"><small>CHANGE {n + 1}</small>{c.item}</div>
                          <div className="ba"><div className="before">{c.before}</div><div className="arrow">→</div><div className="after">{c.after}</div></div>
                          <div className="why">{c.why} <span className="cite">{c.citation}</span></div>
                        </div>
                      ))}
                      {fix.human_todo.length > 0 && (<>
                        <div className="kick" style={{ marginTop: 18 }}>Still needs a person</div>
                        <ul className="todo">{fix.human_todo.map((t, i) => <li key={i}><span className="box" />{t}</li>)}</ul>
                      </>)}
                      <div className="kick" style={{ marginTop: 18 }}>Corrected application (changes highlighted)</div>
                      <MarkedText text={fix.corrected_text} />
                      <div className="kick" style={{ marginTop: 18 }}>Cover note to the city</div>
                      <div className="summary" style={{ whiteSpace: "pre-wrap" }}>{fix.cover_note}</div>
                      <div className="actions">
                        <button className="btn primary" onClick={() => download("shotclock-corrected.md", [
                          "# Corrected ADU application (draft by Shotclock)", "", stripMarks(fix.corrected_text), "", "## Changes made", "",
                          ...fix.corrections.map((c, i) => `${i + 1}. **${c.item}**: ${c.before} → ${c.after} (${c.citation})`),
                          "", "## Still needs a person", "", ...fix.human_todo.map((t) => `- [ ] ${t}`),
                          "", "## Cover note to the city", "", fix.cover_note, "", "---", DISCLAIMER].join("\n"))}>
                          <Icon d={ICONS.dl} size={16} />Download corrected application</button>
                      </div>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ---------- City letter ---------- */}
      {tab === "letter" && (
        <div>
          <div className="input-row">
            <span className="field-label" style={{ margin: 0 }}>The city’s comment letter</span>
            <button className="btn sm" onClick={() => { setLetter(demo.letter); setComplete(SAMPLE_DATE); setUseClock(true); }}><Icon d={ICONS.mail} size={16} />Use sample letter</button>
          </div>
          <textarea className="input" value={letter} maxLength={MAX_INPUT_CHARS} onChange={(e) => setLetter(e.target.value)} placeholder="Paste the corrections letter the city sent you…" />
          <div className="controls">
            <label>
              <span className="field-label">Application complete on</span>
              <input className="date" type="date" value={complete} onChange={(e) => setComplete(e.target.value)} />
            </label>
            <label className="toggle">
              <input type="checkbox" checked={useClock} onChange={(e) => setUseClock(e.target.checked)} />
              <span className="sw" />Shot clock
            </label>
          </div>
          <button className="btn primary block" onClick={runLetter} disabled={busy !== null}>{busy === "letter" ? "Checking…" : "Check the letter"}</button>
          {error?.where === "letter" && <div className="error">{error.msg}</div>}

          <div className="results">
            {useClock && complete && <ClockCard complete={complete} />}
            {busy === "letter" ? <Loading label="Checking each request against state law…" seconds={seconds} /> : !let_ ? (
              !(useClock && complete) && <div className="empty"><b>Results appear here</b>Each request is checked against state law, with a draft reply.</div>
            ) : (
              <>
                <div className="summary-bar">
                  <div className="chips">
                    <div className="chip r"><b>{count(letRows, "likely_conflicts")}</b><span>likely conflict</span></div>
                    <div className="chip a"><b>{count(letRows, "unclear")}</b><span>unclear</span></div>
                    <div className="chip g"><b>{count(letRows, "matches_law")}</b><span>lawful</span></div>
                  </div>
                  <span style={{ fontWeight: 600 }}>{count(letRows, "likely_conflicts")} of {letRows.length} requests likely conflict with state law</span>
                </div>
                <div className="summary">{let_.summary}</div>
                <Rows rows={letRows} />
                <h3 className="subhead">Draft reply to the city</h3>
                <p className="subnote">Edit it before sending. Nothing is ever sent automatically.</p>
                <textarea className="reply" value={reply} onChange={(e) => setReply(e.target.value)} />
                <div className="actions">
                  <button className="btn primary" onClick={() => download("shotclock-reply.md", reportMd("Shotclock letter check", let_.summary, letRows, "## Draft reply\n\n" + reply))}><Icon d={ICONS.dl} size={16} />Download reply</button>
                  <button className="btn" onClick={() => navigator.clipboard.writeText(reply).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); })}><Icon d={ICONS.copy} size={16} />{copied ? "Copied" : "Copy reply"}</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* ---------- Accuracy test ---------- */}
      {tab === "acc" && <Accuracy backtest={backtest} />}

      <p className="hint" style={{ marginTop: 22 }}>{DISCLAIMER}</p>
    </div>
  );
}

function Accuracy({ backtest }: { backtest: Backtest }) {
  const [open, setOpen] = useState<number | null>(null);
  if (!backtest?.grade?.matches) return <div className="empty"><b>No accuracy test result loaded.</b></div>;
  const matches = [...backtest.grade.matches].sort((a: Backtest, b: Backtest) => a.finding_number - b.finding_number);
  const n = matches.filter((m: Backtest) => m.caught).length;
  const extra: string[] = backtest.grade.extra_issues || [];
  return (
    <div>
      <h3 className="subhead" style={{ marginTop: 0 }}>Would Shotclock have caught what the state caught?</h3>
      <p className="subnote">In Oct 2025 the state housing department (HCD) found 10 conflicts in San Clemente’s ADU ordinance. Shotclock reviewed the ordinance with HCD’s letter hidden, then a strict second pass compared its list with HCD’s 10 findings.</p>
      <div className="score">
        <div className="bignum"><span>{n}</span>/{matches.length}</div>
        <div className="dots">
          {matches.map((m: Backtest) => <div key={m.finding_number} className={`dotn ${m.caught ? "y" : "n"}`} title={m.finding}>{m.finding_number}</div>)}
        </div>
      </div>
      <p className="caveat">Input: San Clemente Municipal Code § 17.28.270 (Ord. 1742, the version HCD reviewed). The model may have seen public reports in training, so treat this as a sanity check, not proof.</p>
      <div className="items">
        {matches.map((m: Backtest, i: number) => (
          <div key={i} className={`item ${open === i ? "open" : ""}`}>
            <button onClick={() => setOpen(open === i ? null : i)} aria-expanded={open === i}>
              <span className={`badge ${m.caught ? "pass" : "unclear"}`}>{m.caught ? "Caught" : "Missed"}</span>
              <span className="title">HCD #{m.finding_number} · {m.finding}</span>
              <span className="chev"><Icon d={ICONS.chev} size={18} /></span>
            </button>
            {open === i && <div className="body"><p>{m.caught ? <><b>Shotclock:</b> {m.matched_issue}</> : "Not caught in this run."}</p></div>}
          </div>
        ))}
        {extra.length > 0 && (
          <div className={`item ${open === -1 ? "open" : ""}`}>
            <button onClick={() => setOpen(open === -1 ? null : -1)} aria-expanded={open === -1}>
              <span className="badge missing">+{extra.length}</span>
              <span className="title">More issues Shotclock flagged (not in HCD’s letter)</span>
              <span className="chev"><Icon d={ICONS.chev} size={18} /></span>
            </button>
            {open === -1 && <div className="body"><ul>{extra.map((e, i) => <li key={i} style={{ marginTop: 8, color: "var(--ink-2)" }}>{e}</li>)}</ul></div>}
          </div>
        )}
      </div>
    </div>
  );
}
