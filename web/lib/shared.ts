// Code shared by the browser and the server: cities, shot clock, source links.

export const CITIES = ["San Clemente", "Dana Point", "Irvine", "Santa Ana", "Anaheim", "Other OC city"] as const;
export type City = (typeof CITIES)[number];

export const MAX_INPUT_CHARS = 40_000;

export const DISCLAIMER =
  'Not legal advice. Results say "likely" because they are an automated reading of the loaded sources. ' +
  "Confirm with the city or an attorney before acting.";

// ---------- shot clock: Gov. Code § 66317(a)(3), plain date math (same as deadlines.py) ----------
export const ADU_DECISION_DAYS = 60;
const DAY = 86_400_000;

export type ShotClock = { complete: Date; due: Date; daysLeft: number; overdue: boolean };

/** `complete` is a YYYY-MM-DD string; dates are compared as calendar days (UTC). */
export function shotClock(complete: string, today: Date = new Date()): ShotClock | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(complete);
  if (!m) return null;
  const c = Date.UTC(+m[1], +m[2] - 1, +m[3]);
  const t = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  const due = c + ADU_DECISION_DAYS * DAY;
  const daysLeft = Math.round((due - t) / DAY);
  return { complete: new Date(c), due: new Date(due), daysLeft, overdue: daysLeft < 0 };
}

export const fmtDate = (d: Date) =>
  d.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric", timeZone: "UTC" });

export function clockSummary(c: ShotClock): string {
  if (c.overdue)
    return (
      `Application complete ${fmtDate(c.complete)}. The city had to approve or deny by ${fmtDate(c.due)}: ` +
      `${-c.daysLeft} days overdue. Under Gov. Code § 66317(a)(3) the application appears to be deemed approved.`
    );
  return (
    `Application complete ${fmtDate(c.complete)}. The city must approve or deny by ${fmtDate(c.due)}: ` +
    `${c.daysLeft} days left (Gov. Code § 66317(a)(3)).`
  );
}

// ---------- readable name + official link for each loaded source ----------
export const SOURCE_LINKS: Record<string, [string, string]> = {
  "gov-code-66310-66342.md": [
    "California Gov. Code §§ 66310–66342 (ADU law)",
    "https://leginfo.legislature.ca.gov/faces/codes_displayexpandedbranch.xhtml?tocCode=GOV&division=1.&title=7.&part=&chapter=13.&article=",
  ],
  "hcd-adu-handbook.md": [
    "HCD ADU Handbook",
    "https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/adu-handbook-update.pdf",
  ],
  "hcd-findings-dana-point-2025-08.md": [
    "HCD Notice of Violation: Dana Point (Aug 2025)",
    "https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/dana-point-adu-nov-081325.pdf",
  ],
  "hcd-findings-san-clemente-2025-10.md": [
    "HCD findings: San Clemente (Oct 2025)",
    "https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/san-clemente-adu-findings-101425.pdf",
  ],
  "hcd-findings-san-clemente-2025-10-fulltext.md": [
    "HCD findings: San Clemente (Oct 2025)",
    "https://www.hcd.ca.gov/sites/default/files/docs/policy-and-research/ordinance-review-letters/san-clemente-adu-findings-101425.pdf",
  ],
  "san-clemente-muni-code-17-28-270-2026.md": [
    "San Clemente Municipal Code § 17.28.270 (2026)",
    "https://library.municode.com/ca/san_clemente/codes/code_of_ordinances?nodeId=TIT17ZO_CH17.28SPUS_17.28.270ACDWUN",
  ],
  "san-clemente-muni-code-17-28-270.md": [
    "San Clemente Municipal Code § 17.28.270 (Ord. 1742)",
    "https://www.sanclemente.gov/DocumentCenter/View/694/ADU-Application-Packet-PDF",
  ],
  "san-clemente-adu-checklist-2023-03.md": [
    "San Clemente ADU Submittal Checklist",
    "https://www.sanclemente.gov/DocumentCenter/View/694/ADU-Application-Packet-PDF",
  ],
  "san-clemente-adu-info-packet-2024-08.md": [
    "San Clemente ADU Information Packet",
    "https://www.sanclemente.gov/DocumentCenter/View/1295",
  ],
};

export function sourceInfo(source: string): { name: string; url: string | null } {
  const key = (source || "").trim().replace(/`/g, "").split("/").pop() || "";
  const hit = SOURCE_LINKS[key];
  return hit ? { name: hit[0], url: hit[1] } : { name: (source || "").trim(), url: null };
}
