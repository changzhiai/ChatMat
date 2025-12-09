#!/usr/bin/env python3
"""
Test XYZ output format to verify it's correct for visualization.
"""

import sys
import os
import io

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ase.io import write
from chatmat.build_structures import create_structure

# Generate SiO2 structure
print("Generating SiO2 structure...")
atoms = create_structure("SiO2", [1, 1, 1])

print(f"\nStructure has {len(atoms)} atoms")
print(f"Atom symbols: {atoms.get_chemical_symbols()}")

# Convert to XYZ
xyz_buffer = io.StringIO()
write(xyz_buffer, atoms, format="xyz")
xyz_string = xyz_buffer.getvalue()

print(f"\n{'='*60}")
print("XYZ Output:")
print(f"{'='*60}")
print(xyz_string)
print(f"{'='*60}")

# Parse and verify
xyz_lines = [line for line in xyz_string.strip().split('\n') if line.strip()]
print(f"\nXYZ Analysis:")
print(f"  Total lines: {len(xyz_lines)}")
print(f"  First line (atom count): '{xyz_lines[0]}'")
try:
    num_atoms = int(xyz_lines[0].strip())
    print(f"  Parsed atom count: {num_atoms}")
    print(f"  Expected: {len(atoms)}")
    if num_atoms == len(atoms):
        print(f"  ✅ Atom count matches!")
    else:
        print(f"  ❌ Atom count mismatch!")
    
    print(f"\n  Atom lines ({len(xyz_lines) - 2} found):")
    for i, line in enumerate(xyz_lines[2:2+num_atoms], 1):
        parts = line.split()
        if len(parts) >= 4:
            element = parts[0]
            print(f"    {i}. {element} at ({parts[1]}, {parts[2]}, {parts[3]})")
        else:
            print(f"    {i}. {line} (⚠️ malformed)")
            
except ValueError as e:
    print(f"  ❌ Could not parse atom count: {e}")

# Test what py3Dmol would see
print(f"\n{'='*60}")
print("What py3Dmol would receive:")
print(f"{'='*60}")
print(f"Length: {len(xyz_string)} characters")
print(f"First 200 chars:\n{xyz_string[:200]}")

