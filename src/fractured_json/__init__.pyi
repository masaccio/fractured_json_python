from typing import Any, Dict, Optional

class CommentPolicy:
    DISALLOW: "CommentPolicy"
    PRESERVE: "CommentPolicy"

class EolStyle:
    SYSTEM: "EolStyle"
    CRLF: "EolStyle"
    LF: "EolStyle"

class FracturedJsonOptions:
    max_total_line_length: int
    max_inline_complexity: int
    max_compact_array_complexity: int
    max_compact_object_complexity: int
    max_compact_array_width: int
    max_compact_object_width: int
    always_expand_depth: int
    indent_spaces: int
    use_tab_to_indent: bool
    comment_policy: CommentPolicy
    json_eol_style: EolStyle
    trailing_comma: bool
    sort_properties: bool

    # Dynamic API
    def __init__(self, **kwargs: Any) -> None: ...
    def list_options(self) -> Dict[str, Dict[str, Any]]: ...
    def get(self, name: str) -> Any: ...
    def set(self, name: str, value: Any) -> None: ...

    # Attribute delegation (via __getattr__/__setattr__)
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

class Formatter:
    def __init__(self, options: Optional[FracturedJsonOptions] = None) -> None: ...
    @property
    def options(self) -> FracturedJsonOptions: ...
    @options.setter
    def options(self, value: FracturedJsonOptions) -> None: ...
    def reformat(self, json_text: str) -> str: ...
    def serialize(self, obj: Any) -> str: ...

# Module re-exports
__all__: list[str]
