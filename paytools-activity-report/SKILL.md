---
name: paytools-activity-report
description: >
  Generate a polished, self-contained HTML team activity report from a Paytools audit log JSON file.
  Use this skill whenever the user uploads or pastes a Paytools audit log (a JSON file containing
  an "audits" array) and asks for a report, summary, or analysis of team activity — even if they
  don't use the exact phrase "activity report". Trigger phrases include: "generate the activity
  report", "create a team report", "build the report from this log", "activity report for [month]",
  "what did the team do", "summarise this audit log", "team summary from paytools", or any request
  to produce a report or visualisation from Paytools JSON data. If the user uploads a JSON file
  and mentions Paytools, payroll activity, or team usage — use this skill.
---

# Paytools Team Activity Report

## What this skill does

Takes a Paytools audit log JSON (an `audits` array) and produces a single self-contained HTML report
with five tabs: Team Overview, User Profiles, BAU Work, Config Changes, and Observations & Alerts.
All the heavy analysis is handled by the bundled Python script — your job is to locate the file,
run the script, and save the output in the right place.

---

## Step 1 — Locate the JSON file

The user will have uploaded a JSON file. Find it:
- Check the uploads directory for `.json` files
- If there are multiple JSON files, ask which one to use
- If the file is missing, ask the user to upload it

---

## Step 2 — Run the analysis script

Copy the bundled script to the outputs directory and run it against the file:

```bash
cp <skill-dir>/scripts/generate_report.py <outputs-dir>/generate_report.py

python3 <outputs-dir>/generate_report.py \
  --input "<path-to-json>" \
  --output "<workspace>/Projects/Team Activity Report/Team_Activity_Report_<MonthYear>.html"
```

**Path mapping in Cowork / shell:**
- The skill directory (where SKILL.md lives) maps to its shell path — use the path you were given
- Workspace folder = `/sessions/<session>/mnt/Claude OS/`
- Outputs dir = `/sessions/<session>/mnt/outputs/`

Make sure the output directory exists before running:
```bash
mkdir -p "<workspace>/Projects/Team Activity Report/"
```

Name the output file `Team_Activity_Report_<MonthYear>.html` where MonthYear is derived from
the date range in the data (e.g., `Team_Activity_Report_May2026.html`).

---

## Step 3 — Handle script errors

If the script errors out:
- A `FileNotFoundError` means the input path is wrong — double-check
- A `KeyError` or `json.JSONDecodeError` means the file may not be a valid Paytools audit log
- Any other error: read the traceback and fix inline; the script is designed to be self-contained

---

## Step 4 — Present the report

Once the script completes successfully, it prints the output path and a brief summary. Present the
file to the user with a `computer://` link. Then briefly surface the 2–3 most significant findings
from the report — things like recurring late checks, approval backlog patterns, or notable config
activity. Keep this summary to 4–6 sentences. Don't explain what the report contains; just give
the user the highlights so they know what to look at first.

---

## Output conventions

- Single `.html` file — all CSS and JS inline, no external dependencies except Google Fonts
- All timestamps displayed in AEDT (UTC+11)
- File saved to `Projects/Team Activity Report/` in the workspace folder
- Tabs suppressed if no data exists for that category (e.g., no Employee Actions tab if no
  adjustment/overpayment/underpayment records)

---

## What the script handles automatically

The bundled `generate_report.py` script does all of the following without any extra prompting:

- Parses the `audits` array (handles both `{"audits": [...]}` wrapper and bare arrays)
- Converts all timestamps from UTC to AEDT (UTC+11)
- Classifies audit records into work categories (Check Tasks, Checklist Actions, File Attachments,
  Comments, Calendar Events, Config/Templates, Employee Work, Governance)
- Computes per-user stats: total actions, active days, sessions, median session span, typical start
  time, out-of-hours flags, weekday activity patterns
- Identifies check completions, reverts, and late completions (vs due_date)
- Surfaces recurring late checks (same check name late 3+ times)
- Builds a user × date activity heatmap
- Groups BAU work by pay period, showing check completion and checklist approval status per event
  occurrence
- Extracts config changes by user (excluding Paytools system user)
- Generates observations, alerts, and recommendations from the data patterns
- Writes a complete, styled HTML file with DM Sans/DM Mono fonts and the Paytools colour palette

The script accepts two arguments: `--input` (path to JSON) and `--output` (path for HTML output).
It prints a one-line summary on success.
