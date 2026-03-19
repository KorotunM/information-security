"""Тесты для Hamming [7,4]."""

from __future__ import annotations

import unittest

from services.hamming_service import HammingService


class HammingServiceTests(unittest.TestCase):
    """Проверяет кодирование, синдром и исправление."""

    def setUp(self) -> None:
        self.service = HammingService()

    def test_encode_block(self) -> None:
        self.assertEqual(self.service.encode_block("1011"), "0110011")

    def test_syndrome_detects_single_error(self) -> None:
        syndrome, position = self.service.analyze_word("0100011")
        self.assertEqual(syndrome, "011")
        self.assertEqual(position, 3)

    def test_correct_payload_restores_information_bits(self) -> None:
        encoded = self.service.encode_message("10110011")
        corrupted, _ = self.service.introduce_error(encoded.encoded, 1, 3)
        corrected, _ = self.service.decode_payload(corrupted)
        self.assertEqual(self.service.decode_to_information_bits(corrected), "10110011")


if __name__ == "__main__":
    unittest.main()
