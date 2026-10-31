from typing import Dict

from pydantic import JsonValue
from typing_extensions import TypeAlias

UsageMetadata: TypeAlias = Dict[str, JsonValue]
