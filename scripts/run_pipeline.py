"""Run the whole Recipe Search pipeline end to end.

Steps, in order:
  1. Extract text from every PDF in raw/ -> extracted/*.txt
  2. Check for cookbooks that have been extracted but not yet authored into
     recipes/ (the one step that needs AI assistance) and report them.
  3. Build the search index -> data/index.json
  4. Generate the static site -> site/

Usage:
    python scripts/run_pipeline.py            # extract, index, build
    python scripts/run_pipeline.py --skip-extract
    python scripts/run_pipeline.py --serve    # also serve site/ on localhost

The authoring step (extracted text -> recipes/*.md) is intentionally not
automated: cookbook layouts vary, so it is done with AI assistance. If any
cookbook still needs authoring, this script prints which ones and (unless
--force) stops before building so the index is never silently out of date.
See .github/prompts/process-cookbook-pdfs.prompt.md for the authoring workflow.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import build_index
import build_site
import extract_text

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw"
EXTRACTED_DIR = ROOT / "extracted"
RECIPES_DIR = ROOT / "recipes"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def authored_sources() -> set[str]:
    """Every PDF filename referenced under `sources:` across recipes/*.md."""
    sources: set[str] = set()
    for path in RECIPES_DIR.glob("*.md"):
        match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
        if not match:
            continue
        block = match.group(1)
        # Grab the `sources:` list items up to the next top-level key.
        in_sources = False
        for line in block.splitlines():
            if re.match(r"^sources\s*:", line):
                in_sources = True
                continue
            if in_sources:
                item = re.match(r"^\s*-\s*(.+?)\s*$", line)
                if item:
                    sources.add(item.group(1).strip().strip("\"'"))
                elif line.strip() and not line.startswith(" "):
                    in_sources = False
    return sources


def unauthored_cookbooks() -> list[str]:
    """PDFs in raw/ that no recipe lists as a source yet.

    Byte-identical PDFs (the repo keeps occasional duplicate copies) count as a
    single cookbook: if any copy in a hash-group is authored, the whole group is
    considered covered.
    """
    authored = authored_sources()
    pdfs = sorted(RAW_DIR.glob("*.pdf"))

    groups: dict[str, list[str]] = {}
    for pdf in pdfs:
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        groups.setdefault(digest, []).append(pdf.name)

    missing: list[str] = []
    for names in groups.values():
        if not any(name in authored for name in names):
            missing.append(names[0])
    return sorted(missing)


def serve_site() -> None:
    import http.server
    import functools

    site = ROOT / "site"
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
    httpd = http.server.HTTPServer(("127.0.0.1", 8000), handler)
    print("\nServing site/ at http://127.0.0.1:8000  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run the Recipe Search pipeline.")
    parser.add_argument(
        "--skip-extract", action="store_true",
        help="Skip PDF text extraction (use existing extracted/*.txt).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Build even if some cookbooks have not been authored yet.",
    )
    parser.add_argument(
        "--serve", action="store_true",
        help="Serve the built site on http://127.0.0.1:8000 afterwards.",
    )
    args = parser.parse_args()

    # 1. Extract.
    if args.skip_extract:
        print("== Step 1/4: extract — skipped ==\n")
    else:
        print("== Step 1/4: extract PDFs ==")
        extract_text.main()
        print()

    # 2. Authoring check.
    print("== Step 2/4: authoring check ==")
    missing = unauthored_cookbooks()
    if missing:
        print("These cookbooks have been extracted but have no recipes yet:")
        for name in missing:
            print(f"  - {name}")
        print(
            "\nAuthor them into recipes/*.md from the matching extracted/*.txt.\n"
            "See .github/prompts/process-cookbook-pdfs.prompt.md for the workflow."
        )
        if not args.force:
            print("\nStopping before build. Re-run with --force to build anyway.")
            return 1
        print("\n--force given: building anyway.")
    else:
        print("All cookbooks in raw/ are represented in recipes/.")
    print()

    # 3. Index.
    print("== Step 3/4: build index ==")
    rc = build_index.main()
    if rc:
        return rc
    print()

    # 4. Site.
    print("== Step 4/4: build site ==")
    rc = build_site.main()
    if rc:
        return rc

    if args.serve:
        serve_site()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
