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


def test_minify():
    json_input = Path("tests/data/test-wide-chars.json").read_text()
    ref_output = Path("tests/data/test-wide-chars.ref-2.json").read_text()
    formatter = Formatter()
    test_output = formatter.minify(json_input)
    assert test_output == ref_output


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
