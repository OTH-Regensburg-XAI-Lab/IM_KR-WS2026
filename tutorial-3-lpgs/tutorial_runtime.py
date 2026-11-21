"""Small notebook helpers for Tutorial 3; no server is started on import.

The Neo4j driver is a Bolt client here; the server remains Memgraph.
All Cypher values are passed as parameters. Imports use MERGE on the supplied
fixture identifiers so rerunning an unchanged fixture does not duplicate it.
"""
from __future__ import annotations

import os
from pathlib import Path

_driver = None


def connect(uri=None):
    """Connect to an already-running Memgraph; close the previous driver."""
    from neo4j import GraphDatabase

    global _driver
    close()
    target = uri or os.environ.get("MEMGRAPH_URI", "bolt://localhost:7687")
    auth = (os.environ.get("MEMGRAPH_USER", ""),
            os.environ.get("MEMGRAPH_PASSWORD", ""))
    candidate = GraphDatabase.driver(target, auth=auth, connection_timeout=5)
    try:
        candidate.verify_connectivity()
    except Exception:
        candidate.close()
        raise
    _driver = candidate
    return target


def close():
    """Release the client connection; leave the database and containers intact."""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def run_cypher(query, parameters=None):
    """Run one Cypher statement and return a pandas DataFrame, including columns.

    A session.run auto-commit query is consumed before its session is closed,
    including write statements. An empty result keeps its declared column names.
    """
    import pandas as pd

    if _driver is None:
        raise RuntimeError("Run the connection cell before executing Cypher.")
    with _driver.session() as session:
        result = session.run(query, parameters or {})
        columns = list(result.keys())
        rows = [record.data() for record in result]
        result.consume()
    return pd.DataFrame.from_records(rows, columns=columns)


def load_flights(data_dir):
    """Load only the small, validated teaching CSV schema, without global reset.

    Original HHMM values are preserved. Missing/ambiguous derived times remain
    absent properties in Memgraph (setting a property to None removes it).
    Flight numbers identify rows only within this synthetic fixture.
    """
    from tutorial_data import get_flight_data

    airports, airlines, flights, issues = get_flight_data(Path(data_dir))
    issue_by_flight = {row["flightNumber"]: row["issue"] for row in issues}
    enriched = [dict(row, timeIssue=issue_by_flight.get(row["flightNumber"]))
                for row in flights]
    run_cypher("""
UNWIND $rows AS row
MERGE (a:Airport {airport_code: row.airport_code})
SET a.city = row.city, a.country = row.country
""", {"rows": airports})
    run_cypher("""
UNWIND $rows AS row
MERGE (a:Airline {airline_code: row.airline_code})
SET a.name = row.name
""", {"rows": airlines})
    run_cypher("""
UNWIND $rows AS row
MATCH (o:Airport {airport_code: row.origin_airport}),
      (d:Airport {airport_code: row.destination_airport}),
      (a:Airline {name: row.Airline})
MERGE (f:Flight {flightNumber: row.flightNumber})
SET f.departureTime = row.departureTime,
    f.arrivalTime = row.arrivalTime,
    f.departureMinutes = row.departureMinutes,
    f.arrivalMinutes = row.arrivalMinutes,
    f.durationMinutes = row.durationMinutes,
    f.timeIssue = row.timeIssue
MERGE (f)-[:DEPARTS_FROM]->(o)
MERGE (f)-[:ARRIVES_AT]->(d)
MERGE (f)-[:OPERATED_BY]->(a)
""", {"rows": enriched})
    return {
        "airports": len(airports), "airlines": len(airlines),
        "flights": len(flights), "relationships": 3 * len(flights),
        "time_issues": issues,
    }
