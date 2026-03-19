"""Сервис кода Хэмминга [7,4]."""

from __future__ import annotations

from models.crypto_models import HammingCorrectionResult, HammingEncodingResult
from utils.validation import InputValidationError, validate_binary_string


class HammingService:
    """Учебная реализация кода Хэмминга [7,4] с синдромным декодированием."""

    def encode_message(self, bits: str) -> HammingEncodingResult:
        """Кодирует бинарную строку блоками по 4 бита."""

        clean_bits = validate_binary_string(bits, "Информационное сообщение")
        padding = (-len(clean_bits)) % 4
        padded_bits = clean_bits + ("0" * padding)
        codewords: list[str] = []
        lines = [
            "Кодирование кодом Хэмминга [7,4]:",
            f"Исходные биты: {clean_bits}",
            f"Добавлено дополняющих нулей: {padding}",
        ]

        for block_index in range(0, len(padded_bits), 4):
            data_block = padded_bits[block_index : block_index + 4]
            codeword = self.encode_block(data_block)
            codewords.append(codeword)
            lines.append(
                f"Блок {block_index // 4 + 1}: {data_block} -> {codeword}"
            )

        encoded = self.format_payload(len(clean_bits), codewords)
        return HammingEncodingResult(
            original_bits=clean_bits,
            padded_bits=padded_bits,
            codewords=codewords,
            encoded=encoded,
            padding=padding,
            steps="\n".join(lines),
        )

    def encode_block(self, data_bits: str) -> str:
        """Кодирует один 4-битный блок."""

        if len(data_bits) != 4 or any(bit not in "01" for bit in data_bits):
            raise InputValidationError("Для Hamming [7,4] нужен блок из 4 бит.")
        d1, d2, d3, d4 = [int(bit) for bit in data_bits]
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p4 = d2 ^ d3 ^ d4
        return f"{p1}{p2}{d1}{p4}{d2}{d3}{d4}"

    def introduce_error(self, payload: str, block_index: int, position: int) -> tuple[str, str]:
        """Вносит одну ошибку в выбранный блок и позицию."""

        original_length, codewords = self.parse_payload(payload)
        if not 1 <= block_index <= len(codewords):
            raise InputValidationError("Номер блока для ошибки выходит за допустимые пределы.")
        if not 1 <= position <= 7:
            raise InputValidationError("Позиция ошибки должна быть в диапазоне 1..7.")

        target = list(codewords[block_index - 1])
        target[position - 1] = "0" if target[position - 1] == "1" else "1"
        codewords[block_index - 1] = "".join(target)
        corrupted = self.format_payload(original_length, codewords)
        steps = (
            f"В блоке {block_index} инвертирован бит {position}. "
            f"Получено искажённое кодовое слово: {codewords[block_index - 1]}"
        )
        return corrupted, steps

    def analyze_word(self, word: str) -> tuple[str, int]:
        """Вычисляет синдром и позицию ошибки для одного кодового слова."""

        if len(word) != 7 or any(bit not in "01" for bit in word):
            raise InputValidationError("Кодовое слово должно состоять из 7 бит.")
        bits = [int(bit) for bit in word]
        s1 = bits[0] ^ bits[2] ^ bits[4] ^ bits[6]
        s2 = bits[1] ^ bits[2] ^ bits[5] ^ bits[6]
        s4 = bits[3] ^ bits[4] ^ bits[5] ^ bits[6]
        syndrome = f"{s4}{s2}{s1}"
        position = int(syndrome, 2)
        return syndrome, position

    def correct_word(self, word: str) -> HammingCorrectionResult:
        """Исправляет одно 7-битное кодовое слово."""

        syndrome, position = self.analyze_word(word)
        corrected = list(word)
        if position:
            index = position - 1
            corrected[index] = "0" if corrected[index] == "1" else "1"
        corrected_word = "".join(corrected)
        decoded = self.decode_word(corrected_word)
        lines = [
            f"Принятое слово: {word}",
            f"Синдром: {syndrome}",
            f"Позиция ошибки: {position if position else 'ошибка не обнаружена'}",
            f"Исправленное слово: {corrected_word}",
            f"Извлечённые информационные биты: {decoded}",
        ]
        return HammingCorrectionResult(
            received_word=word,
            syndrome=syndrome,
            error_position=position,
            corrected_word=corrected_word,
            decoded_bits=decoded,
            steps="\n".join(lines),
        )

    def decode_payload(self, payload: str) -> tuple[str, str]:
        """Исправляет все кодовые слова полезной нагрузки и восстанавливает исходное сообщение."""

        original_length, codewords = self.parse_payload(payload)
        corrected_words: list[str] = []
        decoded_bits = ""
        lines = [
            "Синдромное декодирование Hamming [7,4]:",
        ]

        for index, word in enumerate(codewords, start=1):
            result = self.correct_word(word)
            corrected_words.append(result.corrected_word)
            decoded_bits += result.decoded_bits
            lines.append(f"Блок {index}:\n{result.steps}")

        trimmed = decoded_bits[:original_length]
        corrected_payload = self.format_payload(original_length, corrected_words)
        lines.append(f"После удаления дополнения: {trimmed}")
        lines.append(f"Исправленная полезная нагрузка: {corrected_payload}")
        return corrected_payload, "\n".join(lines)

    def decode_word(self, word: str) -> str:
        """Извлекает информационные биты из корректного 7-битного слова."""

        return f"{word[2]}{word[4]}{word[5]}{word[6]}"

    def decode_to_information_bits(self, payload: str) -> str:
        """Возвращает исходные информационные биты без этапа исправления."""

        original_length, codewords = self.parse_payload(payload)
        bits = "".join(self.decode_word(word) for word in codewords)
        return bits[:original_length]

    def parity_count_for_data(self, data_length: int) -> int:
        """Вычисляет минимальное число проверочных битов."""

        r = 0
        while 2**r < data_length + r + 1:
            r += 1
        return r

    @staticmethod
    def format_payload(original_length: int, codewords: list[str]) -> str:
        """Форматирует кодовые слова как `length|w1 w2 ...`."""

        return f"{original_length}|{' '.join(codewords)}"

    @staticmethod
    def parse_payload(payload: str) -> tuple[int, list[str]]:
        """Разбирает строковое представление кодовых слов."""

        if "|" not in payload:
            raise InputValidationError("Кодовое слово должно быть в формате `длина|слова`.")
        length_part, words_part = payload.split("|", maxsplit=1)
        try:
            original_length = int(length_part.strip())
        except ValueError as error:
            raise InputValidationError("Длина исходного сообщения должна быть целым числом.") from error
        words = words_part.split()
        if not words:
            raise InputValidationError("Не найдено ни одного кодового слова.")
        for word in words:
            if len(word) != 7 or any(bit not in "01" for bit in word):
                raise InputValidationError("Каждое кодовое слово должно состоять из 7 бит.")
        return original_length, words

    @staticmethod
    def example_bits() -> str:
        """Возвращает демонстрационное сообщение."""

        return "10110011"
