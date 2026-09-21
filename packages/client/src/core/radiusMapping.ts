/**
 * Default dynamic-range floor, in dB.
 *
 * A floor is required because dB is unbounded below: a null at -60 dB would
 * collapse to the origin and produce degenerate spikes. -40 dB keeps the
 * main lobe and the first sidelobes legible for typical datasheet patterns.
 */
export const DEFAULT_FLOOR_DB = -40;

/**
 * Maps a magnitude in dB to a normalized radius in [0, 1].
 *
 * The contract normalizes magnitudes so the maximum is 0 dB, so the mapping
 * runs from `floorDb` to 0. This is a visualization decision, not a physical
 * one, which is why it lives in the client and not in the contract.
 *
 * Note this maps a dB value; it never combines two dB values arithmetically.
 */
export function magnitudeToRadius(
  magnitudeDb: number,
  floorDb: number,
): number {
  const span = 0 - floorDb;
  const t = (magnitudeDb - floorDb) / span;
  return Math.min(1, Math.max(0, t));
}
