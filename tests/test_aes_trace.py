"""Known-answer and intermediate-state tests for the illustration."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from aes_trace import (SBOX, first_round, expand_key, shift_rows,
                       gf_mul, encrypt_example, PLAINTEXT, KEY, CIPHERTEXT)


class AESTraceTests(unittest.TestCase):
    def test_sbox(self):
        self.assertEqual(SBOX[0], 0x63)
        self.assertEqual(SBOX[0x53], 0xED)
        self.assertEqual(len(set(SBOX)), 256)

    def test_gf_multiplication(self):
        self.assertEqual(gf_mul(0x57, 0x13), 0xFE)

    def test_initial_add_round_key(self):
        self.assertEqual(first_round()['start'].hex(), '00102030405060708090a0b0c0d0e0f0')

    def test_sub_bytes(self):
        self.assertEqual(first_round()['sub'].hex(), '63cab7040953d051cd60e0e7ba70e18c')

    def test_shift_rows(self):
        self.assertEqual(first_round()['shift'].hex(), '6353e08c0960e104cd70b751bacad0e7')

    def test_mix_columns(self):
        self.assertEqual(first_round()['mix'].hex(), '5f72641557f5bc92f7be3b291db9f91a')

    def test_first_round_key(self):
        self.assertEqual(expand_key(KEY)[1].hex(), 'd6aa74fdd2af72fadaa678f1d6ab76fe')

    def test_first_round_output(self):
        self.assertEqual(first_round()['out'].hex(), '89d810e8855ace682d1843d8cb128fe4')

    def test_full_known_answer(self):
        self.assertEqual(encrypt_example(PLAINTEXT, KEY), CIPHERTEXT)

    def test_shift_rows_is_permutation(self):
        original=bytes(range(16))
        a=original
        for _ in range(4):
            a=shift_rows(a)
        self.assertEqual(a, original)

    def test_invalid_key_length(self):
        with self.assertRaises(ValueError):
            expand_key(b'bad-key')


if __name__=='__main__':
    unittest.main()
