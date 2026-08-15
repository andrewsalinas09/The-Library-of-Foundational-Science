#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Prose lint for the Library of Foundational Science.

Astro's Zod schema already validates frontmatter and fails the build on a bad
tag, so this tool deliberately does not repeat that. It checks the things a
schema cannot see: whether the document actually follows the house style in
first_principles_explainer_prompt.md.

    uv run tools/lint.py                 # check every document
    uv run tools/lint.py docs/foo.md     # check one
    uv run tools/lint.py --strict        # warnings become failures

Exit code is non-zero when errors are found (or warnings, under --strict), so
it drops straight into a pre-commit hook or CI step.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REGISTRY = ROOT / "ideas.yaml"

# House style, from first_principles_explainer_prompt.md.
WORD_TARGET = (8000, 10000)

# The nine-section spine. Each entry is (label, pattern matched against any
# heading, required?).
SPINE: list[tuple[str, str, bool]] = [
    ("preface", r"\bpreface\b", True),
    ("Part I (raw materials)", r"^part\s+i\b|raw materials", True),
    ("Part II (the mechanism)", r"^part\s+ii\b|the mechanism", True),
    ("worked numerical example", r"worked|watching it run|by hand", True),
    ("the deep part", r"deep part|actually lives|where the .*(went|lives)", False),
    ("real-world instance", r"real.?world|in the wild|the real board|instances", False),
    ("the fine print", r"fine print", True),
    ("the idea underneath the idea", r"idea underneath", True),
    ("glossary appendix", r"glossary|vocabulary", True),
]

SEVERITY_ORDER = {"error": 0, "warn": 1, "info": 2}


@dataclass
class Finding:
    severity: str
    line: int
    message: str


@dataclass
class Document:
    path: Path
    meta: dict
    body: str
    body_offset: int
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, line: int, message: str) -> None:
        self.findings.append(Finding(severity, line, message))


# --------------------------------------------------------------------- parse

FRONTMATTER = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.S)
FENCE = re.compile(r"^(```|~~~)")


def load(path: Path) -> Document | None:
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER.match(raw)
    if not match:
        doc = Document(path, {}, raw, 0)
        doc.add("error", 1, "No YAML frontmatter. Astro cannot load this file.")
        return doc

    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        doc = Document(path, {}, raw, 0)
        doc.add("error", 1, f"Frontmatter is not valid YAML: {exc}")
        return doc

    offset = raw[: match.end()].count("\n")
    return Document(path, meta, raw[match.end():], offset)


def prose_lines(doc: Document) -> list[tuple[int, str]]:
    """Body lines outside fenced code blocks, with 1-based file line numbers."""
    out: list[tuple[int, str]] = []
    in_fence = False
    for index, line in enumerate(doc.body.splitlines()):
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append((doc.body_offset + index + 1, line))
    return out


def headings(doc: Document) -> list[tuple[int, int, str]]:
    """(line number, depth, text) for every ATX heading outside code fences."""
    found = []
    for line_no, line in prose_lines(doc):
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            found.append((line_no, len(match.group(1)), match.group(2).strip()))
    return found


# --------------------------------------------------------------------- checks


def check_headings(doc: Document) -> None:
    """Numbered sections must all sit at the same level, below their Part."""
    numbered_depths: dict[int, list[tuple[int, str]]] = {}

    for line_no, depth, text in headings(doc):
        if re.match(r"^\d+\.", text):
            numbered_depths.setdefault(depth, []).append((line_no, text))
        elif depth == 1 and not re.match(r"^(part|appendix)\b", text, re.I):
            doc.add(
                "warn",
                line_no,
                f'Top-level "# {text}" is neither a Part nor an Appendix. '
                "Only Parts and the Appendix belong at h1.",
            )

    if len(numbered_depths) > 1:
        majority = max(numbered_depths, key=lambda d: len(numbered_depths[d]))
        for depth, entries in sorted(numbered_depths.items()):
            if depth == majority:
                continue
            for line_no, text in entries:
                doc.add(
                    "error",
                    line_no,
                    f'Section "{text}" uses {"#" * depth} but most sections use '
                    f'{"#" * majority}. The sidebar recovers from this, but the '
                    "document outline is wrong.",
                )


def check_spine(doc: Document) -> None:
    texts = [text.lower() for _, _, text in headings(doc)]
    if not texts:
        return
    for label, pattern, required in SPINE:
        if any(re.search(pattern, text, re.I) for text in texts):
            continue
        doc.add(
            "error" if required else "info",
            1,
            f"No section matching the house-style element: {label}.",
        )


def check_em_dashes(doc: Document) -> None:
    for line_no, line in prose_lines(doc):
        if "—" in line:
            column = line.index("—")
            excerpt = line[max(0, column - 34) : column + 35].strip()
            doc.add(
                "warn",
                line_no,
                f'Em dash (style guide forbids these): "...{excerpt}..."',
            )


def check_word_count(doc: Document) -> None:
    words = 0
    for _, line in prose_lines(doc):
        if line.lstrip().startswith(("#", "|", ">")):
            continue
        words += len(re.findall(r"\b[\w'-]+\b", line))

    low, high = WORD_TARGET
    if words < low:
        doc.add("warn", 1, f"{words:,} words, below the {low:,}-word house target.")
    elif words > high * 1.25:
        doc.add(
            "info",
            1,
            f"{words:,} words, well past the {high:,}-word target. "
            "Consider whether it wants splitting.",
        )


def check_dollar_signs(doc: Document) -> None:
    """Unescaped currency will be eaten by single-dollar math parsing."""
    for line_no, line in prose_lines(doc):
        stripped = re.sub(r"\$\$.*?\$\$", "", line)
        stripped = re.sub(r"(?<!\\)\$[^$\n]{1,120}?(?<!\\)\$", "", stripped)
        for match in re.finditer(r"(?<!\\)\$(?=\d)", stripped):
            doc.add(
                "warn",
                line_no,
                f'Unescaped "$" before a digit at column {match.start() + 1}. '
                "Write \\$ so it is not parsed as inline math.",
            )


def check_glossary(doc: Document, pedantic: bool = False) -> None:
    """Cross-check the glossary appendix against bolded terms in the body.

    The house style bolds two very different things: terms of art on first use,
    and whole load-bearing sentences. Only the former belong in the glossary,
    and no heuristic separates them cleanly, so by default this reports a count
    and leaves the judgement to the author. `--pedantic` lists every candidate.
    """
    body = doc.body
    split = re.split(r"^#{1,6}\s*(?:appendix|.*glossary).*$", body, flags=re.I | re.M)
    if len(split) < 2:
        # Some documents run the appendix as a bare paragraph.
        parts = re.split(r"^\*?appendix[:\s]", body, flags=re.I | re.M)
        if len(parts) < 2:
            doc.add("error", 1, "No glossary appendix found.")
            return
        main, appendix = parts[0], "".join(parts[1:])
    else:
        main, appendix = split[0], "".join(split[1:])

    defined: set[str] = set()
    for match in re.finditer(r"\*\*(.+?)\*\*", appendix):
        for alias in re.split(r"\s*/\s*", match.group(1)):
            alias = re.sub(r"\([^)]*\)", "", alias).strip().lower()
            if alias:
                defined.add(alias)

    if not defined:
        doc.add("error", 1, "Glossary section contains no **bolded** headwords.")
        return

    seen: set[str] = set()
    candidates: list[tuple[int, str]] = []
    for match in re.finditer(r"\*\*(.+?)\*\*", main):
        term = match.group(1).strip()
        # Load-bearing sentences are bolded too; they are not glossary terms.
        if len(term) > 40 or len(term.split()) > 4 or term.endswith("."):
            continue
        key = re.sub(r"\([^)]*\)", "", term).strip().lower().rstrip(".,;:")
        if not key or key in seen or key in defined:
            continue
        if key.rstrip("s") in defined or f"{key}s" in defined:
            continue
        seen.add(key)
        line_no = doc.body_offset + body[: match.start()].count("\n") + 1
        candidates.append((line_no, term))

    if not candidates:
        return

    if pedantic:
        for line_no, term in candidates:
            doc.add("info", line_no, f'Bolded term "{term}" has no glossary entry.')
    else:
        preview = ", ".join(term for _, term in candidates[:4])
        doc.add(
            "info",
            candidates[0][0],
            f"{len(candidates)} bolded term(s) have no glossary entry "
            f"({preview}{', ...' if len(candidates) > 4 else ''}). "
            "Run with --pedantic to list them all.",
        )

    # Entries defined but never bolded in the body are usually leftovers.
    body_lower = main.lower()
    orphans = [term for term in sorted(defined) if f"**{term}" not in body_lower]
    if orphans:
        doc.add(
            "info",
            1,
            f"{len(orphans)} glossary entr(y/ies) never bolded in the body: "
            f"{', '.join(orphans[:5])}{', ...' if len(orphans) > 5 else ''}.",
        )


def check_registry(doc: Document, registry: dict) -> None:
    known_ideas = set((registry.get("ideas") or {}).keys())
    known_mech = set((registry.get("mechanisms") or {}).keys())

    for field_name, pool in (("ideas", known_ideas), ("mechanisms", known_mech)):
        for value in doc.meta.get(field_name) or []:
            if value not in pool:
                doc.add(
                    "error",
                    1,
                    f'{field_name}: "{value}" is not registered in ideas.yaml.',
                )


def check_analogy(doc: Document) -> None:
    if not doc.meta.get("analogy"):
        doc.add(
            "info",
            1,
            "No `analogy` in frontmatter. The house style asks for one central "
            "analogy carried through the whole document.",
        )


def check_wikilinks(doc: Document, known_slugs: set[str]) -> None:
    for line_no, line in prose_lines(doc):
        for match in re.finditer(r"\[\[([^\]|#]+)", line):
            slug = match.group(1).strip()
            if slug not in known_slugs:
                doc.add(
                    "info",
                    line_no,
                    f'Wikilink to "{slug}", which does not exist yet.',
                )


# --------------------------------------------------------------------- report

COLOURS = {"error": "\033[31m", "warn": "\033[33m", "info": "\033[36m"}
RESET = "\033[0m"


def report(docs: list[Document], use_colour: bool) -> tuple[int, int]:
    errors = warnings = 0

    for doc in docs:
        if not doc.findings:
            continue
        rel = doc.path.relative_to(ROOT).as_posix()
        print(f"\n{rel}")
        for finding in sorted(
            doc.findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.line)
        ):
            if finding.severity == "error":
                errors += 1
            elif finding.severity == "warn":
                warnings += 1
            tint = COLOURS[finding.severity] if use_colour else ""
            end = RESET if use_colour else ""
            print(
                f"  {tint}{finding.severity:>5}{end} "
                f"{rel}:{finding.line}  {finding.message}"
            )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--strict", action="store_true", help="warnings fail too")
    parser.add_argument("--pedantic", action="store_true", help="list every glossary candidate")
    parser.add_argument("--no-colour", action="store_true")
    args = parser.parse_args()

    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}

    targets = args.paths or sorted(DOCS.rglob("*.md")) + sorted(DOCS.rglob("*.mdx"))
    targets = [p for p in targets if not p.name.startswith("_")]
    if not targets:
        print("No documents found under docs/.")
        return 0

    known_slugs = {p.stem for p in targets}

    docs: list[Document] = []
    for path in targets:
        doc = load(path)
        if doc is None:
            continue
        if doc.meta:
            check_headings(doc)
            check_spine(doc)
            check_em_dashes(doc)
            check_word_count(doc)
            check_dollar_signs(doc)
            check_glossary(doc, pedantic=args.pedantic)
            check_registry(doc, registry)
            check_analogy(doc)
            check_wikilinks(doc, known_slugs)
        docs.append(doc)

    errors, warnings = report(docs, use_colour=not args.no_colour)

    print(
        f"\n{len(docs)} document(s): "
        f"{errors} error(s), {warnings} warning(s)."
    )
    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
