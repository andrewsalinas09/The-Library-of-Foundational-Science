#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Convert plain-text engineering notation into LaTeX across the library.

The documents were authored before the reader could render math, so they spell
formulas in ASCII: `10^-12`, `4.0 × 10^-21`, `σ / √N`, `10·log10(...)`,
`minus 130 dBm`. All of that now renders properly, so this rewrites it once.

    uv run tools/mathify.py            # dry run: report every proposed change
    uv run tools/mathify.py --apply    # write the files

Frontmatter, fenced code, and text already inside $...$ are never touched.
Units stay as prose (`ns`, `kΩ`, `pF`, `dBm`); only the quantities become math,
which is the usual engineering convention and keeps KaTeX out of the units.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

# Sentinel that cannot occur in the source, used to hide protected spans.
GUARD = "\x00{}\x00"


def protect(text: str) -> tuple[str, list[str]]:
    """Replace spans that must not be rewritten with opaque placeholders."""
    stash: list[str] = []

    def keep(match: re.Match) -> str:
        stash.append(match.group(0))
        return GUARD.format(len(stash) - 1)

    # Order matters: frontmatter, then fenced code, then inline code, then math.
    text = re.sub(r"\A---\n.*?\n---\n", keep, text, count=1, flags=re.S)
    text = re.sub(r"^```.*?^```", keep, text, flags=re.S | re.M)
    # Headings stay plain text. Their content is reused as the sidebar entry,
    # the anchor slug, link text, and search results, none of which render
    # LaTeX; a Unicode √ reads correctly in every one of those places.
    text = re.sub(r"^#{1,6} .*$", keep, text, flags=re.M)
    text = re.sub(r"`[^`\n]+`", keep, text)
    text = re.sub(r"\$\$.+?\$\$", keep, text, flags=re.S)
    text = re.sub(r"(?<!\$)\$[^$\n]+\$(?!\$)", keep, text)
    return text, stash


def restore(text: str, stash: list[str]) -> str:
    for index, original in enumerate(stash):
        text = text.replace(GUARD.format(index), original)
    return text


# --------------------------------------------------------------------- units
# Units must render upright. Writing `$nV/\sqrt{Hz}$` italicises them, so the
# reader sees the product of variables n, V, H and z rather than nanovolts per
# root hertz. \text{} keeps them upright and copes with µ and Ω directly.

UNITS = {
    "Hz", "kHz", "MHz", "GHz", "THz",
    "s", "ms", "µs", "ns", "ps",
    "V", "mV", "µV", "nV", "kV",
    "W", "mW", "µW", "nW", "kW",
    "A", "mA", "µA",
    "F", "pF", "nF", "µF",
    "Ω", "kΩ", "MΩ",
    "K", "J", "C",
    "m", "km", "cm", "mm", "nm",
    "dB", "dBm", "dBW", "dBc", "dBi",
    "ppm", "ppb", "ppt",
    "bit", "bits", "LSB", "sps",
}

SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def token(value: str) -> str:
    """Render one token: units upright, everything else as a math variable."""
    return f"\\text{{{value}}}" if value in UNITS else value


def _term(value: str) -> str:
    """Render one side of a ratio, e.g. `2,046,000 Hz` or `chip rate`."""
    value = value.strip()
    match = re.fullmatch(r"([\d.,]+)\s*([A-Za-zµΩ]+)?", value)
    if match:
        # Bare commas get thousands-separator spacing in math mode; {,} fixes it.
        number = match.group(1).replace(",", "{,}")
        unit = match.group(2)
        return f"{number}\\,{token(unit)}" if unit else number
    return f"\\text{{{value}}}"


def _argument(value: str) -> str:
    """Render a logarithm's argument, which is nearly always a ratio."""
    if "/" in value:
        left, _, right = value.partition("/")
        return f"{_term(left)} / {_term(right)}"
    return _term(value)


# --------------------------------------------------------------------- rules
# Each rule is (name, pattern, replacement); a replacement may be a callable
# taking the match. Order is significant: the most specific patterns must run
# before the general ones so they are not half-consumed.

RULES: list[tuple[str, str, object]] = [
    # --- named formulas, most specific first -------------------------------
    # remark-math only treats $$ as display when the delimiters sit on their
    # own lines; `$$x$$` inline renders at text size, which is not what a
    # standalone formula wants.
    (
        "sigma-average formula",
        r"\*\*σ_average\s*=\s*σ\s*/\s*√N\.?\*\*",
        "$$\n\\\\sigma_{\\\\text{avg}} = \\\\frac{\\\\sigma}{\\\\sqrt{N}}\n$$",
    ),
    (
        "thermal noise formula",
        r"^>\s*N\s*=\s*k\s*T\s*B\s*$",
        "$$\nN = kTB\n$$\n",
    ),
    ("Ohm's law", r"\bI = V/R\b", r"$I = V/R$"),
    ("capacitor law", r"\bV = Q/C\b", r"$V = Q/C$"),
    # --- decibel logarithms -------------------------------------------------
    (
        "10·log10(...)",
        r"10·log10\(([^)]*)\)",
        lambda m: "$10\\log_{10}(" + _argument(m.group(1)) + ")$",
    ),
    ("bare log10", r"\blog10\b", r"$\\log_{10}$"),
    # --- scientific notation ------------------------------------------------
    (
        "coefficient × power",
        r"(?<![\w.])(\d+(?:\.\d+)?)\s*×\s*10\^(-?\d+)",
        r"$\1 \\times 10^{\2}$",
    ),
    (
        "bare power of ten",
        r"(?<![\w.^{])\b(\d+)\^(-?\d+)",
        r"$\1^{\2}$",
    ),
    # --- units carrying an exponent, e.g. V²/Hz -----------------------------
    (
        "unit ratio with exponent",
        r"\b([A-Za-zµΩ]{1,3})([²³])\s*/\s*([A-Za-zµΩ]{1,3})\b",
        lambda m: (
            f"${token(m.group(1))}^{m.group(2).translate(SUPERSCRIPT)}"
            f"/{token(m.group(3))}$"
        ),
    ),
    # --- roots --------------------------------------------------------------
    (
        "sigma over root",
        r"σ\s*/\s*√([A-Za-z0-9]+)",
        lambda m: f"$\\sigma/\\sqrt{{{token(m.group(1))}}}$",
    ),
    (
        "quantity over root",
        # Left side restricted to a single letter, a number, or a known unit,
        # so an English article is never mistaken for a variable.
        r"(?<![\w$])([A-Za-z]|\d+(?:\.\d+)?|µ?[A-Za-z]{1,3})\s*/\s*√([A-Za-z0-9]+)",
        lambda m: f"${token(m.group(1))}/\\sqrt{{{token(m.group(2))}}}$",
    ),
    (
        "root of quantity",
        r"√\(?([A-Za-z0-9]+)\)?",
        lambda m: f"$\\sqrt{{{token(m.group(1))}}}$",
    ),
    # --- Unicode superscripts on variables ---------------------------------
    (
        "variable with superscript",
        r"(?<![\w$])([A-Za-zσ])([²³⁸])",
        lambda m: (
            "$"
            + ("\\sigma" if m.group(1) == "σ" else m.group(1))
            + f"^{m.group(2).translate(SUPERSCRIPT)}$"
        ),
    ),
    (
        # The decimal point must be inside the capture, or `0.2²` becomes
        # `0.$2^{2}$` with the leading digits stranded outside the math.
        "number with superscript",
        r"(?<![\w$.])(\d+(?:\.\d+)?)([²³⁸])",
        lambda m: f"${m.group(1)}^{{{m.group(2).translate(SUPERSCRIPT)}}}$",
    ),
    # --- negative decibels: spelled-out minus becomes a real minus sign ------
    (
        "minus before dB unit",
        r"\bminus\s+(\d+(?:\.\d+)?)\s*(dBm/Hz|dB-Hz|dBm|dBW|dBc|dB)\b",
        "−" + r"\1 \2",
    ),
    (
        "minus before bare number in dB context",
        r"\bminus\s+(\d+(?:\.\d+)?)\b(?=[,.]?\s+(?:and|to|dBm|dBW|is|means))",
        "−" + r"\1",
    ),
    # --- Greek used as a variable ------------------------------------------
    ("sigma equals", r"σ\s*=\s*(\d+(?:\.\d+)?)", r"$\\sigma = \1$"),
    ("tau variable", r"(?<![\w$])τ(?![\w])", r"$\\tau$"),
    ("sigma variable", r"(?<![\w$_])σ(?![\w])", r"$\\sigma$"),
    ("capital delta", r"\(Δ\)", r"($\\Delta$)"),
    ("capital sigma", r"\(Σ\)", r"($\\Sigma$)"),
]

COMPILED = [(name, re.compile(pattern, re.M), repl) for name, pattern, repl in RULES]


def convert(text: str) -> tuple[str, Counter, dict[str, list[tuple[str, str]]]]:
    text, stash = protect(text)
    counts: Counter = Counter()
    samples: dict[str, list[tuple[str, str]]] = {}

    for name, pattern, replacement in COMPILED:
        def swap(match: re.Match, _name=name, _repl=replacement) -> str:
            new = _repl(match) if callable(_repl) else match.expand(_repl)
            counts[_name] += 1
            samples.setdefault(_name, [])
            if len(samples[_name]) < 3:
                samples[_name].append((match.group(0), new))
            return new

        text = pattern.sub(swap, text)

    text = merge_spans(text)
    return restore(text, stash), counts, samples


OPERATORS = {"·": r"\cdot", "×": r"\times"}


def merge_spans(text: str) -> str:
    """Join neighbouring math spans into single expressions.

    The rules above convert fragments, so `N·a / √N = √N · a` would otherwise
    come out as `N·$a/\\sqrt{N}$ = $\\sqrt{N}$ · a`: half typeset, half not, and
    worse than leaving it alone. Absorbing the operators and bare operands on
    either side produces one span that reads as the equation it is.
    """
    patterns = [
        # $a$ · $b$  ->  $a \cdot b$
        (r"\$([^$\n]+?)\$\s*([·×])\s*\$([^$\n]+?)\$",
         lambda m: f"${m.group(1)} {OPERATORS[m.group(2)]} {m.group(3)}$"),
        # N· $a$  ->  $N \cdot a$
        (r"(?<![\w$\\])([A-Za-z0-9]+)\s*([·×])\s*\$([^$\n]+?)\$",
         lambda m: f"${m.group(1)} {OPERATORS[m.group(2)]} {m.group(3)}$"),
        # $a$ ·N  ->  $a \cdot N$
        (r"\$([^$\n]+?)\$\s*([·×])\s*([A-Za-z0-9]+)(?![\w$])",
         lambda m: f"${m.group(1)} {OPERATORS[m.group(2)]} {m.group(3)}$"),
        # $a$ = $b$  ->  $a = b$
        (r"\$([^$\n]+?)\$\s*=\s*\$([^$\n]+?)\$",
         lambda m: f"${m.group(1)} = {m.group(2)}$"),
        # $a$ / $b$  ->  $a/b$
        (r"\$([^$\n]+?)\$\s*/\s*\$([^$\n]+?)\$",
         lambda m: f"${m.group(1)}/{m.group(2)}$"),
        # √($10^{6}$)  ->  $\sqrt{10^{6}}$   (the power rule ran first)
        (r"√\(\$([^$\n]+?)\$\)",
         lambda m: f"$\\sqrt{{{m.group(1)}}}$"),
        # Collapse a stray empty gap left by an earlier merge.
        (r"\$\s+\$", " "),
    ]

    for _ in range(4):  # a handful of passes reaches a fixed point
        before = text
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        if text == before:
            break
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the files")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()

    targets = [
        p.resolve() for p in (args.paths or sorted(DOCS.rglob("*.md")) + sorted(DOCS.rglob("*.mdx")))
    ]
    total: Counter = Counter()

    for path in targets:
        original = path.read_text(encoding="utf-8")
        updated, counts, samples = convert(original)
        total.update(counts)

        if not counts:
            continue

        print(f"\n{path.relative_to(ROOT).as_posix()}  ({sum(counts.values())} changes)")
        for name, count in counts.most_common():
            print(f"  {count:>4}  {name}")
            for before, after in samples.get(name, []):
                before_flat = before.replace("\n", " ")[:58]
                print(f"          {before_flat!r}  ->  {after[:58]!r}")

        if args.apply:
            path.write_text(updated, encoding="utf-8")

    print(f"\nTotal: {sum(total.values())} changes across {len(targets)} document(s).")
    if not args.apply:
        print("Dry run. Re-run with --apply to write.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
