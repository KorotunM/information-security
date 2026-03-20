"""Учебные мультипликативные рюкзачные схемы."""

from __future__ import annotations

from math import gcd, prod

from models.crypto_models import KnapsackCipherPayload, MultiplicativeKnapsackKeyPair
from utils.number_theory import choose_coprime, factor_with_bound, mod_inverse, next_prime
from utils.text_codec import (
    binary_coefficients_to_fixed_alphabet_text,
    fixed_alphabet_text_to_binary_coefficients,
    format_length_prefixed_payload,
    split_sequence,
    validate_fixed_alphabet_text,
)
from utils.validation import InputValidationError, parse_length_prefixed_numbers


class MultiplicativeKnapsackService:
    """Сервис для классического и обобщённого мультипликативного рюкзака."""

    MAX_EDUCATIONAL_PRODUCT = 100_000_000

    def generate_keys(
        self,
        length: int,
        coefficient_limit: int = 1,
        private_primes: list[int] | None = None,
        modulus: int | None = None,
        secret_exponent: int | None = None,
    ) -> tuple[MultiplicativeKnapsackKeyPair, str]:
        """Строит учебные ключи мультипликативного рюкзака в форме b_i^s ≡ w_i (mod m)."""

        private_values = private_primes or self._default_private_primes(length)
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
                f"Модуль m должен быть больше {max_product}, чтобы произведение восстанавливалось без наложений."
            )

        if any(value >= chosen_modulus for value in private_values):
            raise InputValidationError("Все элементы закрытого рюкзака W должны быть меньше модуля m.")

        chosen_exponent = (
            secret_exponent if secret_exponent is not None else choose_coprime(chosen_modulus - 1, start=3)
        )
        if not 1 < chosen_exponent < chosen_modulus - 1:
            raise InputValidationError("Секретный показатель s должен удовлетворять условию 1 < s < m - 1.")
        if gcd(chosen_exponent, chosen_modulus - 1) != 1:
            raise InputValidationError("Показатель s должен быть взаимно простым с m - 1.")

        inverse_exponent = mod_inverse(chosen_exponent, chosen_modulus - 1)
        public_sequence = [pow(value, inverse_exponent, chosen_modulus) for value in private_values]

        key_pair = MultiplicativeKnapsackKeyPair(
            private_primes=private_values,
            public_sequence=public_sequence,
            modulus=chosen_modulus,
            secret_exponent=chosen_exponent,
            inverse_exponent=inverse_exponent,
            coefficient_limit=coefficient_limit,
        )

        lines = [
            "Генерация ключей мультипликативного рюкзака:",
            f"1. Закрытый рюкзак W = {private_values}",
            f"2. Ограничение коэффициентов: 0..{coefficient_limit}",
            f"3. Выбран простой модуль m = {chosen_modulus}, причём m > {max_product}",
            f"4. Выбран секретный показатель s = {chosen_exponent}, gcd(s, m - 1) = 1",
            f"5. Вычислен показатель s^(-1) mod (m - 1) = {inverse_exponent}",
            f"6. Открытый рюкзак B = [w_i^(s^(-1)) mod m] = {public_sequence}",
            "7. Для каждого i выполняется сравнение b_i^s ≡ w_i (mod m)",
        ]
        return key_pair, "\n".join(lines)

    def encrypt_coefficients(
        self,
        coefficients: list[int],
        key_pair: MultiplicativeKnapsackKeyPair,
    ) -> KnapsackCipherPayload:
        """Шифрует коэффициенты мультипликативной схемой."""

        self._validate_coefficients(coefficients, key_pair.coefficient_limit)
        block_size = len(key_pair.public_sequence)
        blocks, padding = split_sequence(coefficients, block_size, pad_value=0)
        cipher_values: list[int] = []
        lines = [
            "Шифрование мультипликативным рюкзаком:",
            f"Размер блока: {block_size}",
            f"Добавлено дополняющих коэффициентов: {padding}",
        ]

        for block_index, block in enumerate(blocks, start=1):
            factors = [
                pow(base, digit, key_pair.modulus)
                for digit, base in zip(block, key_pair.public_sequence, strict=True)
            ]
            cipher_value = 1
            for factor in factors:
                cipher_value = (cipher_value * factor) % key_pair.modulus
            cipher_values.append(cipher_value)
            lines.append(
                f"Блок {block_index}: {block} -> c = ∏ b_i^x_i mod m = {' * '.join(map(str, factors))} mod {key_pair.modulus} = {cipher_value}"
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
            f"Используем секретный показатель s = {key_pair.secret_exponent}",
        ]

        for block_index, cipher_value in enumerate(parsed.values, start=1):
            intermediate = pow(cipher_value, key_pair.secret_exponent, key_pair.modulus)
            restored = factor_with_bound(
                intermediate,
                key_pair.private_primes,
                key_pair.coefficient_limit,
            )
            coefficients.extend(restored)
            lines.append(
                f"Блок {block_index}: u = c^s mod m = {cipher_value}^{key_pair.secret_exponent} mod {key_pair.modulus} = {intermediate}, коэффициенты = {restored}"
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
        indices, coefficients, width = fixed_alphabet_text_to_binary_coefficients(
            normalized_message,
            "Сообщение",
        )
        bits = "".join(str(bit) for bit in coefficients)
        payload = self.encrypt_coefficients(coefficients, key_pair)
        preface = [
            "Подготовка открытого сообщения:",
            "Сообщение кодируется по схеме a→0, b→1, ..., z→25, пробел→26.",
            f"Сообщение: {normalized_message}",
            f"Числовые эквиваленты Q: {indices}",
            f"Фиксированная двоичная ширина: {width}",
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
        restored, indices, width = binary_coefficients_to_fixed_alphabet_text(coefficients)
        validate_fixed_alphabet_text(restored, "Расшифрованное сообщение")
        lines = [
            steps,
            f"Восстановленные числовые эквиваленты Q: {indices}",
            f"Фиксированная двоичная ширина: {width}",
            f"Восстановленная битовая строка: {bits}",
            f"Восстановленное сообщение: {restored}",
        ]
        return restored, "\n".join(lines)

    def validate_private_primes(self, values: list[int]) -> None:
        """Проверяет корректность приватного множества."""

        if len(values) < 1:
            raise InputValidationError("Нужен хотя бы один приватный множитель.")
        if any(value <= 1 for value in values):
            raise InputValidationError("Все элементы закрытого рюкзака W должны быть больше 1.")
        if len(set(values)) != len(values):
            raise InputValidationError("Элементы закрытого рюкзака W должны быть попарно различными.")
        for value in values:
            for divisor in range(2, int(value**0.5) + 1):
                if value % divisor == 0:
                    raise InputValidationError(
                        "Для учебной мультипликативной схемы используйте простые элементы закрытого рюкзака."
                    )

    def _validate_coefficients(self, coefficients: list[int], coefficient_limit: int) -> None:
        for digit in coefficients:
            if not 0 <= digit <= coefficient_limit:
                raise InputValidationError(
                    f"Коэффициенты должны лежать в диапазоне 0..{coefficient_limit}."
                )

    @staticmethod
    def _default_private_primes(count: int) -> list[int]:
        """Возвращает первые `count` простых чисел."""

        if count < 1:
            raise InputValidationError("Количество элементов рюкзака должно быть положительным.")
        result: list[int] = []
        candidate = 2
        while len(result) < count:
            for divisor in range(2, int(candidate**0.5) + 1):
                if candidate % divisor == 0:
                    break
            else:
                result.append(candidate)
            candidate += 1
        return result

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает демонстрационные значения."""

        return {
            "length": "6",
            "private_primes": "2, 3, 5, 7, 11, 13",
            "message": "code",
        }
