import { visit } from "unist-util-visit";

/**
 * Derive reading statistics and stash them on the frontmatter object Astro
 * exposes as `remarkPluginFrontmatter`.
 *
 * These are computed rather than authored because authored counts go stale
 * the moment anyone edits a paragraph. The house style targets 8,000-10,000
 * words, so `wordCount` is the field that tells you whether a draft is
 * actually finished; the Python lint reads the same numbers to report
 * documents that have drifted out of range.
 */

/** Words per minute for dense technical prose read carefully, not skimmed. */
const READING_SPEED = 200;

export function remarkReadingData() {
  return (tree, file) => {
    let words = 0;
    let emDashes = 0;
    let boldRuns = 0;
    let mathNodes = 0;
    let tables = 0;

    visit(tree, (node) => {
      switch (node.type) {
        case "text": {
          const found = node.value.match(/\S+/g);
          if (found) words += found.length;
          // The style guide forbids em dashes outright, so count rather than
          // silently normalise; the author should decide the rewrite.
          const dashes = node.value.match(/—/g);
          if (dashes) emDashes += dashes.length;
          break;
        }
        case "strong":
          boldRuns += 1;
          break;
        case "inlineMath":
        case "math":
          mathNodes += 1;
          break;
        case "table":
          tables += 1;
          break;
        default:
          break;
      }
    });

    const data = file.data ?? (file.data = {});
    const astro = data.astro ?? (data.astro = {});
    const frontmatter = astro.frontmatter ?? (astro.frontmatter = {});

    frontmatter.wordCount = words;
    frontmatter.readingMinutes = Math.max(1, Math.round(words / READING_SPEED));
    frontmatter.emDashCount = emDashes;
    frontmatter.boldRuns = boldRuns;
    frontmatter.mathNodes = mathNodes;
    frontmatter.tableCount = tables;
    // `mermaidBlocks` and `needsMermaid` are set by remark-mermaid, which runs
    // earlier and consumes the fences before this plugin could see them.
  };
}

export default remarkReadingData;
