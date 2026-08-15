import { parse as parseYaml } from "yaml";
// Inlined at bundle time. Reading it from disk at runtime would resolve
// relative to dist/ once the server entry is bundled, which it will not find.
import registryYaml from "../../ideas.yaml?raw";

export interface Registry {
  ideas: Record<string, string>;
  mechanisms: Record<string, string>;
}

/**
 * The controlled vocabulary, read from the repository root.
 *
 * Both the content schema and the idea pages read this file, and so does the
 * Python prose lint. One source of truth is the whole point: a tag system
 * with no registry drifts into four spellings of one idea by document 300.
 */
export const registry: Registry = parseYaml(registryYaml);

export const KNOWN_IDEAS = new Set(Object.keys(registry.ideas ?? {}));
export const KNOWN_MECHANISMS = new Set(Object.keys(registry.mechanisms ?? {}));

/** Suggest the closest registered slug so a typo is a one-line fix. */
export function nearest(value: string, pool: Set<string>): string | null {
  let best: string | null = null;
  let bestScore = Infinity;
  for (const candidate of pool) {
    const score = editDistance(value, candidate);
    if (score < bestScore) {
      bestScore = score;
      best = candidate;
    }
  }
  return bestScore <= Math.max(3, value.length / 3) ? best : null;
}

function editDistance(a: string, b: string): number {
  const row = Array.from({ length: b.length + 1 }, (_, i) => i);
  for (let i = 1; i <= a.length; i++) {
    let diagonal = row[0];
    row[0] = i;
    for (let j = 1; j <= b.length; j++) {
      const previous = row[j];
      row[j] = Math.min(
        row[j] + 1,
        row[j - 1] + 1,
        diagonal + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
      diagonal = previous;
    }
  }
  return row[b.length];
}
