# Accessibility Review Workflow (Approval-Based)

This is the single workflow for Pressbooks accessibility remediation with human approval gates.

## Project Principles (Must Keep)

- Treat WCAG 2.2 AA as the required accessibility baseline for remediation decisions.
- Prioritize screen-reader clarity over raw URL link text.
- Use descriptive link text that communicates destination or purpose.
- In reference lists and citation-heavy sections, keep full URLs visible as plain text when needed for print, verification, or citation conventions.
- Apply citation-style requirements (for example MLA/APA) together with accessibility best practices, not instead of them.
- When style-guide expectations and accessibility patterns conflict, escalate for human approval and record the decision.

### Pressbooks Link Pattern

Preferred pattern in most contexts:

- Make the hyperlink text descriptive.
- Keep the full URL as adjacent plain text when required by editorial/citation context.

Example:

```html
<!-- avoid -->
<a href="https://example.org/report.pdf">https://example.org/report.pdf</a>

<!-- preferred -->
<a href="https://example.org/report.pdf">Example Report (PDF)</a> (URL: https://example.org/report.pdf)
```

Reference-list note:

- For Works Cited/References/Bibliography sections, preserve required citation structure while still avoiding generic or raw URL-only link text where possible.
- Use the Foundations of Education approach as precedent: keep citations readable and citable, but ensure linked text is meaningful for assistive technology.

## Workflow Rules

- Run audits in read-only mode first.
- Do not apply edits unless the user explicitly approves.
- Track every finding with a status: `pending`, `approved`, `rejected`, `applied`.
- Re-scan after edits and report before/after counts.

## 1. Pull Content Locally

```bash
python3 pressbooks_api.py toc
python3 pressbooks_api.py pull-all
```

Expected local files:

- `<book-folder>/<id>_<slug>.html`
- `<book-folder>/<id>_<slug>.json`

## 2. Run the Standard Read-Only Audit

Use the repository script as the canonical audit step:

- `scripts/editoria11y_style_audit.py`

Run on a full book folder:

```bash
python3 scripts/editoria11y_style_audit.py <book-folder>
```

Run on one chapter:

```bash
python3 scripts/editoria11y_style_audit.py <book-folder>/<chapter>.html
```

Default artifacts:

- `<book-folder>/image_audit/editoria11y_style_manifest.json`
- `<book-folder>/image_audit/editoria11y_style_summary.md`

Use the JSON manifest as the source of truth for approvals and automation.

## 3. Build the Approval Queue

Create one row per finding from the manifest with these fields:

- `id`
- `rule_id`
- `file:line`
- `message`
- `suggestion`
- `manual_review` (`yes/no`)
- `proposed_change`
- `status` (`pending/approved/rejected/applied`)

Group rows into review batches if helpful (for example by chapter, rule, or severity).

## 4. Human Approval Gate (All Change Types)

This gate applies to every change class, not just links.

Required behavior:

- Present proposed changes in issue or batch form.
- Ask for explicit approval (`approve` or `reject`).
- Record decisions in the queue before editing.
- Apply only rows marked `approved`.

Policy decisions that must be confirmed before applying related edits:

- Link behavior policy (`target="_blank"` keep/remove/warn).
- URL/link-text policy (descriptive link text with visible plain URL where required, especially in reference lists).
- Alt text policy for uncertain images (`manual_review` findings).
- Citation-style integration policy for references (MLA/APA requirements plus accessibility behavior).

## 5. Apply Approved Remediation Only

When implementing:

- Edit only approved rows.
- Keep changes narrowly scoped.
- Do not refactor unrelated markup.
- Update status from `approved` to `applied` only after successful edit.

## 6. Re-Run Audit and Validate Closure

Run the same audit command used in Step 2:

```bash
python3 scripts/editoria11y_style_audit.py <book-folder>
```

Then produce a short validation summary:

- total findings before vs after
- findings cleared
- findings remaining
- remaining `manual_review` items

## 7. Push in Controlled Stages

Push one approved chapter first:

```bash
python3 pressbooks_api.py push <chapter_id>
```

If successful, push the rest of the approved set.

## 8. Required Project Deliverables

Keep these artifacts per book:

- `editoria11y_style_manifest.json` (pre and post if stored separately)
- `editoria11y_style_summary.md`
- approval queue/table with status history
- push log (chapter IDs, status, URLs if available)
- `<book-folder>/remediation_audit_trail_report.md`

## 9. Required Narrative Audit Trail

Create `<book-folder>/remediation_audit_trail_report.md` with:

1. Scope and goal
2. First scan command + results
3. Approval decisions and policy choices
4. What changed (with examples)
5. Final scan command + results
6. Push/publish log
7. Approval statement (`approved in chat` if needed)

Do not close remediation work until this report is saved.

## 10. Reusable Prompt Sequence for Codex/LLMs

1. "Run the standard read-only audit script and create an approval queue from the manifest."
2. "Do not apply edits yet. Ask me to approve or reject each issue/batch."
3. "Apply only approved items and update statuses."
4. "Re-run the same audit and summarize before/after counts."
5. "Push one chapter first, then push the remaining approved chapters."
6. "Write `remediation_audit_trail_report.md` with commands, approvals, and outcomes."
