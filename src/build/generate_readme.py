"""Patch the README template with the most recent command-line help."""

import subprocess
from os import environ
from pathlib import Path
from typing import Final


def main() -> None:
    docs_readme: Final[Path] = Path("docs/README.md")
    out_readme: Final[Path] = Path("README.md")

    environ["COLUMNS"] = "76"
    result = subprocess.run(
        ["fractured-json", "--help"],  # noqa: S607
        check=True,
        capture_output=True,
        text=True,
        env={**subprocess.os.environ, "COLUMNS": "76"},
    )
    help_text = result.stdout

    text = docs_readme.read_text(encoding="utf-8")

    marker = "__COMMAND_LINE_HELP__\n"
    if marker not in text:
        msg = f"Marker {marker!r} not found in {docs_readme}"
        raise RuntimeError(msg)

    if not help_text.endswith("\n"):
        help_text += "\n"
    new_text = text.replace(marker, help_text)

    out_readme.write_text(new_text, encoding="utf-8")


if __name__ == "__main__":
    main()
