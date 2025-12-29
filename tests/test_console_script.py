import re
from io import StringIO
from os import environ
from pathlib import Path
from shutil import copy
from sys import modules
from tomllib import loads as toml_loads

import pytest

from fractured_json import (
    __version__ as fractured_json_version,  # pyright: ignore[reportAttributeAccessIssue]
)


def test_version(script_runner):
    ret = script_runner.run(["fractured-json", "--version"], print_result=False)
    assert ret.success
    assert ret.stdout.strip() == fractured_json_version
    assert ret.stderr == ""

    project_toml = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    toml = toml_loads(project_toml)
    project_version = toml["project"]["version"]
    assert ret.stdout.strip() == project_version


def test_help(script_runner):
    ret = script_runner.run(["fractured-json", "--help"], print_result=False)
    assert ret.success
    assert "Format JSON into compact, human readable form" in ret.stdout
    assert "max-total-line-length N" in ret.stdout
    assert ret.stderr == ""


def test_no_args(script_runner):
    ret = script_runner.run(["fractured-json"], print_result=False)
    assert ret.success
    assert "Format JSON into compact, human readable form" in ret.stdout
    assert "max-total-line-length N" in ret.stdout
    assert ret.stderr == ""


def test_question_mark(script_runner):
    ret = script_runner.run(["fractured-json", "-?"], print_result=False)
    assert ret.success
    assert "Format JSON into compact, human readable form" in ret.stdout
    assert "max-total-line-length N" in ret.stdout
    assert ret.stderr == ""


def test_all_args(script_runner, pytestconfig):
    ret = script_runner.run(
        [
            "fractured-json",
            "--allow-trailing-commas",
            "--always-expand-depth=2",
            "--colon-before-prop-name-padding",
            "--colon-padding",
            "--comma-padding",
            "--comment-padding",
            "--comment-policy=PRESERVE",
            "--indent-spaces=2",
            "--json-eol-style=LF",
            "--max-compact-array-complexity=2",
            "--max-inline-complexity=2",
            "--max-prop-name-padding=2",
            "--max-table-row-complexity=2",
            "--max-total-line-length=100",
            "--min-compact-array-row-items=2",
            "--nested-bracket-padding",
            "--number-list-alignment=LEFT",
            "--prefix-string=::",
            "--preserve-blank-lines",
            "--simple-bracket-padding",
            "--table-comma-placement=BEFORE_PADDING_EXCEPT_NUMBERS",
            "--use-tab-to-indent",
            "--east-asian-chars",
            "tests/data/test-comments-0.jsonc",
        ],
        print_result=False,
    )

    ref_output = Path("tests/data/test-comments-0.ref-1.jsonc").read_text()
    if pytestconfig.getoption("test_verbose") and ret.stdout != ref_output:
        json_string_dbg = ">" + re.sub(r"\n", "<\n>", ret.stdout) + "<"
        ref_json_dbg = ">" + re.sub(r"\n", "<\n>", ref_output) + "<"
        print("===== TEST")
        print(json_string_dbg)
        print("===== REF")
        print(ref_json_dbg)
        print("=====")

    assert ret.stderr == ""
    assert ret.success
    assert ret.stdout == ref_output


def test_unicode(script_runner):
    ret = script_runner.run(
        [
            "fractured-json",
            "--east-asian-chars",
            "--json-eol-style=CRLF",
            "tests/data/test-wide-chars.json",
        ],
        print_result=False,
    )
    assert ret.stderr == ""
    assert ret.success
    # Use read_bytes() to get \r
    ref_output = Path("tests/data/test-wide-chars.ref-1.json").read_bytes().decode("utf-8")
    assert ret.stdout == ref_output


@pytest.mark.script_launch_mode("subprocess")
def test_main(script_runner):
    # We need to run as a subprocess so we force the child to read coverage setup if
    # the current pytest is running with coverage
    env = environ.copy()
    if "coverage" in modules:
        env["COVERAGE_PROCESS_START"] = "pyproject.toml"
    ret = script_runner.run(
        ["python3", "-m", "fractured_json", "--help"],
        print_result=False,
        env=env,
    )
    assert ret.stderr == ""
    assert ret.success
    assert "[-h] [-V] [--in-place] [--output OUTPUT]" in ret.stdout


def test_multifile(script_runner):
    ret = script_runner.run(
        ["fractured-json", "tests/data/test-bool.json", "tests/data/test-bool.json"],
        print_result=False,
    )
    assert ret.stderr == ""
    assert ret.success
    assert ret.stdout == '{ "bools": {"true": true, "false": false} }\n' * 2


def test_output(script_runner, tmp_path):
    tmp_file = tmp_path / "test.json"
    ret = script_runner.run(
        ["fractured-json", "tests/data/test-bool.json", "--output", str(tmp_file)],
        print_result=False,
    )
    assert ret.stderr == ""
    assert ret.success
    assert tmp_file.read_text() == '{ "bools": {"true": true, "false": false} }\n'


def test_in_place(script_runner, tmp_path):
    tmp_file = tmp_path / "test.json"
    copy(Path("tests/data/test-bool.json"), tmp_file)
    ret = script_runner.run(
        ["fractured-json", "--in-place", tmp_file],
        print_result=False,
    )
    assert ret.stderr == ""
    assert ret.success
    assert tmp_file.read_text() == '{ "bools": {"true": true, "false": false} }\n'

    timestamp = tmp_file.stat().st_mtime_ns

    ret = script_runner.run(
        ["fractured-json", "--in-place", tmp_file],
        print_result=False,
    )
    assert ret.stderr == ""
    assert ret.success
    assert tmp_file.read_text() == '{ "bools": {"true": true, "false": false} }\n'

    assert timestamp == tmp_file.stat().st_mtime_ns


def test_mismatched_file_count(script_runner):
    ret = script_runner.run(
        [
            "fractured-json",
            "tests/data/test-bool.json",
            "--output",
            "foo",
            "--output",
            "bar",
        ],
        print_result=False,
    )
    assert ret.stderr == "fractured-json: the numbers of input and output file names do not match\n"
    assert ret.returncode == 1


def test_pipe_stdin(script_runner):
    json_input_fh = StringIO(Path("tests/data/test-bool.json").read_text())
    ret = script_runner.run(["fractured-json", "-"], stdin=json_input_fh, print_result=False)
    assert ret.success
    assert ret.stderr == ""
    assert ret.success
    assert ret.stdout == '{ "bools": {"true": true, "false": false} }\n'


def test_missing_file(script_runner, tmp_path):
    ret = script_runner.run(
        ["fractured-json", "file-does-not-exist.json"],
        print_result=False,
    )
    assert not ret.success
    assert "[Errno 2] No such file or directory: 'file-does-not-exist.json'" in ret.stderr
    assert ret.stdout == ""
