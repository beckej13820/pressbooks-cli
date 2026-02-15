#!/usr/bin/env python3
"""
Pressbooks CLI
--------------
Pull chapters, edit content, and push updates back to Pressbooks.

Usage:
    python pressbooks_api.py toc                    # Show table of contents
    python pressbooks_api.py pull <content_id>      # Pull chapter/front-matter/back-matter item
    python pressbooks_api.py push <content_id>      # Push local HTML file back to Pressbooks
    python pressbooks_api.py pull-all               # Pull all book content locally

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
    toc = fetch_toc(cfg)

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


def fetch_toc(cfg=None):
    if cfg is None:
        cfg = get_config()
    r = requests.get(f"{cfg['api_base']}/toc")
    r.raise_for_status()
    return r.json()


def endpoint_from_toc_id(content_id, toc):
    for item in toc.get("front-matter", []):
        if item.get("id") == content_id:
            return "front-matter"

    for part in toc.get("parts", []):
        for item in part.get("chapters", []):
            if item.get("id") == content_id:
                return "chapters"

    for item in toc.get("back-matter", []):
        if item.get("id") == content_id:
            return "back-matter"

    return None


def endpoint_label(endpoint):
    if endpoint == "chapters":
        return "chapter"
    if endpoint == "front-matter":
        return "front matter"
    if endpoint == "back-matter":
        return "back matter"
    return "content"


def pull_chapter(content_id, auth=None):
    cfg = get_config()
    toc = fetch_toc(cfg)
    endpoint = endpoint_from_toc_id(content_id, toc)
    if endpoint is None:
        print(f"Error: ID {content_id} was not found in the table of contents.")
        sys.exit(1)

    r = requests.get(f"{cfg['api_base']}/{endpoint}/{content_id}")
    r.raise_for_status()
    chapter = r.json()

    title = chapter["title"]["rendered"]
    content = chapter["content"]["rendered"]
    slug = chapter.get("slug", f"content-{content_id}")

    cfg["chapters_dir"].mkdir(parents=True, exist_ok=True)
    filepath = cfg["chapters_dir"] / f"{content_id}_{slug}.html"
    filepath.write_text(content, encoding="utf-8")

    # Save metadata alongside
    meta = {
        "id": content_id,
        "type": endpoint,
        "title": title,
        "slug": slug,
        "status": chapter.get("status"),
        "link": chapter.get("link"),
    }
    meta_path = cfg["chapters_dir"] / f"{content_id}_{slug}.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Pulled {endpoint_label(endpoint)}: [{content_id}] {title}")
    print(f"  HTML: {filepath}")
    print(f"  Meta: {meta_path}")
    return filepath


def push_chapter(content_id, auth=None):
    cfg = get_config()
    if auth is None:
        auth = get_auth()

    # Find the local HTML file
    matches = list(cfg["chapters_dir"].glob(f"{content_id}_*.html"))
    if not matches:
        print(f"Error: No local file found for content ID {content_id}")
        print(f"  Run 'pull {content_id}' first.")
        sys.exit(1)

    filepath = matches[0]
    content = filepath.read_text(encoding="utf-8")

    # Load metadata for title
    meta_path = filepath.with_suffix(".json")
    title = None
    endpoint = None
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        title = meta.get("title")
        endpoint = meta.get("type")

    if endpoint not in {"chapters", "front-matter", "back-matter"}:
        toc = fetch_toc(cfg)
        endpoint = endpoint_from_toc_id(content_id, toc)

    if endpoint is None:
        print(f"Error: Could not determine content type for ID {content_id}.")
        print("  Pull the item again so metadata includes its type.")
        sys.exit(1)

    data = {"content": content}
    if title:
        data["title"] = title

    r = requests.post(
        f"{cfg['api_base']}/{endpoint}/{content_id}",
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
    print(f"Pushed {endpoint_label(endpoint)}: [{content_id}] {result['title']['rendered']}")
    print(f"  Status: {result.get('status')}")
    print(f"  Link: {result.get('link')}")


def pull_all():
    cfg = get_config()
    toc = fetch_toc(cfg)

    content_ids = []
    for item in toc.get("front-matter", []):
        content_ids.append(item["id"])
    for part in toc.get("parts", []):
        for ch in part.get("chapters", []):
            content_ids.append(ch["id"])
    for item in toc.get("back-matter", []):
        content_ids.append(item["id"])

    print(f"Pulling {len(content_ids)} items (front matter, chapters, back matter)...\n")
    for cid in content_ids:
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
