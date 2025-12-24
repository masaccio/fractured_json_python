import importlib.metadata
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from warnings import warn

from pythonnet import load

__version__ = importlib.metadata.version("fractured-json")


def _get_version() -> str:
    return __version__


__all__ = [
    "CommentPolicy",
    "EolStyle",
    "Formatter",
    "FracturedJsonOptions",
    "TableCommaPlacement",
]


def pythonnet_runtime() -> str:
    # Mono is not supported on Apple Silicon Macs, so we prefer the Core Runtime
    return os.environ.get("PYTHONNET_RUNTIME", "coreclr")


def load_runtime() -> None:
    here = Path(__file__).resolve().parent
    dll_path = here / "FracturedJson.dll"
    if not dll_path.is_file():
        msg = f"FracturedJson.dll not found at {dll_path}"
        raise FileNotFoundError(msg)

    runtime = pythonnet_runtime()
    try:
        load(runtime)
    except RuntimeError as e:
        msg = f"Failed to load pythonnet runtime '{runtime}'. "
        raise RuntimeError(msg) from e


load_runtime()

import clr  # noqa: E402
from System import (  # noqa: E402 # pyright: ignore[reportMissingImports]
    Activator,
    Boolean,
    Int16,
    Int32,
    Int64,
    String,
    Type,
)
from System.Reflection import BindingFlags  # pyright: ignore[reportMissingImports] # noqa: E402


def get_object_types() -> dict[str, "System.RuntimeType"]:
    assembly = clr.AddReference("fractured_json/FracturedJson")  # pyright: ignore[reportAttributeAccessIssue]

    return {t.Name: t for t in assembly.GetTypes() if t.BaseType is not None}


def to_snake_case(name: str, upper: bool = True) -> str:
    """Convert PascalCase or camelCase to SNAKE_CASE or snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.upper() if upper else s2.lower()


class NativeEnum:
    """Generic base class that dynamically maps .NET enums to Pythonic attributes."""

    _native_type = None
    _native_map = None

    def __init_subclass__(cls, native_type: object | None = None, **kwargs: dict[str, Any]) -> None:
        super().__init_subclass__(**kwargs)
        if native_type is None:
            msg = f"{cls.__name__} must set _native_type"
            raise ValueError(msg)

        native_names = [
            str(x)
            for x in native_type.GetEnumNames()  # pyright: ignore[reportAttributeAccessIssue]
        ]
        native_values = [
            int(x)
            for x in native_type.GetEnumValues()  # pyright: ignore[reportAttributeAccessIssue]
        ]

        name_to_value = dict(zip(native_names, native_values, strict=True))

        for native_name in native_names:
            py_name = to_snake_case(native_name, upper=True)
            native_value = name_to_value[native_name]
            # Create instance and store on class
            instance = cls(py_name, native_value)
            setattr(cls, py_name, instance)

    def __init__(self, py_name: str, native_value: str) -> None:
        self._py_name = py_name
        self.value = native_value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self._py_name}"

    def __eq__(self, other: "NativeEnum") -> bool:
        if isinstance(other, self.__class__):
            return self.value == other.value
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)


types = get_object_types()
FormatterType = types["Formatter"]
FracturedJsonOptionsType = types["FracturedJsonOptions"]
CommentPolicyType = types["CommentPolicy"]
EolStyleType = types["EolStyle"]
TableCommaPlacementType = types["TableCommaPlacement"]


def allowed_enum_values(enum_type: str) -> list[str]:
    return [str(x) for x in types[enum_type].GetEnumNames()]


class CommentPolicy(NativeEnum, native_type=CommentPolicyType):
    """FracturedJson.CommentPolicy wrapper."""


class EolStyle(NativeEnum, native_type=EolStyleType):
    """FracturedJson.EolStyle wrapper."""


class TableCommaPlacement(NativeEnum, native_type=TableCommaPlacementType):
    """FracturedJson.TableCommaPlacement wrapper."""


class FracturedJsonOptions:
    """FracturedJson.FracturedJsonOptions wrapper."""

    def __init__(self, **kwargs: dict[str, int | str | NativeEnum]) -> None:
        """Initialize FracturedJsonOptions with optional keyword arguments."""
        self._dotnet_instance = Activator.CreateInstance(FracturedJsonOptionsType)
        self._properties: dict[str, dict[str, Any]] = {}
        self._get_dotnet_props()

        for key, value in kwargs.items():
            self.set(key, value)

    def _get_dotnet_props(self) -> None:
        """Dynamically populate the list of available options through .NET reflection."""
        t = Type.GetType(self._dotnet_instance.GetType().AssemblyQualifiedName)
        props = t.GetProperties(BindingFlags.Public | BindingFlags.Instance)
        for prop in props:
            py_name = to_snake_case(prop.Name, upper=False)
            dotnet_type_name = prop.PropertyType.FullName.split(".")
            is_enum = bool(prop.PropertyType.IsEnum)
            enum_names = (
                [
                    to_snake_case(str(x), upper=True)
                    for x in types[dotnet_type_name[1]].GetEnumNames()
                ]
                if is_enum
                else []
            )
            self._properties[py_name] = {
                "prop": prop,
                "dotnet_name": prop.Name,
                "type": str(prop.PropertyType.FullName),
                "can_read": bool(prop.CanRead),
                "can_write": bool(prop.CanWrite),
                "is_enum": bool(prop.PropertyType.IsEnum),
                "enum_names": enum_names,
            }

    def list_options(self) -> dict[str, dict[str, Any]]:
        """Return a dictionary of available options and their metadata."""
        return self._properties

    def get(self, name: str) -> int | bool | str | NativeEnum:
        """Getter for an option that calls the .NET class."""
        prop = self._properties[name]["prop"]
        if not prop.CanRead:
            msg = f"Option {name} is write-only"
            raise AttributeError(msg)
        return prop.GetValue(self._dotnet_instance, None)

    def set(self, name: str, value: int | bool | str | NativeEnum) -> None:  # noqa: FBT001
        """Setter for an option that calls the .NET class."""
        prop = self._properties[name]["prop"]
        if not prop.CanWrite:
            msg = f"Option {name} is read-only"
            raise AttributeError(msg)

        target_type = prop.PropertyType

        if target_type.FullName in ("System.Int16"):
            value = Int16(value)
        elif target_type.FullName in ("System.Int32"):
            value = Int32(value)
        elif target_type.FullName in ("System.Int64"):
            value = Int64(value)
        elif target_type.FullName == "System.Boolean":
            value = Boolean(value)
        elif target_type.IsEnum:
            value = Int32(value.value)
        else:
            warn(f"Unhandled property type: {target_type.FullName}", stacklevel=2)

        prop.SetValue(self._dotnet_instance, value, None)

    def __getattr__(self, name: str) -> int | bool | str | NativeEnum:
        """Attribute delegation to get option values dynamically."""
        try:
            return self.get(name)
        except AttributeError:
            msg = f"{type(self).__name__} has no attribute {name!r}"
            raise AttributeError(msg) from None

    def __setattr__(self, name: str, value: int | bool | str | NativeEnum) -> None:  # noqa: FBT001
        """Attribute delegation to set option values dynamically."""
        if name in {"_dotnet_instance", "_properties"}:
            object.__setattr__(self, name, value)
        else:
            try:
                self.set(name, value)
            except AttributeError:
                object.__setattr__(self, name, value)


class Formatter:
    """Python wrapper around the FracturedJson .NET Formatter."""

    def __init__(self, options: FracturedJsonOptions | None = None) -> None:
        """Create a new Formatter wrapper; optionally set `options`."""
        if options is None:
            self._dotnet_instance = Activator.CreateInstance(FormatterType)
        else:
            self._dotnet_instance = Activator.CreateInstance(
                FormatterType,
                options._dotnet_instance,  # noqa: SLF001
            )

    def reformat(self, json_text: str) -> str:
        """Reformat a JSON string and return the formatted result."""
        if not isinstance(json_text, str):
            msg = "json_text must be a str"
            raise TypeError(msg)
        result = self._dotnet_instance.Reformat(String(json_text))
        return str(result)

    def serialize(self, obj: Any) -> str:
        """Serialize a Python object to JSON using the underlying .NET implementation."""
        result = self._dotnet_instance.Serialize(obj)
        return str(result)

    @property
    def string_length_func(self) -> Callable[[str], int]:
        """Get current string length function."""
        dotnet_func = self._dotnet_instance.StringLengthFunc
        return lambda s: dotnet_func(String(s))

    @string_length_func.setter
    def string_length_func(self, func: Callable[[str], int]) -> None:
        """Set string length function for Formatter class."""
        if not callable(func):
            msg = "Must be callable (e.g. lambda s: len(s))"
            raise TypeError(msg)

        from System import Func  # pyright: ignore[reportMissingImports] # noqa: PLC0415

        # Wrap Python func as .NET Func<string, int>
        def dotnet_wrapper(s_dotnet: String) -> Int32:
            s_python = str(s_dotnet)
            result = func(s_python)
            return Int32(result)

        self._dotnet_instance.StringLengthFunc = Func[String, Int32](dotnet_wrapper)
