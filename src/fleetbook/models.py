"""Plain data classes for the booking domain."""

from dataclasses import asdict, dataclass


@dataclass
class Vehicle:
    id: int
    vehicle_type: str        # bus / car / van
    registration_no: str
    capacity: int
    price_per_km_per_seat: float
    active: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Vehicle":
        return cls(**data)


@dataclass
class Route:
    id: int
    source: str
    destination: str
    distance_km: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Route":
        return cls(**data)

    @property
    def label(self) -> str:
        return f"{self.source} -> {self.destination}"


@dataclass
class Trip:
    id: int
    route_id: int
    vehicle_id: int
    date: str                # YYYY-MM-DD
    departure_time: str      # HH:MM

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Trip":
        return cls(**data)


@dataclass
class Booking:
    id: int
    trip_id: int
    customer_name: str
    phone: str
    seats: int
    fare: float
    status: str = "CONFIRMED"   # CONFIRMED / CANCELLED
    refund: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Booking":
        return cls(**data)
