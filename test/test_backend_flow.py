#!/usr/bin/env python3
"""
Test the backend API flow to see what's actually being sent/received.
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from chatmat.build_structures import create_structure

# Simulate what the frontend sends
def simulate_frontend_request(material_name, compound=None, structure_type=None):
    """Simulate the payload the frontend would send."""
    payload = {
        "intent": "CALCULATE",
        "material_name": material_name,
        "structure_details": {
            "supercell_dims": [1, 1, 1],
            "structure_type": structure_type,
            "compound": compound
        }
    }
    return payload

# Simulate what the backend does
def simulate_backend_processing(payload):
    """Simulate backend processing."""
    material_name = payload["material_name"]
    details = payload["structure_details"]
    
    print(f"📥 Backend received:")
    print(f"   Material: {material_name}")
    print(f"   Supercell: {details['supercell_dims']}")
    print(f"   Structure type: {details.get('structure_type')}")
    print(f"   Compound: {details.get('compound')}")
    
    # This is what backend does
    atoms = create_structure(
        material_name,
        details["supercell_dims"],
        structure_type=details.get("structure_type"),
        lattice_param=details.get("lattice_parameter"),
        compound=details.get("compound")
    )
    
    print(f"\n✅ Backend generated:")
    print(f"   Atoms: {len(atoms)}")
    print(f"   Types: {set(atoms.get_chemical_symbols())}")
    print(f"   All: {atoms.get_chemical_symbols()}")
    
    return atoms

# Test cases
print("="*60)
print("🧪 Testing Backend Flow")
print("="*60)

# Test 1: SiO2 without compound (should still work via name lookup)
print("\n📋 Test 1: SiO2 without compound parameter")
payload1 = simulate_frontend_request("SiO2")
atoms1 = simulate_backend_processing(payload1)

# Test 2: SiO2 with compound
print("\n📋 Test 2: SiO2 with compound parameter")
payload2 = simulate_frontend_request("SiO2", compound=["Si", "O"])
atoms2 = simulate_backend_processing(payload2)

# Test 3: What frontend actually sends (based on parser)
print("\n📋 Test 3: What frontend parser would send for 'SiO2'")
# Based on the parser, when user types "SiO2", it should:
# - Find in compound_map
# - Set material_name="SiO2"
# - Set compound=["Si", "O"]
# - Set structure_type="quartz"
payload3 = simulate_frontend_request("SiO2", compound=["Si", "O"], structure_type="quartz")
atoms3 = simulate_backend_processing(payload3)

print("\n" + "="*60)
print("✅ All tests complete!")
print("="*60)

