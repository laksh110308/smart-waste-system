"""
modules/bin_monitoring/bin_service.py
---------------------------------------
The main service for MODULE 1 - Smart Waste Bin Monitoring.
"""

import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.database import get_connection
from modules.bin_monitoring import sensor


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def add_bin(bin_id, location_name, latitude, longitude,
            waste_type="Mixed", fill_level=0.0, threshold=75.0):
    conn = get_connection()
    conn.execute(
        """INSERT INTO bins
           (bin_id, location_name, latitude, longitude, waste_type,
            fill_level, threshold, status, collection_status, last_updated)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (bin_id, location_name, latitude, longitude, waste_type,
         fill_level, threshold,
         "Collection Required" if fill_level >= threshold else "Normal",
         "Pending", _now())
    )
    conn.commit()
    conn.close()


def get_all_bins():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM bins ORDER BY bin_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bin(bin_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM bins WHERE bin_id = ?", (bin_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_bins_requiring_collection():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM bins WHERE status = 'Collection Required' "
        "AND collection_status = 'Pending' ORDER BY fill_level DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_fill_level(bin_id, new_fill_level):
    conn = get_connection()
    bin_row = conn.execute("SELECT threshold FROM bins WHERE bin_id = ?", (bin_id,)).fetchone()
    if bin_row is None:
        conn.close()
        raise ValueError(f"Bin {bin_id} does not exist")

    threshold = bin_row["threshold"]
    new_status = "Collection Required" if new_fill_level >= threshold else "Normal"

    conn.execute(
        """UPDATE bins SET fill_level = ?, status = ?, last_updated = ?
           WHERE bin_id = ?""",
        (new_fill_level, new_status, _now(), bin_id)
    )
    conn.execute(
        "INSERT INTO sensor_readings (bin_id, fill_level, recorded_at) VALUES (?, ?, ?)",
        (bin_id, new_fill_level, _now())
    )
    conn.commit()
    conn.close()
    return new_status


def set_threshold(bin_id, new_threshold):
    conn = get_connection()
    conn.execute("UPDATE bins SET threshold = ? WHERE bin_id = ?", (new_threshold, bin_id))
    conn.commit()
    conn.close()


def simulate_all_sensors():
    conn = get_connection()
    rows = conn.execute("SELECT bin_id, fill_level FROM bins").fetchall()
    conn.close()

    readings = sensor.simulate_batch(rows)
    summary = []
    for r in readings:
        status = update_fill_level(r["bin_id"], r["new_fill_level"])
        summary.append({
            "bin_id": r["bin_id"],
            "fill_level": r["new_fill_level"],
            "status": status
        })
    return summary


def detect_full_bins():
    return get_bins_requiring_collection()


def mark_collection_status(bin_id, collection_status):
    conn = get_connection()
    if collection_status == "Collected":
        conn.execute(
            """UPDATE bins SET collection_status = 'Pending',
               status = 'Normal', fill_level = 0, last_updated = ?
               WHERE bin_id = ?""",
            (_now(), bin_id)
        )
    else:
        conn.execute(
            "UPDATE bins SET collection_status = ? WHERE bin_id = ?",
            (collection_status, bin_id)
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    from database.database import reset_db
    reset_db()

    print("\nAdding 5 test bins...")
    add_bin("B1", "T. Nagar Main Road", 13.0418, 80.2341, "Mixed", fill_level=35, threshold=75)
    add_bin("B2", "Anna Nagar Tower Park", 13.0850, 80.2101, "Plastic", fill_level=85, threshold=75)
    add_bin("B3", "Velachery Bus Stand", 12.9791, 80.2183, "Organic", fill_level=92, threshold=75)
    add_bin("B4", "Adyar Signal", 13.0067, 80.2570, "Mixed", fill_level=40, threshold=75)
    add_bin("B5", "Guindy Industrial Estate", 13.0067, 80.2206, "E-Waste", fill_level=78, threshold=75)

    print("\nAll bins:")
    for b in get_all_bins():
        print(f"  {b['bin_id']:4s} {b['location_name']:28s} fill={b['fill_level']:5.1f}%  status={b['status']}")

    print("\nBins requiring collection (as Module 2 would receive them):")
    for b in get_bins_requiring_collection():
        print(f"  {b['bin_id']} - {b['location_name']} ({b['fill_level']}%)")

    print("\nSimulating one new sensor reading for every bin...")
    for s in simulate_all_sensors():
        print(f"  {s['bin_id']}: {s['fill_level']}% -> {s['status']}")

    print("\nBins requiring collection AFTER simulation:")
    for b in detect_full_bins():
        print(f"  {b['bin_id']} - {b['location_name']} ({b['fill_level']}%)")