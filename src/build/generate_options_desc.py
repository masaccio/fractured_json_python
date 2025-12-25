"""Generate options descriptions from the FracturedJson wiki."""  # noqa: INP001

import re

import requests
from bs4 import BeautifulSoup

WIKI_OPTIONS = "https://github.com/j-brooke/FracturedJson/wiki/Options"


def to_snake_case(name: str, upper: bool = False) -> str:
    """Convert PascalCase or camelCase to SNAKE_CASE or snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.upper() if upper else s2.lower()


def fetch_options() -> dict[str, str]:
    # Fetch the page
    resp = requests.get(WIKI_OPTIONS)  # noqa: S113
    resp.raise_for_status()

    # Parse HTML
    soup = BeautifulSoup(resp.text, "html.parser")

    options: dict[str, str] = {}
    option_name_map: dict[str, str] = {}
    started = False

    # Each option name is in an H2 inside a DIV.markdown-heading
    for heading_div in soup.select("div.markdown-heading > h2"):
        option_name = heading_div.get_text(strip=True)

        # Some H2 tags are misinterpreted before this first option
        if not started and option_name != "MaxTotalLineLength":
            continue
        started = True

        # Walk forward to find the first <p> after this heading
        desc = None
        for sib in heading_div.parent.next_siblings:
            # Skip non-tag items (whitespace, etc.)
            if not getattr(sib, "name", None):
                continue
            # Stop if we hit another heading section
            if sib.name in {"h1", "h2", "h3"} or (
                sib.name == "div" and "markdown-heading" in sib.get("class", [])
            ):
                break
            # First paragraph is the description
            p = sib.find("p") if sib.name != "p" else sib
            if p:
                # Preserve spaces around <code> tags
                desc = p.get_text(" ", strip=True)
                break

        if desc:
            desc = re.sub(r"\s+\(.*", "", desc)
            desc = re.sub(r"\s+", " ", desc)
            desc = re.sub(r"The default.*", "", desc)
            py_option_name = to_snake_case(option_name, upper=False)
            option_name_map[py_option_name] = option_name
            options[py_option_name] = desc

    # Descriptions may refer to .NET names; convert to Pythonic names
    for py_name, desc in options.items():
        for py_name_2, dotnet_name in option_name_map.items():
            desc = desc.replace(dotnet_name, py_name_2)  # noqa: PLW2901
            desc = desc.replace("_", "-")  # noqa: PLW2901
        options[py_name] = desc
    return options


if __name__ == "__main__":
    options = fetch_options()
    with open("src/fractured_json/generated/option_descriptions.py", "w") as f:
        f.write("# Auto-generated file; do not edit.\n")
        f.write("FLAG_DESCRIPTIONS = {\n")
        f.writelines(f'    "{name}": "{desc}",\n' for name, desc in sorted(options.items()))
        f.write("}\n")
