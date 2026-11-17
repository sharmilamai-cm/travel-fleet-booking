"""Input validation helpers. Every function raises ValidationError on bad input."""

import re
from datetime import date, datetime


class ValidationError(ValueError):
    """Raised when user input fails validation."""


VEHICLE_TYPES = ("bus", "car", "van")


def validate_name(value: str, field: str = "Name") -> str:
    value = (value or "").strip()
    if len(value) < 2:
        raise ValidationError(f"{field} must have at least 2 characters.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", value):
        raise ValidationError(f"{field} may contain only letters, spaces, '.', '-' and apostrophes.")
    return value


def validate_phone(value: str) -> str:
    value = (value or "").strip()
    if not re.fullmatch(r"[6-9]\d{9}", value):
        raise ValidationError("Phone must be a 10-digit Indian mobile number starting with 6-9.")
    return value


def validate_registration_no(value: str) -> str:
    value = (value or "").strip().upper().replace(" ", "")
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}", value):
        raise ValidationError("Registration number must look like TN01AB1234.")
    return value


def validate_vehicle_type(value: str) -> str:
    value = (value or "").strip().lower()
    if value not in VEHICLE_TYPES:
        raise ValidationError(f"Vehicle type must be one of: {', '.join(VEHICLE_TYPES)}.")
    return value


def validate_positive_int(value, field: str, maximum: int = 100) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a whole number.") from None
    if number < 1 or number > maximum:
        raise ValidationError(f"{field} must be between 1 and {maximum}.")
    return number


def validate_positive_float(value, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a number.") from None
    if number <= 0:
        raise ValidationError(f"{field} must be greater than zero.")
    return number


def validate_date(value: str, allow_past: bool = False) -> str:
    try:
        parsed = datetime.strptime((value or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("Date must be in YYYY-MM-DD format.") from None
    if not allow_past and parsed < date.today():
        raise ValidationError("Date cannot be in the past.")
    return parsed.isoformat()


def validate_time(value: str) -> str:
    try:
        parsed = datetime.strptime((value or "").strip(), "%H:%M")
    except ValueError:
        raise ValidationError("Time must be in 24-hour HH:MM format.") from None
    return parsed.strftime("%H:%M")


def validate_city(value: str, field: str = "City") -> str:
    value = (value or "").strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z .-]{1,39}", value):
        raise ValidationError(f"{field} must be 2-40 letters.")
    return value.title()
