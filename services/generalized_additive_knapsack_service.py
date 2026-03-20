"""Обобщённый аддитивный рюкзак для алфавитных сообщений."""

from __future__ import annotations

from models.crypto_models import AdditiveKnapsackKeyPair, KnapsackCipherPayload
from services.additive_knapsack_service import AdditiveKnapsackService
from utils.text_codec import (
    AlphabetCodec,
    FIXED_INPUT_ALPHABET,
    base_digits_to_int,
    int_to_base_digits,
    validate_fixed_alphabet_text,
)
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
            raise InputValidationError("Параметр p должен быть не меньше 2.")
        if base**length <= len(FIXED_INPUT_ALPHABET) - 1:
            raise InputValidationError(
                "Параметры p и n слишком малы: все символы алфавита должны помещаться в p-ичное представление длины n."
            )

        key_pair, base_steps = self.base_service.generate_keys(
            length=length,
            coefficient_limit=base - 1,
            private_sequence=private_sequence,
            modulus=modulus,
            multiplier=multiplier,
        )

        prefix = [
            "Генерация ключей GAKP:",
            f"1. Выбран параметр p = {base}, коэффициенты x_i ∈ {{0, 1, ..., {base - 1}}}",
            f"2. Длина p-ичного блока n = {length}",
            f"3. Закрытый рюкзак W должен удовлетворять условию w_i > ({base - 1}) * Σ(w_j), j < i",
        ]
        return key_pair, "\n".join(prefix + [base_steps])

    def encrypt_text(
        self,
        text: str,
        key_pair: AdditiveKnapsackKeyPair,
        base: int,
        alphabet: str = FIXED_INPUT_ALPHABET,
    ) -> tuple[str, str, KnapsackCipherPayload]:
        """Шифрует строку, переводя символы в p-ичное представление фиксированной длины."""

        normalized_text = validate_fixed_alphabet_text(text, "Сообщение")
        codec = AlphabetCodec(alphabet)
        indices = codec.text_to_indices(normalized_text)
        width = len(key_pair.public_sequence)
        if base**width <= max(indices, default=0):
            raise InputValidationError(
                "Текущие параметры p и n не позволяют закодировать все символы сообщения."
            )

        blocks = [int_to_base_digits(index, base, width) for index in indices]
        coefficients = [digit for block in blocks for digit in block]
        payload = self.base_service.encrypt_coefficients(coefficients, key_pair)
        cipher_per_symbol = payload.values[: len(indices)]
        encoded = payload.encoded

        lines = [
            "Подготовка сообщения для GAKP:",
            f"Кодирование символов: a→0, b→1, ..., z→25, пробел→26",
            f"Множество числовых эквивалентов Q = {{0, 1, 2, ..., 25, 26}}",
            f"Параметр p = {base}",
            f"Длина p-ичного блока n = {width}",
            f"Числовые эквиваленты сообщения: {indices}",
        ]
        for position, (symbol, index, block) in enumerate(zip(normalized_text, indices, blocks, strict=True), start=1):
            lines.append(
                f"Символ {position}: '{symbol}' → {index} → {''.join(map(str, block))}_{base} = {block}"
            )

        if normalized_text == "hi" and base == 3 and key_pair.private_sequence == [2, 5, 16, 50]:
            lines.extend(
                [
                    "Пример для слова hi:",
                    "h → 7 → 0021_3, коэффициенты (0, 0, 2, 1)",
                    "i → 8 → 0022_3, коэффициенты (0, 0, 2, 2)",
                    f"Открытый рюкзак B = {key_pair.public_sequence}",
                    f"Для h: c = 0*{key_pair.public_sequence[0]} + 0*{key_pair.public_sequence[1]} + 2*{key_pair.public_sequence[2]} + 1*{key_pair.public_sequence[3]} = {cipher_per_symbol[0]}",
                    f"Для i: c = 0*{key_pair.public_sequence[0]} + 0*{key_pair.public_sequence[1]} + 2*{key_pair.public_sequence[2]} + 2*{key_pair.public_sequence[3]} = {cipher_per_symbol[1]}",
                ]
            )

        lines.extend(
            [
                payload.steps,
                self.describe_spaces(len(indices), len(alphabet), base, width),
            ]
        )
        payload.encoded = encoded
        payload.steps = "\n".join(lines)
        return encoded, payload.steps, payload

    def decrypt_text(
        self,
        payload: str,
        key_pair: AdditiveKnapsackKeyPair,
        alphabet: str = FIXED_INPUT_ALPHABET,
        base: int = 3,
    ) -> tuple[str, str]:
        """Расшифровывает алфавитное сообщение GAKP."""

        coefficients, base_steps = self.base_service.decrypt_coefficients(payload, key_pair)
        width = len(key_pair.private_sequence)
        if len(coefficients) % width != 0:
            raise InputValidationError("Длина восстановленных коэффициентов не делится на размер p-ичного блока.")

        blocks = [coefficients[index : index + width] for index in range(0, len(coefficients), width)]
        indices = [base_digits_to_int(block, base) for block in blocks]
        codec = AlphabetCodec(alphabet)
        text = codec.indices_to_text(indices)

        steps = [
            base_steps,
            f"Параметр p = {base}",
            f"Длина p-ичного блока n = {width}",
            f"Восстановленные коэффициенты: {coefficients}",
        ]
        for position, block in enumerate(blocks, start=1):
            steps.append(
                f"Блок {position}: {''.join(map(str, block))}_{base} = {indices[position - 1]}"
            )
        steps.extend(
            [
                f"Восстановленные числовые эквиваленты Q: {indices}",
                f"Восстановленный текст: {text}",
                self.describe_spaces(len(indices), len(alphabet), base, width),
            ]
        )
        return text, "\n".join(steps)

    @staticmethod
    def describe_spaces(symbol_count: int, alphabet_size: int, base: int, block_size: int) -> str:
        """Возвращает учебное описание пространств сообщения, ключей и шифртекста."""

        return (
            "Пространства учебной схемы:\n"
            f"- Открытые сообщения: строки длины {symbol_count} над алфавитом мощности {alphabet_size}\n"
            f"- Пространство коэффициентов блока: p-ичные векторы длины {block_size}, где p = {base}\n"
            f"- Пространство ключей: закрытый рюкзак W длины {block_size}, модуль m и множитель a\n"
            f"- Пространство шифртекстов: последовательности целых сумм по одному числу на p-ичный блок"
        )

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает пример для GAKP."""

        return {
            "length": "4",
            "base": "3",
            "private_sequence": "2, 5, 16, 50",
            "modulus": "149",
            "multiplier": "31",
            "message": "hi",
        }
