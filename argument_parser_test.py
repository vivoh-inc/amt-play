import unittest
from argparser import process_amt_url

class TestAmtArgParser(unittest.TestCase):

    legacy = "amt://162.250.138.201@232.162.250.138:1234"
    relay = "162.250.137.254"
    parameterized = "amt://232.162.250.138:1234?relay=162.250.137.254&timeout=2&source=162.250.138.201"

    def test_legacy(self):
        r, m, s, t = process_amt_url(self.legacy, self.relay)
        self.assertEqual(r, "162.250.137.254")
        self.assertEqual(m, "232.162.250.138:1234")
        self.assertEqual(s, "162.250.138.201")
        self.assertEqual(t, 1000)

    def test_paramterized(self):
        r, m, s, t = process_amt_url(self.parameterized)
        self.assertEqual(r, "162.250.137.254")
        self.assertEqual(m, "232.162.250.138:1234")
        self.assertEqual(s, "162.250.138.201")
        self.assertEqual(t, '2')

if __name__ == '__main__':
    unittest.main()