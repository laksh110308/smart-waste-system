"""
modules/collection/vehicle_service.py
----------------------------------------
MODULE 3 - manages collection vehicles: registration, availability,
and capacity checks.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import get_connection


def register_vehicle(vehicle_id, vehicle_name, capacity):
    conn = get_connection()
    conn.execute(
        "INSERT INTO vehicles (vehicle_id, vehicle_name, capacity, available) VALUES (?, ?, ?, 1)",
        (vehicle_id, vehicle_name, capacity)
    )
    conn.commit()
    conn.close()


def get_all_vehicles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM vehicles ORDER BY vehicle_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_available_vehicles():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM vehicles WHERE available = 1 ORDER BY capacity DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_best_available_vehicle(bins_needed):
    candidates = [v for v in get_available_vehicles() if v["capacity"] >= bins_needed]
    if not candidates:
        return None
    return min(candidates, key=lambda v: v["capacity"])


def set_vehicle_availability(vehicle_id, available: bool):
    conn = get_connection()
    conn.execute(
        "UPDATE vehicles SET available = ? WHERE vehicle_id = ?",
        (1 if available else 0, vehicle_id)
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("All vehicles:")
    for v in get_all_vehicles():
        status = "Available" if v["available"] else "On route"
        print(f"  {v['vehicle_id']}  {v['vehicle_name']:15s} capacity={v['capacity']}  {status}")

    print("\nBest vehicle for an 8-bin route:")
    best = get_best_available_vehicle(8)
    print(f"  {best}")