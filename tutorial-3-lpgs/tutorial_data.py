"""Small, dependency-free fixtures for the LPG Memgraph tutorial.

The seven KNOWS relationships have additional fictional "since" years for
teaching relationship properties. These years are new illustrative metadata;
they were not part of the original student exercise.

Flight CSV files are read without modifying them. The original HHMM columns are
retained as integers. Derived minute values use an explicitly fictional common
time zone and the same day. They are clock differences for this teaching
fixture, NOT real travel durations. The data has no dates or time-zone offsets:
an arrival before departure is ambiguous and never triggers an inferred
next-day arrival.
"""

from __future__ import annotations

import csv
from pathlib import Path

__all__ = [
    "STUDENTS",
    "SOCIAL_RELATIONSHIPS",
    "get_flight_data",
    "hhmm_to_minutes",
]


STUDENTS = [
    {"name": "Anna", "age": 22, "field_of_study": "Data Science"},
    {"name": "Ben", "age": 24, "field_of_study": "Computer Science"},
    {"name": "Clara", "age": 21, "field_of_study": "Medicine"},
    {"name": "David", "age": 25, "field_of_study": "Mathematics"},
    {"name": "Eva", "age": 23, "field_of_study": "Design"},
    {"name": "Frank", "age": 26, "field_of_study": "Economics"},
    {"name": "Grace", "age": 22, "field_of_study": "Physics"},
    {"name": "Hannah", "age": 20, "field_of_study": "Computer Science"},
    {"name": "Ian", "age": 24, "field_of_study": "Mathematics"},
    {"name": "Julia", "age": 21, "field_of_study": "Data Science"},
]

# BEST_FRIEND is symmetric in this fixture: each friendship is stored in both
# directions. KNOWS, LOVES, and HATES retain their original directed meaning.
SOCIAL_RELATIONSHIPS = [
    {"source": "Anna", "target": "Eva", "type": "BEST_FRIEND"},
    {"source": "Eva", "target": "Anna", "type": "BEST_FRIEND"},
    {"source": "Anna", "target": "Ben", "type": "KNOWS", "since": 2023},
    {"source": "Anna", "target": "David", "type": "LOVES"},
    {"source": "Ben", "target": "David", "type": "BEST_FRIEND"},
    {"source": "David", "target": "Ben", "type": "BEST_FRIEND"},
    {"source": "Ben", "target": "Anna", "type": "LOVES"},
    {"source": "Ben", "target": "Eva", "type": "KNOWS", "since": 2024},
    {"source": "Ben", "target": "Clara", "type": "HATES"},
    {"source": "David", "target": "Clara", "type": "KNOWS", "since": 2022},
    {"source": "David", "target": "Julia", "type": "LOVES"},
    {"source": "Clara", "target": "Julia", "type": "BEST_FRIEND"},
    {"source": "Julia", "target": "Clara", "type": "BEST_FRIEND"},
    {"source": "Clara", "target": "Anna", "type": "KNOWS", "since": 2024},
    {"source": "Eva", "target": "Ben", "type": "LOVES"},
    {"source": "Eva", "target": "Grace", "type": "KNOWS", "since": 2025},
    {"source": "Eva", "target": "Frank", "type": "KNOWS", "since": 2023},
    {"source": "Frank", "target": "Grace", "type": "BEST_FRIEND"},
    {"source": "Grace", "target": "Frank", "type": "BEST_FRIEND"},
    {"source": "Frank", "target": "Ben", "type": "HATES"},
    {"source": "Grace", "target": "Ben", "type": "LOVES"},
    {"source": "Grace", "target": "Clara", "type": "BEST_FRIEND"},
    {"source": "Clara", "target": "Grace", "type": "BEST_FRIEND"},
    {"source": "Hannah", "target": "Clara", "type": "KNOWS", "since": 2024},
    {"source": "Hannah", "target": "Julia", "type": "BEST_FRIEND"},
    {"source": "Julia", "target": "Hannah", "type": "BEST_FRIEND"},
    {"source": "Ian", "target": "Frank", "type": "BEST_FRIEND"},
    {"source": "Frank", "target": "Ian", "type": "BEST_FRIEND"},
    {"source": "Ian", "target": "Julia", "type": "LOVES"},
    {"source": "Julia", "target": "Eva", "type": "BEST_FRIEND"},
    {"source": "Eva", "target": "Julia", "type": "BEST_FRIEND"},
    {"source": "Julia", "target": "Anna", "type": "HATES"},
]


def hhmm_to_minutes(value: int | str) -> int:
    """Convert a valid HHMM clock value to minutes after midnight.

    Accept integers or strings containing one to four ASCII digits, optionally
    surrounded by whitespace. Reject booleans, floats, negative values, 24:00,
    invalid minute components, and other invalid inputs with ValueError.
    """
    if isinstance(value, bool):
        raise ValueError(f"Invalid HHMM clock value: {value!r}")
    if isinstance(value, int):
        hhmm = value
    elif isinstance(value, str):
        stripped = value.strip()
        if not (
            1 <= len(stripped) <= 4
            and stripped.isascii()
            and stripped.isdecimal()
        ):
            raise ValueError(f"Invalid HHMM clock value: {value!r}")
        hhmm = int(stripped)
    else:
        raise ValueError(f"Invalid HHMM clock value: {value!r}")

    hours, minutes = divmod(hhmm, 100)
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"Invalid HHMM clock value: {value!r}")
    return hours * 60 + minutes


def _read_csv(path: Path, expected_fields: tuple[str, ...]) -> list[dict]:
    """Read the small tutorial schema, rejecting malformed or incomplete rows."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        actual_fields = reader.fieldnames or []
        if (
            len(actual_fields) != len(expected_fields)
            or set(actual_fields) != set(expected_fields)
        ):
            raise ValueError(
                f"{path.name}: expected columns {list(expected_fields)!r}; "
                f"found {actual_fields!r}"
            )
        rows = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path.name}, row {row_number}: malformed CSV row")
            missing = [key for key, value in row.items() if not value.strip()]
            if missing:
                raise ValueError(
                    f"{path.name}, row {row_number}: empty required fields {missing!r}"
                )
            rows.append(dict(row))
    return rows


def _unique_values(rows: list[dict], field: str, source: str) -> set[str]:
    seen = set()
    for row in rows:
        value = row[field]
        if value in seen:
            raise ValueError(f"{source}: duplicate {field} {value!r}")
        seen.add(value)
    return seen


def get_flight_data(
    data_dir: str | Path,
) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Read the small data_ex21 CSV schema and return validated teaching data.

    Return (airports, airlines, flights, issues), each a list of dictionaries.
    The supplied directory is explicit; no other dataset is loaded.

    Schema errors, empty required fields, duplicate identifiers, ambiguous airline
    names, invalid foreign keys, and non-integer raw times raise ValueError.
    Integer times that are invalid clock values, or whose arrival precedes
    departure, instead produce issues with flightNumber and issue fields.

    Each flight retains its six original columns (the HHMM columns as integers)
    and gains departureMinutes, arrivalMinutes, and durationMinutes. A valid clock
    value has a minute count even if the overall duration is ambiguous. A duration
    is provided only when both clock values are valid and arrival >= departure,
    under the fictional shared-time-zone, same-day teaching assumption.
    """
    data_dir = Path(data_dir)
    # Check the small airport schema first. A data_ex_2 directory therefore fails
    # before its large, incompatible flights.csv could be read.
    airports = _read_csv(
        data_dir / "airports.csv",
        ("airport_code", "city", "country"),
    )
    airlines = _read_csv(
        data_dir / "airlines.csv",
        ("airline_code", "name"),
    )
    flights = _read_csv(
        data_dir / "flights.csv",
        (
            "flightNumber",
            "origin_airport",
            "destination_airport",
            "Airline",
            "departureTime",
            "arrivalTime",
        ),
    )
    airport_codes = _unique_values(airports, "airport_code", "airports.csv")
    _unique_values(airlines, "airline_code", "airlines.csv")
    airline_names = _unique_values(airlines, "name", "airlines.csv")
    _unique_values(flights, "flightNumber", "flights.csv")

    issues = []
    for flight in flights:
        flight_number = flight["flightNumber"]
        for field in ("origin_airport", "destination_airport"):
            if flight[field] not in airport_codes:
                raise ValueError(
                    f"Flight {flight_number}: unknown {field} {flight[field]!r}"
                )
        if flight["Airline"] not in airline_names:
            raise ValueError(
                f"Flight {flight_number}: unknown Airline {flight['Airline']!r}"
            )

        for raw_field, derived_field in (
            ("departureTime", "departureMinutes"),
            ("arrivalTime", "arrivalMinutes"),
        ):
            raw_value = flight[raw_field]
            try:
                flight[raw_field] = int(raw_value)
            except ValueError as error:
                raise ValueError(
                    f"Flight {flight_number}: {raw_field} must be an integer"
                ) from error
            try:
                flight[derived_field] = hhmm_to_minutes(raw_value)
            except ValueError:
                flight[derived_field] = None
                issues.append(
                    {
                        "flightNumber": flight_number,
                        "issue": (
                            f"{raw_field}={flight[raw_field]} is not a valid "
                            "HHMM clock time (00:00-23:59)."
                        ),
                    }
                )

        departure = flight["departureMinutes"]
        arrival = flight["arrivalMinutes"]
        flight["durationMinutes"] = None
        if departure is not None and arrival is not None:
            if arrival >= departure:
                flight["durationMinutes"] = arrival - departure
            else:
                issues.append(
                    {
                        "flightNumber": flight_number,
                        "issue": (
                            "arrivalTime precedes departureTime; date/time-zone "
                            "information is missing, so no day rollover or "
                            "elapsed duration is inferred."
                        ),
                    }
                )
    return airports, airlines, flights, issues
