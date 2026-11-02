"""
Maintenance Guides and Checklist Service.
Provides standard manufacturer-aligned maintenance procedures for Sediment Pre-filters,
Carbon Block Filters, and Reverse Osmosis (RO) Membranes.
"""

from typing import List, Dict, Any, Optional

DEFAULT_GUIDES = [
    {
        "id": "guide-ro-membrane",
        "filter_type": "RO Membrane",
        "title": "Reverse Osmosis (RO) Membrane Replacement Procedure",
        "description": "Standard sanitization and replacement procedure for Thin Film Composite (TFC) RO membranes.",
        "estimated_minutes": 25,
        "checklist_steps": [
            {
                "step_number": 1,
                "title": "Power & Feed Water Isolation",
                "instruction": "Unplug purifier from AC mains power and close the raw water feed angle valve to isolate water pressure.",
                "required": True,
            },
            {
                "step_number": 2,
                "title": "System Depressurization",
                "instruction": "Open the pure water faucet until flow stops completely to release internal pressure from the hydraulic circuit.",
                "required": True,
            },
            {
                "step_number": 3,
                "title": "Membrane Housing Extraction",
                "instruction": "Disconnect quick-connect feed tubing, unlock the membrane housing cap using the filter wrench, and extract the exhausted cartridge.",
                "required": True,
            },
            {
                "step_number": 4,
                "title": "Internal Housing Sanitization",
                "instruction": "Inspect the inside of the housing for biological biofilm or scaling; rinse housing thoroughly with filtered water.",
                "required": True,
            },
            {
                "step_number": 5,
                "title": "New Membrane Insertion",
                "instruction": "Lubricate double O-rings with food-grade silicone grease and firmly push the new membrane element into the brine seal seat.",
                "required": True,
            },
            {
                "step_number": 6,
                "title": "Housing Resealing & Pressure Test",
                "instruction": "Thread the housing cap tightly, reattach tubing, slowly open feed supply, and verify zero leakages around the sealing rim.",
                "required": True,
            },
            {
                "step_number": 7,
                "title": "Initial Membrane Flush & Stabilization",
                "instruction": "Run system for 15 minutes allowing reject brine and initial preservative wash to purge completely before drinking.",
                "required": True,
            },
            {
                "step_number": 8,
                "title": "Confirm Maintenance & Re-baseline",
                "instruction": "Sign off checklist to log the maintenance event and reset monitoring baseline metrics in FilterTwin.",
                "required": True,
            },
        ],
    },
    {
        "id": "guide-sediment-filter",
        "filter_type": "Sediment Pre-Filter",
        "title": "Spun Polypropylene Sediment Cartridge Replacement",
        "description": "Rapid replacement guide for 5-micron spun polypropylene pre-filters.",
        "estimated_minutes": 15,
        "checklist_steps": [
            {
                "step_number": 1,
                "title": "Isolate Water & Pressure Release",
                "instruction": "Turn off water supply shutoff valve and press the red pressure relief button on the bowl head.",
                "required": True,
            },
            {
                "step_number": 2,
                "title": "Bowl Disassembly & Cartridge Removal",
                "instruction": "Unscrew the transparent sump bowl clockwise using the spanner tool; safely dispose of old sediment cartridge.",
                "required": True,
            },
            {
                "step_number": 3,
                "title": "Bowl Cleaning & Cartridge Seating",
                "instruction": "Wash bowl interior with mild soapy water; insert fresh 5-micron cartridge ensuring it centers over the bottom standpipe.",
                "required": True,
            },
            {
                "step_number": 4,
                "title": "Reassembly & Leak Check",
                "instruction": "Inspect bowl O-ring, screw housing firmly back in place, restore feed valve, and inspect for leaks under operating line pressure.",
                "required": True,
            },
        ],
    },
]

def get_all_guides() -> List[Dict[str, Any]]:
    return DEFAULT_GUIDES

def get_guide_by_id(guide_id: str) -> Optional[Dict[str, Any]]:
    for g in DEFAULT_GUIDES:
        if g["id"] == guide_id or g["filter_type"].lower() in guide_id.lower():
            return g
    return DEFAULT_GUIDES[0]
