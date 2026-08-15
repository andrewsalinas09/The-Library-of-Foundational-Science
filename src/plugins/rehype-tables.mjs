import { visit, SKIP } from "unist-util-visit";

/**
 * Wrap every table so wide ones scroll inside their own box instead of
 * forcing the page body to scroll horizontally. The worked-example tables in
 * this library run to seven numeric columns, which overflows the reading
 * measure on any phone.
 */
export function rehypeTables() {
  return (tree) => {
    visit(tree, "element", (node, index, parent) => {
      if (node.tagName !== "table") return;
      if (!parent || typeof index !== "number") return;

      const className = parent.properties?.className;
      const alreadyWrapped =
        parent.type === "element" &&
        parent.tagName === "div" &&
        Array.isArray(className) &&
        className.includes("table-wrap");
      if (alreadyWrapped) return;

      parent.children[index] = {
        type: "element",
        tagName: "div",
        properties: { className: ["table-wrap"], tabindex: "0", role: "region" },
        children: [node],
      };

      return [SKIP, index + 1];
    });
  };
}

export default rehypeTables;
