# FleetBook - Travel, Transport & Fleet Booking System

**Course:** B.Tech | **Subject:** Software Engineering - Assignment 2 (Mini-Project Implementation using Git)
**Student:** C.M.Sharmila Mai | **Register No:** 2503917720522221

FleetBook is a command-line application that manages a transport fleet (buses, vans, cars),
the routes they serve, scheduled trips, and customer seat bookings with fare calculation
and cancellation refunds.

## Problem Statement and Objectives

Small travel and transport operators often track vehicles, trips and bookings on paper or in
spreadsheets, which leads to double-booked vehicles, overbooked trips and inconsistent fares.

Objectives:

1. Maintain a registry of fleet vehicles with capacity and pricing.
2. Define routes and schedule trips without allowing a vehicle to be double-booked.
3. Let customers search trips and book seats while preventing overbooking.
4. Calculate fares automatically, including a discount for hiring a whole vehicle.
5. Support cancellation with a transparent, time-based refund policy.
6. Validate all input and handle errors without crashing.

## Features / Modules

| Module | File | Responsibility |
|---|---|---|
| Validation | `src/fleetbook/validation.py` | Names, phone numbers, registration numbers, dates, times, numbers |
| Models | `src/fleetbook/models.py` | `Vehicle`, `Route`, `Trip`, `Booking` data classes |
| Storage | `src/fleetbook/storage.py` | JSON persistence, atomic writes, corrupted-file detection |
| Core logic | `src/fleetbook/system.py` | Fleet, routes, trip scheduling, booking, fares, cancellation/refunds |
| CLI | `src/fleetbook/cli.py` | Command-line commands and user-friendly error messages |
| Tests | `tests/` | 30 unit tests |

Business rules:

- A vehicle cannot be scheduled on two trips on the same date.
- Bookings cannot exceed the free seats of the trip's vehicle.
- Fare = distance (km) x price per km per seat x seats; booking **all** seats gives a 10% discount.
- Refund on cancellation: 90% if 48 hours or more before departure, 50% for 24-48 hours, 0% under 24 hours;
  trips that have already departed cannot be cancelled.

## Technology Stack and Tools

- Python 3.9 or newer (standard library only: `argparse`, `json`, `dataclasses`, `unittest`)
- JSON file for data storage
- Git and GitHub for version control

## Prerequisites and Installation

1. Install Python 3.9+ (`python --version` to check).
2. Clone the repository:
   ```
   git clone <your-github-repository-url>
   cd travel-fleet-booking
   ```
3. No packages need to be installed (`requirements.txt` documents this).

## How to Run

All commands use `python main.py <command>`. Data is stored in `data/fleetbook.json`
(created automatically, ignored by Git). Use `--db <path>` to choose another file.

| Command | Purpose |
|---|---|
| `add-vehicle --type bus --reg TN01AB1234 --capacity 40 --price 1.5` | Register a vehicle |
| `add-route --from Chennai --to Madurai --km 460` | Add a route |
| `schedule --route 1 --vehicle 1 --date 2026-12-20 --time 21:30` | Schedule a trip |
| `list-vehicles`, `list-routes`, `list-trips`, `list-bookings` | Show records |
| `search --from Chennai --to Madurai --date 2026-12-20` | Find trips, free seats and fare per seat |
| `book --trip 1 --name "Sharmila Mai" --phone 9876543210 --seats 3` | Book seats |
| `cancel --booking 1` | Cancel and compute the refund |

## Sample Inputs and Outputs

```
$ python main.py add-vehicle --type bus --reg TN01AB1234 --capacity 40 --price 1.5
Vehicle added: #1 bus TN01AB1234 (40 seats)

$ python main.py search --from Chennai --to Madurai --date 2026-12-20
Trip  Date        Time   Vehicle  Free  Fare/seat
-------------------------------------------------
1     2026-12-20  21:30  bus      40    Rs.690.00

$ python main.py book --trip 1 --name "Sharmila Mai" --phone 9876543210 --seats 3
Booking confirmed: #1 for Sharmila Mai, 3 seat(s), fare Rs.2070.00

$ python main.py cancel --booking 1
Booking #1 cancelled. Refund: Rs.1863.00 of Rs.2070.00

$ python main.py book --trip 1 --name "Arun" --phone 12345 --seats 2
Error: Phone must be a 10-digit Indian mobile number starting with 6-9.
```

## Testing Performed and Results

Run all tests:

```
python -m unittest discover -s tests -v
```

Result: **30 tests, all passing.** They cover validation rules, fare calculation, full-vehicle
discount, overbooking prevention, double-booked vehicles, persistence, corrupted data files,
and every cancellation refund tier.

Issue found during testing: the first run of `test_invalid_phone_rejected` failed because a valid
10-digit number had been placed in the list of invalid numbers by mistake. The test data was
corrected to an 11-digit number (see commit history). Manual testing of invalid inputs
(short phone numbers, unknown IDs, past dates, overbooking, unknown vehicle type) confirmed that the
application prints a clear error and exits with a non-zero code instead of crashing.

## Git Workflow Used

- `main` holds stable code; work was committed in stages (setup, validation, models/storage,
  core logic, CLI, tests, documentation).
- Feature branch `feature/cancellation-refund` implemented cancellation and refunds with its own
  commits, then was merged into `main` using `git merge --no-ff`.

## Team Details and Individual Contributions

Individual project. All design, implementation, testing and documentation:
C.M.Sharmila Mai (Reg. No. 2503917720522221).

## Known Limitations and Future Enhancements

- Command-line only; a web or mobile front end would improve usability.
- JSON file storage is not suitable for many simultaneous users; a database (SQLite/PostgreSQL) would be better.
- No user accounts, authentication or online payment integration.
- Seat numbers are not assigned; only seat counts are tracked.
- Possible additions: round trips, driver management, revenue reports, email/SMS confirmations.

## Acknowledgements

Built using only the Python standard library. No external code, datasets or repositories were copied.
