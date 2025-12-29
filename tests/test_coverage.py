import pytest

from fractured_json import CommentPolicy, FracturedJsonOptions, NumberListAlignment


def test_eq_and_hash():
    assert CommentPolicy.REMOVE != CommentPolicy.PRESERVE
    assert NumberListAlignment.LEFT == 0
    a = dict()
    a[CommentPolicy.REMOVE] = "test"
    assert list(a.keys())[0].name == "REMOVE"
    assert list(a.keys())[0].value == 1


def test_from_dotnet():
    with pytest.raises(ValueError, match="dotnet_instance cannot be None"):
        FracturedJsonOptions._from_dotnet(None)

    class FakeInstance:
        def GetType(self):
            return "FakeInstance"

    with pytest.raises(TypeError, match="Expected .*FracturedJsonOptions"):
        FracturedJsonOptions._from_dotnet(FakeInstance())


def test_from_dotnet_success():
    options = FracturedJsonOptions()
    wrapper = FracturedJsonOptions._from_dotnet(options._dotnet_instance)

    assert isinstance(wrapper, FracturedJsonOptions)
    assert wrapper._dotnet_instance is options._dotnet_instance
