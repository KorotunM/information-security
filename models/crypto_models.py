"""Dataclass-модели для криптографических сервисов."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RSAKeyPair:
    """Учебная пара ключей RSA."""

    p: int
    q: int
    n: int
    phi: int
    e: int
    d: int


@dataclass(slots=True)
class RSACipherPayload:
    """Шифртекст RSA с метаданными по длинам блоков."""

    blocks: list[int]
    block_lengths: list[int]
    block_size: int
    encoded: str
    steps: str = ""


@dataclass(slots=True)
class AdditiveKnapsackKeyPair:
    """Пара ключей для аддитивного рюкзака."""

    private_sequence: list[int]
    public_sequence: list[int]
    modulus: int
    multiplier: int
    inverse_multiplier: int
    coefficient_limit: int = 1


@dataclass(slots=True)
class MultiplicativeKnapsackKeyPair:
    """Пара ключей для мультипликативного рюкзака."""

    private_primes: list[int]
    public_logs: list[int]
    modulus: int
    generator: int
    coefficient_limit: int = 1
    discrete_log_table: dict[int, int] = field(default_factory=dict)


@dataclass(slots=True)
class KnapsackCipherPayload:
    """Шифртекст рюкзачной схемы с длиной исходной последовательности."""

    values: list[int]
    data_length: int
    block_size: int
    encoded: str
    steps: str = ""


@dataclass(slots=True)
class AlphabetEncodingResult:
    """Промежуточное представление алфавитного сообщения."""

    text: str
    alphabet: str
    base: int
    width: int
    indices: list[int]
    digits: list[int]


@dataclass(slots=True)
class HammingEncodingResult:
    """Результат кодирования кодом Хэмминга."""

    original_bits: str
    padded_bits: str
    codewords: list[str]
    encoded: str
    padding: int
    steps: str = ""


@dataclass(slots=True)
class HammingCorrectionResult:
    """Результат исправления кодового слова."""

    received_word: str
    syndrome: str
    error_position: int
    corrected_word: str
    decoded_bits: str
    steps: str = ""

