"""
data/sample_data.py
---------------------
Seeds the database with realistic demo data:
  - 18 waste bins spread across real Chennai locations
  - 3 collection vehicles
  - A depot and a dumping station (used by Module 2's road network)

Run this file directly to reset the DB and load fresh sample data:
    python data/sample_data.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import reset_db, get_connection
from modules.bin_monitoring.bin_service import add_bin


SAMPLE_BINS = [
    ("B1",  "T. Nagar Main Road",          13.0418, 80.2341, "Mixed",        35),
    ("B2",  "Anna Nagar Tower Park",       13.0850, 80.2101, "Plastic",      85),
    ("B3",  "Velachery Bus Stand",         12.9791, 80.2183, "Organic",      92),
    ("B4",  "Adyar Signal",                13.0067, 80.2570, "Mixed",        40),
    ("B5",  "Guindy Industrial Estate",    13.0067, 80.2206, "E-Waste",      78),
    ("B6",  "Nungambakkam High Road",      13.0569, 80.2425, "Mixed",        55),
    ("B7",  "Mylapore Tank",               13.0339, 80.2697, "Organic",      88),
    ("B8",  "Egmore Railway Station",      13.0732, 80.2609, "Mixed",        30),
    ("B9",  "Kilpauk Garden Colony",       13.0778, 80.2419, "Plastic",      95),
    ("B10", "Perambur Market",             13.1143, 80.2329, "Organic",      60),
    ("B11", "Vadapalani Signal",           13.0503, 80.2124, "Mixed",        82),
    ("B12", "Porur Junction",              13.0381, 80.1565, "Construction", 45),
    ("B13", "Tambaram Sanatorium",         12.9229, 80.1275, "Mixed",        90),
    ("B14", "Chromepet Bus Depot",         12.9516, 80.1462, "Plastic",      70),
    ("B15", "Sholinganallur IT Corridor",  12.9010, 80.2279, "E-Waste",      65),
    ("B16", "Besant Nagar Beach Road",     13.0002, 80.2669, "Mixed",        50),
    ("B17", "Royapettah Hospital Road",    13.0526, 80.2646, "Hazardous",    87),
    ("B18", "Ashok Nagar Signal",          13.0345, 80.2101, "Mixed",        38),
]

SAMPLE_VEHICLES = [
    ("V1", "Truck Alpha", 8),
    ("V2", "Truck Bravo", 6),
    ("V3", "Truck Charlie", 10),
]

DEPOT = ("DEPOT", "Corporation Depot - Ripon Building", 13.0878, 80.2785)
DUMPING_STATION = ("DUMP", "Kodungaiyur Dumping Yard", 13.1425, 80.2489)


def load_sample_data():
    print("Resetting database...")
    reset_db()

    print("Adding depot and dumping station as special reference points...")
    conn = get_connection()
    conn.execute(
        """INSERT INTO bins (bin_id, location_name, latitude, longitude,
           waste_type, fill_level, threshold, status, collection_status, last_updated)
           VALUES (?, ?, ?, ?, 'N/A', 0, 999, 'Normal', 'Pending', datetime('now'))""",
        DEPOT
    )
    conn.execute(
        """INSERT INTO bins (bin_id, location_name, latitude, longitude,
           waste_type, fill_level, threshold, status, collection_status, last_updated)
           VALUES (?, ?, ?, ?, 'N/A', 0, 999, 'Normal', 'Pending', datetime('now'))""",
        DUMPING_STATION
    )
    conn.commit()
    conn.close()

    print(f"Adding {len(SAMPLE_BINS)} waste bins across Chennai...")
    for bin_id, name, lat, lng, wtype, fill in SAMPLE_BINS:
        add_bin(bin_id, name, lat, lng, waste_type=wtype, fill_level=fill, threshold=75)

    print(f"Adding {len(SAMPLE_VEHICLES)} vehicles...")
    conn = get_connection()
    for vid, name, capacity in SAMPLE_VEHICLES:
        conn.execute(
            "INSERT INTO vehicles (vehicle_id, vehicle_name, capacity, available) VALUES (?, ?, ?, 1)",
            (vid, name, capacity)
        )
    conn.commit()
    conn.close()

    print("\nSample data loaded successfully.")
    print(f"  Total bins: {len(SAMPLE_BINS)} (+ depot + dumping station)")
    print(f"  Total vehicles: {len(SAMPLE_VEHICLES)}")


if __name__ == "__main__":
    load_sample_data()

    from modules.bin_monitoring.bin_service import get_all_bins, get_bins_requiring_collection

    print("\n--- Bins requiring collection right now ---")
    for b in get_bins_requiring_collection():
        print(f"  {b['bin_id']:6s} {b['location_name']:30s} {b['fill_level']}%")

    total = len(get_all_bins())
    required = len(get_bins_requiring_collection())
    print(f"\nTotal locations in DB (incl. depot/dump): {total}")
    print(f"Bins currently needing collection: {required}")