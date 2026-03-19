"""Учебная реализация RSA."""

from __future__ import annotations

from math import gcd
from random import Random

from models.crypto_models import RSAKeyPair, RSACipherPayload
from utils.number_theory import choose_coprime, generate_prime, is_probable_prime, mod_inverse
from utils.text_codec import (
    AlphabetCodec,
    FIXED_INPUT_ALPHABET,
    format_length_prefixed_payload,
    validate_fixed_alphabet_text,
)
from utils.validation import InputValidationError, parse_length_prefixed_numbers


class RSAService:
    """Сервис учебной криптосистемы RSA."""

    def __init__(self, rng: Random | None = None) -> None:
        self.rng = rng or Random()

    def generate_keys(self, p: int, q: int, e: int | None = None) -> tuple[RSAKeyPair, str]:
        """Генерирует учебную пару ключей RSA."""

        if not is_probable_prime(p):
            raise InputValidationError("Число p должно быть простым.")
        if not is_probable_prime(q):
            raise InputValidationError("Число q должно быть простым.")
        if p == q:
            raise InputValidationError("Простые числа p и q должны различаться.")

        n = p * q
        phi = (p - 1) * (q - 1)
        chosen_e = e if e is not None else choose_coprime(phi, 65537 if phi > 65537 else 3)
        if not 1 < chosen_e < phi:
            raise InputValidationError("Показатель e должен удовлетворять условию 1 < e < phi(n).")
        if gcd(chosen_e, phi) != 1:
            raise InputValidationError("Число e должно быть взаимно простым с phi(n).")

        d = mod_inverse(chosen_e, phi)
        key_pair = RSAKeyPair(p=p, q=q, n=n, phi=phi, e=chosen_e, d=d)
        steps = "\n".join(
            [
                "Генерация RSA-ключей:",
                f"1. p = {p}, q = {q}",
                f"2. n = p * q = {n}",
                f"3. phi(n) = (p - 1) * (q - 1) = {phi}",
                f"4. Выбрано e = {chosen_e}, gcd(e, phi(n)) = 1",
                f"5. Найдено d = e^(-1) mod phi(n) = {d}",
                f"6. Открытый ключ: ({chosen_e}, {n})",
                f"7. Закрытый ключ: ({d}, {n})",
            ]
        )
        return key_pair, steps

    def auto_generate_keys(
        self,
        bit_length: int = 10,
        e: int | None = None,
    ) -> tuple[RSAKeyPair, str]:
        """Автоматически генерирует простые числа для RSA."""

        p = generate_prime(bit_length, self.rng)
        q = generate_prime(bit_length, self.rng)
        while q == p:
            q = generate_prime(bit_length, self.rng)
        key_pair, steps = self.generate_keys(p, q, e)
        return key_pair, f"Автогенерация простых чисел ({bit_length} бит).\n{steps}"

    def encrypt_text(self, text: str, key_pair: RSAKeyPair) -> RSACipherPayload:
        """Шифрует текст в кодировке Q = {0..26}."""

        normalized_text = validate_fixed_alphabet_text(text, "Открытый текст")
        codec = AlphabetCodec(FIXED_INPUT_ALPHABET)
        plain_values = codec.text_to_indices(normalized_text)
        if key_pair.n <= len(FIXED_INPUT_ALPHABET):
            raise InputValidationError("Модуль RSA слишком мал для кодирования символов множества Q.")

        cipher_blocks = [pow(value, key_pair.e, key_pair.n) for value in plain_values]
        encoded = format_length_prefixed_payload(len(plain_values), cipher_blocks)

        lines = [
            "Шифрование RSA:",
            "Кодирование символов:",
            "a→0, b→1, c→2, ..., z→25, пробел→26",
            f"Числовые эквиваленты сообщения Q: {plain_values}",
        ]
        for index, (plain, cipher) in enumerate(
            zip(plain_values, cipher_blocks, strict=True),
            start=1,
        ):
            lines.append(
                f"Блок {index}: c = m^e mod n = {plain}^{key_pair.e} mod {key_pair.n} = {cipher}"
            )
        return RSACipherPayload(
            blocks=cipher_blocks,
            block_lengths=[1] * len(cipher_blocks),
            block_size=1,
            encoded=encoded,
            steps="\n".join(lines),
        )

    def decrypt_text(self, payload: str, key_pair: RSAKeyPair) -> tuple[str, str]:
        """Расшифровывает строку RSA-шифртекста."""

        parsed = parse_length_prefixed_numbers(payload, "Шифртекст")
        plain_values = [pow(block, key_pair.d, key_pair.n) for block in parsed.values]
        trimmed_values = plain_values[: parsed.length]
        codec = AlphabetCodec(FIXED_INPUT_ALPHABET)
        text = codec.indices_to_text(trimmed_values)

        lines = [
            "Расшифрование RSA:",
            f"Принятые блоки шифртекста: {parsed.values}",
        ]
        for index, (cipher, plain) in enumerate(zip(parsed.values, plain_values, strict=True), start=1):
            lines.append(
                f"Блок {index}: m = c^d mod n = {cipher}^{key_pair.d} mod {key_pair.n} = {plain}"
            )
        lines.append(f"Восстановленные числовые эквиваленты Q: {trimmed_values}")
        lines.append(f"Восстановленный текст: {text}")
        return text, "\n".join(lines)

    @staticmethod
    def example_values() -> dict[str, str]:
        """Возвращает демонстрационные значения."""

        return {
            "p": "1009",
            "q": "1013",
            "e": "17",
            "text": "hello rsa",
        }
