import unittest
import bookclub


class TestBookclub(unittest.TestCase):
    def test_status_str(self):
        # Check that correct numbers output string.
        self.assertEqual(type(bookclub.status_str("-1")), str)
        self.assertEqual(type(bookclub.status_str("0")), str)
        self.assertEqual(type(bookclub.status_str("25")), str)
        self.assertEqual(type(bookclub.status_str("50")), str)
        self.assertEqual(type(bookclub.status_str("75")), str)
        self.assertEqual(type(bookclub.status_str("100")), str)
        self.assertEqual(bookclub.status_str("99"), ":clock9:")
        self.assertEqual(bookclub.status_str("28"), ":clock3:")


if __name__ == "__main__":
    unittest.main()
