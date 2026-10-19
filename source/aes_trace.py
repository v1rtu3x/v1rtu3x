"""AES-128 values for the banner. Educational visualization, not a crypto library.

State is a flat 16-byte sequence in the column-major order of FIPS 197.
No user data is encrypted by this module. Only a public known-answer vector
is used to draw the first forward round.
"""
from __future__ import annotations

PLAINTEXT = bytes.fromhex('00112233445566778899aabbccddeeff')
KEY = bytes.fromhex('000102030405060708090a0b0c0d0e0f')
CIPHERTEXT = bytes.fromhex('69c4e0d86a7b0430d8cdb78070b4c55a')


def gf_mul(a: int, b: int) -> int:
    out = 0
    for _ in range(8):
        if b & 1:
            out ^= a
        a = ((a << 1) ^ (0x11B if a & 0x80 else 0)) & 0xFF
        b >>= 1
    return out


def gf_pow(a: int, n: int) -> int:
    out = 1
    while n:
        if n & 1:
            out = gf_mul(out, a)
        a = gf_mul(a, a)
        n >>= 1
    return out


def _rot(x: int, n: int) -> int:
    return ((x << n) | (x >> (8 - n))) & 255


def _sub(x: int) -> int:
    inv = gf_pow(x, 254) if x else 0
    return inv ^ _rot(inv, 1) ^ _rot(inv, 2) ^ _rot(inv, 3) ^ _rot(inv, 4) ^ 0x63


SBOX = tuple(_sub(x) for x in range(256))


def sub_bytes(state: bytes) -> bytes:
    return bytes(SBOX[x] for x in state)


def shift_rows(state: bytes) -> bytes:
    return bytes(state[4 * ((c + r) % 4) + r] for c in range(4) for r in range(4))


def mix_columns(state: bytes) -> bytes:
    out = bytearray(16)
    mat = ((2, 3, 1, 1), (1, 2, 3, 1), (1, 1, 2, 3), (3, 1, 1, 2))
    for c in range(4):
        for r in range(4):
            out[4*c+r] = (gf_mul(mat[r][0], state[4*c]) ^
                          gf_mul(mat[r][1], state[4*c+1]) ^
                          gf_mul(mat[r][2], state[4*c+2]) ^
                          gf_mul(mat[r][3], state[4*c+3]))
    return bytes(out)


def add_round_key(state: bytes, key: bytes) -> bytes:
    if len(state) != 16 or len(key) != 16:
        raise ValueError('AES state and round key must each be 16 bytes')
    return bytes(a ^ b for a, b in zip(state, key))


def expand_key(key: bytes) -> list[bytes]:
    if len(key) != 16:
        raise ValueError('Only AES-128 is supported in this illustration')
    words = [list(key[n:n+4]) for n in range(0, 16, 4)]
    rc = 1
    for i in range(4, 44):
        temp = words[-1][:]
        if i % 4 == 0:
            temp = [SBOX[v] for v in (temp[1:] + temp[:1])]
            temp[0] ^= rc
            rc = gf_mul(rc, 2)
        words.append([a ^ b for a, b in zip(words[i-4], temp)])
    return [bytes(v for word in words[j:j+4] for v in word) for j in range(0, 44, 4)]


def encrypt_example(block: bytes, key: bytes) -> bytes:
    """Reference calculation for tests only; not intended for production use."""
    keys = expand_key(key)
    state = add_round_key(block, keys[0])
    for rnd in range(1, 11):
        state = shift_rows(sub_bytes(state))
        if rnd < 10:
            state = mix_columns(state)
        state = add_round_key(state, keys[rnd])
    return state


def first_round() -> dict[str, bytes]:
    keys = expand_key(KEY)
    start = add_round_key(PLAINTEXT, keys[0])
    sb = sub_bytes(start)
    sr = shift_rows(sb)
    mc = mix_columns(sr)
    return dict(start=start, sub=sb, shift=sr, mix=mc, key=keys[1],
                out=add_round_key(mc, keys[1]))
