import importlib.metadata
import os
import re
from pathlib import Path
from typing import Any, Optional
from warnings import warn

from pythonnet import load

__version__ = importlib.metadata.version("fractured-json")


def _get_version() -> str:
    return __version__


__all__ = [
    "Formatter",
    "FracturedJsonOptions",
    "CommentPolicy",
    "EolStyle",
    "TableCommaPlacement",
]


def pythonnet_runtime() -> str:
    # Mono is not supported on Apple Silicon Macs, so we prefer the Core Runtime
    return os.environ.get("PYTHONNET_RUNTIME", "coreclr")


def load_runtime() -> None:
    here = Path(__file__).resolve().parent
    dll_path = here / "FracturedJson.dll"
    if not dll_path.is_file():
        raise FileNotFoundError(f"FracturedJson.dll not found at {dll_path}")

    runtime = pythonnet_runtime()
    try:
        load(runtime)
    except RuntimeError as e:
        raise RuntimeError(f"Failed to load pythonnet runtime '{runtime}'. ") from e


load_runtime()

import clr  # noqa: E402
from System import (  # noqa: E402
    Activator,
    Boolean,
    Int16,
    Int32,
    Int64,
    String,
    Type,  # noqa: E402
)
from System.Reflection import BindingFlags  # noqa: E402


def get_object_types() -> dict[str, "System.RuntimeType"]:
    assembly = clr.AddReference("fractured_json/FracturedJson")

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

    def __init_subclass__(cls, native_type=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if native_type is None:
            raise ValueError(f"{cls.__name__} must set _native_type")

        native_names = [str(x) for x in native_type.GetEnumNames()]
        native_values = [int(x) for x in native_type.GetEnumValues()]

        name_to_value = {}
        for name, value in zip(native_names, native_values):
            name_to_value[name] = value

        for native_name in native_names:
            py_name = to_snake_case(native_name, upper=True)
            native_value = name_to_value[native_name]
            # Create instance and store on class
            instance = cls(py_name, native_value)
            setattr(cls, py_name, instance)

    def __init__(self, py_name, native_value):
        self._py_name = py_name
        self.value = native_value

    def __repr__(self):
        return f"{self.__class__.__name__}.{self._py_name}"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.value == other.value
        return self.value == other

    def __hash__(self):
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
    def __init__(self, **kwargs) -> None:
        self._dotnet = Activator.CreateInstance(FracturedJsonOptionsType)
        self._properties: dict[str, dict[str, Any]] = {}
        self._get_dotnet_properties()

        for key, value in kwargs.items():
            self.set(key, value)

    def _get_dotnet_properties(self) -> None:
        t = Type.GetType(self._dotnet.GetType().AssemblyQualifiedName)
        properties = t.GetProperties(BindingFlags.Public | BindingFlags.Instance)
        for property in properties:
            py_name = to_snake_case(property.Name, upper=False)
            dotnet_type_name = property.PropertyType.FullName.split(".")
            is_enum = bool(property.PropertyType.IsEnum)
            enum_names = (
                [
                    to_snake_case(str(x), upper=True)
                    for x in types[dotnet_type_name[1]].GetEnumNames()
                ]
                if is_enum
                else []
            )
            self._properties[py_name] = {
                "property": property,
                "dotnet_name": property.Name,
                "type": str(property.PropertyType.FullName),
                "can_read": bool(property.CanRead),
                "can_write": bool(property.CanWrite),
                "is_enum": bool(property.PropertyType.IsEnum),
                "enum_names": enum_names,
            }

    def list_options(self) -> dict[str, dict[str, Any]]:
        return self._properties

    def _resolve_net_name(self, name: str) -> str:
        if name in self._prop_by_py_name:
            return self._prop_by_py_name[name]
        snake = to_snake_case(name, upper=False)
        if snake in self._prop_by_py_name:
            return self._prop_by_py_name[snake]
        raise AttributeError(f"No such option: {name!r}")

    def get(self, name: str) -> Any:
        property = self._properties[name]["property"]
        if not property.CanRead:
            raise AttributeError(f"Option {name} is write-only")
        return property.GetValue(self._dotnet, None)

    def set(self, name: str, value: Any) -> None:
        property = self._properties[name]["property"]
        if not property.CanWrite:
            raise AttributeError(f"Option {name} is read-only")

        target_type = property.PropertyType

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

        property.SetValue(self._dotnet, value, None)

    def __getattr__(self, name: str) -> Any:
        try:
            return self.get(name)
        except AttributeError:
            raise AttributeError(f"{type(self).__name__} has no attribute {name!r}") from None

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_dotnet", "_properties"}:
            object.__setattr__(self, name, value)
        else:
            try:
                self.set(name, value)
            except AttributeError:
                object.__setattr__(self, name, value)


class Formatter:
    def __init__(self, options: Optional[FracturedJsonOptions] = None) -> None:
        self._dotnet = Activator.CreateInstance(FormatterType)
        if options is not None:
            self.options = options

    @property
    def options(self) -> FracturedJsonOptions:
        opt = FracturedJsonOptions()
        opt._dotnet = self._dotnet.Options
        return opt

    @options.setter
    def options(self, value: FracturedJsonOptions) -> None:
        self._dotnet.Options = value._dotnet

    def reformat(self, json_text: str) -> str:
        if not isinstance(json_text, str):
            raise TypeError("json_text must be a str")
        result = self._dotnet.Reformat(String(json_text))
        return str(result)

    def serialize(self, obj: Any) -> str:
        result = self._dotnet.Serialize(obj)
        return str(result)
