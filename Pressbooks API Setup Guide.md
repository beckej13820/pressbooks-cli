# Pressbooks API Setup Guide

A step-by-step guide for using an AI coding assistant (Claude Code, OpenAI Codex, etc.) to set up a pull-edit-push workflow for your Pressbooks textbook. You'll handle the browser steps; the AI handles the code.

---

## What You'll End Up With

A Python script that lets your AI assistant:
- **Pull** any chapter from your Pressbooks textbook as a local file
- **Edit** the content (accessibility fixes, formatting, find-and-replace, etc.)
- **Push** the changes back to Pressbooks automatically

The whole setup takes about 15 minutes.

---

## Step 1: Find Your Book URL

Go to your Pressbooks textbook in a browser and copy the URL from the address bar. It will look something like:

```
https://yourschool.pressbooks.pub/your-book-name/
```

**Examples:**
- `https://cwi.pressbooks.pub/aiethics/`
- `https://open.umn.edu/intro-to-philosophy/`
- `https://pressbooks.bccampus.ca/businesswriting/`

Keep this URL handy. You'll give it to your AI assistant in Step 5.

---

## Step 2: Test the API in Your Browser

Before any setup, confirm the API is active. Paste this into your browser, replacing the example with your book URL:

```
https://yourschool.pressbooks.pub/your-book-name/wp-json/pressbooks/v2/toc
```

**If you see a wall of structured text (JSON):** The API is active. You're good to go.

**If you get an error or a blank page:** The API may not be enabled. Contact your Pressbooks administrator.

---

## Step 3: Generate an Application Password

This is the one step you **must do yourself** in the browser. The AI assistant cannot (and should not) do this for you, because it involves logging into your account.

1. **Log in to Pressbooks** as you normally would

2. **Go to your profile page.** Paste this into your browser, replacing the URL:
   ```
   https://yourschool.pressbooks.pub/wp-admin/profile.php
   ```

3. **Scroll down** to the section called **"Application Passwords"**

4. Type a name like `Claude API Access` and click **"Add New Application Password"**

5. **A password will appear.** It looks something like:
   ```
   xxxx xxxx xxxx xxxx xxxx xxxx
   ```

6. **Copy it immediately.** It's only shown once. Save it somewhere safe (a password manager, a note on your desktop, etc.).

> **What is this?** An Application Password is a separate credential just for API access. It's not your regular Pressbooks login. You can revoke it anytime from this same profile page.

> **Don't see "Application Passwords"?** Your Pressbooks instance may not support it. Contact your administrator and ask if Application Passwords or another REST API authentication method is available.

---

## Step 4: Choose a Folder

Decide where you want to keep the script and chapter files on your computer. Some suggestions:

- `~/Documents/Pressbooks/`
- `~/Documents/OER/Pressbooks/`
- Anywhere that makes sense for your workflow

Remember this location. You'll tell the AI where to put things.

---

## Step 5: Ask Your AI Assistant to Set Everything Up

Now hand it off to the AI. Open Claude Code (or Codex, or your preferred AI coding tool) and give it a prompt like this:

> **Copy and customize this prompt:**
>
> *I need you to create a Pressbooks API script that can pull, edit, and push chapters from my textbook. Here's my setup:*
>
> - *My book URL is: `https://yourschool.pressbooks.pub/your-book-name/`*
> - *My Pressbooks username is: `your_username`*
> - *Put the script and files in: `~/Documents/Pressbooks/`*
>
> *Please:*
> 1. *Create a Python script called `pressbooks_api.py` that supports these commands: `toc`, `pull <id>`, `push <id>`, and `pull-all`*
> 2. *Create a `.env` file for my credentials (I'll add the password myself)*
> 3. *Make sure the script reads credentials from the `.env` file automatically*
> 4. *Run the `toc` command to test that the API connection works*

The AI will create the script, set up the folder structure, and test the connection for you.

---

## Step 6: Add Your Password

After the AI creates the `.env` file, open it and replace the placeholder password with the real Application Password you copied in Step 3.

The file will look like:
```
PRESSBOOKS_USER=your_username
PRESSBOOKS_APP_PASSWORD=PASTE_YOUR_PASSWORD_HERE
```

Change it to:
```
PRESSBOOKS_USER=your_username
PRESSBOOKS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

> **Can't find the `.env` file?** Files starting with a dot are hidden by default. On Mac, press `Cmd + Shift + .` in Finder to show hidden files. Or ask your AI assistant: *"Open the .env file in the Pressbooks folder so I can add my password."*

> **Security note:** Never paste your Application Password directly into the chat with your AI assistant. Always edit the `.env` file yourself.

---

## Step 7: Test the Full Workflow

Ask your AI assistant to verify everything works:

> *Run the Pressbooks `toc` command to show me all the chapters.*

You should see a list of your book's chapters, each with an ID number in brackets. Then test a pull and push:

> *Pull chapter [ID] from my Pressbooks, then push it back without changes to test that authentication works.*

If the push succeeds, you're fully set up.

**If it fails with "Authentication failed":**
- Double-check the password in your `.env` file
- Make sure there are no extra spaces or blank lines
- Make sure the username matches your Pressbooks login exactly

---

## Using It Day-to-Day

Once setup is complete, here are the kinds of things you can ask your AI assistant to do:

### Pull and review a chapter

> *Pull chapter 39 from my Pressbooks and show me the table of contents first so I can find the right ID.*

### Fix accessibility issues

> *Pull chapter 25, check it for WCAG 2.1 accessibility issues, fix them, and push it back.*

Common accessibility fixes the AI can handle:
- Adding alt text to images
- Fixing table headers (`<th>` instead of `<td>`)
- Adding language attributes to foreign terms
- Converting `<div>` callout boxes to semantic `<aside>` elements
- Removing inline styles
- Fixing heading hierarchy

### Batch operations

> *Pull all chapters and check which ones have images missing alt text.*

> *Pull chapter 42, change every instance of "Artificial Intelligence" to "AI" in the body text, and push it back.*

### Backup your book

> *Pull all chapters from my Pressbooks to create a local backup.*

---

## What the Files Look Like

When you pull a chapter, two files appear in a subfolder:

| File | What it is |
|------|-----------|
| `25_chapter-slug.html` | The chapter content as HTML. This is what gets edited. |
| `25_chapter-slug.json` | Metadata: title, status, URL. The title can be edited here too. |

The HTML is the same content you'd see in the Pressbooks visual editor, just in raw HTML form. The AI reads and edits this directly.

---

## Adding a CLAUDE.md File (Recommended)

If you're using Claude Code, ask it to create a `CLAUDE.md` file in your Pressbooks folder. This gives Claude automatic context about your setup every time you work in that folder.

> *Create a CLAUDE.md file in this folder that documents my Pressbooks setup: the book URL, what the script does, all available commands, and any accessibility remediation patterns we've used.*

Next time you open Claude Code in that folder, it will already know your setup without you having to explain it again.

---

## Troubleshooting

| Problem | What to do |
|---------|-----------|
| Browser shows error when testing the API URL | Double-check your book URL. The slug must match exactly. |
| "Authentication failed" on push | Check username and password in `.env`. No extra spaces or line breaks. |
| "Permission denied" on push | Your account may not have editor/admin access to the book. |
| Script not found when running commands | Make sure you're in the right folder. Ask the AI: *"Where is my Pressbooks script?"* |
| Changes don't appear on the website | Clear your browser cache or check in an incognito window. Pressbooks may cache pages. |
| Python not installed | Ask your AI assistant: *"Check if Python is installed and install the requests library."* |

---

## Quick Reference: What to Ask Your AI

| What you want | What to say |
|---------------|------------|
| See all chapters | *"Run the Pressbooks toc command."* |
| Download a chapter | *"Pull chapter 39 from Pressbooks."* |
| Download everything | *"Pull all chapters from Pressbooks."* |
| Fix accessibility | *"Pull chapter 39, fix it for WCAG 2.1 compliance, and push it back."* |
| Push changes | *"Push chapter 39 back to Pressbooks."* |
| Find something across chapters | *"Pull all chapters and find which ones reference Aristotle."* |
| Batch edit | *"Pull all chapters and remove every inline style attribute, then push them all back."* |
