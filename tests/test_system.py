import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fleetbook.storage import JsonStore, StorageError  # noqa: E402
from fleetbook.system import BookingError, FleetBookingSystem, NotFoundError  # noqa: E402
from fleetbook.validation import ValidationError  # noqa: E402

FUTURE = "2099-01-15"


class SystemTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "db.json")
        self.system = FleetBookingSystem(JsonStore(self.path))
        self.bus = self.system.add_vehicle("bus", "TN01AB1234", 10, 2.0)
        self.route = self.system.add_route("Chennai", "Madurai", 450)
        self.trip = self.system.schedule_trip(self.route.id, self.bus.id, FUTURE, "21:00")

    def tearDown(self):
        self.tmp.cleanup()


class FleetAndTripTests(SystemTestCase):
    def test_duplicate_registration_rejected(self):
        with self.assertRaises(ValidationError):
            self.system.add_vehicle("car", "TN01AB1234", 4, 3.0)

    def test_same_source_destination_rejected(self):
        with self.assertRaises(ValidationError):
            self.system.add_route("Chennai", "chennai", 10)

    def test_vehicle_double_booked_on_same_date_rejected(self):
        with self.assertRaises(BookingError):
            self.system.schedule_trip(self.route.id, self.bus.id, FUTURE, "06:00")

    def test_unknown_route_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.system.schedule_trip(99, self.bus.id, FUTURE, "06:00")

    def test_search_trips(self):
        found = self.system.search_trips("chennai", "madurai", FUTURE)
        self.assertEqual([t.id for t in found], [self.trip.id])
        self.assertEqual(self.system.search_trips("Chennai", "Salem"), [])

    def test_data_persists_between_sessions(self):
        reloaded = FleetBookingSystem(JsonStore(self.path))
        self.assertEqual(len(reloaded.list_vehicles()), 1)
        self.assertEqual(len(reloaded.list_trips()), 1)

    def test_corrupted_data_file_reported(self):
        with open(self.path, "w") as handle:
            handle.write("{not valid json")
        with self.assertRaises(StorageError):
            FleetBookingSystem(JsonStore(self.path))


class BookingTests(SystemTestCase):
    def test_fare_calculation(self):
        # 450 km * Rs.2 * 3 seats
        self.assertEqual(self.system.calculate_fare(self.trip.id, 3), 2700.0)

    def test_full_vehicle_gets_discount(self):
        # 450 * 2 * 10 seats = 9000, minus 10% = 8100
        self.assertEqual(self.system.calculate_fare(self.trip.id, 10), 8100.0)

    def test_booking_reduces_availability(self):
        self.system.book_seats(self.trip.id, "Sharmila Mai", "9876543210", 4)
        self.assertEqual(self.system.seats_available(self.trip.id), 6)

    def test_overbooking_rejected(self):
        self.system.book_seats(self.trip.id, "Sharmila Mai", "9876543210", 8)
        with self.assertRaises(BookingError):
            self.system.book_seats(self.trip.id, "Arun Kumar", "9123456780", 3)

    def test_invalid_customer_data_rejected(self):
        with self.assertRaises(ValidationError):
            self.system.book_seats(self.trip.id, "Arun", "12345", 1)
        with self.assertRaises(ValidationError):
            self.system.book_seats(self.trip.id, "Arun", "9123456780", 0)

    def test_booking_unknown_trip(self):
        with self.assertRaises(NotFoundError):
            self.system.book_seats(42, "Arun Kumar", "9123456780", 1)


if __name__ == "__main__":
    unittest.main()
