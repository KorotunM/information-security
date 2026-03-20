"""Тесты для рюкзачных схем."""

from __future__ import annotations

import unittest

from services.additive_knapsack_service import AdditiveKnapsackService
from services.generalized_additive_knapsack_service import GeneralizedAdditiveKnapsackService
from services.generalized_multiplicative_knapsack_service import GeneralizedMultiplicativeKnapsackService
from services.multiplicative_knapsack_service import MultiplicativeKnapsackService
from utils.text_codec import FIXED_INPUT_ALPHABET


class KnapsackServiceTests(unittest.TestCase):
    """Проверяет учебные примеры шифрования/дешифрования."""

    def setUp(self) -> None:
        self.additive = AdditiveKnapsackService()
        self.multiplicative = MultiplicativeKnapsackService()
        self.generalized_additive = GeneralizedAdditiveKnapsackService()
        self.generalized_multiplicative = GeneralizedMultiplicativeKnapsackService()
        self.alphabet = FIXED_INPUT_ALPHABET

    def test_classical_additive_roundtrip(self) -> None:
        key_pair, _ = self.additive.generate_keys(
            length=8,
            private_sequence=[2, 3, 7, 14, 30, 57, 120, 251],
            modulus=491,
            multiplier=41,
        )
        payload, _ = self.additive.encrypt_message("hello", key_pair)
        restored, _ = self.additive.decrypt_message(payload.encoded, key_pair)
        self.assertEqual(restored, "hello")

    def test_classical_additive_uses_q_to_binary_encoding(self) -> None:
        key_pair, _ = self.additive.generate_keys(
            length=8,
            private_sequence=[2, 3, 7, 14, 30, 57, 120, 251],
            modulus=491,
            multiplier=41,
        )
        payload, steps = self.additive.encrypt_message("hi", key_pair)
        self.assertTrue(payload.encoded.startswith("10|"))
        self.assertIn("Числовые эквиваленты Q: [7, 8]", steps)

    def test_classical_multiplicative_roundtrip(self) -> None:
        key_pair, _ = self.multiplicative.generate_keys(
            length=6,
            private_primes=[2, 3, 5, 7, 11, 13],
        )
        payload, _ = self.multiplicative.encrypt_message("code", key_pair)
        restored, _ = self.multiplicative.decrypt_message(payload.encoded, key_pair)
        self.assertEqual(restored, "code")

    def test_classical_multiplicative_uses_q_to_binary_encoding(self) -> None:
        key_pair, _ = self.multiplicative.generate_keys(
            length=6,
            private_primes=[2, 3, 5, 7, 11, 13],
        )
        payload, steps = self.multiplicative.encrypt_message("hi", key_pair)
        self.assertTrue(payload.encoded.startswith("10|"))
        self.assertIn("Числовые эквиваленты Q: [7, 8]", steps)

    def test_generalized_additive_roundtrip(self) -> None:
        key_pair, _ = self.generalized_additive.generate_keys(
            length=4,
            base=3,
            private_sequence=[2, 5, 16, 50],
            modulus=149,
            multiplier=31,
        )
        payload, _, _ = self.generalized_additive.encrypt_text(
            "hi",
            key_pair,
            alphabet=self.alphabet,
            base=3,
        )
        restored, _ = self.generalized_additive.decrypt_text(payload, key_pair, self.alphabet, base=3)
        self.assertEqual(restored, "hi")
        self.assertEqual(payload, "8|158 218")

    def test_generalized_multiplicative_roundtrip(self) -> None:
        key_pair, _ = self.generalized_multiplicative.generate_keys(
            length=3,
            base=3,
            private_primes=[2, 3, 5],
            modulus=1009,
            secret_exponent=5,
        )
        payload, steps, _ = self.generalized_multiplicative.encrypt_text(
            "hi",
            key_pair,
            alphabet=self.alphabet,
            base=3,
        )
        restored, _ = self.generalized_multiplicative.decrypt_text(payload, key_pair, self.alphabet, base=3)
        self.assertEqual(restored, "hi")
        self.assertEqual(payload, "6|934 16")
        self.assertIn("Открытый рюкзак B = [328, 738, 659]", steps)


if __name__ == "__main__":
    unittest.main()
