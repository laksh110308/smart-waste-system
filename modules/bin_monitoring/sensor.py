"""
modules/bin_monitoring/sensor.py
---------------------------------
Simulates IoT ultrasonic fill-level sensors, since no physical hardware
is available for this college project.
"""

import random


def simulate_reading(current_fill_level: float) -> float:
    increment = random.uniform(1.0, 9.0)
    new_level = current_fill_level + increment
    return round(min(new_level, 100.0), 2)


def simulate_batch(bins: list) -> list:
    results = []
    for b in bins:
        new_level = simulate_reading(b["fill_level"])
        results.append({"bin_id": b["bin_id"], "new_fill_level": new_level})
    return results


if __name__ == "__main__":
    level = 20.0
    print("Simulating 5 sensor readings starting at 20%:")
    for i in range(5):
        level = simulate_reading(level)
        print(f"  Reading {i+1}: {level}%")