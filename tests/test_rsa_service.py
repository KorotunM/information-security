"""Тесты для RSA и числовых утилит."""

from __future__ import annotations

import unittest

from services.rsa_service import RSAService
from utils.number_theory import extended_gcd, mod_inverse


class NumberTheoryTests(unittest.TestCase):
    """Проверяет базовую арифметику."""

    def test_extended_gcd_returns_correct_gcd_and_coefficients(self) -> None:
        gcd_value, x, y = extended_gcd(240, 46)
        self.assertEqual(gcd_value, 2)
        self.assertEqual(240 * x + 46 * y, gcd_value)

    def test_mod_inverse(self) -> None:
        self.assertEqual(mod_inverse(17, 3120), 2753)


class RSAServiceTests(unittest.TestCase):
    """Проверяет генерацию, шифрование и дешифрование RSA."""

    def setUp(self) -> None:
        self.service = RSAService()
        self.key_pair, _ = self.service.generate_keys(61, 53, 17)

    def test_encrypt_decrypt_roundtrip(self) -> None:
        payload = self.service.encrypt_text("hi", self.key_pair)
        restored, _ = self.service.decrypt_text(payload.encoded, self.key_pair)
        self.assertEqual(restored, "hi")


if __name__ == "__main__":
    unittest.main()
