"""Обобщённый аддитивный рюкзак для алфавитных сообщений."""

from __future__ import annotations

from models.crypto_models import AdditiveKnapsackKeyPair, KnapsackCipherPayload
from services.additive_knapsack_service import AdditiveKnapsackService
from utils.text_codec import AlphabetCodec, FIXED_INPUT_ALPHABET, validate_fixed_alphabet_text
from utils.validation import InputValidationError


class GeneralizedAdditiveKnapsackService:
    """Сервис GAKP/GAKR в учебной постановке."""

    COEFFICIENT_LIMIT = len(FIXED_INPUT_ALPHABET) - 1

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

        if base != len(FIXED_INPUT_ALPHABET):
            raise InputValidationError(
                f"Для учебной модели GAKP используется фиксированное множество Q мощности {len(FIXED_INPUT_ALPHABET)}."
            )
        return self.base_service.generate_keys(
            length=length,
            coefficient_limit=self.COEFFICIENT_LIMIT,
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
        """Шифрует строку, напрямую переводя символы в Q = {0..26}."""

        normalized_text = validate_fixed_alphabet_text(text, "Сообщение")
        codec = AlphabetCodec(alphabet)
        indices = codec.text_to_indices(normalized_text)
        payload = self.base_service.encrypt_coefficients(indices, key_pair)
        encoded = payload.encoded
        steps = "\n".join(
            [
                "Подготовка сообщения для GAKP:",
                "Кодирование символов:",
                "a→0, b→1, c→2, ..., z→25, пробел→26",
                f"Множество числовых эквивалентов Q = {{0, 1, 2, ..., 25, 26}}",
                f"Числовые эквиваленты сообщения: {indices}",
                payload.steps,
                self.describe_spaces(len(indices), len(alphabet), len(key_pair.public_sequence)),
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

        coefficients, base_steps = self.base_service.decrypt_coefficients(payload, key_pair)
        codec = AlphabetCodec(alphabet)
        text = codec.indices_to_text(coefficients)
        steps = "\n".join(
            [
                base_steps,
                f"Восстановленные числовые эквиваленты Q: {coefficients}",
                f"Восстановленный текст: {text}",
                self.describe_spaces(len(coefficients), len(alphabet), len(key_pair.public_sequence)),
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
    def example_values() -> dict[str, str]:
        """Возвращает пример для GAKP."""

        return {
            "length": "10",
            "base": "27",
            "message": "code",
        }
