import argparse  # noqa: I001
import sys

from wcwidth import wcswidth

from fractured_json import Formatter, FracturedJsonOptions, object_property_info
from fractured_json import __version__ as fractured_json_version  # pyright: ignore[reportAttributeAccessIssue]
from fractured_json.generated.option_descriptions import FLAG_DESCRIPTIONS


def command_line_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Format JSON into compact, human readable form",
        add_help=False,
    )

    parser.add_argument(
        "-h",
        "--help",
        default=False,
        action="store_true",
        help="Show this help message and exit",
    )
    parser.add_argument(
        "-?",
        dest="dos_help",
        default=False,
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Output the script version and exit",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        default=False,
        help="Save any edits back to the input file",
    )
    parser.add_argument(
        "--output",
        "-o",
        action="append",
        help="The output file name(s). The number of output file names must match "
        "the number of input files.",
    )
    default_options = FracturedJsonOptions()
    for name, info in object_property_info(default_options).items():
        # for name, info in sorted(default_options.list_options().items()):
        default = getattr(default_options, name)
        desc = FLAG_DESCRIPTIONS.get(name, "")
        if info["is_enum"]:
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                type=str,
                choices=info["enum_names"],
                default=default.name,
                help=f"{desc} (default={default.name})",
            )
        elif isinstance(default, bool):
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                action="store_true",
                default=default,
                help=f"{desc} (default={default})",
            )
        elif isinstance(default, int):
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                metavar="N",
                type=type(default),
                default=getattr(default_options, name),
                help=f"{desc} (default={default})",
            )
        else:
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                type=type(default),
                default=getattr(default_options, name),
                help=f"{desc} (default={default})",
            )

    parser.add_argument(
        "json",
        nargs="*",
        help='JSON file(s) to parse (or stdin with "-")',
    )
    parser.add_argument(
        "--east-asian-chars",
        default=False,
        action="store_true",
        help="Treat strings as unicode East Asian characters",
    )

    return parser


def main() -> None:
    parser = command_line_parser()

    def die(message: str) -> None:
        print(f"{parser.prog}: {message}", file=sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    if args.version:
        print(fractured_json_version)
    elif len(args.json) == 0 or args.help or args.dos_help:
        parser.print_help()
    else:
        options = FracturedJsonOptions()
        for name in object_property_info(options):
            # for name in options.list_options():
            setattr(options, name, getattr(args, name))
        formatter = Formatter(options=options)
        if args.east_asian_chars:
            formatter.string_length_func = lambda s: wcswidth(s)

        in_files = args.json

        if args.in_place:
            out_files = args.json
        elif args.output is None:
            out_files = [None] * len(in_files)
        else:
            if len(in_files) != len(args.output):
                die("the numbers of input and output file names do not match")
            out_files = args.output

        for fn_in, fn_out in zip(in_files, out_files, strict=True):
            if fn_in == "-":
                in_json_string = sys.stdin.read()
            else:
                try:
                    in_json_string = open(fn_in).read()
                except FileNotFoundError as e:
                    die(str(e))

            out_json_string = formatter.reformat(in_json_string)

            if fn_out is None:
                sys.stdout.write(out_json_string)
            elif not args.in_place or in_json_string != out_json_string:
                open(fn_out, "w").write(out_json_string)


if __name__ == "__main__":  # pragma: no cover
    # execute only if run as a script
    main()
