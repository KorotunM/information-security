"""Валидация пользовательского ввода."""

from __future__ import annotations

from dataclasses import dataclass


class InputValidationError(ValueError):
    """Ошибка проверки ввода пользователя."""


@dataclass(slots=True)
class ParsedPayload:
    """Унифицированное представление строки вида `length|values...`."""

    length: int
    values: list[int]


def parse_int(text: str, field_name: str, minimum: int | None = None) -> int:
    """Преобразует строку в целое число и проверяет нижнюю границу."""

    stripped = text.strip()
    if not stripped:
        raise InputValidationError(f"Поле «{field_name}» не должно быть пустым.")

    try:
        value = int(stripped)
    except ValueError as error:
        raise InputValidationError(
            f"Поле «{field_name}» должно содержать целое число."
        ) from error

    if minimum is not None and value < minimum:
        raise InputValidationError(
            f"Поле «{field_name}» должно быть не меньше {minimum}."
        )
    return value


def parse_int_sequence(
    text: str,
    field_name: str,
    minimum_len: int | None = None,
    item_minimum: int | None = None,
) -> list[int]:
    """Преобразует строку чисел, разделённых запятыми, в список."""

    raw_items = [item.strip() for item in text.replace(";", ",").split(",")]
    items = [item for item in raw_items if item]
    if not items:
        raise InputValidationError(f"Поле «{field_name}» не должно быть пустым.")

    values: list[int] = []
    for item in items:
        try:
            value = int(item)
        except ValueError as error:
            raise InputValidationError(
                f"Поле «{field_name}» должно содержать только целые числа."
            ) from error
        if item_minimum is not None and value < item_minimum:
            raise InputValidationError(
                f"Все элементы поля «{field_name}» должны быть не меньше {item_minimum}."
            )
        values.append(value)

    if minimum_len is not None and len(values) < minimum_len:
        raise InputValidationError(
            f"В поле «{field_name}» должно быть как минимум {minimum_len} элементов."
        )
    return values


def validate_binary_string(bits: str, field_name: str = "двоичная строка") -> str:
    """Проверяет строку на двоичный алфавит."""

    normalized = bits.strip().replace(" ", "")
    if not normalized:
        raise InputValidationError(f"Поле «{field_name}» не должно быть пустым.")
    if any(bit not in "01" for bit in normalized):
        raise InputValidationError(
            f"Поле «{field_name}» должно содержать только символы 0 и 1."
        )
    return normalized


def parse_length_prefixed_numbers(
    text: str,
    field_name: str = "шифртекст",
) -> ParsedPayload:
    """Разбирает строку формата `length|v1 v2 v3`."""

    stripped = text.strip()
    if "|" not in stripped:
        raise InputValidationError(
            f"Поле «{field_name}» должно быть в формате «длина|значения»."
        )

    length_part, values_part = stripped.split("|", maxsplit=1)
    length = parse_int(length_part, f"{field_name}: длина", minimum=0)

    if not values_part.strip():
        raise InputValidationError(
            f"Поле «{field_name}» должно содержать хотя бы одно значение после символа '|'."
        )

    try:
        values = [int(item) for item in values_part.replace(",", " ").split()]
    except ValueError as error:
        raise InputValidationError(
            f"Поле «{field_name}» должно содержать только целые числа."
        ) from error

    if not values:
        raise InputValidationError(
            f"Поле «{field_name}» должно содержать хотя бы одно значение."
        )

    return ParsedPayload(length=length, values=values)

