import os
import re
from collections.abc import Callable
from pathlib import Path

from pythonnet import load

from fractured_json._version import __version__  # noqa: F401


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
    ArgumentException,
    Boolean,
    Enum,
    Int32,
    String,
    Type,
)
from System.Reflection import BindingFlags  # pyright: ignore[reportMissingImports] # noqa: E402


def get_object_types() -> dict[str, "System.RuntimeType"]:
    assembly = clr.AddReference("fractured_json/FracturedJson")  # pyright: ignore[reportAttributeAccessIssue]

    return {t.Name: t for t in assembly.GetTypes() if t.BaseType is not None}


def to_snake_case(name: str, upper: bool = True) -> str:  # noqa: FBT001 FBT002
    """Convert Pascal case or camel case to snake case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.upper() if upper else s2.lower()


def snake_enum_to_pascal(name: str) -> str:
    """Convert snake case enum to Pascal case."""
    words = name.split("_")
    return "".join(word.capitalize() for word in words)


class NativeEnum:
    """Generic base class that dynamically maps .NET enums to Pythonic attributes."""

    _native_type = None

    def __init_subclass__(
        cls,
        native_type: object | None = None,
        **kwargs: dict[str, bool | int | str],
    ) -> None:
        super().__init_subclass__(**kwargs)

        # If class is dynamically constructed using type()
        if hasattr(cls, "_native_type") and cls._native_type is not None:
            native_type = cls._native_type

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

    @property
    def name(self) -> str:
        """The string name of the enum value."""
        return self._py_name

    @property
    def value(self) -> int:
        """The integer value of the enum."""
        return self._py_value

    def __init__(self, py_name: str, native_value: int) -> None:
        self._py_name = py_name
        self._py_value = native_value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self._py_name}"

    def __eq__(self, other: "NativeEnum") -> bool:
        if isinstance(other, self.__class__):
            return self._py_value == other._py_value
        return self._py_value == other

    def __hash__(self) -> int:
        return hash(self._py_value)


types = get_object_types()
FormatterType = types["Formatter"]
FracturedJsonOptionsType = types["FracturedJsonOptions"]

__all__ = [
    "Formatter",
    "FracturedJsonOptions",
]
for enum_name in [x.Name for x in types.values() if x.IsEnum]:
    enum_type = type(enum_name, (NativeEnum,), {"_native_type": types[enum_name]})
    globals()[enum_name] = enum_type
    __all__.append(enum_type)  # noqa: PYI056


class FracturedJsonOptions:
    """FracturedJson.FracturedJsonOptions wrapper."""

    def __init__(self, **kwargs: dict[str, int | str | NativeEnum]) -> None:
        """Initialize FracturedJsonOptions with optional keyword arguments."""
        self._dotnet_instance = Activator.CreateInstance(FracturedJsonOptionsType)
        self._properties: dict[str, dict[str, object | str | list | bool]] = {}
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
                "is_enum": bool(prop.PropertyType.IsEnum),
                "enum_names": enum_names,
            }

    def list_options(self) -> dict[str, dict[str, object | str | list | bool]]:
        """Return a dictionary of available options and their metadata."""
        return self._properties

    def get(self, name: str) -> int | bool | str | NativeEnum:
        """Getter for an option that calls the .NET class."""
        prop = self._properties[name]["prop"]
        if self._properties[name]["is_enum"]:
            native_value = prop.GetValue(self._dotnet_instance)
            derived_enum = type(prop.Name, (NativeEnum,), {"_native_type": prop.PropertyType})
            return derived_enum(to_snake_case(str(native_value), upper=True), (int(native_value)))

        return prop.GetValue(self._dotnet_instance)

    @staticmethod
    def _to_dotnet_type(
        prop: "System.Reflection.RuntimePropertyInfo",
        value: int | bool | str | NativeEnum,  # noqa: FBT001
    ) -> Int32 | Boolean | Enum:
        """Convert a Python value to the appropriate .NET type."""
        target_type = prop.PropertyType
        if target_type.FullName in ("System.Int32") and isinstance(value, int):
            return Int32(value)
        if target_type.FullName == "System.Boolean" and isinstance(value, bool):
            return Boolean(value)
        if target_type.FullName == "System.String" and isinstance(value, str):
            return String(value)
        if target_type.IsEnum and isinstance(value, NativeEnum):
            return Enum.Parse(prop.PropertyType, snake_enum_to_pascal(value.name))
        if target_type.IsEnum and isinstance(value, str):
            return Enum.Parse(prop.PropertyType, snake_enum_to_pascal(value))

        msg = f"Unhandled property type: {target_type.FullName}"
        raise ValueError(msg)

    def set(self, name: str, value: int | bool | str | NativeEnum) -> None:  # noqa: FBT001
        """Setter for an option that calls the .NET class."""
        if name not in self._properties:
            msg = f"Unknown option '{name}'"
            raise KeyError(msg)

        prop = self._properties[name]["prop"]
        try:
            prop.SetValue(self._dotnet_instance, self._to_dotnet_type(prop, value), None)
        except ArgumentException as e:
            msg = f"Invalid value '{value}' for option {name}"
            raise ValueError(msg) from e
        except ValueError as e:
            msg = f"Invalid value '{value}' for option {name}"
            raise ValueError(msg) from e

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
        self._dotnet_instance = Activator.CreateInstance(FormatterType)
        if options is not None:
            options_property = FormatterType.GetProperty("Options")
            options_property.SetValue(self._dotnet_instance, options._dotnet_instance)  # noqa: SLF001

    def reformat(self, json_text: str) -> str:
        """Reformat a JSON string and return the formatted result."""
        if not isinstance(json_text, str):
            msg = "json_text must be a str"
            raise TypeError(msg)
        result = self._dotnet_instance.Reformat(String(json_text))
        return str(result)

    def serialize(self, obj: object) -> str:
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
