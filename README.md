# fractured-json

[![build:](https://github.com/masaccio/fractured-json/actions/workflows/run-all-tests.yml/badge.svg)](https://github.com/masaccio/fractured-json/actions/workflows/run-all-tests.yml)
[![build:](https://github.com/masaccio/fractured-json/actions/workflows/codeql.yml/badge.svg)](https://github.com/masaccio/fractured-json/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/masaccio/fractured-json/branch/main/graph/badge.svg?token=EKIUFGT05E)](https://codecov.io/gh/masaccio/fractured-json)


`fractured-json` is primarily a python wrapper of of [FracturedJson](https://github.com/j-brooke/FracturedJson) by [j-brooke](https://github.com/j-brooke).

There is a pure Python implementation of a JSON compactor called (`compact-json`)[https://github.com/masaccio/compact-json] however this is unlikely to get maintenance beyond critical bugfixes.

## Plans

**THE PACKAGE IS CURRENTLY UNDER DEVELOPMENT**

Feel free to [join the discussion about the python wrapper](https://github.com/j-brooke/FracturedJson/discussions/48). The goal of the python wrapper is to track the .NET core of the JSON formatter and provide all the features of the .NET version in python. The command-line capabilities of `compact-json` and the FracturedJson CLI are expected to merge.

The API naming style of the python implementation is deliberately different to the .NET core to be as pythonic as possible. Specifically:

* All classes are Pascal case, e.g. FracturedJsonOptions
* All properties are snake case, e.g. json_eol_style
* All enumerations are upper-case snake case within a Python Object, e.g. EolStyle.CRLF. They are not derived from `Enum` but have the same behaviors.

## Installation

You will need to install a .NET runtime that is compatible with [Python.NET](https://pythonnet.github.io) (`pythonnet`). The package honors the environment variable `PYTHONNET_RUNTIME` for selecting the runtime variant but defaults to `coreclr`. As of current testing, Python 3.14 and .NET 10.0 are not supported by `pythonnet`. You can download the Core .NET runtime from the [Microsoft .NET website](https://dotnet.microsoft.com/en-us/download/dotnet/8.0) and version 8.0 is recommended as the stable and long-term supported version.

Once .NET is available, installation is simply:

``` shell
python3 -m pip install fractured-json
```

## License

All code in this repository is licensed under the [MIT License](https://github.com/masaccio/fractured-json/blob/master/LICENSE.rst)

## Contribute

Contributions are greatly appreciated and welcomed. Please follow the [project guidance](CONTRIBUTING.md) on how to contribute.
