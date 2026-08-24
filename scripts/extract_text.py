"""Extract selectable text from every PDF in raw/ into extracted/<name>.txt.

These PDFs are text-based (no OCR). Each output file preserves the original
PDF filename (with a .txt extension) so later stages can trace recipes back to
their source cookbook.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import pymupdf  # PyMuPDF (>=1.24)
except ImportError:  # pragma: no cover
    sys.exit(
        "PyMuPDF is required. Install dependencies with:\n"
        "    pip install -r requirements.txt"
    )

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw"
OUT_DIR = ROOT / "extracted"

PAGE_SEPARATOR = "\n\n----- PAGE {n} -----\n\n"


def extract_pdf(pdf_path: Path) -> tuple[str, int]:
    """Return (text, page_count) for a single PDF."""
    parts: list[str] = []
    with pymupdf.open(pdf_path) as doc:
        page_count = doc.page_count
        for index, page in enumerate(doc, start=1):
            parts.append(PAGE_SEPARATOR.format(n=index))
            parts.append(page.get_text("text"))
    return "".join(parts).strip(), page_count


def main() -> int:
    if not RAW_DIR.is_dir():
        sys.exit(f"Missing raw directory: {RAW_DIR}")

    OUT_DIR.mkdir(exist_ok=True)

    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {RAW_DIR}")

    empty: list[str] = []
    print(f"Extracting {len(pdfs)} PDF(s) -> {OUT_DIR}\n")

    for pdf_path in pdfs:
        try:
            text, pages = extract_pdf(pdf_path)
        except (RuntimeError, OSError, ValueError) as exc:
            print(f"  [ERROR] {pdf_path.name}: {exc}")
            continue

        out_path = OUT_DIR / (pdf_path.stem + ".txt")
        out_path.write_text(text, encoding="utf-8")

        char_count = len(text)
        flag = ""
        if char_count < 200:
            empty.append(pdf_path.name)
            flag = "  <-- little/no text (possibly scanned)"
        print(f"  {pdf_path.name}: {pages} page(s), {char_count} chars{flag}")

    print("\nDone.")
    if empty:
        print(
            "\nWARNING: the following files produced little or no selectable "
            "text and may be scanned images needing OCR:"
        )
        for name in empty:
            print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
