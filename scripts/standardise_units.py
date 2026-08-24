"""Standardise units/measurements across every recipe in recipes/.

Encodes the house style from the ``measurement-standardisation`` skill:

  * abbreviations -> full words (tbsp -> tablespoons, g -> grams, ml ->
    millilitres, ...), choosing singular/plural from the quantity,
  * Unicode fractions -> ASCII (1/2, 1/4, 3/4, ...),
  * oven temperatures -> ``180°C`` / ``350°F`` form.

All replacements are *number-anchored*: a unit is only rewritten when it
immediately follows a quantity, so ordinary prose ("2 green chillies",
"1 lemon") is never touched. The script is idempotent -- running it again
makes no further changes.

Only the Markdown body is transformed; the YAML frontmatter is left as-is.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECIPES_DIR = ROOT / "recipes"

# --- Unicode fractions -----------------------------------------------------

FRACTIONS = {
    "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5", "⅙": "1/6",
    "⅚": "5/6", "⅐": "1/7", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8",
    "⅞": "7/8", "⅑": "1/9", "⅒": "1/10",
}
_FRAC_CLASS = "".join(re.escape(g) for g in FRACTIONS)

# --- Units (matched case-insensitively, longest alternative first) ---------

# abbreviation -> (singular, plural)
UNIT_FORMS = {
    "tbsp": ("tablespoon", "tablespoons"),
    "tbs": ("tablespoon", "tablespoons"),
    "tbl": ("tablespoon", "tablespoons"),
    "tsp": ("teaspoon", "teaspoons"),
    "kgs": ("kilogram", "kilograms"),
    "kg": ("kilogram", "kilograms"),
    "mg": ("milligram", "milligrams"),
    "grm": ("gram", "grams"),
    "gm": ("gram", "grams"),
    "gr": ("gram", "grams"),
    "g": ("gram", "grams"),
    "mls": ("millilitre", "millilitres"),
    "ml": ("millilitre", "millilitres"),
    "cl": ("centilitre", "centilitres"),
    "dl": ("decilitre", "decilitres"),
    "ltr": ("litre", "litres"),
    "l": ("litre", "litres"),
    "floz": ("fluid ounce", "fluid ounces"),
    "fl oz": ("fluid ounce", "fluid ounces"),
    "oz": ("ounce", "ounces"),
    "lbs": ("pound", "pounds"),
    "lb": ("pound", "pounds"),
    "pt": ("pint", "pints"),
    "qt": ("quart", "quarts"),
    "gal": ("gallon", "gallons"),
    "cm": ("centimetre", "centimetres"),
    "mm": ("millimetre", "millimetres"),
    "mins": ("minute", "minutes"),
    "min": ("minute", "minutes"),
    "hrs": ("hour", "hours"),
    "hr": ("hour", "hours"),
    "secs": ("second", "seconds"),
    "sec": ("second", "seconds"),
}

# Longest-first so e.g. "kg"/"ml"/"lb" win over the bare "g"/"l".
_UNIT_ALT = "|".join(
    re.escape(u) for u in sorted(UNIT_FORMS, key=len, reverse=True)
)
# quantity = mixed number ("1 1/2"), plain fraction ("1/2") or a decimal.
_QTY = r"\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?"
UNIT_RE = re.compile(
    rf"(?P<qty>{_QTY})\s*(?P<unit>{_UNIT_ALT})\b",
    re.IGNORECASE,
)

FRONTMATTER_RE = re.compile(r"^(---\s*\n.*?\n---\s*\n?)(.*)$", re.DOTALL)


def is_plural(qty: str) -> bool:
    qty = qty.strip()
    if " " in qty:          # mixed number like "1 1/2" -> > 1
        return True
    if "/" in qty:          # proper fraction -> < 1
        return False
    return float(qty) != 1


def replace_unit(match: re.Match) -> str:
    qty = match.group("qty")
    singular, plural = UNIT_FORMS[match.group("unit").lower()]
    word = plural if is_plural(qty) else singular
    return f"{qty} {word}"


def convert_fractions(text: str) -> str:
    # Composed fraction slash: "1⁄4" -> "1/4".
    text = text.replace("\u2044", "/")
    # "1½" or "1 ½" -> "1 1/2".
    text = re.sub(
        rf"(\d)\s*([{_FRAC_CLASS}])",
        lambda m: f"{m.group(1)} {FRACTIONS[m.group(2)]}",
        text,
    )
    # Standalone glyphs: "½ cup" -> "1/2 cup".
    for glyph, rep in FRACTIONS.items():
        text = text.replace(glyph, rep)
    return text


def convert_temperatures(text: str) -> str:
    # 3-digit oven temperatures only, so cup measures ("2 C") are never hit.
    text = re.sub(
        r"(\d{3})\s*(?:°|degrees?|deg)?\s*C\b", r"\1°C", text
    )
    text = re.sub(
        r"(\d{3})\s*(?:°|degrees?|deg)?\s*F\b", r"\1°F", text
    )
    return text


def standardise(body: str) -> str:
    body = convert_fractions(body)
    body = UNIT_RE.sub(replace_unit, body)
    body = convert_temperatures(body)
    return body


def main() -> None:
    changed = 0
    for path in sorted(RECIPES_DIR.glob("*.md")):
        original = path.read_text(encoding="utf-8")
        m = FRONTMATTER_RE.match(original)
        if m:
            head, body = m.group(1), m.group(2)
        else:
            head, body = "", original
        new = head + standardise(body)
        if new != original:
            path.write_text(new, encoding="utf-8")
            changed += 1
    print(f"Standardised measurements in {changed} recipe file(s).")


if __name__ == "__main__":
    main()
