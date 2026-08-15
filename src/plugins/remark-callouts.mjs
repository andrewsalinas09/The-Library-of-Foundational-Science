import { visit } from "unist-util-visit";

/**
 * Callout blocks, authored with remark-directive syntax:
 *
 *   :::key
 *   The precision was never in the scale. It emerged from the history
 *   of corrections.
 *   :::
 *
 *   :::objection[But surely the error has to go somewhere?]
 *   It went fast. ...
 *   :::
 *
 * The house style leans on a few recurring rhetorical moves, so the types
 * here are named after those moves rather than after generic severities.
 * `key` is for the ownership-of-property sentences the style guide asks the
 * author to hunt for; `objection` is for the "the question that should be
 * nagging you" turn.
 */
const TYPES = {
  key: "Key idea",
  note: "Note",
  aside: "Aside",
  caution: "Caution",
  history: "History",
  objection: "The objection",
  vocabulary: "Vocabulary hook",
};

/** Flatten a node's text content without pulling in mdast-util-to-string. */
function textOf(node) {
  if (!node) return "";
  if (typeof node.value === "string") return node.value;
  if (!Array.isArray(node.children)) return "";
  return node.children.map(textOf).join("");
}

export function remarkCallouts() {
  return (tree) => {
    visit(tree, (node) => {
      if (node.type !== "containerDirective" && node.type !== "leafDirective") {
        return;
      }
      const name = node.name;
      if (!Object.prototype.hasOwnProperty.call(TYPES, name)) return;

      // remark-directive parses `:::key[Some title]` into a leading paragraph
      // flagged as the directive label. Promote it to the callout heading.
      let title = TYPES[name];
      const first = node.children?.[0];
      if (first && first.type === "paragraph" && first.data?.directiveLabel) {
        const label = textOf(first).trim();
        if (label) title = label;
        node.children.shift();
      }

      node.data = {
        ...(node.data ?? {}),
        hName: "aside",
        hProperties: {
          className: ["callout", `callout--${name}`],
          "data-callout": name,
          "data-title": title,
        },
      };
    });
  };
}

export default remarkCallouts;
