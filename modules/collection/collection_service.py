"""
modules/collection/collection_service.py
--------------------------------------------
MODULE 3 core orchestrator. Completes the full pipeline:
Module 1 -> Module 2 -> Module 3 -> Database -> Dashboard.
"""

import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import get_connection
from modules.route_optimization.route_service import generate_optimized_route
from modules.collection.vehicle_service import get_best_available_vehicle, set_vehicle_availability
from modules.bin_monitoring.bin_service import mark_collection_status


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def assign_route_to_vehicle():
    route = generate_optimized_route()
    if route is None:
        return {"error": "No bins currently require collection."}
    if "error" in route:
        return route

    vehicle = get_best_available_vehicle(route["bins_count"])
    if vehicle is None:
        return {"error": "No available vehicle with enough capacity right now."}

    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO routes
           (vehicle_id, total_distance_km, estimated_time_min, bins_count, status, created_at)
           VALUES (?, ?, ?, ?, 'Planned', ?)""",
        (vehicle["vehicle_id"], route["total_distance_km"], route["estimated_time_min"],
         route["bins_count"], _now())
    )
    route_id = cursor.lastrowid

    for order, bin_id in enumerate(route["bin_sequence"], start=1):
        conn.execute(
            "INSERT INTO route_bins (route_id, bin_id, sequence_order, collected) VALUES (?, ?, ?, 0)",
            (route_id, bin_id, order)
        )

    conn.commit()
    conn.close()

    set_vehicle_availability(vehicle["vehicle_id"], available=False)
    for bin_id in route["bin_sequence"]:
        mark_collection_status(bin_id, "Assigned")

    return {
        "route_id": route_id,
        "vehicle_id": vehicle["vehicle_id"],
        "vehicle_name": vehicle["vehicle_name"],
        "bin_sequence": route["bin_sequence"],
        "total_distance_km": route["total_distance_km"],
        "estimated_time_min": route["estimated_time_min"],
        "bins_count": route["bins_count"]
    }


def start_collection(route_id):
    conn = get_connection()
    conn.execute("UPDATE routes SET status = 'In Progress' WHERE route_id = ?", (route_id,))
    conn.commit()
    conn.close()


def mark_bin_collected(route_id, bin_id):
    conn = get_connection()
    conn.execute(
        "UPDATE route_bins SET collected = 1 WHERE route_id = ? AND bin_id = ?",
        (route_id, bin_id)
    )
    conn.commit()
    conn.close()

    mark_collection_status(bin_id, "Collected")


def complete_route(route_id):
    conn = get_connection()
    route = conn.execute("SELECT * FROM routes WHERE route_id = ?", (route_id,)).fetchone()
    if route is None:
        conn.close()
        return {"error": f"Route {route_id} not found"}

    conn.execute(
        "UPDATE routes SET status = 'Completed', completed_at = ? WHERE route_id = ?",
        (_now(), route_id)
    )
    conn.commit()
    conn.close()

    set_vehicle_availability(route["vehicle_id"], available=True)
    return {"route_id": route_id, "status": "Completed"}


def get_route_progress(route_id):
    conn = get_connection()
    route = conn.execute("SELECT * FROM routes WHERE route_id = ?", (route_id,)).fetchone()
    stops = conn.execute(
        "SELECT * FROM route_bins WHERE route_id = ? ORDER BY sequence_order", (route_id,)
    ).fetchall()
    conn.close()

    if route is None:
        return None

    return {
        "route": dict(route),
        "stops": [dict(s) for s in stops]
    }


def get_active_routes():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM routes WHERE status IN ('Planned', 'In Progress') ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    print("Assigning an optimized route to the best available vehicle...\n")
    result = assign_route_to_vehicle()

    if "error" in result:
        print("ERROR:", result["error"])
    else:
        print(f"Route #{result['route_id']} assigned to {result['vehicle_name']} ({result['vehicle_id']})")
        print(f"  Stops: {' -> '.join(result['bin_sequence'])}")
        print(f"  Distance: {result['total_distance_km']} km | ETA: {result['estimated_time_min']} min")

        route_id = result["route_id"]

        print(f"\nStarting collection on route #{route_id}...")
        start_collection(route_id)

        print("Collecting each bin one by one...")
        for bin_id in result["bin_sequence"]:
            mark_bin_collected(route_id, bin_id)
            print(f"  Collected {bin_id}")

        print(f"\nCompleting route #{route_id}...")
        complete_result = complete_route(route_id)
        print(f"  {complete_result}")

        print("\nFinal progress check:")
        progress = get_route_progress(route_id)
        print(f"  Route status: {progress['route']['status']}")
        for stop in progress["stops"]:
            mark = "Collected" if stop["collected"] else "Pending"
            print(f"    {stop['bin_id']}: {mark}")