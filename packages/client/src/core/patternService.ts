import { validatePattern3d, type Pattern3d } from "schema";

/**
 * Development fixture. The real source is the REST API in packages/server,
 * which does not exist yet (roadmap phase 3); this keeps the client
 * independently runnable until it does.
 */
const FIXTURE_URL = "/fixtures/dipole-pattern3d.json";

/**
 * Loads a pattern3d block and validates it before any consumer sees it.
 * A malformed grid must fail here rather than render as a plausible but
 * wrong pattern.
 */
export async function loadPattern3d(
  url: string = FIXTURE_URL,
): Promise<Pattern3d> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load pattern from ${url}: ${response.status}`);
  }

  const pattern = (await response.json()) as Pattern3d;
  validatePattern3d(pattern);
  return pattern;
}
