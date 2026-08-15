import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";
import { KNOWN_IDEAS, KNOWN_MECHANISMS, nearest } from "./lib/registry";

function registered(pool: Set<string>, label: string) {
  return (values: string[], ctx: z.RefinementCtx) => {
    for (const value of values) {
      if (pool.has(value)) continue;
      const hint = nearest(value, pool);
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message:
          `Unregistered ${label} "${value}".` +
          (hint ? ` Did you mean "${hint}"?` : "") +
          ` Add it to ideas.yaml with a one-line definition, or fix the tag.`,
      });
    }
  };
}

const docs = defineCollection({
  // Content lives at the repository root, not buried under src/. The library
  // is the product; the site machinery is an implementation detail.
  //
  // A document is either a flat file (`docs/foo.md`) or a folder holding an
  // index plus its own components (`docs/foo/index.mdx` next to `Demo.tsx`).
  // Folders are what documents with live demos want, so the simulator lives
  // beside the prose it illustrates rather than in a distant shared directory.
  //
  // The `[^_]` prefix keeps underscore-prefixed partials and drafts out of the
  // collection, and avoids the loader matching root-level files twice.
  loader: glob({
    pattern: "**/[^_]*.{md,mdx}",
    base: "./docs",
    generateId: ({ entry }) =>
      entry.replace(/\.(md|mdx)$/, "").replace(/\/index$/, ""),
  }),
  schema: z.object({
    /** Stable across renames. The search index and cross-links key on this. */
    uid: z
      .string()
      .regex(/^[0-9a-z]{8,}$/, "uid must be 8+ lowercase alphanumerics"),

    title: z.string().min(1),
    subtitle: z.string().min(1),

    /** Free text. The human-browsable subject, e.g. "metrology / timekeeping". */
    domain: z.string().min(1),

    /** What a reader must already know. House style says: nothing. */
    assumes: z.string().default("nothing"),

    /** The concrete machines this document explains. */
    mechanisms: z
      .array(z.string())
      .min(1)
      .superRefine(registered(KNOWN_MECHANISMS, "mechanism")),

    /** The cross-cutting principles. This is what makes the library a graph. */
    ideas: z
      .array(z.string())
      .min(1)
      .superRefine(registered(KNOWN_IDEAS, "idea")),

    /** The single central analogy the house style requires each document carry. */
    analogy: z.string().optional(),

    /** The concrete claim the preface promises to earn. Shown on the index card. */
    claim: z.string().optional(),

    status: z.enum(["draft", "review", "published"]).default("draft"),
    created: z.coerce.date(),
    updated: z.coerce.date().optional(),

    /** Hidden from listings and search when true. */
    draft: z.boolean().default(false),
  }),
});

export const collections = { docs };
