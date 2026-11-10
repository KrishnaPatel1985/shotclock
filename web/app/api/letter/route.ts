import { askClaude, who } from "@/lib/claude";
import { handle, text } from "@/lib/routes";
import { LetterResult } from "@/lib/schemas";
import { clockSummary, shotClock } from "@/lib/shared";

export const runtime = "nodejs";
export const maxDuration = 300;

export async function POST(req: Request) {
  return handle(req, async (body, city) => {
    const letter = text(body.letter, "city letter");
    // The shot clock is computed here in plain date math, never by Claude.
    const clock = typeof body.complete === "string" && body.complete ? shotClock(body.complete) : null;
    const clockFact = clock ? `\nShot clock (computed, not by you): ${clockSummary(clock)}\n` : "";
    return askClaude(
      `City: ${city}\n${who(city)}${clockFact}\nSplit this city comment letter into its individual requests. For ` +
        `each, decide: matches_law (the city may ask this), likely_conflicts (state ADU law appears to prohibit it), ` +
        `or unclear (not covered by loaded sources). Then draft a short, polite reply from the applicant: agree to ` +
        `the lawful items, ask the city to withdraw the conflicting ones citing the statute, and if the 60-day ` +
        `decision deadline has passed, note that, quote § 66317(a)(3) that the application appears to be deemed ` +
        `approved, and ask the city to confirm the approval in writing. Sign it [Applicant name].\n\n` +
        `<letter>\n${letter}\n</letter>`,
      LetterResult,
      { effort: "medium" }, // measured: medium ~30 s vs ~58 s at high, same labels
    );
  });
}
