"""Source watcher page: shows how Shotclock's library stays current (Scale)."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "watcher"))
import source_watcher as sw  # noqa: E402

st.set_page_config(page_title="Shotclock · Source watcher", page_icon="🔄", layout="wide")
st.title("🔄 Source watcher")
st.markdown(
    "Shotclock only answers from official documents in its library. Laws, HCD letters and city checklists change, "
    "so this bot **re-downloads every official source, fingerprints it, and flags anything that changed, moved or "
    "disappeared**. It never edits the library itself: a person reviews each change and approves it, because this "
    "is legal information.")

c1, c2, c3 = st.columns(3)
c1.metric("Library files", len(sw.find_sources()))
c2.metric("Re-check", "weekly (scheduled)")
c3.metric("Stale after", f"{sw.STALE_DAYS} days")

changelog = sw.load_json(Path(sw.__file__).parent / "changelog.json", {"entries": []})["entries"]
if changelog:
    st.subheader("Change log: real updates caught so far")
    for e in changelog:
        with st.container(border=True):
            st.markdown(f"**{e['date']} · [{e['source']}]({e['url']})**  \n"
                        f"🚩 {e['flag']}  \n🔎 **Found:** {e['found']}  \n✅ **Done:** {e['action']}")

st.subheader("Run a check")
handbook = next((u for s in sw.find_sources() for u in s.urls if "adu-handbook" in u), None)
demo = st.toggle("Demo: pretend HCD just updated the ADU Handbook", value=False,
                 help="Simulates a changed fingerprint for one source. Nothing is downloaded or saved differently.")

if st.button("Check all sources now", type="primary"):
    with st.spinner("Checking each official source (one request at a time per site)…"):
        st.session_state["watch"] = sw.run(pretend_changed=handbook if demo else None)

rep = st.session_state.get("watch")
if not rep:
    st.info("Press **Check all sources now**. It can take up to a minute.")
    st.stop()

checks = rep["checks"]
n = {k: sum(c["status"] == k for c in checks) for k in sw.ICON}
attention = n["changed"] + n["unreachable"] + n["moved"] + n["new"]
(st.warning if attention else st.success)(
    f"Checked {len(checks)} official links at {rep['run_at'][11:16]}: "
    f"{n['unchanged']} unchanged, {n['online']} web pages online, **{n['changed']} changed**, "
    f"{n['unreachable']} unreachable, {n['moved']} moved.")

st.subheader("Library sources")
order = {"changed": 0, "unreachable": 1, "moved": 2, "new": 3, "online": 4, "unchanged": 5}
for c in sorted(checks, key=lambda c: order.get(c["status"], 9)):
    files = ", ".join(f"`{Path(f).name}`" for f in c["files"])
    line = f"{sw.ICON.get(c['status'], '?')} **{c['status']}** · [{c['url'][:90]}]({c['url']})  \nused by {files}"
    if c["note"]:
        line += f"  \n_{c['note']}_"
    if c["status"] == "changed":
        st.error(line + "  \n**Next step:** review the new version, update the file in `docs/`, then approve.")
    elif c["status"] in ("unreachable", "moved"):
        st.warning(line)
    else:
        st.markdown(line)

st.subheader("Waiting to be added")
st.caption("Known official documents that aren't in the library yet. Adding a city means adding its documents, "
           "with no code changes.")
for w in rep["candidates"]:
    if w["in_library"]:
        continue
    state = "✅ online, ready to review and add" if w["reachable"] else f"⚠️ not reachable ({w['note']})"
    st.markdown(f"- **{w['name']}** · [link]({w['url']}) · {state} → `{w['would_go_in']}`")

st.subheader("Freshness")
st.dataframe(
    [{"file": f["file"], "last verified": f["last_verified"] or "never",
      "age (days)": f["age_days"], "status": "⚠️ stale" if f["stale"] else "✅ fresh"} for f in rep["freshness"]],
    hide_index=True, width="stretch")

with st.expander("How this runs in production"):
    st.markdown(
        "1. A scheduled job runs `python watcher/source_watcher.py` weekly (cron or GitHub Actions).\n"
        "2. Anything changed, moved or unreachable opens a review task for a person.\n"
        "3. The reviewer updates the file in `docs/` and runs `python watcher/source_watcher.py --approve` "
        "to save the new fingerprints in `watcher/manifest.json`.\n"
        "4. Every answer in the app is based only on approved sources, and each source shows when it was last verified.")
