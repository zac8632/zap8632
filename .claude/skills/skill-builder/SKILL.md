---
name: skill-builder
description: Build a new Claude skill from the current conversation or a spec. Writes the SKILL.md with proper frontmatter, names it, writes a trigger-optimised description, and packages it ready to install. Triggers on "/skill-builder", "/build-skill", "/make-this-a-skill", "turn this into a skill", "make this a skill", "skill this", "package this as a skill", or any time the creator wants to capture a workflow as a reusable skill. The meta skill that builds the others.
---

# Skill Builder

The skill that builds other skills. The infrastructure for the whole system.

## When to run this

- A workflow just worked in chat and should be repeatable
- Skill Opportunity Finder flagged a candidate
- An idea for a skill needs packaging
- An existing skill needs editing

## Modes

**From current conversation:** extract the workflow you just did, build the skill from it.
**From spec:** the creator describes the skill, you build it.

## Inputs

Optional:
- Existing skills to disambiguate triggers against
- A reference SKILL.md to match style

## SKILL.md anatomy

```
---
name: kebab-case-name
description: [Triggering-optimised paragraph with 5+ trigger phrases]
---

# Human-readable name
## When to run this
## Inputs
## Output structure
## Process
## Critical rules
```

## Description-writing principles

The description is the only thing Claude sees when deciding to trigger. It must:
1. Open with what the skill does
2. List 5+ trigger phrases explicitly
3. Name the contexts where it applies
4. Be slightly pushy — instruct triggering even without the exact name

## Process

1. Identify source: conversation or spec
2. If from conversation, summarise the pattern and confirm before writing
3. Name (kebab-case)
4. Write the description per the principles
5. Write the body (when to run, inputs, output, process, rules)
6. Output the complete SKILL.md as a code block + save the file
7. Give the install path
8. Offer a test prompt

## Critical rules

- Confirm the workflow before writing — never invent intent.
- Description MUST list 5+ trigger phrases.
- "Critical rules" section is non-negotiable in every skill built.
- Name is kebab-case — no spaces, underscores, capitals.
- Flag overlaps with existing skills — propose merge, replace, or differentiate.
- Output as code block AND save the file.
- Always offer a test prompt.
- Bridge the gap from "thinking about a skill" to "having a skill" — don't leave them at the spec stage.
