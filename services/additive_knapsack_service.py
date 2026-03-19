"""Учебные аддитивные рюкзачные схемы."""

from __future__ import annotations

from math import gcd

from models.crypto_models import AdditiveKnapsackKeyPair, KnapsackCipherPayload
from utils.number_theory import generalized_superincreasing_sequence, mod_inverse, next_prime
from utils.text_codec import (
    bits_to_text,
    validate_fixed_alphabet_text,
    format_length_prefixed_payload,
    split_sequence,
    text_to_bits,
)
from utils.validation import InputValidationError, parse_length_prefixed_numbers


class AdditiveKnapsackService:
    """Сервис для классического и обобщённого аддитивного рюкзака."""

    def generate_keys(
        self,
        length: int,
        coefficient_limit: int = 1,
        private_sequence: list[int] | None = None,
        modulus: int | None = None,
        multiplier: int | None = None,
    ) -> tuple[AdditiveKnapsackKeyPair, str]:
        """Формирует приватный и публичный рюкзак."""

        if private_sequence is None:
            private_sequence = generalized_superincreasing_sequence(
                length=length,
                coefficient_limit=coefficient_limit,
            )
        self.validate_private_sequence(private_sequence, coefficient_limit)

        max_sum = coefficient_limit * sum(private_sequence)
        chosen_modulus = modulus if modulus is not None else next_prime(max_sum + length + 5)
        if chosen_modulus <= max_sum:
            raise InputValidationError(
                f"Модуль m должен быть больше {max_sum}, чтобы не возникало наложения сумм."
            )

        chosen_multiplier = multiplier if multiplier is not None else self._pick_multiplier(chosen_modulus)
        if not 1 < chosen_multiplier < chosen_modulus:
            raise InputValidationError("Множитель a должен удовлетворять условию 1 < a < m.")
        if gcd(chosen_multiplier, chosen_modulus) != 1:
            raise InputValidationError("Множитель a должен быть взаимно простым с модулем m.")

        public_sequence = [(chosen_multiplier * value) % chosen_modulus for value in private_sequence]
        inverse_multiplier = mod_inverse(chosen_multiplier, chosen_modulus)

        key_pair = AdditiveKnapsackKeyPair(
            private_sequence=private_sequence,
            public_sequence=public_sequence,
            modulus=chosen_modulus,
            multiplier=chosen_multiplier,
            inverse_multiplier=inverse_multiplier,
            coefficient_limit=coefficient_limit,
        )
        lines = [
            "Генерация ключей аддитивного рюкзака:",
            f"1. Закрытый рюкзак w = {private_sequence}",
            f"2. Ограничение коэффициентов: 0..{coefficient_limit}",
            f"3. Выбран модуль m = {chosen_modulus}, при этом m > {max_sum}",
            f"4. Выбран множитель a = {chosen_multiplier}, gcd(a, m) = 1",
            f"5. Публичный рюкзак b = a * w mod m = {public_sequence}",
            f"6. Обратный множитель a^(-1) mod m = {inverse_multiplier}",
        ]
        return key_pair, "\n".join(lines)

    def encrypt_coefficients(
        self,
        coefficients: list[int],
        key_pair: AdditiveKnapsackKeyPair,
    ) -> KnapsackCipherPayload:
        """Шифрует последовательность коэффициентов рюкзака."""

        self._validate_coefficients(coefficients, key_pair.coefficient_limit)
        block_size = len(key_pair.public_sequence)
        blocks, padding = split_sequence(coefficients, block_size, pad_value=0)
        cipher_values: list[int] = []
        lines = [
            "Шифрование аддитивным рюкзаком:",
            f"Размер блока: {block_size}",
            f"Добавлено дополняющих коэффициентов: {padding}",
        ]

        for block_index, block in enumerate(blocks, start=1):
            products = [digit * weight for digit, weight in zip(block, key_pair.public_sequence, strict=True)]
            cipher_value = sum(products)
            cipher_values.append(cipher_value)
            lines.append(
                f"Блок {block_index}: {block} -> сумма Σ(x_i * b_i) = {' + '.join(map(str, products))} = {cipher_value}"
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
        key_pair: AdditiveKnapsackKeyPair,
    ) -> tuple[list[int], str]:
        """Расшифровывает коэффициенты аддитивного рюкзака."""

        parsed = parse_length_prefixed_numbers(payload)
        coefficients: list[int] = []
        lines = [
            "Расшифрование аддитивного рюкзака:",
            f"Обратный множитель a^(-1) = {key_pair.inverse_multiplier}",
        ]

        for block_index, cipher_value in enumerate(parsed.values, start=1):
            transformed = (cipher_value * key_pair.inverse_multiplier) % key_pair.modulus
            restored = self._recover_superincreasing_digits(
                transformed,
                key_pair.private_sequence,
                key_pair.coefficient_limit,
            )
            coefficients.extend(restored)
            lines.append(
                f"Блок {block_index}: c = {cipher_value}, s = c * a^(-1) mod m = {transformed}, коэффициенты = {restored}"
            )

        trimmed = coefficients[: parsed.length]
        lines.append(f"После удаления дополнения: {trimmed}")
        return trimmed, "\n".join(lines)

    def encrypt_message(
        self,
        message: str,
        key_pair: AdditiveKnapsackKeyPair,
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
        key_pair: AdditiveKnapsackKeyPair,
    ) -> tuple[str, str]:
        """Расшифровывает сообщение в текст фиксированного учебного алфавита."""

        coefficients, steps = self.decrypt_coefficients(payload, key_pair)
        bits = "".join(str(bit) for bit in coefficients)
        restored = bits_to_text(bits)
        validate_fixed_alphabet_text(restored, "Расшифрованное сообщение")
        result_lines = [
            steps,
            f"Восстановленная битовая строка: {bits}",
            f"Восстановленное сообщение: {restored}",
        ]
        return restored, "\n".join(result_lines)

    def validate_private_sequence(self, sequence: list[int], coefficient_limit: int = 1) -> None:
        """Проверяет свойство (обобщённой) сверхвозрастаемости."""

        if len(sequence) < 2:
            raise InputValidationError("Закрытый рюкзак должен содержать не меньше двух элементов.")
        total = 0
        for index, value in enumerate(sequence, start=1):
            if value <= 0:
                raise InputValidationError("Все элементы закрытого рюкзака должны быть положительными.")
            if index > 1 and value <= coefficient_limit * total:
                raise InputValidationError(
                    "Последовательность должна быть сверхвозрастающей "
                    f"с учётом коэффициентов 0..{coefficient_limit}."
                )
            total += value

    def _recover_superincreasing_digits(
        self,
        value: int,
        sequence: list[int],
        coefficient_limit: int,
    ) -> list[int]:
        """Жадно восстанавливает коэффициенты по сверхвозрастающему рюкзаку."""

        digits = [0] * len(sequence)
        remaining = value
        for index in range(len(sequence) - 1, -1, -1):
            weight = sequence[index]
            digit = min(coefficient_limit, remaining // weight)
            digits[index] = digit
            remaining -= digit * weight
        if remaining != 0:
            raise InputValidationError(
                "Не удалось восстановить сообщение: остаток после жадного декодирования не равен нулю."
            )
        return digits

    def _validate_coefficients(self, coefficients: list[int], coefficient_limit: int) -> None:
        for digit in coefficients:
            if not 0 <= digit <= coefficient_limit:
                raise InputValidationError(
                    f"Коэффициенты должны лежать в диапазоне 0..{coefficient_limit}."
                )

    @staticmethod
    def _pick_multiplier(modulus: int) -> int:
        candidate = 2
        while gcd(candidate, modulus) != 1:
            candidate += 1
        return candidate

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает демонстрационные параметры классической схемы."""

        return {
            "length": "8",
            "private_sequence": "2, 3, 7, 14, 30, 57, 120, 251",
            "modulus": "491",
            "multiplier": "41",
            "message": "hello",
        }
