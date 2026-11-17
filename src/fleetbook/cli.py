"""Command-line interface for FleetBook."""

import argparse
import os
import sys

from .storage import JsonStore, StorageError
from .system import BookingError, FleetBookingSystem, NotFoundError
from .validation import ValidationError

DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "fleetbook.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fleetbook", description="Travel, Transport & Fleet Booking System")
    parser.add_argument("--db", default=DEFAULT_DB, help="path to the JSON data file")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add-vehicle", help="register a vehicle in the fleet")
    p.add_argument("--type", required=True, dest="vehicle_type")
    p.add_argument("--reg", required=True, dest="registration_no")
    p.add_argument("--capacity", required=True)
    p.add_argument("--price", required=True, help="price per km per seat (Rs.)")

    sub.add_parser("list-vehicles", help="show the fleet")

    p = sub.add_parser("add-route", help="add a travel route")
    p.add_argument("--from", required=True, dest="source")
    p.add_argument("--to", required=True, dest="destination")
    p.add_argument("--km", required=True)

    sub.add_parser("list-routes", help="show routes")

    p = sub.add_parser("schedule", help="schedule a trip")
    p.add_argument("--route", required=True)
    p.add_argument("--vehicle", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--time", required=True)

    sub.add_parser("list-trips", help="show scheduled trips with seat availability")

    p = sub.add_parser("search", help="search trips by route and date")
    p.add_argument("--from", required=True, dest="source")
    p.add_argument("--to", required=True, dest="destination")
    p.add_argument("--date")

    p = sub.add_parser("book", help="book seats on a trip")
    p.add_argument("--trip", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--phone", required=True)
    p.add_argument("--seats", required=True)

    p = sub.add_parser("cancel", help="cancel a booking and compute the refund")
    p.add_argument("--booking", required=True)

    sub.add_parser("list-bookings", help="show all bookings")
    return parser


def _print_table(headers, rows):
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)] if rows else [len(h) for h in headers]
    line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def run(args, system: FleetBookingSystem) -> None:
    cmd = args.command
    if cmd == "add-vehicle":
        v = system.add_vehicle(args.vehicle_type, args.registration_no, args.capacity, args.price)
        print(f"Vehicle added: #{v.id} {v.vehicle_type} {v.registration_no} ({v.capacity} seats)")
    elif cmd == "list-vehicles":
        _print_table(["ID", "Type", "Reg No", "Seats", "Rs/km/seat"],
                     [(v.id, v.vehicle_type, v.registration_no, v.capacity, v.price_per_km_per_seat)
                      for v in system.list_vehicles()])
    elif cmd == "add-route":
        r = system.add_route(args.source, args.destination, args.km)
        print(f"Route added: #{r.id} {r.label} ({r.distance_km:g} km)")
    elif cmd == "list-routes":
        _print_table(["ID", "From", "To", "Km"],
                     [(r.id, r.source, r.destination, f"{r.distance_km:g}") for r in system.list_routes()])
    elif cmd == "schedule":
        t = system.schedule_trip(args.route, args.vehicle, args.date, args.time)
        print(f"Trip scheduled: #{t.id} on {t.date} at {t.departure_time}")
    elif cmd == "list-trips":
        rows = []
        for t in system.list_trips():
            route, veh = system.get_route(t.route_id), system.get_vehicle(t.vehicle_id)
            rows.append((t.id, route.label, veh.registration_no, t.date, t.departure_time,
                         f"{system.seats_available(t.id)}/{veh.capacity}"))
        _print_table(["ID", "Route", "Vehicle", "Date", "Time", "Free seats"], rows)
    elif cmd == "search":
        trips = system.search_trips(args.source, args.destination, args.date)
        if not trips:
            print("No trips found for that route/date.")
            return
        rows = []
        for t in trips:
            veh = system.get_vehicle(t.vehicle_id)
            rows.append((t.id, t.date, t.departure_time, veh.vehicle_type, system.seats_available(t.id),
                         f"Rs.{system.calculate_fare(t.id, 1):.2f}"))
        _print_table(["Trip", "Date", "Time", "Vehicle", "Free", "Fare/seat"], rows)
    elif cmd == "book":
        b = system.book_seats(args.trip, args.name, args.phone, args.seats)
        print(f"Booking confirmed: #{b.id} for {b.customer_name}, {b.seats} seat(s), fare Rs.{b.fare:.2f}")
    elif cmd == "cancel":
        b = system.cancel_booking(args.booking)
        print(f"Booking #{b.id} cancelled. Refund: Rs.{b.refund:.2f} of Rs.{b.fare:.2f}")
    elif cmd == "list-bookings":
        _print_table(["ID", "Trip", "Customer", "Seats", "Fare", "Status", "Refund"],
                     [(b.id, b.trip_id, b.customer_name, b.seats, f"{b.fare:.2f}", b.status, f"{b.refund:.2f}")
                      for b in system.list_bookings()])


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        system = FleetBookingSystem(JsonStore(args.db))
        run(args, system)
    except (ValidationError, BookingError, NotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except StorageError as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 2
    return 0
