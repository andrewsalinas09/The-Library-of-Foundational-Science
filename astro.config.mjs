// @ts-check
import { fileURLToPath } from "node:url";
import { defineConfig } from "astro/config";
import mdx from "@astrojs/mdx";
import sitemap from "@astrojs/sitemap";
import pagefind from "astro-pagefind";

import remarkDirective from "remark-directive";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeSlug from "rehype-slug";
import rehypeAutolinkHeadings from "rehype-autolink-headings";

import { remarkWikiLink } from "./src/plugins/remark-wiki-link.mjs";
import { remarkCallouts } from "./src/plugins/remark-callouts.mjs";
import { remarkMermaid } from "./src/plugins/remark-mermaid.mjs";
import { remarkReadingData } from "./src/plugins/remark-reading-data.mjs";
import { rehypeTables } from "./src/plugins/rehype-tables.mjs";
import { rehypeGlossary } from "./src/plugins/rehype-glossary.mjs";

// Change this when the library gets a real home; the sitemap needs it.
const SITE = "https://library.local";

export default defineConfig({
  site: SITE,
  vite: {
    resolve: {
      alias: {
        // Interactive demos live under src/ so Vite applies the JSX pipeline
        // to them, but documents import them by a stable name rather than by
        // counting ../ hops out of docs/.
        "@demos": fileURLToPath(new URL("./src/components/demos", import.meta.url)),
      },
    },
  },
  integrations: [mdx(), sitemap(), pagefind()],
  markdown: {
    // Order matters. remark-directive must parse `:::key` blocks before
    // remarkCallouts can style them; wikilinks run before math so they never
    // see KaTeX output; reading data runs last so it counts final prose.
    remarkPlugins: [
      remarkDirective,
      remarkCallouts,
      remarkMermaid,
      remarkWikiLink,
      remarkMath,
      remarkReadingData,
    ],
    rehypePlugins: [
      rehypeSlug,
      [
        rehypeAutolinkHeadings,
        {
          behavior: "append",
          properties: { className: ["heading-anchor"], ariaLabel: "Permalink" },
          // The anchor must contribute no text. Astro extracts heading text
          // after rehype runs, so a literal "#" here ends up appended to every
          // entry in the sidebar. The glyph is drawn in CSS instead.
          content: [],
        },
      ],
      [
        rehypeKatex,
        {
          // Rendered at build time to HTML+CSS. No KaTeX JS ships to the client.
          strict: false,
          trust: false,
          macros: {
            "\\ppm": "\\text{ppm}",
            "\\ppb": "\\text{ppb}",
          },
        },
      ],
      // After math, so neither pass has to reason about KaTeX's markup.
      rehypeTables,
      rehypeGlossary,
    ],
    shikiConfig: {
      themes: { light: "github-light", dark: "github-dark" },
      wrap: true,
    },
    // Curly quotes and proper dashes in prose.
    smartypants: true,
    gfm: true,
  },
});
