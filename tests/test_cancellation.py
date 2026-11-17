import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fleetbook.system import BookingError, NotFoundError  # noqa: E402
from tests.test_system import FUTURE, SystemTestCase  # noqa: E402

DEPARTURE = datetime(2099, 1, 15, 21, 0)


class CancellationTests(SystemTestCase):
    def setUp(self):
        super().setUp()
        # 450 km * Rs.2 * 4 seats = Rs.3600
        self.booking = self.system.book_seats(self.trip.id, "Sharmila Mai", "9876543210", 4)

    def test_cancel_three_days_before_gives_90_percent(self):
        result = self.system.cancel_booking(self.booking.id, now=datetime(2099, 1, 12, 9, 0))
        self.assertEqual(result.status, "CANCELLED")
        self.assertEqual(result.refund, 3240.0)

    def test_cancel_between_24_and_48_hours_gives_50_percent(self):
        result = self.system.cancel_booking(self.booking.id, now=datetime(2099, 1, 14, 0, 0))
        self.assertEqual(result.refund, 1800.0)

    def test_cancel_within_24_hours_gives_no_refund(self):
        result = self.system.cancel_booking(self.booking.id, now=datetime(2099, 1, 15, 10, 0))
        self.assertEqual(result.refund, 0.0)

    def test_cancel_after_departure_rejected(self):
        with self.assertRaises(BookingError):
            self.system.cancel_booking(self.booking.id, now=datetime(2099, 1, 16, 0, 0))

    def test_double_cancel_rejected(self):
        self.system.cancel_booking(self.booking.id, now=datetime(2099, 1, 1))
        with self.assertRaises(BookingError):
            self.system.cancel_booking(self.booking.id, now=datetime(2099, 1, 1))

    def test_cancel_frees_seats(self):
        self.assertEqual(self.system.seats_available(self.trip.id), 6)
        self.system.cancel_booking(self.booking.id, now=datetime(2099, 1, 1))
        self.assertEqual(self.system.seats_available(self.trip.id), 10)

    def test_cancel_unknown_booking(self):
        with self.assertRaises(NotFoundError):
            self.system.cancel_booking(999)


if __name__ == "__main__":
    unittest.main()
