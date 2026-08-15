import { visit } from "unist-util-visit";

/**
 * Hand ```mermaid fences straight to the browser as `<pre class="mermaid">`
 * instead of letting Shiki syntax-highlight them into oblivion.
 *
 * This runs in remark, before Astro's rehype-stage highlighter ever sees the
 * node, which is simpler than trying to undo highlighting afterwards.
 *
 * The Mermaid bundle is ~3.5 MB, so it is loaded by an island that only
 * renders on pages where `needsMermaid` is set. A document with no diagram
 * ships no diagram code.
 */
function escapeHtml(value) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function remarkMermaid() {
  return (tree, file) => {
    let found = 0;

    visit(tree, "code", (node, index, parent) => {
      if (node.lang !== "mermaid" || !parent || typeof index !== "number") return;
      found += 1;
      parent.children[index] = {
        type: "html",
        value:
          `<figure class="diagram">` +
          `<pre class="mermaid">${escapeHtml(node.value)}</pre>` +
          (node.meta ? `<figcaption>${escapeHtml(node.meta)}</figcaption>` : "") +
          `</figure>`,
      };
    });

    // Recorded here rather than in remark-reading-data, because this plugin
    // consumes the ```mermaid fences: by the time any later plugin runs there
    // are no mermaid code nodes left to count.
    const data = file.data ?? (file.data = {});
    const astro = data.astro ?? (data.astro = {});
    const frontmatter = astro.frontmatter ?? (astro.frontmatter = {});
    frontmatter.mermaidBlocks = found;
    frontmatter.needsMermaid = found > 0;
  };
}

export default remarkMermaid;
