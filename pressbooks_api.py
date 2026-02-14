#!/usr/bin/env python3
"""
Pressbooks CLI
--------------
Pull chapters, edit content, and push updates back to Pressbooks.

Usage:
    python pressbooks_api.py toc                    # Show table of contents
    python pressbooks_api.py pull <chapter_id>      # Pull chapter to local HTML file
    python pressbooks_api.py push <chapter_id>      # Push local HTML file back to Pressbooks
    python pressbooks_api.py pull-all               # Pull all chapters locally

Configuration:
    Add your book URL and credentials to the .env file:
        PRESSBOOKS_URL=https://yourschool.pressbooks.pub/your-book-name
        PRESSBOOKS_USER=your_username
        PRESSBOOKS_APP_PASSWORD=xxxx xxxx xxxx xxxx
"""

import os
import sys
import json
import getpass
import requests
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR / ".env"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def get_config():
    book_url = os.environ.get("PRESSBOOKS_URL")
    if not book_url:
        print("Error: PRESSBOOKS_URL not set in .env file.")
        print("  Add a line like: PRESSBOOKS_URL=https://yourschool.pressbooks.pub/your-book-name")
        sys.exit(1)
    book_url = book_url.rstrip("/")
    parsed = urlparse(book_url)
    path_slug = parsed.path.strip("/").split("/")[-1]
    # Single-book domains can have no path (e.g., https://book.example.edu/).
    # Fall back to the hostname so local chapter files stay namespaced.
    slug = path_slug or (parsed.netloc.split(":")[0] if parsed.netloc else "pressbooks-book")
    return {
        "book_url": book_url,
        "api_base": f"{book_url}/wp-json/pressbooks/v2",
        "chapters_dir": SCRIPT_DIR / slug,
        "slug": slug,
    }


def get_auth():
    user = os.environ.get("PRESSBOOKS_USER")
    if not user:
        print("Error: PRESSBOOKS_USER not set in .env file.")
        sys.exit(1)
    password = os.environ.get("PRESSBOOKS_APP_PASSWORD")
    if not password:
        password = getpass.getpass("Application Password: ")
    return (user, password)


def get_toc():
    cfg = get_config()
    r = requests.get(f"{cfg['api_base']}/toc")
    r.raise_for_status()
    toc = r.json()

    print(f"\n=== {cfg['slug']} — Table of Contents ===\n")

    if toc.get("front-matter"):
        print("Front Matter:")
        for item in toc["front-matter"]:
            print(f"  [{item['id']}] {item['title']}")
        print()

    for part in toc.get("parts", []):
        print(f"Part: {part['title']} (ID: {part['id']})")
        for ch in part.get("chapters", []):
            status = "✓" if ch.get("status") == "publish" else "draft"
            print(f"  [{ch['id']}] {ch['title']}  ({status})")
        print()

    if toc.get("back-matter"):
        print("Back Matter:")
        for item in toc["back-matter"]:
            print(f"  [{item['id']}] {item['title']}")
        print()


def pull_chapter(chapter_id, auth=None):
    cfg = get_config()
    r = requests.get(f"{cfg['api_base']}/chapters/{chapter_id}")
    r.raise_for_status()
    chapter = r.json()

    title = chapter["title"]["rendered"]
    content = chapter["content"]["rendered"]
    slug = chapter.get("slug", f"chapter-{chapter_id}")

    cfg["chapters_dir"].mkdir(parents=True, exist_ok=True)
    filepath = cfg["chapters_dir"] / f"{chapter_id}_{slug}.html"
    filepath.write_text(content, encoding="utf-8")

    # Save metadata alongside
    meta = {
        "id": chapter_id,
        "title": title,
        "slug": slug,
        "status": chapter.get("status"),
        "link": chapter.get("link"),
    }
    meta_path = cfg["chapters_dir"] / f"{chapter_id}_{slug}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Pulled: [{chapter_id}] {title}")
    print(f"  HTML: {filepath}")
    print(f"  Meta: {meta_path}")
    return filepath


def push_chapter(chapter_id, auth=None):
    cfg = get_config()
    if auth is None:
        auth = get_auth()

    # Find the local HTML file
    matches = list(cfg["chapters_dir"].glob(f"{chapter_id}_*.html"))
    if not matches:
        print(f"Error: No local file found for chapter {chapter_id}")
        print(f"  Run 'pull {chapter_id}' first.")
        sys.exit(1)

    filepath = matches[0]
    content = filepath.read_text(encoding="utf-8")

    # Load metadata for title
    meta_path = filepath.with_suffix(".json")
    title = None
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        title = meta.get("title")

    data = {"content": content}
    if title:
        data["title"] = title

    r = requests.post(
        f"{cfg['api_base']}/chapters/{chapter_id}",
        json=data,
        auth=auth,
    )

    if r.status_code == 401:
        print("Error: Authentication failed.")
        print("  Check your username and application password.")
        print("  Make sure the app password has no extra spaces.")
        sys.exit(1)
    elif r.status_code == 403:
        print("Error: Permission denied. Your account may not have edit access to this book.")
        sys.exit(1)

    r.raise_for_status()
    result = r.json()
    print(f"Pushed: [{chapter_id}] {result['title']['rendered']}")
    print(f"  Status: {result.get('status')}")
    print(f"  Link: {result.get('link')}")


def pull_all():
    cfg = get_config()
    r = requests.get(f"{cfg['api_base']}/toc")
    r.raise_for_status()
    toc = r.json()

    chapter_ids = []
    for part in toc.get("parts", []):
        for ch in part.get("chapters", []):
            chapter_ids.append(ch["id"])

    print(f"Pulling {len(chapter_ids)} chapters...\n")
    for cid in chapter_ids:
        pull_chapter(cid)
    print(f"\nDone. Files saved to: {cfg['chapters_dir']}")


def main():
    load_env()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "toc":
        get_toc()
    elif cmd == "pull" and len(sys.argv) == 3:
        pull_chapter(int(sys.argv[2]))
    elif cmd == "push" and len(sys.argv) == 3:
        push_chapter(int(sys.argv[2]))
    elif cmd == "pull-all":
        pull_all()
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
