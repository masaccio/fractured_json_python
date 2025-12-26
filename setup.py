"""Build script including dynamic version.py."""

from pathlib import Path
from tomllib import load as toml_load
from typing import cast

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py as _build_py

ROOT_DIR = Path(__file__).parent


def load_project_metadata() -> dict[str, str | list]:
    """Extract the project data from pyproject.toml."""
    pyproject_file = ROOT_DIR / "pyproject.toml"
    with pyproject_file.open("rb") as f:
        toml = toml_load(f)
        return toml["project"]


def write_version_file(version: str) -> None:
    """Create a __version__ from pyproject.toml."""
    version_file = ROOT_DIR / "src" / "fractured_json" / "_version.py"
    with version_file.open("w") as f:
        print("# Auto-generated during build. Do not edit.", file=f)
        print(file=f)
        print(f'__version__ = "{version}"', file=f)


class build_py(_build_py):  # noqa: N801
    """Overload build_py to generate a version file."""

    def run(self) -> None:
        """Whenever build happens, create the version.py."""
        version = cast("str", load_project_metadata()["version"])
        write_version_file(version)
        super().run()


project = load_project_metadata()
name = cast("str", project["name"])
version = cast("str", project["version"])
description = cast("str", project["description"])
long_description = (ROOT_DIR / cast("str", project["readme"])).read_text(encoding="utf-8")
author_info = cast("dict[str, str]", project["authors"][0])
author = author_info["name"]
author_email = author_info["email"]
license_name = cast("str", project["license"])
python_requires = cast("str", project["requires-python"])
classifiers = cast("list[str]", project["classifiers"])
dependencies = cast("list[str]", project["dependencies"])

setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=author,
    author_email=author_email,
    license=license_name,
    python_requires=python_requires,
    classifiers=classifiers,
    install_requires=dependencies,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "fractured_json": ["FracturedJson.dll"],
    },
    entry_points={
        "console_scripts": [
            "fractured-json = fractured_json._fractured_json:main",
        ],
    },
    cmdclass={
        "build_py": build_py,
    },
)
