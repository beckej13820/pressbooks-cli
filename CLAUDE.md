# Pressbooks CLI

## Overview

This repository provides a pull-edit-push workflow for Pressbooks textbooks via the REST API. Configuration is stored in `.env` (not committed to git).

## Files

- `pressbooks_api.py` — CLI tool for pulling, editing, and pushing chapter content
- `.env` — Stores book URL and credentials (gitignored)
- `.env.example` — Template for `.env` configuration
- Book chapters are pulled into a subdirectory named after the book slug

## Commands

```bash
python pressbooks_api.py toc                    # Show table of contents with IDs
python pressbooks_api.py pull <chapter_id>      # Pull chapter to local HTML + JSON
python pressbooks_api.py push <chapter_id>      # Push local HTML back to Pressbooks
python pressbooks_api.py pull-all               # Pull all chapters locally
```

## Workflow

1. Run `toc` to find the chapter ID
2. Run `pull <id>` to download the chapter HTML and metadata
3. Edit the `.html` file (content is HTML format)
4. Run `push <id>` to publish the changes back to Pressbooks

## Chapter File Format

Each pulled chapter creates two files:
- `{id}_{slug}.html` — The chapter body content (HTML)
- `{id}_{slug}.json` — Metadata (id, title, slug, status, link)

The push command reads the HTML file and sends it back via the API. If you update the title in the JSON file, that change will also be pushed.

## Configuration

Credentials and book URL are stored in `.env`:
```
PRESSBOOKS_URL=https://yourschool.pressbooks.pub/your-book-name
PRESSBOOKS_USER=your_username
PRESSBOOKS_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

## API Details

- **Read** (no auth required): `GET /wp-json/pressbooks/v2/chapters/{id}`
- **Write** (auth required): `POST /wp-json/pressbooks/v2/chapters/{id}`
- **Content format**: HTML inside JSON
- **Auth method**: HTTP Basic Auth with WordPress Application Passwords

## WCAG 2.1 Remediation Notes

When editing chapters for accessibility, common issues to check:
- **SC 3.1.2 (AA)**: Foreign language terms need `lang` attributes (e.g., `<span lang="grc">dialogos</span>`)
- **SC 2.4.4 (A)**: Link text must be descriptive (avoid bare URLs or symbols)
- **SC 1.3.1 (A)**: Use semantic HTML (`<aside>` with `role="note"`) instead of `<div>` for callout boxes
- Remove inline presentation styles — use CSS instead
- Check images for alt text
- Ensure heading hierarchy is correct (no skipped levels)
- Convert `<td>` to `<th scope="col">` in table header rows
