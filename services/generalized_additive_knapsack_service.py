"""Обобщённый аддитивный рюкзак для алфавитных сообщений."""

from __future__ import annotations

from models.crypto_models import AdditiveKnapsackKeyPair, KnapsackCipherPayload
from services.additive_knapsack_service import AdditiveKnapsackService
from utils.text_codec import AlphabetCodec, FIXED_INPUT_ALPHABET, validate_fixed_alphabet_text
from utils.validation import InputValidationError


class GeneralizedAdditiveKnapsackService:
    """Сервис GAKP/GAKR в учебной постановке."""

    def __init__(self) -> None:
        self.base_service = AdditiveKnapsackService()

    def generate_keys(
        self,
        length: int,
        base: int,
        private_sequence: list[int] | None = None,
        modulus: int | None = None,
        multiplier: int | None = None,
    ) -> tuple[AdditiveKnapsackKeyPair, str]:
        """Генерирует ключи обобщённого аддитивного рюкзака."""

        if base < 2:
            raise InputValidationError("Основание кодирования должно быть не меньше 2.")
        return self.base_service.generate_keys(
            length=length,
            coefficient_limit=base - 1,
            private_sequence=private_sequence,
            modulus=modulus,
            multiplier=multiplier,
        )

    def encrypt_text(
        self,
        text: str,
        key_pair: AdditiveKnapsackKeyPair,
        base: int,
        alphabet: str = FIXED_INPUT_ALPHABET,
    ) -> tuple[str, str, KnapsackCipherPayload]:
        """Шифрует строку, предварительно переводя её в цифры выбранного алфавита."""

        normalized_text = validate_fixed_alphabet_text(text, "Сообщение")
        codec = AlphabetCodec(alphabet)
        encoding = codec.encode_to_digits(normalized_text, base)
        payload = self.base_service.encrypt_coefficients(encoding.digits, key_pair)
        encoded = self._format_payload(
            digit_count=len(encoding.digits),
            symbol_count=len(encoding.indices),
            width=encoding.width,
            base=base,
            values=payload.values,
        )
        steps = "\n".join(
            [
                "Подготовка сообщения для GAKP:",
                f"Алфавит содержит {len(alphabet)} символов.",
                f"Индексы символов: {encoding.indices}",
                f"Основание B = {base}, цифр на символ = {encoding.width}",
                f"Цифровое представление: {encoding.digits}",
                payload.steps,
                self.describe_spaces(len(encoding.indices), len(alphabet), len(key_pair.public_sequence)),
            ]
        )
        payload.encoded = encoded
        payload.steps = steps
        return encoded, steps, payload

    def decrypt_text(
        self,
        payload: str,
        key_pair: AdditiveKnapsackKeyPair,
        alphabet: str = FIXED_INPUT_ALPHABET,
    ) -> tuple[str, str]:
        """Расшифровывает алфавитное сообщение GAKP."""

        digit_count, symbol_count, width, base, inner_payload = self._parse_payload(payload)
        digits, base_steps = self.base_service.decrypt_coefficients(inner_payload, key_pair)
        trimmed_digits = digits[:digit_count]
        codec = AlphabetCodec(alphabet)
        text = codec.decode_from_digits(trimmed_digits, base, width, symbol_count)
        steps = "\n".join(
            [
                base_steps,
                f"Цифры после удаления дополнения: {trimmed_digits}",
                f"Восстановленный текст: {text}",
                self.describe_spaces(symbol_count, len(alphabet), len(key_pair.public_sequence)),
            ]
        )
        return text, steps

    @staticmethod
    def describe_spaces(symbol_count: int, alphabet_size: int, block_size: int) -> str:
        """Возвращает учебное описание пространств сообщения, ключей и шифртекста."""

        return (
            "Пространства учебной схемы:\n"
            f"- Открытые сообщения: строки длины {symbol_count} над алфавитом мощности {alphabet_size}\n"
            f"- Пространство ключей: последовательности длины {block_size}, модуль и множитель\n"
            f"- Пространство шифртекстов: последовательности целых сумм по одному числу на блок"
        )

    @staticmethod
    def _format_payload(
        digit_count: int,
        symbol_count: int,
        width: int,
        base: int,
        values: list[int],
    ) -> str:
        return f"{digit_count},{symbol_count},{width},{base}|{' '.join(str(value) for value in values)}"

    @staticmethod
    def _parse_payload(payload: str) -> tuple[int, int, int, int, str]:
        if "|" not in payload:
            raise InputValidationError("Шифртекст GAKP должен содержать метаданные и символ '|'.")
        meta, values = payload.split("|", maxsplit=1)
        parts = [item.strip() for item in meta.split(",")]
        if len(parts) != 4:
            raise InputValidationError("Шифртекст GAKP должен иметь формат `digits,symbols,width,base|...`.")
        try:
            digit_count, symbol_count, width, base = [int(item) for item in parts]
        except ValueError as error:
            raise InputValidationError("Метаданные GAKP должны быть целыми числами.") from error
        return digit_count, symbol_count, width, base, f"{digit_count}|{values}"

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает пример для GAKP."""

        return {
            "length": "10",
            "base": "4",
            "message": "code",
        }
