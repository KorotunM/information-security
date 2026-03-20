"""Преобразование текста, битов и цифр для учебных схем."""

from __future__ import annotations

from dataclasses import dataclass

from models.crypto_models import AlphabetEncodingResult
from utils.validation import InputValidationError


FIXED_INPUT_ALPHABET = "abcdefghijklmnopqrstuvwxyz "


@dataclass(slots=True)
class RSABlockData:
    """Блоки текста для RSA."""

    integers: list[int]
    lengths: list[int]
    block_size: int


class AlphabetCodec:
    """Кодек для отображения символов в индексы и цифры по основанию."""

    def __init__(self, alphabet: str) -> None:
        if not alphabet:
            raise InputValidationError("Алфавит не должен быть пустым.")
        if len(set(alphabet)) != len(alphabet):
            raise InputValidationError("Символы алфавита должны быть уникальными.")
        self.alphabet = alphabet
        self.lookup = {char: index for index, char in enumerate(alphabet)}

    def width_for_base(self, base: int) -> int:
        """Возвращает количество цифр на один символ."""

        if base < 2:
            raise InputValidationError("Основание системы счисления должно быть не меньше 2.")
        width = 1
        capacity = base
        while capacity < len(self.alphabet):
            width += 1
            capacity *= base
        return width

    def text_to_indices(self, text: str) -> list[int]:
        """Преобразует строку в индексы символов."""

        indices: list[int] = []
        for char in text:
            if char not in self.lookup:
                raise InputValidationError(
                    f"Символ «{char}» отсутствует в выбранном алфавите."
                )
            indices.append(self.lookup[char])
        return indices

    def indices_to_text(self, indices: list[int]) -> str:
        """Преобразует индексы обратно в строку."""

        chars: list[str] = []
        for index in indices:
            if not 0 <= index < len(self.alphabet):
                raise InputValidationError(
                    f"Индекс {index} не входит в диапазон выбранного алфавита."
                )
            chars.append(self.alphabet[index])
        return "".join(chars)

    def encode_to_digits(self, text: str, base: int) -> AlphabetEncodingResult:
        """Кодирует текст как последовательность цифр по основанию `base`."""

        indices = self.text_to_indices(text)
        width = self.width_for_base(base)
        digits: list[int] = []
        for index in indices:
            digits.extend(int_to_base_digits(index, base, width))
        return AlphabetEncodingResult(
            text=text,
            alphabet=self.alphabet,
            base=base,
            width=width,
            indices=indices,
            digits=digits,
        )

    def decode_from_digits(
        self,
        digits: list[int],
        base: int,
        width: int,
        symbol_count: int,
    ) -> str:
        """Восстанавливает строку из цифр фиксированной ширины."""

        needed = symbol_count * width
        if len(digits) < needed:
            raise InputValidationError("Недостаточно цифр для восстановления сообщения.")

        indices: list[int] = []
        for start in range(0, needed, width):
            chunk = digits[start : start + width]
            index = base_digits_to_int(chunk, base)
            indices.append(index)
        return self.indices_to_text(indices)


def validate_fixed_alphabet_text(text: str, field_name: str = "Сообщение") -> str:
    """Проверяет, что текст использует только строчные латинские буквы и пробел."""

    normalized = text.strip()
    if not normalized:
        raise InputValidationError(f"Поле «{field_name}» не должно быть пустым.")
    invalid = sorted({char for char in normalized if char not in FIXED_INPUT_ALPHABET})
    if invalid:
        symbols = ", ".join(repr(char) for char in invalid)
        raise InputValidationError(
            f"Поле «{field_name}» может содержать только строчные английские буквы и пробел. "
            f"Недопустимые символы: {symbols}."
        )
    return normalized


def fixed_alphabet_indices(text: str, field_name: str = "Сообщение") -> list[int]:
    """Преобразует текст фиксированного учебного алфавита в числовые эквиваленты Q."""

    normalized = validate_fixed_alphabet_text(text, field_name)
    codec = AlphabetCodec(FIXED_INPUT_ALPHABET)
    return codec.text_to_indices(normalized)


def fixed_alphabet_width() -> int:
    """Возвращает минимальную двоичную ширину для множества Q фиксированного алфавита."""

    return max(1, (len(FIXED_INPUT_ALPHABET) - 1).bit_length())


def fixed_alphabet_text_to_binary_coefficients(
    text: str,
    field_name: str = "Сообщение",
) -> tuple[list[int], list[int], int]:
    """Кодирует текст как Q={0..26}, затем переводит каждый символ в двоичное слово фиксированной длины."""

    indices = fixed_alphabet_indices(text, field_name)
    width = fixed_alphabet_width()
    bits = [bit for index in indices for bit in int_to_base_digits(index, 2, width)]
    return indices, bits, width


def binary_coefficients_to_fixed_alphabet_text(coefficients: list[int]) -> tuple[str, list[int], int]:
    """Восстанавливает текст фиксированного алфавита из двоичных коэффициентов фиксированной длины."""

    width = fixed_alphabet_width()
    if len(coefficients) % width != 0:
        raise InputValidationError(
            "Длина двоичной последовательности должна делиться на 5, чтобы восстановить символы множества Q."
        )
    if any(bit not in (0, 1) for bit in coefficients):
        raise InputValidationError("Классический рюкзак допускает только двоичные коэффициенты 0 и 1.")

    codec = AlphabetCodec(FIXED_INPUT_ALPHABET)
    indices = [
        base_digits_to_int(coefficients[start : start + width], 2)
        for start in range(0, len(coefficients), width)
    ]
    return codec.indices_to_text(indices), indices, width


def int_to_base_digits(number: int, base: int, width: int) -> list[int]:
    """Преобразует число в список цифр фиксированной длины."""

    if number < 0:
        raise InputValidationError("Число для перевода в цифры не должно быть отрицательным.")
    digits = [0] * width
    current = number
    for index in range(width - 1, -1, -1):
        digits[index] = current % base
        current //= base
    if current != 0:
        raise InputValidationError("Число не помещается в заданную ширину.")
    return digits


def base_digits_to_int(digits: list[int], base: int) -> int:
    """Собирает число из списка цифр."""

    value = 0
    for digit in digits:
        if not 0 <= digit < base:
            raise InputValidationError(
                f"Цифра {digit} не входит в допустимый диапазон 0..{base - 1}."
            )
        value = value * base + digit
    return value


def text_to_bits(text: str) -> str:
    """Преобразует строку UTF-8 в битовую последовательность."""

    return "".join(f"{byte:08b}" for byte in text.encode("utf-8"))


def bits_to_text(bits: str) -> str:
    """Преобразует битовую последовательность обратно в UTF-8."""

    if len(bits) % 8 != 0:
        raise InputValidationError("Длина битовой строки для текста должна делиться на 8.")
    data = bytes(int(bits[index : index + 8], 2) for index in range(0, len(bits), 8))
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InputValidationError(
            "Не удалось декодировать биты как UTF-8. Проверьте параметры и шифртекст."
        ) from error


def split_sequence(sequence: list[int], block_size: int, pad_value: int = 0) -> tuple[list[list[int]], int]:
    """Разбивает последовательность на блоки фиксированной длины."""

    if block_size < 1:
        raise InputValidationError("Размер блока должен быть положительным.")
    data = list(sequence)
    padding = (-len(data)) % block_size
    if padding:
        data.extend([pad_value] * padding)
    blocks = [data[index : index + block_size] for index in range(0, len(data), block_size)]
    return blocks, padding


def text_to_rsa_blocks(text: str, modulus: int) -> RSABlockData:
    """Преобразует текст в блоки целых чисел, меньших `modulus`."""

    raw = text.encode("utf-8")
    block_size = max(1, (modulus.bit_length() - 1) // 8)
    if block_size < 1:
        raise InputValidationError("Модуль RSA слишком мал для кодирования текста.")

    integers: list[int] = []
    lengths: list[int] = []
    for index in range(0, len(raw), block_size):
        chunk = raw[index : index + block_size]
        value = int.from_bytes(chunk, "big")
        if value >= modulus:
            raise InputValidationError(
                "Полученный блок не меньше модуля RSA. Увеличьте p и q."
            )
        integers.append(value)
        lengths.append(len(chunk))
    return RSABlockData(integers=integers, lengths=lengths, block_size=block_size)


def rsa_blocks_to_text(blocks: list[int], lengths: list[int]) -> str:
    """Восстанавливает текст по блокам чисел и длинам исходных байтов."""

    if len(blocks) != len(lengths):
        raise InputValidationError("Количество RSA-блоков и длин блоков должно совпадать.")
    raw = bytearray()
    for value, length in zip(blocks, lengths, strict=True):
        raw.extend(value.to_bytes(length, "big"))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InputValidationError(
            "Не удалось декодировать RSA-блоки как UTF-8."
        ) from error


def format_rsa_payload(lengths: list[int], blocks: list[int]) -> str:
    """Форматирует RSA-шифртекст в строку `l:c l:c ...`."""

    return " ".join(f"{length}:{block}" for length, block in zip(lengths, blocks, strict=True))


def parse_rsa_payload(text: str) -> tuple[list[int], list[int]]:
    """Разбирает строку RSA-шифртекста."""

    parts = text.strip().split()
    if not parts:
        raise InputValidationError("Поле «Шифртекст» не должно быть пустым.")

    lengths: list[int] = []
    blocks: list[int] = []
    for part in parts:
        if ":" not in part:
            raise InputValidationError(
                "RSA-шифртекст должен быть в формате `длина:значение`."
            )
        length_part, block_part = part.split(":", maxsplit=1)
        try:
            length = int(length_part)
            block = int(block_part)
        except ValueError as error:
            raise InputValidationError(
                "RSA-шифртекст должен содержать только целые числа."
            ) from error
        if length < 1 or block < 0:
            raise InputValidationError(
                "Длины блоков должны быть положительными, значения блоков — неотрицательными."
            )
        lengths.append(length)
        blocks.append(block)
    return lengths, blocks


def format_length_prefixed_payload(length: int, values: list[int]) -> str:
    """Форматирует полезную нагрузку вида `length|values...`."""

    return f"{length}|{' '.join(str(value) for value in values)}"
