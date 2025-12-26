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


_native_enum_cache: dict[str, type] = {}


class NativeEnum:
    """Generic base class that dynamically maps .NET enums to Pythonic attributes.

    Prefer explicit creation via `NativeEnum.from_dotnet_type(dotnet_type)` rather than relying
    on implicit subclass side-effects.
    """

    _native_type = None

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

    @classmethod
    def from_dotnet_type(cls, dotnet_type: object) -> type:
        key = str(dotnet_type)
        if key in _native_enum_cache:
            return _native_enum_cache[key]

        # Create subclass
        name = dotnet_type.Name
        new_cls = type(name, (cls,), {"_native_type": dotnet_type})

        native_names = [str(x) for x in dotnet_type.GetEnumNames()]
        native_values = [int(x) for x in dotnet_type.GetEnumValues()]

        name_to_value: dict[str, int] = {}
        value_to_member: dict[int, NativeEnum] = {}

        for n, v in zip(native_names, native_values, strict=False):
            py_name = to_snake_case(n, upper=True)
            inst = new_cls(py_name, v)
            setattr(new_cls, py_name, inst)
            name_to_value[py_name] = v
            value_to_member[v] = inst

        def from_value(cls2: type, value: int) -> "NativeEnum":
            try:
                return value_to_member[int(value)]
            except Exception as e:
                msg = f"{value} is not a valid value for {cls2.__name__}"
                raise ValueError(msg) from e

        def from_name(cls2: type, name: str) -> "NativeEnum":
            py_name = to_snake_case(name, upper=True)
            try:
                return getattr(cls2, py_name)
            except Exception as e:
                msg = f"{name} is not a valid name for {cls2.__name__}"
                raise ValueError(msg) from e

        def names_fn(_cls: type) -> list[str]:
            return list(name_to_value.keys())

        def values_fn(_cls: type) -> list[int]:
            return list(value_to_member.keys())

        new_cls.from_value = classmethod(from_value)
        new_cls.from_name = classmethod(from_name)
        new_cls.names = classmethod(names_fn)
        new_cls.values = classmethod(values_fn)

        _native_enum_cache[key] = new_cls
        return new_cls


types = get_object_types()
FormatterType = types["Formatter"]
FracturedJsonOptionsType = types["FracturedJsonOptions"]

__all__ = [
    "Formatter",
    "FracturedJsonOptions",
]
for enum_name in [x.Name for x in types.values() if x.IsEnum]:
    enum_type = NativeEnum.from_dotnet_type(types[enum_name])
    globals()[enum_name] = enum_type
    __all__.append(enum_type)  # noqa: PYI056


class FracturedJsonOptions:
    """Configuration container for FracturedJson formatting options."""

    def __init__(self, **kwargs: dict[str, int | str | NativeEnum]) -> None:
        """Initialize FracturedJsonOptions with optional keyword arguments."""
        self._dotnet_instance = Activator.CreateInstance(FracturedJsonOptionsType)
        self._properties: dict[str, dict[str, object | str | list | bool]] = {}

        # Dynamically populate the list of available options through .NET reflection.
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

        for key, value in kwargs.items():
            self.set(key, value)

    def list_options(self) -> dict[str, dict[str, object | str | list | bool]]:
        """Return a dictionary of available options and their metadata."""
        return self._properties

    def get(self, name: str) -> int | bool | str | NativeEnum:
        """Getter for an option that calls the .NET class."""
        prop = self._properties[name]["prop"]
        if self._properties[name]["is_enum"]:
            native_value = prop.GetValue(self._dotnet_instance)
            derived_enum = NativeEnum.from_dotnet_type(prop.PropertyType)
            return derived_enum.from_value(int(native_value))

        return prop.GetValue(self._dotnet_instance)

    @classmethod
    def _from_dotnet(cls, dotnet_instance: object) -> "FracturedJsonOptions":
        """Create Python wrapper from existing .NET FracturedJsonOptions instance."""
        if dotnet_instance is None:
            msg = "dotnet_instance cannot be None"
            raise ValueError(msg)

        if str(dotnet_instance.GetType()) != str(FracturedJsonOptionsType):
            msg = f"Expected {FracturedJsonOptionsType}, got {dotnet_instance.GetType()}"
            raise TypeError(msg)

        wrapper = cls()
        wrapper._dotnet_instance = dotnet_instance  # Reuse existing instance
        return wrapper

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
    """Formatter wrapper around the FracturedJson .NET formatter."""

    def __init__(self, options: FracturedJsonOptions | None = None) -> None:
        """Create a new Formatter wrapper; optionally set `options`."""
        self._dotnet_instance = Activator.CreateInstance(FormatterType)
        if options is not None:
            options_property = FormatterType.GetProperty("Options")
            options_property.SetValue(self._dotnet_instance, options._dotnet_instance)  # noqa: SLF001

    @property
    def options(self) -> FracturedJsonOptions:
        """Gets/sets the formatting options (FracturedJsonOptions)."""
        prop = FormatterType.GetProperty("Options")
        dotnet_options = prop.GetValue(self._dotnet_instance, None)
        return FracturedJsonOptions._from_dotnet(dotnet_options)

    @options.setter
    def options(self, value: FracturedJsonOptions) -> None:
        prop = FormatterType.GetProperty("Options")
        prop.SetValue(self._dotnet_instance, value._dotnet_instance)

    def reformat(self, json_text: str) -> str:
        """Reformat a JSON string and return the formatted result."""
        if not isinstance(json_text, str):
            msg = "json_text must be a str"
            raise TypeError(msg)
        result = self._dotnet_instance.Reformat(String(json_text))
        return str(result)

    def minify(self, json_text: str) -> str:
        """Minify JSON text to most compact form."""
        if not isinstance(json_text, str):
            msg = "json_text must be a str"
            raise TypeError(msg)
        result = self._dotnet_instance.Minify(String(json_text))
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
