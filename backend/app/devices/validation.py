import re


def normalize_identifier(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().upper()

    return normalized or None


def normalize_imei(value: str | None) -> str | None:
    normalized = normalize_identifier(value)

    if normalized is None:
        return None

    digits = re.sub(r"[^0-9]", "", normalized)

    if len(digits) != 15:
        raise ValueError("IMEI must contain exactly 15 digits")

    return digits


def validate_imei(value: str | None) -> bool:
    try:
        normalized = normalize_imei(value)
    except ValueError:
        return False

    if normalized is None:
        return False

    total = 0

    for index, digit in enumerate(reversed(normalized)):
        number = int(digit)

        if index % 2 == 1:
            number *= 2

            if number > 9:
                number -= 9

        total += number

    return total % 10 == 0
