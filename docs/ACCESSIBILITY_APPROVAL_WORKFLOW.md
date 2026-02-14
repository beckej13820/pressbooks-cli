# Accessibility Review Workflow (Approval-Based)

This workflow documents how to run chapter accessibility remediation with human approval at each decision point.

It is designed for Pressbooks projects where you want to:

- pull chapters locally,
- run a read-only audit,
- generate a remediation table,
- approve changes in batches,
- apply only approved edits,
- push updated chapters back to Pressbooks.

## 1. Pull Content Locally

```bash
python3 pressbooks_api.py toc
python3 pressbooks_api.py pull-all
```

This creates local chapter files in:

`<book-hostname>/`

Each chapter has:

- `<id>_<slug>.html` (editable HTML)
- `<id>_<slug>.json` (metadata)

## 2. Run a Read-Only Audit

Scan for high-value WCAG issues before editing anything:

- table semantics (`<th>` usage),
- image alt text quality,
- heading structure,
- vague link text,
- URL-as-link-text patterns (`http://` / `https://` as visible anchor text),
- optional advisory checks (inline styles, bare URL anchors).

Example checks used in this project:

```bash
rg -n -P '<img(?![^>]*\balt=)[^>]*>' <book-folder>/*.html
rg -n -P '<img\b[^>]*\balt=""[^>]*>' <book-folder>/*.html
rg -n -P '<a\b[^>]*>\s*(click here|here|read more|more|link)\s*</a>' -i <book-folder>/*.html
rg -n -P '<a\b[^>]*>\s*https?://[^<]+' <book-folder>/*.html
```

### URL-as-Link-Text Rule (Pressbooks-Specific)

In this project, links should be descriptive for screen-reader users, while still exposing full URLs for print/manual inspection.

Use this pattern:

- Link the descriptive title/text.
- Keep full URL visible as plain text in parentheses right after the link.

Example:

```html
<!-- before -->
<a href="https://example.org/report.pdf">https://example.org/report.pdf</a>

<!-- after -->
<a href="https://example.org/report.pdf">Example Report (PDF)</a> (URL: https://example.org/report.pdf)
```

Notes:

- This pattern is especially useful in reference lists and bibliography sections.
- If citation style requires visible URL strings, keep them as plain text, not as link text.

For table header structure:

```bash
python3 - <<'PY'
import re
from pathlib import Path
root=Path('<book-folder>')
for f in sorted(root.glob('*.html')):
    txt=f.read_text(encoding='utf-8')
    for m in re.finditer(r'<table\b.*?</table>', txt, re.I|re.S):
        if not re.search(r'<th\b', m.group(0), re.I):
            line=txt.count('\n',0,m.start())+1
            print(f"{f}:{line}")
PY
```

## 3. Generate an Audit Table

Create a table with one row per issue:

- ID
- File:line
- URL (for image issues)
- Issue type
- Proposed remediation
- Proposed replacement text/code
- Status (`pending`, `approved`, `rejected`, `applied`)

### Image Audit Sub-Workflow (Download + Visual Inspection)

For image alt-text work, use a local audit folder so the AI can inspect visuals before proposing text.

Recommended location:

- `<book-folder>/image_audit/`

Why this location:

- Keeps audit artifacts scoped to one book.
- Avoids mixing findings from different books.
- Stays out of normal chapter file listings while still being easy to find.

This workflow uses a visible folder by default for easier discovery in IDE file trees.

Recommended steps:

1. Detect image tags with empty alt text.
2. Extract `file`, `line`, and image `url`.
3. Download each image into `<book-folder>/image_audit/`.
4. Save a machine-readable manifest.
5. Visually inspect local image files.
6. Generate a proposal table for user approval.

Example implementation pattern:

```bash
python3 - <<'PY'
import re, json, urllib.request
from pathlib import Path

root = Path('restoryingeducation.pressbooks.sunycreate.cloud')
audit = Path('image_audit')
audit.mkdir(exist_ok=True)

rows = []
pat = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*\balt=""[^>]*>', re.I)
for f in sorted(root.glob('*.html')):
    txt = f.read_text(encoding='utf-8')
    for m in pat.finditer(txt):
        line = txt.count('\n', 0, m.start()) + 1
        url = m.group(1)
        local = audit / url.split('/')[-1]
        urllib.request.urlretrieve(url, local)
        rows.append({"file": str(f), "line": line, "url": url, "local": str(local)})

(audit / 'manifest.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(f"downloaded {len(rows)} images")
PY
```

After inspection, write proposal output to:

- `<book-folder>/image_audit/alt_text_proposals.md`

In this project we saved proposal artifacts under:

- `<book-folder>/image_audit/manifest.json`
- `<book-folder>/image_audit/alt_text_proposals.md`

## 4. Human-in-the-Loop Review

Review issues one-by-one or in batches:

- Ask for explicit `yes/no` approval per issue, or
- ask for grouped approval (e.g., “Batch A/B/C”).

No edits should be applied until explicitly approved.

### Required Decision Gate: `_blank` Link Behavior

For findings related to links opening new windows/tabs, do not auto-apply edits.
Before changing any `target="_blank"` behavior, ask and record which option is approved:

1. Keep `target="_blank"` and add a clear warning in link text/label.
2. Remove `target="_blank"` so links open in the same tab/window.
3. Leave unchanged for editorial reasons.

Record the decision in the batch artifact before applying any link changes.

## 5. Bulk-Approval Pattern

When the user approves a batch:

1. Apply only rows in status `approved`.
2. Leave `rejected` rows unchanged.
3. Re-run checks for that issue class to confirm closure.
4. Update audit status to `applied`.

Recommended batch grouping:

- Quote portraits
- Conceptual diagrams
- Historical artifacts

This keeps review fast while preserving editorial control.

## 6. Apply Remediation Safely

Make narrowly scoped edits:

- Table headers: convert `<td>` in header rows to `<th scope="col">`.
- Alt text: replace `alt=""` with concise, context-aware text.
- URL-as-link-text: move the hyperlink to descriptive text and keep the full URL as visible plain text.
- Avoid unrelated formatting churn.

Then validate:

```bash
rg -n -P '<img\b[^>]*\balt=""[^>]*>' <book-folder>/*.html || true
```

## 7. Pre-Push Summary

Before pushing, produce a short checklist:

- missing `alt` attributes: pass/fail
- empty alt values: pass/fail
- tables without `<th>`: pass/fail
- generic link text: pass/fail
- heading jump checks: pass/fail
- advisory counts (bare URL link text, inline style volume)

## 8. Push in Controlled Stages

Push one chapter first:

```bash
python3 pressbooks_api.py push <chapter_id>
```

If successful, push approved remainder:

```bash
python3 pressbooks_api.py push <chapter_id>
```

## 9. Suggested Reusable Prompt Flow

Use this sequence with Codex (or similar):

1. "Run a read-only accessibility audit and produce an issue table with file/line references."
2. "Do not auto-fix anything. Ask me for approval per issue."
3. "For image alt-text issues, include the image URL and propose alt text."
4. "Group proposed changes into batches and wait for my batch approvals."
5. "Apply only approved batches, then re-run checks and summarize pass/fail."
6. "Push one chapter first, then push the rest if successful."

## 10. Editoria11y-Style Rule Audit (Local Script)

This repository now includes:

- `scripts/editoria11y_style_audit.py`

Run against one chapter:

```bash
python3 scripts/editoria11y_style_audit.py \
  restoryingeducation.pressbooks.sunycreate.cloud/194_towards-a-philosophy-of-education.html
```

Run against all chapter HTML in a folder:

```bash
python3 scripts/editoria11y_style_audit.py \
  restoryingeducation.pressbooks.sunycreate.cloud
```

Default output for both commands above:

- `restoryingeducation.pressbooks.sunycreate.cloud/image_audit/editoria11y_style_manifest.json`
- `restoryingeducation.pressbooks.sunycreate.cloud/image_audit/editoria11y_style_summary.md`

Then use the markdown summary for batch approvals and the JSON manifest for automation.

## 11. Deliverables to Keep Per Project

- Audit source data (`manifest.json`)
- Proposal table (`alt_text_proposals.md` or equivalent)
- Final pass/fail checklist
- Chapter IDs pushed and resulting URLs/status

## 12. Final Deliverable: Narrative Audit Trail Report

For each approved remediation batch, produce a final narrative report that a nontechnical reader can follow.

Save report to:

- `<book-folder>/remediation_audit_trail_report.md`

Required sections:

1. **Scope and Goal**
- What was reviewed (book/folder, chapter range, issue class).
- Why the remediation was needed.

2. **First Scan Results (Before Changes)**
- Include scan date/time and exact command(s).
- Include a results table with:
  - check name,
  - files affected,
  - issue count,
  - artifact path (manifest/findings file).

3. **Remediation Narrative (What Changed)**
- Short plain-language summary of the editorial/accessibility intent.
- Technical summary of the change pattern (e.g., HTML/link pattern updates).

4. **Change Tables (All Changes)**
- Include a table covering all changed entries.
- Minimum columns:
  - ID,
  - file:line,
  - issue type,
  - before,
  - after,
  - status.
- If the full table is large, place it in an appendix within the same report and reference it from the summary.

5. **Summative Scan Results (After Changes)**
- Re-run the same scans used in the first scan.
- Include a pass/fail table with counts after remediation.
- Explicitly call out unresolved items, if any.

6. **Push/Publish Log**
- List chapter IDs pushed and resulting status/URL.

7. **Approval Statement**
- Record who approved and when (if available), or note "approved in chat".

Recommended command snippets:

```bash
# first scan (example for URL-as-link-text)
rg -n -P '<a\b[^>]*>\s*https?://[^<]+' <book-folder>/*.html > <book-folder>/image_audit/url_as_link_text_findings.txt

# summative scan (same check after remediation)
rg -n -P '<a\b[^>]*>\s*https?://[^<]+' <book-folder>/*.html | wc -l
```

Deliverable requirement:

- Do not close remediation work until this narrative audit trail report is created and saved.
This creates a repeatable, reviewable remediation trail for future books.
