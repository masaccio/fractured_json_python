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
PYPROJECT_FILE = ROOT_DIR / "pyproject.toml"


def build_binaries() -> None:
    """Build the DLL and CLI as a new .NET project."""
    chdir(BUILD_DIR)
    shutil.rmtree(BUILD_DIR / "bin", ignore_errors=True)
    shutil.rmtree(BUILD_DIR / "obj", ignore_errors=True)

    cmd = ["dotnet", "publish", "-c", "Release"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        print("🛑 CLI build failed")
        print(e.output)
        exit(1)

    print("✅ Built CLI project and DLLs")


def parse_assets_json() -> tuple[Path, str]:
    """Parse project.assets.json for FracturedJson version."""
    assets_filename = BUILD_DIR / "obj" / "project.assets.json"
    if not assets_filename.exists():
        print("🛑 project.assets.json missing")
        msg = f"Run 'dotnet restore' first: {assets_filename}"
        raise FileNotFoundError(msg)

    assets = json.load(assets_filename.open())
    framework = next(iter(assets["projectFileDependencyGroups"].keys()))
    library_version = assets["project"]["version"]

    print(f"✅ Latest version is {library_version}")
    return (BUILD_DIR / "bin" / "Release" / framework / "publish", library_version)


def update_version(version: str) -> None:
    """Update pyproject.toml if FracturedJson version is newer."""
    new_project_toml = ""
    patch_version = True
    for line in PYPROJECT_FILE.read_text().splitlines():
        if line.startswith("version"):
            # Expect: version = "5.0.0post5" / version = "5.0.1"
            toml_version = line.split("=")[1].strip().replace('"', "")
            patch_version = False
            if "post" in toml_version:
                toml_base_version = toml_version.split("post")[0]
                if toml_base_version != version:
                    patch_version = True
            elif toml_version != version:
                patch_version = True
            if patch_version:
                line = f'version = "{version}'  # noqa: PLW2901
        new_project_toml += line + "\n"
    if patch_version:
        PYPROJECT_FILE.write_text(new_project_toml)
        print(f"⚠️ Updated pyproject.toml with version {version}")
    else:
        print(f"✅ pyproject.toml version {toml_version} matches version {version}")


def copy_binary(bin_dir: Path, file: str, target_dir: Path) -> None:
    """Copy built binaries into Python folders."""
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bin_dir / file, target_dir / file)


def main() -> None:
    """Build all the .NET dependencies and copy to the Python package."""
    build_binaries()

    bin_dir, version = parse_assets_json()
    update_version(version)
    copy_binary(bin_dir, "FracturedJson.dll", SRC_DIR)
    copy_binary(bin_dir, "Mono.Options.dll", TEST_DIR)
    copy_binary(bin_dir, "FracturedJson.dll", TEST_DIR)
    copy_binary(bin_dir, "FracturedJsonCli", TEST_DIR)
    copy_binary(bin_dir, "FracturedJsonCli.runtimeconfig.json", TEST_DIR)
    copy_binary(bin_dir, "FracturedJsonCli.dll", TEST_DIR)
    print("✅ Copied binaries to test folder")


if __name__ == "__main__":
    main()
