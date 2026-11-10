import { askClaude, who } from "@/lib/claude";
import { handle, text } from "@/lib/routes";
import { CorrectedApplication } from "@/lib/schemas";

export const runtime = "nodejs";
export const maxDuration = 300;

export async function POST(req: Request) {
  return handle(req, async (body, city) => {
    const application = text(body.application, "application");
    const findings = text(body.findings, "pre-check findings");
    return askClaude(
      `City: ${city}\n${who(city)}\nDraft the corrected version of this ADU application so it can be submitted ` +
        `without a correction round. Use the pre-check findings below. For each problem or missing item give ` +
        `'before' (exact wording from the application, or '(not in application)') and 'after' (the exact replacement ` +
        `wording or text to add, with the specific numbers the law sets). Never invent facts about the property: use ` +
        `a bracketed placeholder like [CONFIRM: walking distance to the transit stop]. Put drawings, reports, ` +
        `signatures and fees in human_todo. Then write corrected_text (the full revised application) with every ` +
        `changed or added passage wrapped as [CHANGE n] ... [/CHANGE n], where n is the 1-based position of that ` +
        `change in corrections, and a short cover_note to the city listing what changed.\n\n` +
        `<application>\n${application}\n</application>\n\n<precheck_findings>\n${findings}\n</precheck_findings>`,
      CorrectedApplication,
      { effort: "medium", maxTokens: 20000 },
    );
  });
}
