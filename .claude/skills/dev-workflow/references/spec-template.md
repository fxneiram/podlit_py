# Spec template

Save as `specs/<branch-slug>.md`. Keep it short enough to actually get read — this is a
working contract for the tests and the self-review, not a design document to impress anyone.

```markdown
# <Title>

Source: <GitHub issue URL, or "user instruction" + one-line paraphrase>
Branch: <feature|fix>/<slug>

## Problem / goal
What's broken or missing, in 1-3 sentences. Why it matters if that's not obvious.

## Scope
What this change does and does not cover. Be explicit about the "does not" — that's what
prevents scope creep during implementation and gives the self-review something to check against.

## Acceptance criteria
Numbered, testable statements. Every one of these should map to at least one unit or
integration test later.

1. ...
2. ...

## Edge cases / open questions
Anything ambiguous in the source issue/instruction, resolved here after asking the user.
If nothing was ambiguous, write "none".

## Out of scope
Explicitly excluded related work, so future readers don't wonder why it's missing.
```
