"""Core business logic: fleet, routes, trip scheduling and seat booking."""

from datetime import datetime
from typing import List, Optional

from .models import Booking, Route, Trip, Vehicle
from .storage import JsonStore
from .validation import (
    ValidationError,
    validate_city,
    validate_date,
    validate_name,
    validate_phone,
    validate_positive_float,
    validate_positive_int,
    validate_registration_no,
    validate_time,
    validate_vehicle_type,
)

FULL_VEHICLE_DISCOUNT = 0.10   # 10% off when a whole vehicle is hired

# Refund policy: (minimum hours before departure, refund fraction)
REFUND_POLICY = ((48, 0.90), (24, 0.50), (0, 0.0))


class NotFoundError(LookupError):
    """Raised when an id does not exist."""


class BookingError(RuntimeError):
    """Raised when a booking rule is violated (e.g. not enough seats)."""


class FleetBookingSystem:
    def __init__(self, store: JsonStore):
        self.store = store
        self.db = store.load()

    # ---------- helpers ----------
    def _next_id(self, kind: str) -> int:
        self.db["counters"][kind] += 1
        return self.db["counters"][kind]

    def _save(self) -> None:
        self.store.save(self.db)

    # ---------- fleet ----------
    def add_vehicle(self, vehicle_type, registration_no, capacity, price_per_km_per_seat) -> Vehicle:
        vehicle_type = validate_vehicle_type(vehicle_type)
        registration_no = validate_registration_no(registration_no)
        capacity = validate_positive_int(capacity, "Capacity", maximum=60)
        price = validate_positive_float(price_per_km_per_seat, "Price per km per seat")
        if any(v["registration_no"] == registration_no for v in self.db["vehicles"]):
            raise ValidationError(f"Vehicle {registration_no} is already registered.")
        vehicle = Vehicle(self._next_id("vehicles"), vehicle_type, registration_no, capacity, price)
        self.db["vehicles"].append(vehicle.to_dict())
        self._save()
        return vehicle

    def list_vehicles(self) -> List[Vehicle]:
        return [Vehicle.from_dict(v) for v in self.db["vehicles"]]

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        for item in self.db["vehicles"]:
            if item["id"] == vehicle_id:
                return Vehicle.from_dict(item)
        raise NotFoundError(f"Vehicle {vehicle_id} not found.")

    # ---------- routes ----------
    def add_route(self, source, destination, distance_km) -> Route:
        source = validate_city(source, "Source")
        destination = validate_city(destination, "Destination")
        if source == destination:
            raise ValidationError("Source and destination must be different.")
        distance = validate_positive_float(distance_km, "Distance")
        route = Route(self._next_id("routes"), source, destination, distance)
        self.db["routes"].append(route.to_dict())
        self._save()
        return route

    def list_routes(self) -> List[Route]:
        return [Route.from_dict(r) for r in self.db["routes"]]

    def get_route(self, route_id: int) -> Route:
        for item in self.db["routes"]:
            if item["id"] == route_id:
                return Route.from_dict(item)
        raise NotFoundError(f"Route {route_id} not found.")

    # ---------- trips ----------
    def schedule_trip(self, route_id, vehicle_id, date, departure_time, allow_past=False) -> Trip:
        route = self.get_route(int(route_id))
        vehicle = self.get_vehicle(int(vehicle_id))
        date = validate_date(date, allow_past=allow_past)
        departure_time = validate_time(departure_time)
        for existing in self.db["trips"]:
            if existing["vehicle_id"] == vehicle.id and existing["date"] == date:
                raise BookingError(
                    f"Vehicle {vehicle.registration_no} is already scheduled on {date}."
                )
        trip = Trip(self._next_id("trips"), route.id, vehicle.id, date, departure_time)
        self.db["trips"].append(trip.to_dict())
        self._save()
        return trip

    def list_trips(self) -> List[Trip]:
        return [Trip.from_dict(t) for t in self.db["trips"]]

    def get_trip(self, trip_id: int) -> Trip:
        for item in self.db["trips"]:
            if item["id"] == trip_id:
                return Trip.from_dict(item)
        raise NotFoundError(f"Trip {trip_id} not found.")

    def search_trips(self, source: str, destination: str, date: Optional[str] = None) -> List[Trip]:
        source = validate_city(source, "Source")
        destination = validate_city(destination, "Destination")
        matches = []
        for trip in self.list_trips():
            route = self.get_route(trip.route_id)
            if route.source == source and route.destination == destination:
                if date is None or trip.date == date:
                    matches.append(trip)
        return sorted(matches, key=lambda t: (t.date, t.departure_time))

    # ---------- bookings ----------
    def seats_booked(self, trip_id: int) -> int:
        return sum(
            b["seats"] for b in self.db["bookings"]
            if b["trip_id"] == trip_id and b["status"] == "CONFIRMED"
        )

    def seats_available(self, trip_id: int) -> int:
        trip = self.get_trip(trip_id)
        vehicle = self.get_vehicle(trip.vehicle_id)
        return vehicle.capacity - self.seats_booked(trip_id)

    def calculate_fare(self, trip_id: int, seats: int) -> float:
        trip = self.get_trip(trip_id)
        route = self.get_route(trip.route_id)
        vehicle = self.get_vehicle(trip.vehicle_id)
        fare = route.distance_km * vehicle.price_per_km_per_seat * seats
        if seats == vehicle.capacity:
            fare *= 1 - FULL_VEHICLE_DISCOUNT
        return round(fare, 2)

    def book_seats(self, trip_id, customer_name, phone, seats) -> Booking:
        trip = self.get_trip(int(trip_id))
        customer_name = validate_name(customer_name, "Customer name")
        phone = validate_phone(phone)
        seats = validate_positive_int(seats, "Seats", maximum=60)
        available = self.seats_available(trip.id)
        if seats > available:
            raise BookingError(f"Only {available} seat(s) available on trip {trip.id}.")
        booking = Booking(
            self._next_id("bookings"), trip.id, customer_name, phone, seats,
            self.calculate_fare(trip.id, seats),
        )
        self.db["bookings"].append(booking.to_dict())
        self._save()
        return booking

    def list_bookings(self) -> List[Booking]:
        return [Booking.from_dict(b) for b in self.db["bookings"]]

    def get_booking(self, booking_id: int) -> Booking:
        for item in self.db["bookings"]:
            if item["id"] == booking_id:
                return Booking.from_dict(item)
        raise NotFoundError(f"Booking {booking_id} not found.")

    # ---------- cancellation ----------
    def refund_fraction(self, trip: Trip, now: Optional[datetime] = None) -> float:
        now = now or datetime.now()
        departure = datetime.strptime(f"{trip.date} {trip.departure_time}", "%Y-%m-%d %H:%M")
        hours_left = (departure - now).total_seconds() / 3600
        if hours_left < 0:
            raise BookingError("The trip has already departed; it cannot be cancelled.")
        for min_hours, fraction in REFUND_POLICY:
            if hours_left >= min_hours:
                return fraction
        return 0.0

    def cancel_booking(self, booking_id, now: Optional[datetime] = None) -> Booking:
        booking = self.get_booking(int(booking_id))
        if booking.status == "CANCELLED":
            raise BookingError(f"Booking {booking.id} is already cancelled.")
        trip = self.get_trip(booking.trip_id)
        fraction = self.refund_fraction(trip, now)
        booking.status = "CANCELLED"
        booking.refund = round(booking.fare * fraction, 2)
        for index, item in enumerate(self.db["bookings"]):
            if item["id"] == booking.id:
                self.db["bookings"][index] = booking.to_dict()
        self._save()
        return booking
