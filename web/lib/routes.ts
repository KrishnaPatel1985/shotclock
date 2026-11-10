import "server-only";
import { NextResponse } from "next/server";
import { checkRateLimit, UserFacingError } from "./claude";
import { CITIES, City, MAX_INPUT_CHARS } from "./shared";

/** Shared request handling: JSON body, city check, input caps, rate limit, friendly errors. */
export async function handle(
  req: Request,
  run: (body: Record<string, unknown>, city: City) => Promise<unknown>,
) {
  try {
    const body = (await req.json().catch(() => null)) as Record<string, unknown> | null;
    if (!body) throw new UserFacingError("Bad request.", 400);
    const city = (CITIES as readonly string[]).includes(String(body.city)) ? (body.city as City) : "San Clemente";
    for (const v of Object.values(body)) {
      if (typeof v === "string" && v.length > MAX_INPUT_CHARS * 2)
        throw new UserFacingError(`Input too long (max ${MAX_INPUT_CHARS.toLocaleString()} characters).`, 413);
    }
    const ip = (req.headers.get("x-forwarded-for") || "").split(",")[0].trim() || "unknown";
    checkRateLimit(ip);
    return NextResponse.json(await run(body, city));
  } catch (err) {
    if (err instanceof UserFacingError) return NextResponse.json({ error: err.message }, { status: err.status });
    console.error(err);
    return NextResponse.json({ error: "Something went wrong. Please try again." }, { status: 500 });
  }
}

export function text(v: unknown, field: string): string {
  const s = typeof v === "string" ? v.trim() : "";
  if (!s) throw new UserFacingError(`Missing ${field}.`, 400);
  return s.slice(0, MAX_INPUT_CHARS);
}
