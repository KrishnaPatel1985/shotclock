// Structured outputs: the same fields as the Streamlit app's Pydantic models.
import { z } from "zod";

export const PrecheckItem = z.object({
  item: z.string().describe("Short title of the requirement, at most 6 words, e.g. 'Site plan' or 'Impact fees'"),
  status: z.enum(["pass", "missing", "problem"]),
  reason: z.string(),
  fix: z.string().describe("What to do; empty if status is pass"),
  source: z.string().describe("Loaded source file name"),
  citation: z.string().describe("Section, e.g. Gov. Code § 66321(b)"),
  quote: z.string().describe("Short exact quote from the source"),
});
export const PrecheckResult = z.object({ summary: z.string(), items: z.array(PrecheckItem) });

export const Correction = z.object({
  item: z.string().describe("Short title, at most 6 words"),
  before: z.string().describe("Exact wording in the application now, or '(not in application)'"),
  after: z.string().describe("Exact replacement wording or text to add; use [CONFIRM: ...] for unknown facts"),
  why: z.string().describe("One sentence"),
  citation: z.string(),
});
export const CorrectedApplication = z.object({
  corrections: z.array(Correction),
  corrected_text: z
    .string()
    .describe(
      "Full revised application / project description with all corrections applied. Wrap every changed or added " +
        "passage as [CHANGE n] ... [/CHANGE n], where n is the 1-based number of the matching item in corrections",
    ),
  human_todo: z.array(z.string()).describe("Things only a person can produce: drawings, reports, signatures, fees, confirmations"),
  cover_note: z.string().describe("Short note to the city listing what changed in this resubmittal"),
});

export const LetterItem = z.object({
  request: z.string().describe("Short title of the city's request, at most 8 words, e.g. 'Owner-occupancy covenant'"),
  status: z.enum(["matches_law", "likely_conflicts", "unclear"]),
  reason: z.string(),
  source: z.string(),
  citation: z.string(),
  quote: z.string(),
});
export const LetterResult = z.object({
  summary: z.string(),
  items: z.array(LetterItem),
  draft_reply: z.string().describe("Polite reply letter to the city, citing statutes for conflicts"),
});

export type PrecheckResultT = z.infer<typeof PrecheckResult>;
export type CorrectedApplicationT = z.infer<typeof CorrectedApplication>;
export type LetterResultT = z.infer<typeof LetterResult>;
