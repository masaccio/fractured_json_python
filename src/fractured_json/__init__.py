from fractured_json._wrappergen import get_object_property_info, load_assembly

types = load_assembly("FracturedJson")


def object_property_info(obj: object):
    return get_object_property_info(obj, types)


from fractured_json._version import __version__
