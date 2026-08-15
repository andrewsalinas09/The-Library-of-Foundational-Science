# First-Principles Deep Explainer Prompt

Paste everything below the line, then your topic/question, plus any context or documents.

---

I want a long-form, first-principles explanation of the topic I give you below. Follow this specification exactly.

## The core contract

Build the explanation literally from zero. Assume I am highly intelligent but know NOTHING about this field, not even its most basic vocabulary. If the topic were electronics, you would have to explain what a capacitor is before using the word; if it were biology, what a protein is; if it were finance, what a bond is. Identify every concept the explanation depends on, trace each one down to its foundations, and build upward from there. Leave no stone unturned: every load-bearing idea gets built, not name-dropped. Never say "as you may know" or lean on prior knowledge. The test: a smart person from a completely different field can follow every single step without ever feeling a gap was jumped.

## Structure and length

Produce a markdown file of roughly 8,000–10,000 words unless I say otherwise. Organize it as:

1. **A preface stating the punchline up front** — the surprising claim, result, or capability we are going to earn, stated concretely (with numbers or specifics if possible), so the reader knows the destination before the journey. The document's promise is that this claim will go from sounding like magic to feeling inevitable.
2. **Part I: Raw materials** — every foundational concept, built one at a time, each section earning its place. For each concept: what it IS physically/concretely, the governing relationship in plain words BEFORE any equation, and a flag for which property will be load-bearing later ("hold this thought," "remember this number").
3. **Part II: The mechanism** — the actual idea, built stepwise. Critically: start with the naive approach and show exactly WHY it fails, because the failure mode points at the fix. Then introduce the fix through a complete physical analogy (see below), then translate the analogy into the real thing element-by-element, ideally with an explicit mapping table (analogy element → real element → where it appears in my specific context/documents).
4. **A worked numerical example** — actually run the mechanism with concrete numbers, small enough to trace by hand, in a table if appropriate. Let me watch the numbers move and verify the punchline arithmetic myself.
5. **The deep part** — whatever the profound/counterintuitive core of the topic is (the "where did the error go" moment), given its own section with mechanical intuition first and standard technical accounting second, so I know both why it works and what the field's quantitative claims are.
6. **The real-world instance** — if I provided documents, schematics, code, papers, or a specific product/system, pin the abstract story to it in detail: name the actual components/variables/clauses, quote the identifying details, and show how each maps to the story.
7. **The fine print** — honest limitations, trade-offs, failure modes, and the boundaries of where this idea applies. What currency does the trick spend, and why does this particular application have that currency in surplus? Do not sell me a free lunch.
8. **The idea underneath the idea** — zoom out to the general principle, show 4–6 other places in the world where the same pattern appears (the more distant the domains, the better), and give a paragraph of real history: who invented it, when, and crucially WHY it waited until it did (what economic/technological inversion made it viable).
9. **A glossary appendix** — every term of art defined in one line, in one place.

## Style rules

- Analogies must be COMPLETE and load-bearing, not decorative. One central analogy carried through the whole document (like weighing a fish with a balance scale, or water in buckets) beats ten scattered ones. The analogy must be exact enough that the real mechanism is just the analogy transcribed, and you must show that transcription explicitly.
- Physical intuition before mathematics, always. Equations may appear, but only after the plain-words version, and only when they compress rather than replace understanding. Prefer "the flow shrinks as the gap it's erasing shrinks, so of course it's exponential" over handing me e^(−t/τ).
- When something emerges from the mechanism (precision, stability, an invariant), state WHERE it lives with full force: "the precision was never in the scale; it emerged from the history of corrections." Hunt for these ownership-of-property statements; they are the sentences that reorganize a reader's head.
- Prose-first. Headers and the occasional table are fine; avoid bullet-point-itis. Write flowing paragraphs that build.
- Never use em dashes.
- Bold sparingly, only for genuinely load-bearing sentences.
- Numbers make things real: costs, speeds, sizes, dates. Use concrete figures whenever they exist ("a one-cent capacitor," "seven nanoseconds," "1962").
- Vocabulary notes in passing: when a concept I just learned has a standard name or a famous instance I've unknowingly met before (PDM = MEMS microphones; density-averaging = LED dimmers), tell me, so the new knowledge hooks into things I already own.
- Anticipate the objection. At the moment a thoughtful reader would think "wait, but that can't work because X," raise X explicitly and resolve it ("the question that should be nagging you...").
- End sections that earned something by auditing what was earned ("step back and audit where the precision came from: not the capacitor... not the resistors... it came from the clock and arithmetic").

## Process

Before writing, if anything is ambiguous — my background level in adjacent fields, the specific angle I care about, which documents matter most, desired length — ask me your clarifying questions FIRST in a short list, wait for my answers, and only then produce the document. If nothing is ambiguous, just write it.

Deliver as a downloadable .md file.

---

## MY TOPIC / QUESTION:

[paste here]

## CONTEXT / DOCUMENTS:

[paste here]
