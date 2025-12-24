import re
from pathlib import Path

import pytest_check as check
from wcwidth import wcswidth

from fractured_json import EolStyle, Formatter, FracturedJsonOptions


def test_clr_load():
    test_input = (
        '{"Group1":{"X":55,"Y":19,"Z":-4},'
        '"Group2":{"Q":null,"W":[-2,-1,0,1]},'
        '"Distraction":[[],null,null]}'
    )
    ref_output = (
        "{\r\n"
        '  "Group1"     : {"X": 55, "Y": 19, "Z": -4},\r\n'
        '  "Group2"     : { "Q": null, "W": [-2, -1, 0, 1] },\r\n'
        '  "Distraction": [[], null, null]\r\n'
        "}\r\n"
    )

    options = FracturedJsonOptions(
        max_total_line_length=120,
        indent_spaces=2,
        max_compact_array_complexity=2,
        json_eol_style=EolStyle.CRLF,
    )
    formatter = Formatter(options=options)

    test_output = formatter.reformat(test_input)
    assert test_output == ref_output


test_data_path = Path("tests/data")


def test_json(pytestconfig):  # noqa: PLR0912, C901
    if pytestconfig.getoption("test_verbose"):
        print("\n")

    if pytestconfig.getoption("test_file") is not None:
        ref_filename = pytestconfig.getoption("test_file")
        source_filenames = [Path(re.sub(r"[.]ref.*", ".json", ref_filename))]
    else:
        source_filenames = sorted(test_data_path.rglob("*.json"))

    for source_filename in source_filenames:
        if source_filename.match("*.ref*"):
            continue

        if pytestconfig.getoption("test_verbose"):
            print(f"*** Overriding source file: {source_filename}")

        with open(source_filename) as f:
            test_input = f.read()

        if pytestconfig.getoption("test_file") is not None:
            ref_filenames = [pytestconfig.getoption("test_file")]
        else:
            ref_filenames = test_data_path.rglob(source_filename.stem + ".ref*")

        test_options = {}
        for ref_filename in ref_filenames:
            if pytestconfig.getoption("test_verbose"):
                print(f"*** Testing {ref_filename}")
            east_asian_chars = False
            with open(ref_filename) as f:
                ref_json = ""
                for line in f:
                    if line.startswith("@"):
                        (param, value) = re.split(r"\s*=\s*", line[1:])
                        value = value.strip()
                        if param == "east_asian_chars":
                            east_asian_chars = bool(value)
                        else:
                            test_options[param] = value
                    else:
                        ref_json += line

            try:
                options = FracturedJsonOptions(**test_options)
            except KeyError as e:
                print(f"Unknown option {e} in {ref_filename}")
                continue

            formatter = Formatter(options)
            if east_asian_chars:
                formatter.string_length_func = lambda s: wcswidth(s)

            test_output = formatter.reformat(test_input)

            if pytestconfig.getoption("test_verbose") and test_output != ref_json:
                test_output_dbg = ">" + re.sub(r"\n", "<\n>", test_output) + "<"
                ref_json_dbg = ">" + re.sub(r"\n", "<\n>", ref_json) + "<"
                print("===== TEST")
                print(test_output_dbg)
                print("===== REF")
                print(ref_json_dbg)
                print("=====")

            check.equal(test_output, ref_json, f"Mismatch in {source_filename} with {ref_filename}")
