import re
from pathlib import Path

import pytest
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


def test_all_args():
    options = FracturedJsonOptions(
        allow_trailing_commas=True,
        always_expand_depth=2,
        colon_before_prop_name_padding=True,
        colon_padding=True,
        comma_padding=True,
        comment_padding=True,
        comment_policy="PRESERVE",
        indent_spaces=2,
        json_eol_style="LF",
        max_compact_array_complexity=2,
        max_inline_complexity=2,
        max_prop_name_padding=2,
        max_table_row_complexity=2,
        max_total_line_length=100,
        min_compact_array_row_items=2,
        nested_bracket_padding=True,
        number_list_alignment="LEFT",
        prefix_string="::",
        preserve_blank_lines=True,
        simple_bracket_padding=True,
        table_comma_placement="BEFORE_PADDING_EXCEPT_NUMBERS",
        use_tab_to_indent=True,
    )
    formatter = Formatter(options=options)
    test_input = Path("tests/data/test-comments-0.jsonc").read_text()
    test_output = formatter.reformat(test_input)
    ref_output = Path("tests/data/test-comments-0.ref-1.jsonc").read_text()
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
                        if value.lower() in ["true", "false"]:
                            if param == "east_asian_chars":
                                east_asian_chars = bool(value)
                            else:
                                test_options[param] = bool(value)
                        elif value.isnumeric():
                            test_options[param] = int(value)
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


def test_exceptions():
    with pytest.raises(KeyError, match="Unknown option 'non_existent_option'"):
        _ = FracturedJsonOptions(non_existent_option=True)

    with pytest.raises(
        ValueError,
        match="Invalid value 'INVALID' for option table_comma_placement",
    ):
        _ = FracturedJsonOptions(table_comma_placement="INVALID")

    with pytest.raises(
        ValueError,
        match="Invalid value 'INVALID' for option max_total_line_length",
    ):
        _ = FracturedJsonOptions(max_total_line_length="INVALID")

    with pytest.raises(
        ValueError,
        match="Invalid value '5' for option colon_padding",
    ):
        _ = FracturedJsonOptions(colon_padding=5)

    with pytest.raises(
        ValueError,
        match=r"Invalid value 'EolStyle\.CRLF' for option comment_policy",
    ):
        _ = FracturedJsonOptions(comment_policy=EolStyle.CRLF)
