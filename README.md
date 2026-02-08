# Pressbooks CLI

A command-line tool for managing [Pressbooks](https://pressbooks.com/) textbook content. Pull chapters locally, edit them with AI coding assistants, and push updates back, including automated WCAG 2.1 accessibility remediation.

Built for higher ed faculty and instructional designers who maintain OER textbooks on Pressbooks and want a faster, more powerful editing workflow.

## Why Use This?

The Pressbooks visual editor works fine for small changes. But if you need to:

- **Fix accessibility issues across an entire book** (alt text, heading hierarchy, language attributes, semantic HTML)
- **Batch-edit content** (find-and-replace across chapters, remove inline styles, update terminology)
- **Use AI coding assistants** like [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [Codex](https://openai.com/index/codex/) to read, edit, and remediate your chapters
- **Keep local backups** of your textbook content
- **Work in your own editor** instead of a browser

...then this tool gives you a pull-edit-push workflow that makes all of that possible from the command line.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/pressbooks-cli.git
cd pressbooks-cli

# Install the one dependency
pip install requests

# Configure your book (see Setup below)
# Then test the connection:
python pressbooks_api.py toc
```

## Setup

### 1. Find your book's API URL

Go to your Pressbooks textbook in a browser. Your URL will look like:

```
https://yourschool.pressbooks.pub/your-book-name/
```

Confirm the API is active by visiting:

```
https://yourschool.pressbooks.pub/your-book-name/wp-json/pressbooks/v2/toc
```

If you see structured JSON data, you're good. If not, contact your Pressbooks administrator.

### 2. Generate an Application Password

This step must be done in your browser — it requires logging into your Pressbooks account.

1. Log in to Pressbooks
2. Go to your profile page: `https://yourschool.pressbooks.pub/wp-admin/profile.php`
3. Scroll to **Application Passwords**
4. Enter a name (e.g., `CLI Access`) and click **Add New Application Password**
5. Copy the password immediately — it's only shown once

> **What is this?** An Application Password is a separate credential just for API access. It's not your login password. You can revoke it anytime from the same profile page.

### 3. Create your `.env` file

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env`:

```
PRESSBOOKS_URL=https://yourschool.pressbooks.pub/your-book-name
PRESSBOOKS_USER=your_username
PRESSBOOKS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

> **Security:** The `.env` file is gitignored and should never be committed. Don't paste your password into chat with an AI assistant — always edit the file directly.

### 4. Test the connection

```bash
python pressbooks_api.py toc
```

You should see your book's table of contents with chapter IDs.

## Usage

### View table of contents

```bash
python pressbooks_api.py toc
```

Shows all chapters with their IDs. You'll need the ID to pull or push a chapter.

### Pull a chapter

```bash
python pressbooks_api.py pull 39
```

Downloads the chapter as two local files:

| File | Contents |
|------|----------|
| `39_chapter-slug.html` | Chapter body (HTML) — this is what you edit |
| `39_chapter-slug.json` | Metadata (title, status, URL) |

### Push a chapter

```bash
python pressbooks_api.py push 39
```

Sends the local HTML back to Pressbooks. If you edited the title in the JSON file, that change is pushed too.

### Pull all chapters

```bash
python pressbooks_api.py pull-all
```

Downloads every chapter in the book. Useful for backups or batch operations.

## Using with AI Coding Assistants

This tool is designed to work with AI coding assistants that can read and edit files on your computer. The assistant handles the code; you handle the browser steps (login, generating the Application Password).

### With Claude Code

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) can read your chapter files, identify issues, edit the HTML, and push changes — all through natural language.

Example prompts:

```
Pull chapter 39, check it for WCAG 2.1 accessibility issues, fix them, and push it back.

Pull all chapters and tell me which ones have images missing alt text.

Pull chapter 25 and change every instance of "Artificial Intelligence" to "AI" in the body text, then push it back.
```

**Tip:** If you're using Claude Code, the included `CLAUDE.md` file gives Claude automatic context about your setup every time you work in this folder.

### With OpenAI Codex

The same workflow applies — point Codex at this folder and ask it to run the script and edit chapter files.

## Accessibility Remediation

One of the most useful applications is automated WCAG 2.1 accessibility fixes. AI assistants can scan chapter HTML and fix common issues:

| Issue | WCAG Criterion | What gets fixed |
|-------|---------------|-----------------|
| Missing alt text | SC 1.1.1 (A) | Images without `alt` attributes |
| Bad heading hierarchy | SC 1.3.1 (A) | Skipped heading levels (e.g., h2 to h4) |
| Non-semantic callout boxes | SC 1.3.1 (A) | `<div>` boxes converted to `<aside role="note">` |
| Missing language attributes | SC 3.1.2 (AA) | Foreign terms wrapped with `lang` attributes |
| Vague link text | SC 2.4.4 (A) | Bare URLs or symbols replaced with descriptive text |
| Inline styles | Best practice | `style="font-weight: 400"` removed in favor of CSS |
| Missing table headers | SC 1.3.1 (A) | `<td>` in header rows converted to `<th scope="col">` |

### Example: Full accessibility pass

```
Pull chapter 25 and fix it for WCAG 2.1 AA compliance. Specifically check for:
- Images missing alt text
- Heading hierarchy issues
- Foreign language terms that need lang attributes
- Inline styles that should be removed
- Links with non-descriptive text

Show me what you changed, then push it back.
```

## API Reference

The script uses the Pressbooks REST API. All read operations work without authentication; writes require the Application Password.

| Endpoint | Description |
|----------|-------------|
| `GET /wp-json/pressbooks/v2/toc` | Full table of contents |
| `GET /wp-json/pressbooks/v2/chapters` | List all chapters |
| `GET /wp-json/pressbooks/v2/chapters/{id}` | Single chapter |
| `POST /wp-json/pressbooks/v2/chapters/{id}` | Update a chapter (auth required) |
| `GET /wp-json/pressbooks/v2/parts` | Book parts/sections |
| `GET /wp-json/pressbooks/v2/front-matter` | Front matter |
| `GET /wp-json/pressbooks/v2/back-matter` | Back matter |
| `GET /wp-json/pressbooks/v2/metadata` | Book metadata |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API URL returns an error | Double-check your book URL slug matches exactly |
| "Authentication failed" on push | Verify username and password in `.env` — no extra spaces or blank lines |
| "Permission denied" on push | Your account may not have editor/admin access to the book |
| Changes don't appear on the site | Clear your browser cache or check in an incognito window |
| Python not installed | Install Python 3.8+ and run `pip install requests` |
| Can't find the `.env` file | Files starting with `.` are hidden by default. On Mac, press `Cmd+Shift+.` in Finder |

## License

MIT
