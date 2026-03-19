"""Обобщённый мультипликативный рюкзак для алфавитных сообщений."""

from __future__ import annotations

from models.crypto_models import KnapsackCipherPayload, MultiplicativeKnapsackKeyPair
from services.multiplicative_knapsack_service import MultiplicativeKnapsackService
from utils.text_codec import AlphabetCodec, FIXED_INPUT_ALPHABET, validate_fixed_alphabet_text
from utils.validation import InputValidationError


class GeneralizedMultiplicativeKnapsackService:
    """Сервис GMKP/GMKR в учебной постановке."""

    COEFFICIENT_LIMIT = len(FIXED_INPUT_ALPHABET) - 1

    def __init__(self) -> None:
        self.base_service = MultiplicativeKnapsackService()

    def generate_keys(
        self,
        length: int,
        base: int,
        private_primes: list[int] | None = None,
        modulus: int | None = None,
        generator: int | None = None,
    ) -> tuple[MultiplicativeKnapsackKeyPair, str]:
        """Генерирует ключи обобщённого мультипликативного рюкзака."""

        if base != len(FIXED_INPUT_ALPHABET):
            raise InputValidationError(
                f"Для учебной модели GMKP используется фиксированное множество Q мощности {len(FIXED_INPUT_ALPHABET)}."
            )
        return self.base_service.generate_keys(
            length=length,
            coefficient_limit=self.COEFFICIENT_LIMIT,
            private_primes=private_primes,
            modulus=modulus,
            generator=generator,
        )

    def encrypt_text(
        self,
        text: str,
        key_pair: MultiplicativeKnapsackKeyPair,
        base: int,
        alphabet: str = FIXED_INPUT_ALPHABET,
    ) -> tuple[str, str, KnapsackCipherPayload]:
        """Шифрует строку в учебной схеме GMKP."""

        normalized_text = validate_fixed_alphabet_text(text, "Сообщение")
        codec = AlphabetCodec(alphabet)
        indices = codec.text_to_indices(normalized_text)
        payload = self.base_service.encrypt_coefficients(indices, key_pair)
        encoded = payload.encoded
        steps = "\n".join(
            [
                "Подготовка сообщения для GMKP:",
                "Кодирование символов:",
                "a→0, b→1, c→2, ..., z→25, пробел→26",
                f"Множество числовых эквивалентов Q = {{0, 1, 2, ..., 25, 26}}",
                f"Числовые эквиваленты сообщения: {indices}",
                payload.steps,
                self.describe_spaces(len(indices), len(alphabet), len(key_pair.public_logs)),
            ]
        )
        payload.encoded = encoded
        payload.steps = steps
        return encoded, steps, payload

    def decrypt_text(
        self,
        payload: str,
        key_pair: MultiplicativeKnapsackKeyPair,
        alphabet: str = FIXED_INPUT_ALPHABET,
    ) -> tuple[str, str]:
        """Расшифровывает алфавитное сообщение GMKP."""

        coefficients, base_steps = self.base_service.decrypt_coefficients(payload, key_pair)
        codec = AlphabetCodec(alphabet)
        text = codec.indices_to_text(coefficients)
        steps = "\n".join(
            [
                base_steps,
                f"Восстановленные числовые эквиваленты Q: {coefficients}",
                f"Восстановленный текст: {text}",
                self.describe_spaces(len(coefficients), len(alphabet), len(key_pair.public_logs)),
            ]
        )
        return text, steps

    @staticmethod
    def describe_spaces(symbol_count: int, alphabet_size: int, block_size: int) -> str:
        """Возвращает учебное описание пространств схемы."""

        return (
            "Пространства учебной схемы:\n"
            f"- Открытые сообщения: строки длины {symbol_count} над алфавитом мощности {alphabet_size}\n"
            f"- Пространство ключей: приватные простые множители длины {block_size}, модуль q и генератор g\n"
            f"- Пространство шифртекстов: последовательности сумм логарифмов по одному числу на блок"
        )

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает пример для GMKP."""

        return {
            "length": "1",
            "base": "27",
            "message": "code",
        }
