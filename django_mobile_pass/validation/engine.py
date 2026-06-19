from __future__ import annotations

from typing import Any

from django_mobile_pass.exceptions import InvalidPass


def _get_nested(data: dict, dotted_key: str) -> Any:
    current: Any = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def validate_payload(data: dict, rules: dict[str, list[str | tuple]]) -> dict:
    errors: list[str] = []

    for field, constraints in rules.items():
        value = _get_nested(data, field)
        nullable = "nullable" in constraints

        if _is_empty(value):
            if "required" in constraints:
                errors.append(f"{field} is required.")
            continue

        for constraint in constraints:
            if constraint == "required" or constraint == "nullable":
                continue

            if constraint == "string":
                if not isinstance(value, str):
                    errors.append(f"{field} must be a string.")
            elif constraint == "integer":
                if not isinstance(value, int) or isinstance(value, bool):
                    errors.append(f"{field} must be an integer.")
            elif constraint == "array":
                if not isinstance(value, (list, dict)):
                    errors.append(f"{field} must be an array.")
            elif isinstance(constraint, tuple) and constraint[0] == "in":
                allowed = constraint[1]
                if value not in allowed:
                    errors.append(f"{field} must be one of {sorted(allowed)!r}.")
            elif isinstance(constraint, tuple) and constraint[0] == "min":
                minimum = constraint[1]
                if isinstance(value, str) and len(value) < minimum:
                    errors.append(f"{field} must be at least {minimum} characters.")

    if errors:
        raise InvalidPass("; ".join(errors))

    return data
