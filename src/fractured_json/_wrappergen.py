import importlib
import re
import sys
from os import environ
from pathlib import Path

from pythonnet import load


def pythonnet_runtime() -> str:
    """Return the configured .NET runtime."""
    # Mono is not supported on Apple Silicon Macs, so we prefer the Core Runtime
    return environ.get("PYTHONNET_RUNTIME", "coreclr")


def load_runtime() -> None:
    runtime = pythonnet_runtime()
    try:
        load(runtime)
    except RuntimeError as e:
        msg = f"Failed to load pythonnet runtime '{runtime}'. "
        raise RuntimeError(msg) from e


def load_assembly(dll_name: str) -> dict[str, object]:
    """Load the .NET runtime and a .NET assembly."""
    dll_path = Path(__file__).resolve().parent / f"{dll_name}.dll"
    if not dll_path.is_file():
        msg = f"{dll_name}.dll not found at {dll_path}"
        raise FileNotFoundError(msg)

    try:
        clr = importlib.import_module("clr")
        assembly = clr.AddReference(f"{dll_path.parent.name}/{dll_name}")
    except Exception as e:
        msg = f"{dll_name}.dll load failed: {e}"
        raise FileNotFoundError(msg) from e

    module = sys.modules["fractured_json"]
    types = {}
    for t in assembly.GetTypes():
        if t.IsPublic:
            cls = create_enum_wrapper(t) if t.IsEnum else create_pythonic_wrapper_class(t)
            setattr(module, t.Name, cls)
            types[t.Name] = (t, cls)

    return types


load_runtime()


def pascal_to_snake(name: str) -> str:
    """Convert a .NET Pascal case string to a Python snake case string."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def snake_to_pascal(name: str) -> str:
    """Convert a Python snake case string to a .NET Pascal case string."""
    return "".join(part.capitalize() for part in name.split("_"))


def pascal_to_upper_snake(name: str) -> str:
    """Convert a .NET Pascal case string to a Python snake case string."""
    return pascal_to_snake(name).upper()


from System import Activator, Boolean, Double, Enum, Func, Int32, Object, Single, String
from System.Collections import ArrayList
from System.Collections.Generic import Dictionary
from System.Reflection import BindingFlags


def to_enum_if_needed(prop, value):
    """Convert string to .NET enum or validate Python enum object."""
    enum_type = prop.PropertyType
    if enum_type.IsEnum:
        # Accept string -> parse
        if isinstance(value, str):
            # Convert snake_case to PascalCase
            parts = value.split("_")
            pascal_name = "".join(p.capitalize() for p in parts)
            if not Enum.IsDefined(enum_type, pascal_name):
                raise ValueError(f"'{value}' is not a valid value for {enum_type.Name}")
            return Enum.Parse(enum_type, pascal_name)

        if enum_type.Name != type(value).__name__:
            msg = f"Property {prop.Name} expects {enum_type.Name} enum, got {type(value).__name__}"
            raise TypeError(
                msg,
            )

    return value  # not an enum


def to_dotnet(obj: object) -> object:  # noqa: C901, PLR0911
    """Convert a hierarchical Python object to .NET primitives."""
    if hasattr(obj, "_net_obj"):
        return obj._net_obj  # pyright: ignore[reportAttributeAccessIssue] # noqa: SLF001

    if isinstance(obj, dict):
        d = Dictionary[String, Object]()
        for k, v in obj.items():
            d[str(k)] = to_dotnet(v)
        return d
    if isinstance(obj, (list, tuple)):
        array = ArrayList()
        for item in obj:
            array.Add(to_dotnet(item))
        return array
    if isinstance(obj, bool):
        return Boolean(obj)
    if isinstance(obj, int):
        return Int32(obj)
    if isinstance(obj, float):
        return Double(obj)
    if isinstance(obj, str):
        return String(obj)
    if isinstance(obj, Enum):
        return obj
    if obj is None:
        return None

    msg = f"Type {type(obj)} not supported for conversion"
    raise TypeError(msg)


from typing import Any  # noqa: E402


def create_enum_wrapper(enum_type):
    attrs: dict[str, Any] = {}

    for name in Enum.GetNames(enum_type):
        attrs[pascal_to_upper_snake(name)] = Enum.Parse(enum_type, name)

    return type(enum_type.Name, (), attrs)


class PyEnumWrapper:
    def __init__(self, enum_obj):
        self._enum_obj = enum_obj

    @property
    def name(self):
        return pascal_to_upper_snake(self._enum_obj.ToString())

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Enum {self.name}>"

    def __eq__(self, other):
        # Compare to another PyEnumWrapper
        if isinstance(other, PyEnumWrapper):
            return self.value == other.value
        # Compare to int directly
        if isinstance(other, int):
            return self.value == other
        # Compare to .NET enum directly
        try:
            return self.value == int(other)
        except Exception:
            return False


from System import Delegate, Int64

NET_TO_PY = {
    "String": str,
    "Int32": int,
    "Int64": int,
    "Double": float,
    "Single": float,
    "Boolean": bool,
}

PY_TO_NET = {
    "String": String,
    "Int32": Int32,
    "Int64": Int64,
    "Double": Double,
    "Single": Single,
    "Boolean": Boolean,
}


def make_property(p):
    """Create a Python property wrapping a .NET property.

    Handles:
      - Primitives
      - Enums (assumes PyEnumWrapper is declared elsewhere)
      - Nested .NET classes
      - Delegates (dynamically wrap Python callable)
    """
    prop_type = p.PropertyType
    can_write = p.CanWrite

    # --- Delegate wrapper factory ---
    def make_delegate_wrapper(py_func, param_types, return_type):
        def wrapper(*args):
            # Convert .NET args to Python
            py_args = [NET_TO_PY[t](a) if t in NET_TO_PY else a for a, t in zip(args, param_types)]
            result = py_func(*py_args)
            # Convert Python result back to .NET
            if return_type in PY_TO_NET:
                return PY_TO_NET[return_type](result)
            return result

        return wrapper

    # --- Getter ---
    def getter(self):
        val = p.GetValue(self._net_obj, None)
        if val is None:
            return None

        if hasattr(val, "GetType"):
            t = val.GetType()
            if t.IsEnum:
                # Expect PyEnumWrapper declared elsewhere
                return PyEnumWrapper(val)
            if t.IsClass and not callable(val):
                wrapper_class = create_pythonic_wrapper_class(prop_type)
                return wrapper_class(dotnet_obj=val)

        return val  # primitive

    # --- Setter ---
    def setter(self, value):
        if not can_write:
            raise AttributeError(f"Property {p.Name} is read-only")

        val_to_set = to_enum_if_needed(p, value)

        # Delegate handling
        if prop_type.IsSubclassOf(Delegate) and callable(val_to_set):
            invoke_method = prop_type.GetMethod("Invoke")
            param_types = [param.ParameterType.Name for param in invoke_method.GetParameters()]
            return_type = invoke_method.ReturnType.Name
            func_types = [PY_TO_NET[x] for x in param_types + [return_type]]
            wrapper = make_delegate_wrapper(val_to_set, param_types, return_type)
            p.SetValue(self._net_obj, Func[*func_types](wrapper), None)
        else:
            expected_type_name = prop_type.Name
            if expected_type_name in NET_TO_PY:
                py_type = NET_TO_PY[expected_type_name]
                if not isinstance(value, py_type):
                    py_name = pascal_to_snake(p.Name)
                    msg = f"Property {py_name} expects {py_type.__name__}, got {type(value).__name__} '{value}'"
                    raise TypeError(
                        msg,
                    )
            p.SetValue(self._net_obj, to_dotnet(val_to_set), None)

    return property(getter, setter)


from System import Int32, String


def is_string_like(param_type) -> bool:
    """Return True if the .NET type is String or IEnumerable<char>."""
    if param_type.Name == "String":
        return True
    if param_type.IsGenericType:
        generic_def = param_type.GetGenericTypeDefinition()
        args = param_type.GetGenericArguments()
        if (
            generic_def.FullName == "System.Collections.Generic.IEnumerable`1"
            and args[0].Name == "Char"
        ):
            return True
    return False


def create_pythonic_wrapper_class(net_type):
    """Create a Python wrapper class for a .NET RuntimeType."""
    attrs: dict[str, Any] = {}

    # -----------------
    # __init__ constructor
    # -----------------
    def __init__(self, *args, dotnet_obj=None, **kwargs):
        if dotnet_obj is not None:
            self._net_obj = dotnet_obj
            return

        clr_args = [to_dotnet(a) for a in args]
        self._net_obj = Activator.CreateInstance(net_type, clr_args)

        # Dataclass-style property initialization
        for key, value in kwargs.items():
            if not hasattr(self.__class__, key):
                raise AttributeError(f"{net_type.Name} property '{key}' does not exist")
            setattr(self, key, value)

    attrs["__init__"] = __init__

    # -----------------
    # Method wrappers
    # -----------------
    for method in net_type.GetMethods(BindingFlags.Public | BindingFlags.Instance):
        if method.IsSpecialName:
            continue  # skip getters/setters/operators

        py_name = pascal_to_snake(method.Name)
        if py_name in attrs:
            continue  # skip overload duplicates

        param_infos = list(method.GetParameters())
        param_types = [p.ParameterType for p in param_infos]
        param_type_names = [t.Name for t in param_types]
        optional_values = [p.DefaultValue if p.IsOptional else None for p in param_infos]

        return_type = method.ReturnType
        return_type_name = return_type.Name if return_type else None

        def make_method(
            method_name,
            param_types,
            param_type_names,
            optional_values,
            return_type_name,
        ):
            def wrapper(self, *args):
                if len(args) > len(param_types):
                    raise TypeError(
                        f"{method_name} expects at most {len(param_types)} arguments, got {len(args)}",
                    )

                # Fill in missing optional arguments
                full_args = list(args)
                for i in range(len(full_args), len(param_types)):
                    if optional_values[i] is not None:
                        full_args.append(optional_values[i])
                    else:
                        raise TypeError(
                            f"{method_name} missing required argument {i} ({param_type_names[i]})",
                        )

                # Convert and type-check arguments
                clr_args = []
                for i, (arg, expected_type) in enumerate(zip(full_args, param_types)):
                    if is_string_like(expected_type):
                        if not isinstance(arg, str):
                            raise TypeError(
                                f"{method_name} argument {i} must be str, got {type(arg).__name__}",
                            )
                        clr_args.append(String(arg))
                    else:
                        py_type = NET_TO_PY.get(expected_type.Name)
                        if py_type and not isinstance(arg, py_type):
                            raise TypeError(
                                f"{method_name} argument {i} must be {py_type.__name__}, got {type(arg).__name__}",
                            )
                        clr_args.append(to_dotnet(arg))

                # Call the underlying .NET method
                result = getattr(self._net_obj, method_name)(*clr_args)

                # Wrap result
                if result is None:
                    return None
                if hasattr(result, "GetType"):
                    t = result.GetType()
                    if t.IsEnum:
                        return PyEnumWrapper(result)
                    if t.IsClass and not t.IsEnum:
                        wrapper_class = create_pythonic_wrapper_class(t)
                        return wrapper_class(dotnet_obj=result)
                return result

            return wrapper

        attrs[py_name] = make_method(
            method.Name,
            param_types,
            param_type_names,
            optional_values,
            return_type_name,
        )

    # -----------------
    # Properties
    # -----------------
    for prop in net_type.GetProperties(BindingFlags.Public | BindingFlags.Instance):
        py_name = pascal_to_snake(prop.Name)
        attrs[py_name] = make_property(prop)  # handles delegates, enums, type checks

    # -----------------
    # Nested enums
    # -----------------
    for nested in net_type.GetNestedTypes(BindingFlags.Public):
        if nested.IsEnum:
            attrs[pascal_to_snake(nested.Name)] = create_enum_wrapper(nested)

    return type(net_type.Name, (), attrs)


from System import Type


def get_object_property_info(obj: object, types: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a dictionary mapping Pythonic property names to property info for a .NET object."""
    properties: dict[str, dict[str, Any]] = {}
    t = Type.GetType(obj._net_obj.GetType().AssemblyQualifiedName)
    props = t.GetProperties(BindingFlags.Public | BindingFlags.Instance)

    for prop in props:
        py_name = pascal_to_snake(prop.Name)
        dotnet_type_name = prop.PropertyType.FullName.split(".")
        is_enum = prop.PropertyType.IsEnum

        enum_names = []
        if is_enum:
            enum_type_name = dotnet_type_name[-1]  # last part is the type name
            if enum_type_name in types:
                enum_names = [
                    pascal_to_upper_snake(str(x)) for x in types[enum_type_name][0].GetEnumNames()
                ]

        properties[py_name] = {
            "prop": prop,
            "dotnet_name": prop.Name,
            "type": str(prop.PropertyType.FullName),
            "is_enum": is_enum,
            "enum_names": enum_names,
        }

    return properties
