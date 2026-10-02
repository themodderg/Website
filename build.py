#!/usr/bin/env python3
"""Assemble the published site into dist/.

Sources live split across the repo:
  - index.html, portfolio.html, privacy-policy.html  -> site entry points, kept in repo root
  - pages/<mod>/*.html                                -> one folder per mod, flattened on build
  - src/                                              -> shared assets (css, js, images)
  - ads.txt, _redirects                               -> served from the site root

Every page filename is globally unique (mod prefix + name), so pages/<mod>/foo.html
is published flat as dist/foo.html. That keeps the public URLs identical to the old
flat-root layout while letting the sources stay organised in folders.

dist/ is committed and is what Cloudflare serves (see wrangler.jsonc assets.directory).
Run this after any content change, then commit dist/ alongside the sources.
"""

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DIST = REPO_ROOT / "dist"
PAGES_DIR = REPO_ROOT / "pages"
SRC_DIR = REPO_ROOT / "src"

# Entry-point pages that stay in the repo root and publish unchanged at the site root.
ROOT_PAGES = ["index.html", "portfolio.html", "privacy-policy.html"]

# Non-HTML files served straight from the site root.
ROOT_FILES = ["ads.txt", "_redirects"]


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    published: dict[str, Path] = {}

    def claim(name: str, source: Path) -> None:
        if name in published:
            raise SystemExit(
                f"name collision: '{name}' from {source} already published "
                f"from {published[name]}"
            )
        published[name] = source

    # 1. Root entry pages -> dist root, unchanged.
    for name in ROOT_PAGES:
        src = REPO_ROOT / name
        if not src.is_file():
            raise SystemExit(f"missing root page: {src}")
        claim(name, src)
        shutil.copy2(src, DIST / name)

    # 2. pages/<mod>/*.html -> flattened to dist root.
    for html in sorted(PAGES_DIR.rglob("*.html")):
        name = html.name
        claim(name, html)
        shutil.copy2(html, DIST / name)

    # 3. Root-served non-HTML files.
    for name in ROOT_FILES:
        src = REPO_ROOT / name
        if not src.is_file():
            raise SystemExit(f"missing root file: {src}")
        shutil.copy2(src, DIST / name)

    # 4. Shared assets, preserving their src/ path (pages reference ./src/...).
    shutil.copytree(SRC_DIR, DIST / "src")

    html_count = sum(1 for n in published)
    print(f"built dist/: {html_count} html pages + {len(ROOT_FILES)} root files + src/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
