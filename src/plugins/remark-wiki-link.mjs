import { visit, SKIP } from "unist-util-visit";

/**
 * Obsidian-style cross-references between library documents:
 *
 *   [[clock-discipline]]                     -> link, label is the slug
 *   [[clock-discipline|the disciplined clock]] -> link with custom label
 *   [[clock-discipline#the-fine-print]]      -> link to a section
 *
 * Links are emitted unconditionally, including to documents that do not
 * exist yet. That is deliberate: a dangling wikilink marks something worth
 * writing rather than an error. The Python lint reports them as a worklist,
 * and the rendered link carries `data-wikilink` so the layout can style a
 * dangling target differently once it knows the full document set.
 */
const PATTERN = /\[\[([^\]|#]+?)(?:#([^\]|]+?))?(?:\|([^\]]+?))?\]\]/g;

function slugify(value) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .replace(/\s+/g, "-");
}

export function remarkWikiLink() {
  return (tree) => {
    visit(tree, "text", (node, index, parent) => {
      if (!parent || typeof index !== "number") return;
      if (!node.value.includes("[[")) return;

      const out = [];
      let cursor = 0;
      let match;
      PATTERN.lastIndex = 0;

      while ((match = PATTERN.exec(node.value)) !== null) {
        const [full, rawSlug, rawHash, rawLabel] = match;
        if (match.index > cursor) {
          out.push({ type: "text", value: node.value.slice(cursor, match.index) });
        }

        const slug = rawSlug.trim();
        const url = `/${slug}/${rawHash ? `#${slugify(rawHash)}` : ""}`;

        out.push({
          type: "link",
          url,
          children: [{ type: "text", value: (rawLabel ?? rawSlug).trim() }],
          data: {
            hProperties: {
              className: ["wikilink"],
              "data-wikilink": slug,
            },
          },
        });

        cursor = match.index + full.length;
      }

      if (out.length === 0) return;
      if (cursor < node.value.length) {
        out.push({ type: "text", value: node.value.slice(cursor) });
      }

      parent.children.splice(index, 1, ...out);
      // Skip the nodes we just inserted so the visitor does not rescan them.
      return [SKIP, index + out.length];
    });
  };
}

export default remarkWikiLink;
