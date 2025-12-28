import sys

from fractured_json._version import __version__
from fractured_json._wrappergen import (
    create_pythonic_wrapper_class,
    get_object_property_info,
    load_assembly,
)

types = load_assembly("FracturedJson")


def object_property_info(obj: object):
    return get_object_property_info(obj, types)


import clr

system_text_json = clr.AddReference("System.Text.Json")
system_text_json_types = {t.Name: t for t in system_text_json.GetTypes() if t.IsPublic}
cls = create_pythonic_wrapper_class(system_text_json_types["JsonSerializerOptions"])

module = sys.modules["fractured_json"]
module.JsonSerializerOptions = cls


system_text_encodings_web = clr.AddReference("System.Text.Encodings.Web")
system_text_encodings_web_types = {
    t.Name: t for t in system_text_encodings_web.GetTypes() if t.IsPublic
}
cls = create_pythonic_wrapper_class(system_text_encodings_web_types["JavaScriptEncoder"])

module = sys.modules["fractured_json"]
module.JavaScriptEncoder = cls


# from System.Text.Encodings.Web import JavaScriptEncoder
# from System.Text.Json import JsonSerializerOptions as

# json_options = JsonSerializerOptions()
# json_options.Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
# json_options.WriteIndented = True
