import importlib
import sys
from pathlib import Path

import pytest

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
        json_eol_style=EolStyle.CRLF,
        max_total_line_length=120,
        indent_spaces=2,
        max_compact_array_complexity=2,
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


def test_minify():
    json_input = Path("tests/data/test-wide-chars.json").read_text()
    ref_output = Path("tests/data/test-wide-chars.ref-2.json").read_text()
    formatter = Formatter()
    test_output = formatter.minify(json_input)
    assert test_output == ref_output


def test_depth():
    json_input = Path("tests/data/test-bool.json").read_text()
    formatter = Formatter()
    test_output = formatter.reformat(json_input, 2)
    assert test_output == '        { "bools": {"true": true, "false": false} }\n'


def test_exceptions():
    with pytest.raises(
        AttributeError,
        match="FracturedJsonOptions property 'non_existent_option' does not exist",
    ):
        _ = FracturedJsonOptions(non_existent_option=True)

    with pytest.raises(
        ValueError,
        match="'INVALID' is not a valid value for TableCommaPlacement",
    ):
        _ = FracturedJsonOptions(table_comma_placement="INVALID")

    with pytest.raises(
        TypeError,
        match="Property max_total_line_length expects int, got str 'INVALID'",
    ):
        _ = FracturedJsonOptions(max_total_line_length="INVALID")

    with pytest.raises(
        TypeError,
        match="Property colon_padding expects bool, got int '5'",
    ):
        _ = FracturedJsonOptions(colon_padding=5)

    with pytest.raises(
        TypeError,
        match=r"Property CommentPolicy expects CommentPolicy enum, got EolStyle",
    ):
        _ = FracturedJsonOptions(comment_policy=EolStyle.CRLF)

    formatter = Formatter()
    with pytest.raises(TypeError, match="Reformat argument 0 must be str, got NoneType"):
        formatter.reformat(None)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Minify argument 0 must be str, got bytes"):
        formatter.minify(b"{}")  # type: ignore[arg-type]

    options = FracturedJsonOptions()
    with pytest.raises(
        AttributeError,
        match="'FracturedJsonOptions' object has no attribute 'invalid'",
    ):
        _ = options.invalid


def test_dll_missing(path_is_file_fails):  # noqa: ARG001
    if "fractured_json" in sys.modules:
        del sys.modules["fractured_json"]

    with pytest.raises(FileNotFoundError) as exc:
        importlib.import_module("fractured_json")

    assert "FracturedJson.dll not found" in str(exc.value)


def test_load_runtime_file_not_found():
    if "fractured_json" in sys.modules:
        del sys.modules["fractured_json"]

    from fractured_json._wrappergen import load_assembly  # noqa: PLC0415

    with pytest.raises(FileNotFoundError) as exc:
        _ = load_assembly("InvalidPath")

    assert "InvalidPath.dll not found at " in str(exc.value)


def test_load_runtime_fails(path_is_file_succeeds):  # noqa: ARG001
    if "fractured_json" in sys.modules:
        del sys.modules["fractured_json"]

    from fractured_json._wrappergen import load_assembly  # noqa: PLC0415

    with pytest.raises(FileNotFoundError) as exc:
        _ = load_assembly("InvalidPath")

    assert "InvalidPath.dll load failed: Unable to find assembly " in str(exc.value)


def test_string_length_property():
    formatter = Formatter()

    def double_len(s: str) -> int:
        return len(s) * 2

    formatter.string_length_func = double_len
    getter = formatter.string_length_func
    assert callable(getter)
    assert getter("abc") == 6


def test_formatter_options():
    opts = FracturedJsonOptions(
        max_total_line_length=80,
        indent_spaces=3,
        comment_policy="REMOVE",
        table_comma_placement="BEFORE_PADDING_EXCEPT_NUMBERS",
        number_list_alignment="LEFT",
        prefix_string="::",
        use_tab_to_indent=False,
    )

    formatter = Formatter()
    formatter.options = opts

    got = formatter.options
    assert got.max_total_line_length == 80
    assert got.indent_spaces == 3
    assert got.comment_policy.name == "REMOVE"

    got.max_total_line_length = 100
    assert got.max_total_line_length == 100
