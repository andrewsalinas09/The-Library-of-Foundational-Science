# The Library of Foundational Science

Long-form explanations built literally from zero. Each document names a
surprising claim up front, constructs every concept it depends on, runs the
mechanism with real numbers you can check by hand, and then shows where the
same idea turns up in fields that look nothing alike.

## Layout

```
docs/                  the library itself. Markdown or MDX, one file per document.
ideas.yaml             controlled vocabulary: cross-cutting ideas and mechanisms.
first_principles_explainer_prompt.md
                       the house style, and the prompt that generates documents.

src/                   the reader. Astro.
  content.config.ts      frontmatter schema (Zod); an unregistered tag fails the build
  layouts/Base.astro     page shell, theme, scrollspy, progress, lazy Mermaid
  pages/                 document route, index, and one page per idea
  plugins/               remark/rehype passes (callouts, wikilinks, mermaid, glossary)
  styles/                design tokens and long-form prose typography
tools/lint.py          prose lint: the house-style checks a schema cannot do
```

Content lives at the repository root rather than under `src/`, because the
library is the product and the site is an implementation detail. Astro reads it
through a glob loader.

## Working on it

```bash
npm run dev        # http://localhost:4321, hot reload (no search: see below)
npm run build      # static site into dist/, plus the Pagefind index
npm run preview    # serve dist/ exactly as it will ship

uv run tools/lint.py             # house-style check across every document
uv run tools/lint.py --pedantic  # list every glossary candidate
uv run tools/lint.py --strict    # warnings fail too, for CI
```

Search is built by `astro build`, so it is live in `preview` and production but
not in `dev`.

## Authoring

Frontmatter is validated at build time. Required: `uid` (stable across renames,
8+ lowercase alphanumerics), `title`, `subtitle`, `domain`, `mechanisms`,
`ideas`, `created`. Optional but wanted: `analogy` and `claim`.

Every `ideas` and `mechanisms` slug must exist in `ideas.yaml`. This is
deliberate. A tag system with no registry drifts into four spellings of one idea;
the build refuses the fourth spelling and suggests the nearest registered slug.

Beyond CommonMark and GFM, documents can use:

- **Math.** `$\sigma/\sqrt{N}$` inline, `$$...$$` display. Rendered to HTML at
  build time, so no KaTeX JavaScript ships. Escape literal currency as `\$499`.
- **Diagrams.** ` ```mermaid ` fences. The 3.5 MB Mermaid bundle is fetched only
  on pages that contain one.
- **Callouts.** `:::key`, `:::objection[Custom title]`, and also `note`,
  `caution`, `history`, `aside`, `vocabulary`.
- **Cross-links.** `[[slug]]`, `[[slug|label]]`, `[[slug#section]]`. Links to
  documents that do not exist yet are allowed; they are a worklist, and the lint
  reports them.
- **Glossary tooltips.** Nothing to author. Bold a term on first use and define
  it in the appendix as `- **Term**: definition`, and the reader wires the two
  together automatically.
- **Live demos.** See below.

## Documents with demos

A document is either a flat file or a folder:

```
docs/clock-discipline.md               prose only
docs/sigma-delta-conversion/
  index.mdx                            prose, renamed to .mdx so it can import
```

The folder form exists so a document that needs figures, data, or assets keeps
them beside the prose. The URL is unchanged: `index` is stripped from the id.

Interactive demos themselves live in `src/components/demos/` and are imported
through the `@demos` alias:

```mdx
import SigmaDeltaSimulator from "@demos/SigmaDeltaSimulator.astro";

<SigmaDeltaSimulator />
```

Two constraints worth knowing before writing another one, both found the hard
way:

1. **Demos are plain `.astro` components with `is:inline` scripts, not
   framework islands.** Astro does not hoist bundled component scripts through
   content-collection MDX, so a normal `<script>` is silently dropped and the
   demo renders but never runs. `is:inline` emits the code with the markup.
   The cost is plain JavaScript instead of TypeScript.
2. **They live under `src/`, not in the document folder.** Components imported
   from `docs/` do not get the same Vite treatment.

`@astrojs/preact` was tried first and does not currently work with Astro 5.18
(`astro:preact:opts` fails to resolve). Vanilla is smaller anyway for a canvas
simulator, so there is no rush to revisit it.

## Converting old notation

`tools/mathify.py` rewrites ASCII engineering notation into LaTeX: `10^-12`,
`4.0 × 10^-21`, `σ / √N`, `10·log10(...)`, and `minus 130 dBm`. It protects
frontmatter, code fences, and existing math, and renders units upright so
`nV/√Hz` does not come out as a product of the variables n, V, H and z.

```bash
uv run tools/mathify.py            # dry run, reports every proposed change
uv run tools/mathify.py --apply    # write
```

Display equations need `$$` on their own lines; `$$x$$` inline renders at text
size.

## Conventions the tooling enforces

The nine-section spine from the house style, one heading level for all numbered
sections, an 8,000 to 10,000 word target, no em dashes, and a glossary that
covers the terms the body bolds. Run the lint; it explains itself.
