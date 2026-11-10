import { askClaude, who } from "@/lib/claude";
import { handle, text } from "@/lib/routes";
import { PrecheckResult } from "@/lib/schemas";

export const runtime = "nodejs";
export const maxDuration = 300;

export async function POST(req: Request) {
  return handle(req, async (body, city) => {
    const project = text(body.project, "project description");
    return askClaude(
      `City: ${city}\n${who(city)}\nPre-check this ADU project BEFORE submission. List each relevant requirement as ` +
        `pass / missing (document or info not provided) / problem (conflicts with a rule). Give a concrete fix for ` +
        `each non-pass item.\n\n<project>\n${project}\n</project>`,
      PrecheckResult,
      { effort: "low" }, // measured: low ~34 s vs ~81 s at high, same core flags
    );
  });
}
