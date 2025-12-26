# fractured-json

[![build:](https://github.com/masaccio/fractured-json-python/actions/workflows/run-all-tests.yml/badge.svg)](https://github.com/masaccio/fractured-json-python/actions/workflows/run-all-tests.yml)

[![build:](https://github.com/masaccio/fractured-json-python/actions/workflows/codeql.yml/badge.svg)](https://github.com/masaccio/fractured-json-python/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/masaccio/fractured-json-python/branch/main/graph/badge.svg?token=EKIUFGT05E)](https://codecov.io/gh/masaccio/fractured-json-python)

`fractured-json` is a python wrapper of [FracturedJson](https://github.com/j-brooke/FracturedJson) by [j-brooke](https://github.com/j-brooke). The package fully follows the .NET version and includes the required assembly to run as long as you have installed a suitabe .NET runtime.

## Installation

You must install a valid .NET runtime that is compatible with [Python.NET](https://pythonnet.github.io) (`pythonnet`). The package honors the environment variable `PYTHONNET_RUNTIME` for selecting the runtime variant but defaults to `coreclr`. As of current testing, Python versions 3.11 through 3.12 and .NET versions 7.0 and 8.0 are supported. Later versions are currently not supported by `pythonnet`.

You can download the Core .NET runtime from the [Microsoft .NET website](https://dotnet.microsoft.com/en-us/download/dotnet/8.0) and version 8.0 is recommended as the stable and long-term supported version. Once installed, installation is simply:

``` shell
python3 -m pip install fractured-json
```

There is a pure Python implementation of a JSON compactor called [`compact-json`](https://github.com/masaccio/compact-json) however this has now been archived on PyPI and will receive no further development.

The [FracturedJson Wiki](https://github.com/j-brooke/FracturedJson/wiki) provides full documentation of intent, and a description of the options. This README is untended to cover only the Python specific elements of the wrapper.

## Command-line

The package installs a command-line script `fractured-json` which can compact one or more JSON files according to command-line switches.

``` text
usage: fractured-json [-h] [-V] [--output OUTPUT]
                      [--allow-trailing-commas] [--always-expand-depth N]
                      [--colon-before-prop-name-padding] [--colon-padding]
                      [--comma-padding] [--comment-padding]
                      [--comment-policy {TREAT_AS_ERROR,REMOVE,PRESERVE}]
                      [--indent-spaces N]
                      [--json-eol-style {DEFAULT,CRLF,LF}]
                      [--max-compact-array-complexity N]
                      [--max-inline-complexity N]
                      [--max-prop-name-padding N]
                      [--max-table-row-complexity N]
                      [--max-total-line-length N]
                      [--min-compact-array-row-items N]
                      [--nested-bracket-padding]
                      [--number-list-alignment {LEFT,RIGHT,DECIMAL,
                                                NORMALIZE}]
                      [--prefix-string PREFIX_STRING]
                      [--preserve-blank-lines] [--simple-bracket-padding]
                      [--table-comma-placement {BEFORE_PADDING,AFTER_PADDING,
                                                BEFORE_PADDING_EXCEPT_NUMBERS}]
                      [--use-tab-to-indent] [--east-asian-chars]
                      [json ...]

Format JSON into compact, human readable form

positional arguments:
  json                  JSON file(s) to parse (or stdin with "-")

options:
  -h, --help            show this help message and exit
  -V, --version
  --output, -o OUTPUT   The output file name(s). The number of output file
                        names must match the number of input files.
  --allow-trailing-commas
                        If true, the final element in an array or object
                        in the input may have a comma after it; otherwise
                        an exception is thrown. The JSON standard doesn't
                        allow trailing commas, but some other tools allow
                        them, so the option is provided for
                        interoperability with them. (default=False)
  --always-expand-depth N
                        Forces elements close to the root to always fully
                        expand, regardless of other settings. (default=-1)
  --colon-before-prop-name-padding
                        Set to true if you want colons to the left of the
                        spaces uses to line up expanded properties. false
                        puts them after the padding, in a row of their
                        own. (default=False)
  --colon-padding       If true, a space is added after a colon.
                        (default=True)
  --comma-padding       If true, a space is added after a comma.
                        (default=True)
  --comment-padding     If true, a space is added between a prefix/postfix
                        comment and the element to which it is attached.
                        (default=True)
  --comment-policy {TREAT_AS_ERROR,REMOVE,PRESERVE}
                        Determines how comments should be handled. The
                        JSON standard doesn't allow comments, but as an
                        unofficial extension they are fairly wide-spread
                        and useful. (default=TREAT_AS_ERROR)
  --indent-spaces N     Indents by this number of spaces for each level of
                        depth. If use-tab-to-indent=true , tab characters
                        will be used instead of spaces, but the indent-
                        spaces value will still be used to calculate line
                        lengths. (default=4)
  --json-eol-style {DEFAULT,CRLF,LF}
                        Determines which sort of line endings to use.
                        (default=DEFAULT)
  --max-compact-array-complexity N
                        Maximum nesting level that can be arranged
                        spanning multiple lines, with multiple items per
                        line. (default=2)
  --max-inline-complexity N
                        The maximum nesting level that can be displayed on
                        a single line. A primitive type or an empty array
                        or object has a complexity of 0. An object or
                        array has a complexity of 1 greater than its most
                        complex child. (default=2)
  --max-prop-name-padding N
                        Expanded object property values will be lined up
                        as long as the size difference in labels is this
                        value or less. Generally, lining up the property
                        values looks good as long as the labels are
                        roughly the same size, but not if they vary a lot.
                        This only applies to expanded objects; table
                        properties are lined up no matter what.
                        (default=16)
  --max-table-row-complexity N
                        Maximum nesting level allowed in a row of a table-
                        formatted array/object. (default=2)
  --max-total-line-length N
                        Maximum length of a line, including indentation
                        and everything, for purposes of deciding how much
                        to pile together. (default=120)
  --min-compact-array-row-items N
                        Minimum number of items per line to be eligible
                        for compact-multiline-array formatting.
                        (default=3)
  --nested-bracket-padding
                        If true, a space is added between an
                        array/object's brackets and its contents, if that
                        array/object has a complexity of 2 or more. That
                        is, if it contains non-empty arrays/objects.
                        (default=True)
  --number-list-alignment {LEFT,RIGHT,DECIMAL,NORMALIZE}
                        Controls how lists or table columns that contain
                        only numbers and nulls are aligned. In all cases
                        other than Normalize , numbers in the output are
                        exactly the same as in the input document. In all
                        cases, values too big to fit into a 64-bit float
                        or integer are preserved without issue.
                        (default=DECIMAL)
  --prefix-string PREFIX_STRING
                        A string to be included at the start of every line
                        of output. Note that if this string is anything
                        other than whitespace, it will probably make the
                        output invalid as JSON. (default=)
  --preserve-blank-lines
                        If true, blank lines (default=False)
  --simple-bracket-padding
                        If true, a space is added between an
                        array/object's brackets and its contents, if that
                        array/object has a complexity of 1. That is, if it
                        only contains primitive elements and/or empty
                        arrays/objects. (default=False)
  --table-comma-placement {BEFORE_PADDING,AFTER_PADDING,
                           BEFORE_PADDING_EXCEPT_NUMBERS}
                        Where to place commas in table-formatted elements.
                        (default=BEFORE_PADDING_EXCEPT_NUMBERS)
  --use-tab-to-indent   If true, a single tab character is used per
                        indentation level, instead of spaces.
                        (default=False)
  --east-asian-chars    Treat strings as unicode East Asian characters
```

The option `--east-asian-chars` indicates that `fractured-json` should take account of variable width East-Asian character sets when reformatting JSON.

Multiple files and output files can be processed at once but the number of input and output files must match:

``` text
fractured-json --output new_json_1.json --output new_json_2.json json_1.json json_2.json
```

Command-line help is printed when no arguments are passed, with `--help`, ``-h`` or ``-?``.

## API Usage

Follow the following steps to reformat JSON strings:

* Optionally configure  settings using a `fractured_json.FracturedJsonOptions` instance
* Instantiate an instance of `fractured_json.Formatter`
* Call `Formatter.reformat()`.

Example:

``` python
>>> from fractured_json import Formatter, FracturedJsonOptions
>>> options = FracturedJsonOptions(indent_spaces=4)
>>> formatter = Formatter(options)
>>> formatter.reformat('{"a":1}')
'{"a": 1}\n'
```

### Options

A full description of the options available can be found in the [FracturedJson Wiki](https://github.com/j-brooke/FracturedJson/wiki/Options) and these are dynamically created from the .NET library so will always match the .NET implementation.

``` python
from fractured_json import Formatter, FracturedJsonOptions, CommentPolicy
from pathlib import Path

options = FracturedJsonOptions(
    allow_trailing_commas=True,
    always_expand_depth=2,
    colon_before_prop_name_padding=True,
    comment_policy=CommentPolicy.PRESERVE
    indent_spaces=2,
)
formatter = Formatter(options=options)
json_input = Path("example.jsonc").read_text()
json_output = formatter.reformat(json_input)
```

Enumerations can be passed to `FracturedJsonOptions` as strings or as Python-style enums:

``` python
>>> from fractured_json import NumberListAlignment
>>> FracturedJsonOptions(number_list_alignment=NumberListAlignment.LEFT)
<fractured_json.FracturedJsonOptions object at 0x10966fc50>
>>> FracturedJsonOptions(number_list_alignment="LEFT")
<fractured_json.FracturedJsonOptions object at 0x10966f9d0>
```

### Wide character support

When formatting dictionaries, FracturedJson needs to know the length of strings and for some East-Asian characters, the rendering width needs to be adjusted. The `Formatter.string_length_func` property is used to specify an alternative function to calculate strings lengths. The easiest approach is to use `wcwidth.wcswidth` which is packaged with `fractured-json` as a dependency:

``` python
options = FracturedJsonOptions()
formatter = Formatter(options=options)
formatter.string_length_func = lambda s: wcswidth(s)
```

## License

All code in this repository is licensed under the [MIT License](https://github.com/masaccio/fractured-json/blob/master/LICENSE.rst)

## Contribute

Contributions are greatly appreciated and welcomed. Please follow the [project guidance](CONTRIBUTING.md) on how to contribute.

Feel free to [join the discussion about the python wrapper](https://github.com/j-brooke/FracturedJson/discussions/48). The goal of the python wrapper is to track the .NET core of the JSON formatter and provide all the features of the .NET version in python. 
