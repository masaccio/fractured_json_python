import argparse  # noqa: I001
import logging
import sys

from fractured_json import EolStyle, Formatter, FracturedJsonOptions
from fractured_json import _get_version, to_snake_case  # pyright: ignore[reportAttributeAccessIssue]
from fractured_json.generated.option_descriptions import FLAG_DESCRIPTIONS

logger = logging.getLogger(__name__)


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
            default = to_snake_case(str(default), upper=True)
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


def main() -> None:
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
