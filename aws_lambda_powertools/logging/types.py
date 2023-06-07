from typing import Any, Dict, Iterable, Union

from typing_extensions import TypedDict

class TypedLog(TypedDict, total=False):
    level: Union[str, int]
    location: str
    timestamp: Union[str, int]
    service: str
    message: Union[Dict[str, Any], str, bool, Iterable]