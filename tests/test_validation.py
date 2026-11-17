import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fleetbook import validation as v  # noqa: E402


class ValidationTests(unittest.TestCase):
    def test_valid_phone(self):
        self.assertEqual(v.validate_phone("9876543210"), "9876543210")

    def test_invalid_phone_rejected(self):
        for bad in ["12345", "5876543210", "98765432101", "abcdefghij", ""]:
            with self.assertRaises(v.ValidationError):
                v.validate_phone(bad)

    def test_registration_number_normalised(self):
        self.assertEqual(v.validate_registration_no("tn 01 ab 1234"), "TN01AB1234")

    def test_invalid_registration_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_registration_no("1234TN")

    def test_name_rules(self):
        self.assertEqual(v.validate_name("  Sharmila Mai "), "Sharmila Mai")
        with self.assertRaises(v.ValidationError):
            v.validate_name("A")
        with self.assertRaises(v.ValidationError):
            v.validate_name("R2D2")

    def test_past_date_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_date("2001-01-01")
        self.assertEqual(v.validate_date("2001-01-01", allow_past=True), "2001-01-01")

    def test_bad_date_format_rejected(self):
        with self.assertRaises(v.ValidationError):
            v.validate_date("20-12-2030")

    def test_time_format(self):
        self.assertEqual(v.validate_time("9:05"), "09:05")
        with self.assertRaises(v.ValidationError):
            v.validate_time("25:00")

    def test_vehicle_type(self):
        self.assertEqual(v.validate_vehicle_type("BUS"), "bus")
        with self.assertRaises(v.ValidationError):
            v.validate_vehicle_type("plane")

    def test_positive_numbers(self):
        self.assertEqual(v.validate_positive_int("3", "Seats"), 3)
        with self.assertRaises(v.ValidationError):
            v.validate_positive_int("0", "Seats")
        with self.assertRaises(v.ValidationError):
            v.validate_positive_float("-1", "Price")


if __name__ == "__main__":
    unittest.main()
