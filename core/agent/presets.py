"""
AEGIS V2 Pre-Configured AI Security Trigger Presets
"""

PRESET_TRIGGERS = [
    {
        "id": "preset_package",
        "name": "Package & Delivery Watch",
        "category": "Porch Security",
        "description": "Alerts when a courier, delivery worker, or person drops off or picks up a package or box near the entry.",
        "condition_text": "Detect if a delivery driver, courier, or person places or picks up a package, parcel, or box near the front door or porch area.",
        "severity": "warning",
        "capture_snapshot": True,
        "capture_clip": False
    },
    {
        "id": "preset_intruder",
        "name": "Perimeter & Intruder Watch",
        "category": "Property Defense",
        "description": "Triggers immediate critical alerts when an unknown person approaches doors, windows, or restricted zones.",
        "condition_text": "Detect if any person is loitering, crouching, climbing, or approaching restricted doors, windows, or entryways suspiciously.",
        "severity": "critical",
        "capture_snapshot": True,
        "capture_clip": True
    },
    {
        "id": "preset_vehicle",
        "name": "Driveway Vehicle Monitor",
        "category": "Driveway",
        "description": "Detects cars, delivery vans, or trucks parking or pulling into the driveway.",
        "condition_text": "Detect if a car, truck, van, motorcycle, or unauthorized vehicle enters or parks in the driveway or entrance area.",
        "severity": "info",
        "capture_snapshot": True,
        "capture_clip": False
    },
    {
        "id": "preset_pet",
        "name": "Pet Furniture & Countertop Monitor",
        "category": "Home & Pets",
        "description": "Alerts when dogs or cats get onto restricted sofas, beds, or kitchen countertops.",
        "condition_text": "Detect if a dog, cat, or pet jumps on, climbs, or lies on the sofa, bed, dining table, or kitchen counter.",
        "severity": "info",
        "capture_snapshot": True,
        "capture_clip": False
    },
    {
        "id": "preset_loitering",
        "name": "Unattended Object & Loitering",
        "category": "Commercial",
        "description": "Detects individuals standing motionless for an extended duration or leaving unattended luggage.",
        "condition_text": "Detect if any person is standing idle/loitering for a long time, or if an unattended bag, backpack, or suitcase is left behind.",
        "severity": "warning",
        "capture_snapshot": True,
        "capture_clip": True
    },
    {
        "id": "preset_night",
        "name": "Nighttime Anomaly Watch",
        "category": "Night Vision",
        "description": "Detects movement, flashlights, or opening entry points during designated night hours.",
        "condition_text": "Detect any unexpected human presence, flashlight beams, or opening doors/gates in dark or night-vision scenes.",
        "severity": "critical",
        "capture_snapshot": True,
        "capture_clip": True
    }
]
