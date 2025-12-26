import argparse  # noqa: I001
import sys

from wcwidth import wcswidth

from fractured_json import Formatter, FracturedJsonOptions
from fractured_json import __version__ as fractured_json_version  # pyright: ignore[reportAttributeAccessIssue]
from fractured_json.generated.option_descriptions import FLAG_DESCRIPTIONS


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
    for name, info in sorted(default_options.list_options().items()):
        default = default_options.get(name)
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
                default=default_options.get(name),
                help=f"{desc} (default={default})",
            )
        else:
            parser.add_argument(
                f"--{name.replace('_', '-')}",
                type=type(default),
                default=default_options.get(name),
                help=f"{desc} (default={default})",
            )

    parser.add_argument(
        "json",
        nargs="*",
        type=argparse.FileType("r"),
        help='JSON file(s) to parse (or stdin with "-")',
    )
    parser.add_argument(
        "--east-asian-chars",
        default=False,
        action="store_true",
        help="Treat strings as unicode East Asian characters",
    )
    parser.add_argument("-?", dest="dos_help", action="store_true", help=argparse.SUPPRESS)

    return parser


def main() -> None:
    parser = command_line_parser()

    def die(message: str) -> None:
        print(f"{parser.prog}: {message}", file=sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    if args.version:
        print(fractured_json_version)
    elif len(args.json) == 0 or args.dos_help:
        parser.print_help()
    else:
        options = FracturedJsonOptions()
        for name in options.list_options():
            setattr(options, name, getattr(args, name))
        formatter = Formatter(options=options)
        if args.east_asian_chars:
            formatter.string_length_func = lambda s: wcswidth(s)

        in_files = args.json
        out_files = args.output

        if out_files is None:
            for fh in args.json:
                json_input = fh.read()
                output_json = formatter.reformat(json_input)
                print(output_json, end="")
            return

        if len(in_files) != len(out_files):
            die("the numbers of input and output file names do not match")

        for fh_in, fn_out in zip(args.json, args.output, strict=True):
            json_input = fh_in.read()
            output_json = formatter.reformat(json_input)
            with open(fn_out, "w", newline="") as fh_out:
                fh_out.write(output_json)


if __name__ == "__main__":  # pragma: no cover
    # execute only if run as a script
    main()
