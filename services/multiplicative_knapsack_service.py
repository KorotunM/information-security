"""Учебные мультипликативные рюкзачные схемы."""

from __future__ import annotations

from math import prod

from models.crypto_models import KnapsackCipherPayload, MultiplicativeKnapsackKeyPair
from utils.number_theory import (
    discrete_log_table,
    factor_with_bound,
    first_primes,
    next_prime,
    primitive_root,
)
from utils.text_codec import (
    bits_to_text,
    format_length_prefixed_payload,
    split_sequence,
    text_to_bits,
    validate_fixed_alphabet_text,
)
from utils.validation import InputValidationError, parse_length_prefixed_numbers


class MultiplicativeKnapsackService:
    """Сервис для классического и обобщённого мультипликативного рюкзака."""

    MAX_EDUCATIONAL_PRODUCT = 10_000_000

    def generate_keys(
        self,
        length: int,
        coefficient_limit: int = 1,
        private_primes: list[int] | None = None,
        modulus: int | None = None,
        generator: int | None = None,
    ) -> tuple[MultiplicativeKnapsackKeyPair, str]:
        """Строит учебные ключи мультипликативного рюкзака."""

        private_values = private_primes or first_primes(length)
        self.validate_private_primes(private_values)

        max_product = prod(value ** coefficient_limit for value in private_values)
        if max_product > self.MAX_EDUCATIONAL_PRODUCT:
            raise InputValidationError(
                "Параметры слишком велики для учебной реализации МВКР. "
                "Уменьшите длину рюкзака или основание кодирования."
            )
        chosen_modulus = modulus if modulus is not None else next_prime(max_product + 2)
        if chosen_modulus <= max_product:
            raise InputValidationError(
                f"Модуль q должен быть больше {max_product}, чтобы произведение восстанавливалось без наложений."
            )

        chosen_generator = generator if generator is not None else primitive_root(chosen_modulus)
        log_table = discrete_log_table(chosen_generator, chosen_modulus)

        public_logs: list[int] = []
        for value in private_values:
            if value >= chosen_modulus:
                raise InputValidationError("Все приватные множители должны быть меньше модуля q.")
            public_logs.append(log_table[value])

        key_pair = MultiplicativeKnapsackKeyPair(
            private_primes=private_values,
            public_logs=public_logs,
            modulus=chosen_modulus,
            generator=chosen_generator,
            coefficient_limit=coefficient_limit,
            discrete_log_table=log_table,
        )
        lines = [
            "Генерация ключей мультипликативного рюкзака:",
            f"1. Приватные множители p = {private_values}",
            f"2. Ограничение коэффициентов: 0..{coefficient_limit}",
            f"3. Выбран простой модуль q = {chosen_modulus}, причём q > {max_product}",
            f"4. Выбран генератор g = {chosen_generator}",
            f"5. Публичные логарифмы a_i, где g^a_i ≡ p_i (mod q): {public_logs}",
        ]
        return key_pair, "\n".join(lines)

    def encrypt_coefficients(
        self,
        coefficients: list[int],
        key_pair: MultiplicativeKnapsackKeyPair,
    ) -> KnapsackCipherPayload:
        """Шифрует коэффициенты мультипликативной схемой."""

        self._validate_coefficients(coefficients, key_pair.coefficient_limit)
        block_size = len(key_pair.public_logs)
        blocks, padding = split_sequence(coefficients, block_size, pad_value=0)
        cipher_values: list[int] = []
        lines = [
            "Шифрование мультипликативным рюкзаком:",
            f"Размер блока: {block_size}",
            f"Добавлено дополняющих коэффициентов: {padding}",
        ]

        for block_index, block in enumerate(blocks, start=1):
            components = [
                digit * log_value for digit, log_value in zip(block, key_pair.public_logs, strict=True)
            ]
            exponent_sum = sum(components) % (key_pair.modulus - 1)
            cipher_values.append(exponent_sum)
            lines.append(
                f"Блок {block_index}: {block} -> k = Σ(x_i * a_i) mod (q - 1) = {' + '.join(map(str, components))} mod {key_pair.modulus - 1} = {exponent_sum}"
            )

        encoded = format_length_prefixed_payload(len(coefficients), cipher_values)
        return KnapsackCipherPayload(
            values=cipher_values,
            data_length=len(coefficients),
            block_size=block_size,
            encoded=encoded,
            steps="\n".join(lines),
        )

    def decrypt_coefficients(
        self,
        payload: str,
        key_pair: MultiplicativeKnapsackKeyPair,
    ) -> tuple[list[int], str]:
        """Расшифровывает коэффициенты мультипликативного рюкзака."""

        parsed = parse_length_prefixed_numbers(payload)
        coefficients: list[int] = []
        lines = [
            "Расшифрование мультипликативного рюкзака:",
            f"Используем g = {key_pair.generator}, q = {key_pair.modulus}",
        ]

        for block_index, cipher_value in enumerate(parsed.values, start=1):
            product_value = pow(key_pair.generator, cipher_value, key_pair.modulus)
            restored = factor_with_bound(
                product_value,
                key_pair.private_primes,
                key_pair.coefficient_limit,
            )
            coefficients.extend(restored)
            lines.append(
                f"Блок {block_index}: g^k mod q = {key_pair.generator}^{cipher_value} mod {key_pair.modulus} = {product_value}, коэффициенты = {restored}"
            )

        trimmed = coefficients[: parsed.length]
        lines.append(f"После удаления дополнения: {trimmed}")
        return trimmed, "\n".join(lines)

    def encrypt_message(
        self,
        message: str,
        key_pair: MultiplicativeKnapsackKeyPair,
    ) -> tuple[KnapsackCipherPayload, str]:
        """Шифрует текст фиксированного учебного алфавита."""

        normalized_message = validate_fixed_alphabet_text(message, "Сообщение")
        bits = text_to_bits(normalized_message)

        coefficients = [int(bit) for bit in bits]
        payload = self.encrypt_coefficients(coefficients, key_pair)
        preface = [
            "Подготовка открытого сообщения:",
            "Режим: текст из строчных английских букв и пробела",
            f"Сообщение: {normalized_message}",
            f"Битовая последовательность: {bits}",
        ]
        return payload, "\n".join(preface + [payload.steps])

    def decrypt_message(
        self,
        payload: str,
        key_pair: MultiplicativeKnapsackKeyPair,
    ) -> tuple[str, str]:
        """Расшифровывает сообщение."""

        coefficients, steps = self.decrypt_coefficients(payload, key_pair)
        bits = "".join(str(bit) for bit in coefficients)
        restored = bits_to_text(bits)
        validate_fixed_alphabet_text(restored, "Расшифрованное сообщение")
        lines = [
            steps,
            f"Восстановленная битовая строка: {bits}",
            f"Восстановленное сообщение: {restored}",
        ]
        return restored, "\n".join(lines)

    def validate_private_primes(self, values: list[int]) -> None:
        """Проверяет корректность приватного множества."""

        if len(values) < 2:
            raise InputValidationError("Нужно не меньше двух приватных множителей.")
        if any(value <= 1 for value in values):
            raise InputValidationError("Все приватные множители должны быть больше 1.")
        if len(set(values)) != len(values):
            raise InputValidationError("Приватные множители должны быть попарно различными.")
        for value in values:
            for divisor in range(2, int(value**0.5) + 1):
                if value % divisor == 0:
                    raise InputValidationError(
                        "Для учебной мультипликативной схемы используйте простые приватные множители."
                    )

    def _validate_coefficients(self, coefficients: list[int], coefficient_limit: int) -> None:
        for digit in coefficients:
            if not 0 <= digit <= coefficient_limit:
                raise InputValidationError(
                    f"Коэффициенты должны лежать в диапазоне 0..{coefficient_limit}."
                )

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает демонстрационные значения."""

        return {
            "length": "6",
            "private_primes": "2, 3, 5, 7, 11, 13",
            "message": "code",
        }
