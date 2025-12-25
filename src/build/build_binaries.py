"""Build dotnet FracturedJson binaries and copy to Python package."""  # noqa: INP001

import json
import shutil
import subprocess
from os import chdir
from pathlib import Path
from sys import exit

ROOT_DIR = Path(__file__).parent.parent.parent.absolute()
BUILD_DIR = ROOT_DIR / "FracturedJson" / "FracturedJsonCli"
SRC_DIR = ROOT_DIR / "src" / "fractured_json"
TEST_DIR = ROOT_DIR / "tests" / "bin"
VERSION_FILE = SRC_DIR / "_version.py"


def build_binaries() -> None:
    """Build the DLL and CLI as a new .NET project."""
    chdir(BUILD_DIR)
    shutil.rmtree(BUILD_DIR / "bin", ignore_errors=True)
    shutil.rmtree(BUILD_DIR / "obj", ignore_errors=True)

    cmd = ["dotnet", "publish", "-c", "Release"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        print(e.output)
        exit(1)

    print("✅ Built CLI project and DLLs")


def parse_assets_json() -> tuple[Path, str]:
    """Parse project.assets.json for FracturedJson version."""
    assets_filename = BUILD_DIR / "obj" / "project.assets.json"
    if not assets_filename.exists():
        msg = f"Run 'dotnet restore' first: {assets_filename}"
        raise FileNotFoundError(msg)

    assets = json.load(assets_filename.open())
    framework = next(iter(assets["projectFileDependencyGroups"].keys()))
    library_version = assets["project"]["version"]

    print(f"✅ Latest version is {library_version}")
    return (BUILD_DIR / "bin" / "Release" / framework / "publish", library_version)


def create_version_file(version: str) -> None:
    """Create _version.pywith latest FracturedJson version."""
    with open(VERSION_FILE, "w") as f:  # noqa: PTH123
        print('__version__ = "5.0.0"', file=f)
    print(f"✅ Created _version.py with version {version}")


def copy_binary(bin_dir: Path, file: str, target_dir: Path) -> None:
    """Copy built binaries into Python folders."""
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bin_dir / file, target_dir / file)


def main() -> None:
    """Build all the .NET dependencies and copy to the Python package."""
    build_binaries()

    bin_dir, version = parse_assets_json()
    create_version_file(version)
    copy_binary(bin_dir, "FracturedJson.dll", SRC_DIR)
    copy_binary(bin_dir, "Mono.Options.dll", TEST_DIR)
    copy_binary(bin_dir, "FracturedJson.dll", TEST_DIR)
    copy_binary(bin_dir, "FracturedJsonCli", TEST_DIR)
    copy_binary(bin_dir, "FracturedJsonCli.runtimeconfig.json", TEST_DIR)
    copy_binary(bin_dir, "FracturedJsonCli.dll", TEST_DIR)
    print("✅ Copied binaries to test folder")


if __name__ == "__main__":
    main()
