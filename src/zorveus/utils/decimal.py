import re
from zorveus.errors import InvalidDecimalError

DECIMAL_PATTERN = re.compile(r"^\d+(\.\d{1,12})?$")

def validate_decimal_string(val: str) -> str:
    """Validates credit amount as decimal string up to 12 decimal places."""
    if not isinstance(val, str):
        raise InvalidDecimalError(f"Credit amount must be a string, got {type(val).__name__}.")

    if not DECIMAL_PATTERN.match(val):
        raise InvalidDecimalError(
            f"Invalid decimal string format '{val}'. Must be non-negative with up to 12 decimal places."
        )

    return val
