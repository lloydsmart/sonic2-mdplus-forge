from __future__ import annotations

import unittest

from tools.mdplus_builder.driver import saxman_decode


class DriverLoaderTests(unittest.TestCase):
    def test_final_literal_is_processed(self):
        self.assertEqual(saxman_decode(b'\x01\xc9'), b'\xc9')
        self.assertEqual(saxman_decode(b'\x01\xc9', stock_loader=True), b'')

    def test_final_backreference_can_drop_the_entire_ack_and_return(self):
        # Synthetic code, no game data: four literals, then a four-byte match.
        code = bytes.fromhex('32881bc9')
        packed = b'\x0f' + code + bytes.fromhex('eef1')
        self.assertEqual(saxman_decode(packed), code * 2)
        self.assertEqual(saxman_decode(packed, stock_loader=True), code)

    def test_zero_fill_does_not_become_a_reference_when_it_crosses_zero(self):
        self.assertEqual(saxman_decode(bytes.fromhex('0141edf0')), b'A' + bytes(3))


if __name__ == '__main__':
    unittest.main()
