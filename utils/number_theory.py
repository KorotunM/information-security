"""Числовые утилиты для учебной криптографии."""

from __future__ import annotations

from math import gcd, isqrt
from random import Random

from utils.validation import InputValidationError


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Расширенный алгоритм Евклида."""

    if b == 0:
        return abs(a), 1 if a >= 0 else -1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    return g, x, y


def mod_inverse(value: int, modulus: int) -> int:
    """Вычисляет обратный элемент по модулю."""

    g, x, _ = extended_gcd(value, modulus)
    if g != 1:
        raise InputValidationError(
            f"Число {value} не имеет обратного по модулю {modulus}."
        )
    return x % modulus


def is_probable_prime(number: int) -> bool:
    """Детерминированный Miller-Rabin для чисел до 64 бит."""

    if number < 2:
        return False
    small_primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)
    for prime in small_primes:
        if number == prime:
            return True
        if number % prime == 0:
            return False

    d = number - 1
    s = 0
    while d % 2 == 0:
        s += 1
        d //= 2

    for base in (2, 325, 9375, 28178, 450775, 9780504, 1795265022):
        if base % number == 0:
            continue
        x = pow(base, d, number)
        if x in (1, number - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, number)
            if x == number - 1:
                break
        else:
            return False
    return True


def next_prime(number: int) -> int:
    """Возвращает ближайшее простое число не меньше заданного."""

    candidate = max(2, number)
    if candidate == 2:
        return 2
    if candidate % 2 == 0:
        candidate += 1
    while not is_probable_prime(candidate):
        candidate += 2
    return candidate


def generate_prime(bit_length: int, rng: Random | None = None) -> int:
    """Генерирует учебное простое число указанной битовой длины."""

    if bit_length < 4:
        raise InputValidationError("Битовая длина простого числа должна быть не меньше 4.")

    random = rng or Random()
    while True:
        candidate = random.getrandbits(bit_length)
        candidate |= 1
        candidate |= 1 << (bit_length - 1)
        if is_probable_prime(candidate):
            return candidate


def choose_coprime(modulus: int, start: int = 3) -> int:
    """Подбирает небольшое число, взаимно простое с модулем."""

    candidate = max(2, start)
    if candidate % 2 == 0:
        candidate += 1
    while gcd(candidate, modulus) != 1:
        candidate += 2
    return candidate


def prime_factors(number: int) -> list[int]:
    """Возвращает список простых множителей без повторений."""

    n = number
    factors: list[int] = []
    divisor = 2
    while divisor * divisor <= n:
        if n % divisor == 0:
            factors.append(divisor)
            while n % divisor == 0:
                n //= divisor
        divisor = 3 if divisor == 2 else divisor + 2
    if n > 1:
        factors.append(n)
    return factors


def primitive_root(modulus: int) -> int:
    """Находит первообразный корень по простому модулю."""

    if modulus <= 2 or not is_probable_prime(modulus):
        raise InputValidationError("Первообразный корень ищется только для простого модуля > 2.")

    phi = modulus - 1
    factors = prime_factors(phi)
    for candidate in range(2, modulus):
        if all(pow(candidate, phi // factor, modulus) != 1 for factor in factors):
            return candidate
    raise InputValidationError("Не удалось найти первообразный корень.")


def discrete_log_table(generator: int, modulus: int) -> dict[int, int]:
    """Строит полную таблицу дискретных логарифмов для малого простого модуля."""

    table: dict[int, int] = {}
    value = 1
    for exponent in range(modulus - 1):
        table.setdefault(value, exponent)
        value = (value * generator) % modulus
    if len(table) != modulus - 1:
        raise InputValidationError(
            "Не удалось построить полную таблицу дискретных логарифмов: генератор не подходит."
        )
    return table


def first_primes(count: int) -> list[int]:
    """Возвращает первые `count` простых чисел."""

    if count < 1:
        raise InputValidationError("Количество простых чисел должно быть положительным.")

    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if is_probable_prime(candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def generalized_superincreasing_sequence(
    length: int,
    coefficient_limit: int,
    start: int = 2,
) -> list[int]:
    """Генерирует обобщённую сверхвозрастающую последовательность."""

    if length < 2:
        raise InputValidationError("Длина последовательности должна быть не меньше 2.")
    if coefficient_limit < 1:
        raise InputValidationError("Ограничение коэффициентов должно быть положительным.")

    sequence: list[int] = []
    total = 0
    current = max(2, start)
    for index in range(length):
        if index == 0:
            value = current
        else:
            value = coefficient_limit * total + index + 2
        sequence.append(value)
        total += value
        current += 1
    return sequence


def factor_with_bound(value: int, bases: list[int], max_power: int) -> list[int]:
    """Восстанавливает показатели степеней по набору попарно взаимно простых оснований."""

    if value < 1:
        raise InputValidationError("Факторизуемое значение должно быть положительным.")

    exponents: list[int] = []
    current = value
    for base in bases:
        exponent = 0
        while current % base == 0 and exponent < max_power:
            current //= base
            exponent += 1
        exponents.append(exponent)

    if current != 1:
        raise InputValidationError(
            "Не удалось полностью разложить значение по приватным основаниям."
        )
    return exponents


def trial_division(number: int) -> list[tuple[int, int]]:
    """Возвращает разложение числа на простые множители с кратностями."""

    if number < 2:
        return []

    factors: list[tuple[int, int]] = []
    n = number
    divisor = 2
    while divisor <= isqrt(n):
        power = 0
        while n % divisor == 0:
            n //= divisor
            power += 1
        if power:
            factors.append((divisor, power))
        divisor = 3 if divisor == 2 else divisor + 2
    if n > 1:
        factors.append((n, 1))
    return factors

