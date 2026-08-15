export interface RawHeading {
  depth: number;
  slug: string;
  text: string;
}

export interface TocSection {
  slug: string;
  text: string;
  /** Leading section number, when the heading carries one ("12"). */
  number: string | null;
}

export interface TocGroup {
  /** Anchor for the group heading itself, when it has one. */
  slug: string | null;
  title: string;
  sections: TocSection[];
}

const GROUP_PATTERN = /^(part\b|appendix\b)/i;
const NUMBERED_PATTERN = /^(\d+)\.\s*/;

/**
 * Turn a flat heading list into the two-level Part / Section structure the
 * house style actually uses.
 *
 * Deliberately tolerant of malformed source. `clock-discipline.md` promotes
 * its sections 12 through 16 to `#` where every other section is `##`, which
 * would otherwise render as five sibling documents in the sidebar. A heading
 * that *looks* like a numbered section is treated as one regardless of its
 * depth, so the reader stays correct while the Python lint reports the source
 * defect for the author to fix.
 */
export function buildToc(headings: RawHeading[]): TocGroup[] {
  const groups: TocGroup[] = [];
  let current: TocGroup | null = null;

  const openGroup = (group: TocGroup) => {
    groups.push(group);
    current = group;
  };

  for (const heading of headings) {
    const text = heading.text.trim();
    if (!text) continue;

    const isGroup = heading.depth <= 2 && GROUP_PATTERN.test(text);
    const numbered = NUMBERED_PATTERN.exec(text);

    if (isGroup && !numbered) {
      openGroup({ slug: heading.slug, title: text, sections: [] });
      continue;
    }

    // Anything numbered, or any depth-2 heading, is a section.
    const isSection = Boolean(numbered) || heading.depth === 2;
    if (!isSection) continue;

    if (!current) {
      // Sections appearing before the first Part (the preface, typically).
      openGroup({ slug: null, title: "", sections: [] });
    }

    current!.sections.push({
      slug: heading.slug,
      text: numbered ? text.slice(numbered[0].length) : text,
      number: numbered ? numbered[1] : null,
    });
  }

  return groups.filter((group) => group.sections.length > 0 || group.slug);
}

/**
 * Headings whose markdown level contradicts their role. Surfaced in dev so
 * the defect is visible while editing rather than only in a lint run.
 */
export function findHeadingDefects(headings: RawHeading[]): string[] {
  const defects: string[] = [];
  for (const heading of headings) {
    const text = heading.text.trim();
    if (heading.depth === 1 && NUMBERED_PATTERN.test(text)) {
      defects.push(`"${text}" is a numbered section but uses a single # (h1)`);
    }
  }
  return defects;
}
