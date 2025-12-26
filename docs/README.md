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
__COMMAND_LINE_HELP__
```

The option `--east-asian-chars` indicates that `fractured-json` should take account of variable width East-Asian character sets when reformatting JSON.

Multiple files and output files can be processed at once but the number of input and output files must match:

``` text
fractured-json --output new_json_1.json --output new_json_2.json json_1.json json_2.json
```

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
