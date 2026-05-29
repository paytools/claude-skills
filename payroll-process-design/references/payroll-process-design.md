# Payroll Process Design Guide

A specification for how payroll process checklists should be structured, written, and formatted.
Use this as the source of truth when building a new checklist or improving an existing one.

---

## Table of Contents

1. Checklist purpose and overview
2. Writing checks
3. Payroll system references
4. Data and format conventions
5. Files and storage
6. Notifications and references
7. Roles, timing, and dependencies
8. Approvals, exceptions, and conditional logic
9. Examples library

---

## 1. Checklist purpose and overview

Every checklist opens with a short overview that explains why it exists and what it delivers.
Keep this section tight — four lines is usually enough.

The overview should cover:

- **Purpose** — a high-level summary of why the process is needed.
- **Trigger** — the event that starts the process (e.g. a manager submitting a form, a
  fortnightly pay run beginning, an employee termination).
- **Participants** — who is involved (e.g. Pay & Benefits, Managers, HR).
- **Outcome** — the end state once the checklist is complete.

**Example overview:**

> **Purpose:** Process the fortnightly pay run for salaried employees.
> **Trigger:** Period end date reached in the payroll calendar.
> **Participants:** Payroll Officer, Payroll Manager, Finance.
> **Outcome:** Pay run approved, ABA file submitted, STP lodged.

---

## 2. Writing checks

Each checklist breaks the process into clear, action-driven tasks that are easy to follow
and tick off. Think of each step as something someone can physically do or verify.

### 2.1 Step content

- Focus on the action required and how to do it.
- Avoid combining multiple actions in one step. If a step is doing two things, split it.
- Use active language: *Enter*, *Check*, *Select*, *Upload*, *Confirm*.
- Where the step involves a system (e.g. Preceda, SharePoint), include navigation and the
  values to enter.
- Optional or conditional steps sit as sub-items or square-bullet notes beneath the parent step.

### 2.2 Check titles

Each check starts with a title. Titles should be:

- **Short** — aim for six words or fewer.
- **Action-led** — start with the verb, then the subject (*Run*, *Check*, *Save*, *Send*,
  *Approve*, *Review*, *Confirm*, *Enter*).
- **Unpunctuated** — no full stops at the end.
- **Specific** — distinguish similar steps from each other (e.g. *Executive approval* vs
  *Manager approval*).

**Good titles:**
- Run timesheet importer
- Check leave balances
- Send ABA file to bank
- Confirm STP lodgement

**Poor titles:**
- Timesheets (no verb)
- Process (too vague)
- Do the leave check and update balances (two actions)
- Run the timesheet importer. (has a full stop)

### 2.3 Check Description
use line breaks liberally to improve readability of the check description, Particularly where the description is describing inputs or parameters into a form or screen in the payroll system  



---

## 3. Payroll System references

If you don't know what payroll system the process refers to, prompt the user for the name.

Common payroll systems include: Ascender, Chris21, SAP, Micropay, ADP, Dayforce, Preceda,
KeyPay, Employment Hero, Meridian.

Reference screen names, fields, buttons, and navigation paths using a consistent convention.

### 3.1 Screen names

Screen names cover system sections or menu labels.

- Wrap screen names in double square brackets: `[[Entry via Single Screen]]`, `[[Overrides tab]]`.

Screen code name examples:
- Chris21 — CAL, UPD, NPL, TCB, FEU, PRD
- Ascender — RC813, RC922, FD631

### 3.2 Parameters

Parameters are values the user enters into a screen.

- Use the `Field name: value` format.
- Example: *Allowance/Deduction Code: D1*

### 3.3 Navigation paths

Navigation describes how to get to a screen.

- Use the format `System Name > Menu > Page`.
- Example: *Preceda > Payroll > Period Processing*

---

## 4. Data and format conventions

These conventions apply across every checklist so that data is captured and referenced consistently.

### 4.1 Dates and periods

- Dates: `DD.MM.YYYY`
- Pay periods: `Period Ending DD.MM.YYYY`

### 4.2 Codes and entry values

Data entry codes are written as `Label: Code`.

- *Allowance/Deduction Code: D1*
- *Leave Reason: TL*
- *Accrual Method: TIL*

### 4.3 Buttons and actions

Buttons and system actions are written in sentence case with the keyboard shortcut in
brackets where relevant.

- *Press Save (F8)*
- *Click Upload*
- *Select Confirm*

### 4.4 Other formats

- Employee references: Employee ID: Employee Name (e.g. *123456: Smith, J*)
- Currency: always include a dollar sign (e.g. $1,234.56)
- Time: 24-hour format (e.g. 09:30, 17:00)

---

## 5. Files and storage

Storage instructions tell the user where to save a file, what to name it, and what format
to save it in.

### 5.1 Folder paths

- Use a clear folder path that reflects the actual folder structure the user sees in
  SharePoint or the network drive.
- Use the greater-than symbol (`>`) to separate folders.
- Use square brackets `[ ]` to denote a variable the user fills in based on context.
- Example: *Payroll > [Pay Period] > Reports > [Report Name]*

### 5.2 File naming

File names follow this structure:
`[Organisation] - [Document Type] - [Period or Date].[extension]`

- Use title case for each segment.
- Use hyphens to separate segments, not underscores.
- Date placement: at the end of the file name in `DDMMYYYY` format.
- Version suffix: append `-v[N]` only when multiple versions of the same file will coexist
  (e.g. `-v1`, `-v2`). Don't add version suffixes to final/archived files.

Example: *Payroll > FY2526 > Fortnightly > Laminex - Pay Run Report - 27062025.xlsx*

### 5.3 File formats

- Working files and reconciliation: `.xlsx` (unlocked, with formulas visible)
- Files sent for approval or record: `.pdf` (locked)
- ABA payment files: `.aba` (no modification after generation)
- Exported reports: match the format the system produces; convert to `.pdf` before archiving

---

## 6. Notifications and references

Conventions for things sent or referenced outside the checklist — emails, message
templates.

If a step or check refers to emailing someone, this doesn't need to be split into a separate
check but the instruction should clearly state:

- The recipient(s)
- The CC recipients (up to two)
- The subject line
- The email body

In the email body, don't hard-code any dates. Use placeholders for periods and values that
the operator fills in when sending — e.g. `[Period Ending DD.MM.YYYY]`, `[Total Net Pay]`.

Format email templates in a code block:

```
To: finance@organisation.com.au
CC: payrollmanager@organisation.com.au, hr@organisation.com.au
Subject: Pay Run Confirmation – Period Ending [DD.MM.YYYY]

Hi [Finance contact name],

Please find attached the pay run summary for the period ending [DD.MM.YYYY].

Total gross: $[amount]
Total net: $[amount]
Headcount: [number]

The ABA file has been submitted. Please confirm receipt.

Regards,
[Your name]
Payroll
```

 If the step references to message someone using Teams or MS Teams:
 - put the body of the message in a code block 
 - Specify the Teams channel it's going into or ask the user if we don't know which Teams channel
---

## 7. Roles, timing, and dependencies

How to indicate who does what, when it must be done, and what depends on what.

Each check should clearly state which role performs it. If there is a time (day of the week
or time of day), specify it. Include a deadline where relevant.

**Check format with role and timing:**

```
Check name: Run timesheet importer
Assigned to: Payroll Officer
Time: 09:30
Deadline: Day 1 of processing window
```

**Dependency notation:**

If a step depends on a previous step being complete, note it beneath the check:

> ⚠ Requires: *Close pay period* to be complete before starting.

**Day references:**

When referencing days, use relative terms tied to the pay run cycle rather than calendar
days — this makes the checklist reusable across periods.

- Day 1 / Day 2 (processing days, counted from period close)
- Pay day -3 (three business days before pay day)
- Pay day (the day wages are deposited)

---

## 8. Approvals, exceptions, and conditional logic

How to write approval steps, document exceptions, and handle branching logic.

### 8.1 Approval steps

Approval steps follow this pattern:

```
Check name: Manager approval
Assigned to: Payroll Manager
Action: Review the pay run summary and confirm approval in [system].
        If approved → proceed to [next step].
        If rejected → log the issue in [system] and notify Payroll Officer.
```

The approval step must always state:
- Who approves
- What they're approving (what document or output)
- Where the approval is recorded (system, email, form)
- What happens next (approved path and rejection path)

### 8.2 Exception handling

When a step might surface exceptions, include handling instructions:

> If exceptions are found, log in [exception register] and notify [role] before proceeding.
> Do not advance to the next step until exceptions are resolved or escalated.

### 8.3 Conditional logic ("if/then")

Use this notation for branching steps:

```
If [condition] → [action]
If [condition] → [action]
Otherwise → [default action]
```

Example:

```
If employee has a manual adjustment this period → process via [[Manual Overrides]] before running the calculation.
If no manual adjustments → proceed directly to the calculation step.
```

Keep conditionals simple. If a check has more than two branches, consider splitting it into
separate checks or adding a decision table.

---

## 9. Examples library

Side-by-side examples illustrating the conventions above.

### 9.1 Formatting reference

- **Fields:** use `Field Name:` then the content. Example: *Employee ID: Enter ID number*
- **Examples:** when illustrating a value, use italics. Example: *123456 Smith Purchased Leave Request 12.06.2025*

### 9.2 Good vs bad: check titles

| ❌ Bad | ✅ Good |
|--------|---------|
| Timesheets | Import timesheets |
| Process | Run pay calculation |
| Do the leave check and update the balances | Check leave balances |
| Send out the payslips to employees. | Send payslips |
| Approve | Payroll Manager approval |

### 9.3 Good vs bad: check content

**❌ Bad:**
> Timesheets — check that they are all in and process them in the system before moving on to the next step.

Problems: no verb to open, two actions combined, vague ("the system"), no role or timing.

---

**✅ Good:**
> **Import timesheets**
> Assigned to: Payroll Officer | Time: 09:30 | Deadline: Day 1
>
> Navigate to *Preceda > Payroll > Timesheet Import*.
> Select the import file from *Payroll > [Period Ending] > Timesheets > [filename].csv*.
> Press *Import*. Review the exception report and resolve any errors before proceeding.
>
> ⚠ Requires: Managers to have submitted all timesheets by 17:00 on the previous business day.

---

### 9.4 Good vs bad: system references

| ❌ Bad | ✅ Good |
|--------|---------|
| Go to the payroll screen | Navigate to *Preceda > Payroll > Period Processing* |
| Enter D1 | *Allowance/Deduction Code: D1* |
| Save it | *Press Save (F8)* |
| The entry screen | `[[Entry via Single Screen]]` |

### 9.5 Good vs bad: email templates

**❌ Bad:**
> Send an email to finance with the pay run details including the total pay and headcount for 27 June.

Problems: hard-coded date, no subject, no body, no CC.

---

**✅ Good:**
> Send pay run confirmation email to Finance:
>
> ```
> To: finance@organisation.com.au
> CC: payrollmanager@organisation.com.au
> Subject: Pay Run Confirmation – Period Ending [DD.MM.YYYY]
>
> Hi [Finance contact name],
>
> The fortnightly pay run for period ending [DD.MM.YYYY] has been approved and submitted.
>
> Total net pay: $[amount]
> Headcount: [number]
>
> The ABA file has been sent to [bank name]. Please confirm receipt by [time].
>
> Regards,
> [Your name]
> ```

---