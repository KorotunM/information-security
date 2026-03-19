"""Учебная реализация RSA."""

from __future__ import annotations

from math import gcd
from random import Random

from models.crypto_models import RSAKeyPair, RSACipherPayload
from utils.number_theory import choose_coprime, generate_prime, is_probable_prime, mod_inverse
from utils.text_codec import (
    format_rsa_payload,
    parse_rsa_payload,
    rsa_blocks_to_text,
    text_to_rsa_blocks,
    validate_fixed_alphabet_text,
)
from utils.validation import InputValidationError


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
        """Шифрует текст блоками RSA."""

        normalized_text = validate_fixed_alphabet_text(text, "Открытый текст")

        block_data = text_to_rsa_blocks(normalized_text, key_pair.n)
        cipher_blocks = [pow(block, key_pair.e, key_pair.n) for block in block_data.integers]
        encoded = format_rsa_payload(block_data.lengths, cipher_blocks)

        lines = [
            "Шифрование RSA:",
            f"Размер блока по модулю n: {block_data.block_size} байт(а).",
            f"Блоки открытого текста: {block_data.integers}",
        ]
        for index, (plain, cipher) in enumerate(
            zip(block_data.integers, cipher_blocks, strict=True),
            start=1,
        ):
            lines.append(
                f"Блок {index}: c = m^e mod n = {plain}^{key_pair.e} mod {key_pair.n} = {cipher}"
            )
        return RSACipherPayload(
            blocks=cipher_blocks,
            block_lengths=block_data.lengths,
            block_size=block_data.block_size,
            encoded=encoded,
            steps="\n".join(lines),
        )

    def decrypt_text(self, payload: str, key_pair: RSAKeyPair) -> tuple[str, str]:
        """Расшифровывает строку RSA-шифртекста."""

        lengths, blocks = parse_rsa_payload(payload)
        plain_blocks = [pow(block, key_pair.d, key_pair.n) for block in blocks]
        text = rsa_blocks_to_text(plain_blocks, lengths)
        validate_fixed_alphabet_text(text, "Расшифрованный текст")

        lines = [
            "Расшифрование RSA:",
            f"Принятые блоки шифртекста: {blocks}",
        ]
        for index, (cipher, plain) in enumerate(zip(blocks, plain_blocks, strict=True), start=1):
            lines.append(
                f"Блок {index}: m = c^d mod n = {cipher}^{key_pair.d} mod {key_pair.n} = {plain}"
            )
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
