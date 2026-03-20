"""Обобщённый мультипликативный рюкзак для алфавитных сообщений."""

from __future__ import annotations

from models.crypto_models import KnapsackCipherPayload, MultiplicativeKnapsackKeyPair
from services.multiplicative_knapsack_service import MultiplicativeKnapsackService
from utils.text_codec import (
    AlphabetCodec,
    FIXED_INPUT_ALPHABET,
    base_digits_to_int,
    int_to_base_digits,
    validate_fixed_alphabet_text,
)
from utils.validation import InputValidationError


class GeneralizedMultiplicativeKnapsackService:
    """Сервис GMKP/GMKR в учебной постановке."""

    def __init__(self) -> None:
        self.base_service = MultiplicativeKnapsackService()

    def generate_keys(
        self,
        length: int,
        base: int,
        private_primes: list[int] | None = None,
        modulus: int | None = None,
        secret_exponent: int | None = None,
    ) -> tuple[MultiplicativeKnapsackKeyPair, str]:
        """Генерирует ключи обобщённого мультипликативного рюкзака."""

        if base < 2:
            raise InputValidationError("Параметр p должен быть не меньше 2.")
        if base**length <= len(FIXED_INPUT_ALPHABET) - 1:
            raise InputValidationError(
                "Параметры p и n слишком малы: все символы алфавита должны помещаться в p-ичное представление длины n."
            )

        key_pair, base_steps = self.base_service.generate_keys(
            length=length,
            coefficient_limit=base - 1,
            private_primes=private_primes,
            modulus=modulus,
            secret_exponent=secret_exponent,
        )

        prefix = [
            "Генерация ключей GMKP:",
            f"1. Выбран параметр p = {base}, коэффициенты x_i ∈ {{0, 1, ..., {base - 1}}}",
            f"2. Длина p-ичного блока n = {length}",
            "3. Закрытый рюкзак W состоит из простых чисел, а открытый рюкзак B строится из решений b_i^s ≡ w_i (mod m)",
        ]
        return key_pair, "\n".join(prefix + [base_steps])

    def encrypt_text(
        self,
        text: str,
        key_pair: MultiplicativeKnapsackKeyPair,
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
            "Подготовка сообщения для GMKP:",
            "Кодирование символов: a→0, b→1, ..., z→25, пробел→26",
            "Множество числовых эквивалентов Q = {0, 1, 2, ..., 25, 26}",
            f"Параметр p = {base}",
            f"Длина p-ичного блока n = {width}",
            f"Числовые эквиваленты сообщения: {indices}",
        ]
        for position, (symbol, index, block) in enumerate(zip(normalized_text, indices, blocks, strict=True), start=1):
            lines.append(
                f"Символ {position}: '{symbol}' → {index} → {''.join(map(str, block))}_{base} = {block}"
            )
        for position, (block, cipher_value) in enumerate(zip(blocks, cipher_per_symbol, strict=True), start=1):
            lines.append(f"Блок {position}: коэффициенты {block} -> шифртекст {cipher_value}")

        if (
            normalized_text == "hi"
            and base == 3
            and key_pair.private_primes == [2, 3, 5]
            and key_pair.modulus == 1009
            and key_pair.secret_exponent == 5
        ):
            lines.extend(
                [
                    "Пример для слова hi:",
                    "h → 7 → 021_3, коэффициенты (0, 2, 1)",
                    "i → 8 → 022_3, коэффициенты (0, 2, 2)",
                    f"Открытый рюкзак B = {key_pair.public_sequence}",
                    f"Для h: c = {key_pair.public_sequence[0]}^0 * {key_pair.public_sequence[1]}^2 * {key_pair.public_sequence[2]}^1 mod 1009 = {cipher_per_symbol[0]}",
                    f"Для i: c = {key_pair.public_sequence[0]}^0 * {key_pair.public_sequence[1]}^2 * {key_pair.public_sequence[2]}^2 mod 1009 = {cipher_per_symbol[1]}",
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
        key_pair: MultiplicativeKnapsackKeyPair,
        alphabet: str = FIXED_INPUT_ALPHABET,
        base: int = 3,
    ) -> tuple[str, str]:
        """Расшифровывает алфавитное сообщение GMKP."""

        coefficients, base_steps = self.base_service.decrypt_coefficients(payload, key_pair)
        width = len(key_pair.private_primes)
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
        """Возвращает учебное описание пространств схемы."""

        return (
            "Пространства учебной схемы:\n"
            f"- Открытые сообщения: строки длины {symbol_count} над алфавитом мощности {alphabet_size}\n"
            f"- Пространство коэффициентов блока: p-ичные векторы длины {block_size}, где p = {base}\n"
            f"- Пространство ключей: закрытый рюкзак W длины {block_size}, модуль m и секретный показатель s\n"
            f"- Пространство шифртекстов: последовательности произведений по одному числу на p-ичный блок"
        )

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает пример для GMKP."""

        return {
            "length": "3",
            "base": "3",
            "private_primes": "2, 3, 5",
            "modulus": "1009",
            "secret_exponent": "5",
            "message": "hi",
        }
