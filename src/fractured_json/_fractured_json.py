import argparse
import logging
import sys

from fractured_json import EolStyle, Formatter, FracturedJsonOptions, _get_version

logger = logging.getLogger(__name__)

FLAG_DESCRIPTIONS = {
    "max_total_line_length": "Maximum length of a line, including indentation and everything, for purposes of deciding how much to pile together.",
    "max_inline_length": "Like MaxTotalLineLength, this is used to limit how much gets put onto one line. But this one doesn't count indentation. You might use this instead of MaxTotalLineLength if you want to be sure that similar structures at different depths are formatted the same.",
    "max_inline_complexity": "The maximum nesting level that can be displayed on a single line. A primitive type or an empty array or object has a complexity of 0. An object or array has a complexity of 1 greater than its most complex child.",
    "max_compact_array_complexity": "Maximum nesting level that can be arranged spanning multiple lines, with multiple items per line.",
    "max_table_row_complexity": "Maximum nesting level allowed as a row of a table-formatted array/object.",
    "table_comma_placement": "Where to place commas in table-formatted elements.",
    "min_compact_array_row_items": "Minimum number of items per line to be eligible for compact-multiline-array formatting. (This isn't exact - some data sets could confuse the evaluation.)",
    "always_expand_depth": "Forces elements close to the root to always fully expand, regardless of other settings.",
    "indent_spaces": "Indents by this number of spaces for each level of depth. (Ignored if UseTabToIndent=true.)",
    "use_tab_to_indent": "If true, a single tab character is used to indent, instead of spaces.",
    "simple_bracket_padding": "If true, a space is added between an array/object's brackets and its contents, if that array/object has a complexity of 1. That is, if it only contains primitive elements and/or empty arrays/objects.",
    "nested_bracket_padding": "If true, a space is added between an array/object's brackets and its contents, if that array/object has a complexity of 2 or more. That is, if it contains non-empty arrays/objects.",
    "colon_padding": "If true, a space is added after a colon.",
    "comma_padding": "If true, a space is added after a comma.",
    "comment_padding": "If true, a space is added between a prefix/postfix comment and the element to which it is attached.",
    "omit_trailing_whitespace": "If true, the generated JSON text won't have spaces at the ends of lines. If OmitTrailingWhitespace is false and CommaPadding is true, often lines will end in a space. (There are a few other cases where it can happen too.) Defaults to false in the .NET and JavaScript libraries for sake of backward compatibility.",
    "json_eol_style": "Determines which sort of line endings to use.",
    "number_list_alignment": "Controls how lists or table columns that contain only numbers and nulls are aligned.",
    "comment_policy": "Determines how comments should be handled. The JSON standard doesn't allow comments, but as an unofficial extension they are fairly wide-spread and useful.",
    "allow_trailing_commas": "If true, the final element in an array or object in the input may have a comma after it; otherwise an exception is thrown. The JSON standard doesn't allow trailing commas, but some other tools allow them, so the option is provided for interoperability with them.",
    "prefix_string": "A string to be included at the start of every line of output. Note that if this string is anything other than whitespace, it will probably make the output invalid as JSON.",
}


def command_line_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Format JSON into compact, human readable form",
    )
    parser.add_argument("-V", "--version", action="store_true")

    parser.add_argument(
        "--output",
        "-o",
        action="append",
        help="The output file name(s). The number of output file names must match "
        "the number of input files.",
    )
    default_options = FracturedJsonOptions()
    for name, info in default_options.list_options().items():
        default = default_options.get(name)
        help = FLAG_DESCRIPTIONS.get(name, "")
        if info["is_enum"]:
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                type=str,
                choices=info["enum_names"],
                default=default_options.get(name),
                help=f"{help} (default={default})",
            )
        elif isinstance(default, bool):
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                action="store_true" if not default else "store_false",
                default=default,
                help=f"{help} (default={default})",
            )
        else:
            # We know this to be an int
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                metavar="N",
                type=type(default),
                default=default_options.get(name),
                help=f"{help} (default={default})",
            )

    parser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--east-asian-chars",
        default=False,
        action="store_true",
        help="Treat strings as unicode East Asian characters",
    )
    parser.add_argument(
        "json",
        nargs="*",
        type=argparse.FileType("r"),
        help='JSON file(s) to parse (or stdin with "-")',
    )
    return parser


def main() -> None:  # noqa: C901, PLR0915, PLR0912
    parser = command_line_parser()

    def die(message: str) -> None:
        print(f"{parser.prog}: {message}", file=sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    if args.version:
        print(_get_version())
    elif len(args.json) == 0:
        parser.print_help()
    else:
        formatter = Formatter()
        default_options = FracturedJsonOptions()
        for name in default_options.list_options():
            setattr(formatter, name, getattr(args, name))

        hdlr = logging.StreamHandler()
        hdlr.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(hdlr)
        if args.debug:
            logger.setLevel("DEBUG")
        else:
            logger.setLevel("ERROR")

        line_ending = "\r\n" if args.json_eol_style == EolStyle.CRLF else "\n"

        in_files = args.json
        out_files = args.output

        if out_files is None:
            for fh in args.json:
                json_input = fh.read()
                output_json = formatter.reformat(json_input)
                print(output_json, end=line_ending)
            return

        if len(in_files) != len(out_files):
            die("the numbers of input and output file names do not match")

        for fh_in, fn_out in zip(args.json, args.output):
            json_input = fh_in.read()
            output_json = formatter.reformat(json_input)
            with open(fn_out, "w", newline="") as fh_out:
                fh_out.write(output_json)


if __name__ == "__main__":  # pragma: no cover
    # execute only if run as a script
    main()
