import { visit } from "unist-util-visit";

/**
 * Turn the glossary appendix into live tooltips on the body text.
 *
 * The house style asks authors to bold a term of art on first use and then
 * define every one of them in a closing appendix. That convention is machine
 * readable, so nothing needs to be authored twice: this pass reads the
 * appendix, then attaches each definition to the matching bold run earlier in
 * the document. A reader who has forgotten what syntonized means hovers it
 * instead of scrolling to the bottom and losing their place.
 *
 * Two appendix shapes appear in the corpus and both are supported: a bullet
 * list of `**Term**: definition` items, and a single run-on paragraph of the
 * same pattern.
 */

/** Bold runs longer than this are load-bearing sentences, not terms. */
const MAX_TERM_LENGTH = 60;

const GLOSSARY_HEADING = /\b(glossary|vocabulary)\b|^appendix\b/i;

function textOf(node) {
  if (!node) return "";
  if (node.type === "text") return node.value;
  if (node.type === "element" || node.type === "root") {
    return (node.children ?? []).map(textOf).join("");
  }
  return "";
}

/** Normalise a term for matching: case, punctuation, and plural folding. */
function normalise(value) {
  let out = value
    .toLowerCase()
    .replace(/\([^)]*\)/g, " ")
    .replace(/[^\p{L}\p{N}\s/-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (out.endsWith("s") && !out.endsWith("ss") && out.length > 3) {
    out = out.slice(0, -1);
  }
  return out;
}

/**
 * A glossary headword may pack several aliases into one entry, as in
 * "Mean / variance / standard deviation (σ)" or "TCXO / OCXO".
 */
function aliasesFor(headword) {
  const aliases = new Set();
  const add = (value) => {
    const key = normalise(value);
    if (key.length >= 2) aliases.add(key);
  };

  add(headword);
  for (const piece of headword.split("/")) add(piece);
  // Also index the bare form of "Flicker (1/f) noise" style entries.
  add(headword.replace(/\([^)]*\)/g, " "));

  return aliases;
}

function isHeading(node) {
  return (
    node.type === "element" &&
    ["h1", "h2", "h3", "h4", "h5", "h6"].includes(node.tagName)
  );
}

/** Index of the child at which the glossary appendix begins, or -1. */
function findGlossaryStart(root) {
  const children = root.children ?? [];
  for (let i = 0; i < children.length; i++) {
    const node = children[i];
    if (isHeading(node) && GLOSSARY_HEADING.test(textOf(node).trim())) return i;
    // Some documents run the appendix as a bare italic paragraph with no
    // heading of its own.
    if (
      node.type === "element" &&
      node.tagName === "p" &&
      /^appendix\b/i.test(textOf(node).trim())
    ) {
      return i;
    }
  }
  return -1;
}

/**
 * Walk a container's children linearly, treating each <strong> as a headword
 * and everything up to the next <strong> as its definition.
 */
function harvest(container, into) {
  let term = null;
  let buffer = [];

  const flush = () => {
    if (!term) return;
    const definition = buffer
      .join("")
      .replace(/^\s*[:–-]\s*/, "")
      .replace(/\s+/g, " ")
      .trim();
    if (definition.length >= 3) {
      for (const alias of aliasesFor(term)) {
        if (!into.has(alias)) into.set(alias, definition);
      }
    }
    term = null;
    buffer = [];
  };

  for (const child of container.children ?? []) {
    if (child.type === "element" && child.tagName === "strong") {
      flush();
      term = textOf(child).trim();
      continue;
    }
    if (term) buffer.push(textOf(child));
  }
  flush();
}

export function rehypeGlossary() {
  return (tree, file) => {
    const start = findGlossaryStart(tree);
    if (start === -1) return;

    const definitions = new Map();
    for (const node of (tree.children ?? []).slice(start)) {
      if (node.type !== "element") continue;
      if (node.tagName === "ul" || node.tagName === "ol") {
        for (const item of node.children ?? []) {
          if (item.type === "element" && item.tagName === "li") {
            harvest(item, definitions);
          }
        }
      } else if (node.tagName === "p") {
        harvest(node, definitions);
      }
    }

    if (definitions.size === 0) return;

    // Only annotate body text, never the appendix itself.
    const body = { type: "root", children: (tree.children ?? []).slice(0, start) };

    let linked = 0;
    visit(body, "element", (node) => {
      if (node.tagName !== "strong") return;
      const raw = textOf(node).trim();
      if (!raw || raw.length > MAX_TERM_LENGTH) return;

      const definition = definitions.get(normalise(raw));
      if (!definition) return;

      node.properties = node.properties ?? {};
      const existing = node.properties.className;
      node.properties.className = Array.isArray(existing)
        ? [...existing, "gloss"]
        : ["gloss"];
      node.properties["data-def"] = definition;
      node.properties.tabIndex = 0;
      linked += 1;
    });

    const frontmatter = file?.data?.astro?.frontmatter;
    if (frontmatter) {
      frontmatter.glossaryTerms = definitions.size;
      frontmatter.glossaryLinked = linked;
    }
  };
}

export default rehypeGlossary;
