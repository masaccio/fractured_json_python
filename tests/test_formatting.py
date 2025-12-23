from fractured_json import EolStyle, Formatter, FracturedJsonOptions


def test_clr_load():
    json_input = (
        '{"Group1":{"X":55,"Y":19,"Z":-4},'
        '"Group2":{"Q":null,"W":[-2,-1,0,1]},'
        '"Distraction":[[],null,null]}'
    )
    ref_output = '{\r\n  "Group1": {"X": 55, "Y": 19, "Z": -4}, \r\n  "Group2": { "Q": null, "W": [-2, -1, 0, 1] }, \r\n  "Distraction": [[], null, null]\r\n}\r\n'

    options = FracturedJsonOptions(
        max_total_line_length=120,
        indent_spaces=2,
        max_compact_array_complexity=2,
        json_eol_style=EolStyle.CRLF,
    )
    formatter = Formatter(options=options)

    output_json = formatter.reformat(json_input)
    assert output_json == ref_output
