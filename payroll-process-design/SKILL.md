---
name: payroll-process-design
description: 'Design, reformat, or improve a payroll process document. Use this skill whenever someone uploads or pastes a payroll checklist, pay run procedure, or process document and wants it improved, restructured, or formalised. Also triggers when someone wants to build a new payroll process from scratch. Trigger phrases include: "improve this checklist", "reformat this process", "clean up this pay run procedure", "turn this into a proper checklist", "help me write a payroll process", "build a process for [pay run type]", "our checklist is a mess", or any request to document or standardise how a pay run works. If a payroll document is attached and the user wants it better — use this skill.'
---

# Payroll Process Design

A skill for designing, reformatting, and improving payroll process documents. It helps payroll
professionals produce clear, consistent, action-driven checklists that their whole team can
follow — whether they're starting from scratch or tidying up an existing document.

The source of truth for all formatting and structural decisions is the design guide. Read it
before making any changes or building any new content:

> **Read first:** `references/payroll-process-design.md`

---

## How to approach this task

There are two modes: **Improve an existing document** and **Build from scratch**. Determine
which applies before doing anything else.

- If the user uploads or pastes a document → **Improve mode**
- If there's no existing document → **Build from scratch mode**

In both cases, run the interview before writing any output.

---

## Step 1: Interview

Ask these questions before touching any content. Don't ask all at once — read what the user
has already told you and only ask what's missing.

**Organisation context**
1. What payroll system do they use? (e.g. Ascender, Chris21, SAP, Micropay, ADP, Dayforce)
   — needed for screen names and navigation paths. If they don't know, note it and flag steps
   that need system-specific detail.
2. What pay frequency is this process for? (weekly, fortnightly, monthly, or a mix)
3. Is there an approval step, and who approves? (e.g. Payroll Manager, CFO)

**Document context** (only in Improve mode)
5. What was wrong with the existing document, in their words? Is it incomplete, inconsistently
   written, too vague, or just badly formatted?
6. Are there any steps they know are missing that should be added?
7. Are there any house naming conventions or local quirks to preserve? (e.g. they call something
   by a non-standard name)

Keep it conversational. If the document is short and simple, you may not need all of these.

---

## Step 2: Audit (Improve mode only)

Before rewriting, do a quick audit of the existing document and share it with the user. Cover:

- Steps that are combined and should be split
- Steps that are vague, passive, or missing the action verb
- Missing role assignments or timing
- System references that aren't formatted correctly
- Anything structurally out of order

This gives the user a chance to correct your understanding before you rewrite everything.

---

## Step 3: Write or reformat the checklist

Apply the standards in `references/payroll-process-design.md` throughout. Key things to get right:

**Structure**
- Open with a brief overview: purpose, trigger, participants, outcome (see §1 of the design guide)
- Group checks into logical phases (e.g. Pre-run setup → Processing → Reconciliation → Approval → Distribution)
- Keep the sequence logical — if step B depends on step A being complete, A comes first

**Check titles**
- Short (≤6 words), action-led, no full stop
- Verb first: *Run*, *Check*, *Confirm*, *Upload*, *Send*, *Approve*, *Enter*
- Specific enough to distinguish from similar steps

**Check content**
- One action per step — split anything that's doing two things
- Active language throughout
- Include the role, timing, and deadline if known
- Use the formatting conventions from §3–§6 of the design guide for system references,
  parameters, file paths, email templates, and notifications

**What to flag but not invent**
- If a step mentions a system screen you haven't been given the name for, use a placeholder:
  `[[Screen name TBC]]`
- If a folder path isn't provided, use `[Folder path TBC]`
- Don't make up values — flag them clearly so the user can fill them in

---

## Step 4: Output

Default output is a  the same format of the input file if one was provided.

If the user asks for Word, Excel or CSV, produce that instead.

Before generating the file, show the user a plain-text preview of the reformatted checklist
in chat and ask: "Does this look right before I build the document?" This avoids wasted
round-trips on structural issues.

Once confirmed, generate the file. Name it:
`[Organisation or process name] - [Pay Frequency] Pay Run Checklist.docx`

e.g. `Laminex - Fortnightly Pay Run Checklist.docx`

---

## Building from scratch

If there's no existing document, use the interview answers to draft a full checklist from
the standard phases below. Flesh out each phase with the checks you'd expect for that pay
frequency and system, then ask the user to review and add anything missing.

Standard phases for a typical pay run checklist:
1. Pre-run setup (period setup, system config, standing data checks)
2. Timesheet / data collection (importing timesheets, exception handling)
3. Pay run processing (running the calculation, exception reports)
4. Reconciliation (variance checks, headcount, cost centre review)
5. Approval (manager and payroll manager sign-off)
6. Payment processing (ABA file, superannuation, payment confirmation)
7. Post-run tasks (archiving, reporting, STP finalisation if applicable)

Not every phase applies to every organisation — use your judgment based on the interview.

---

## Reference

The design guide contains all formatting conventions, examples of good vs bad checks, and
conventions for system references, file paths, email templates, and roles/timing.

Read `references/payroll-process-design.md` whenever you're unsure about a formatting
decision. It is the authoritative source — don't invent conventions.