#!/usr/bin/env python3
"""
Quick test script to verify structure generation is working correctly.
Run this to debug structure generation issues.
"""

import sys
import os
import io
from ase.io import write

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from chatmat.build_structures import create_structure, create_quartz, COMPOUND_DATABASE
    from ase import Atoms
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the ChatMat directory and dependencies are installed.")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def test_structure(name, dims=[1,1,1], structure_type=None, compound=None):
    """Test structure generation and print results."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"  Supercell: {dims}")
    print(f"  Structure type: {structure_type}")
    print(f"  Compound: {compound}")
    print(f"{'='*60}")
    
    try:
        atoms = create_structure(
            name,
            dims,
            structure_type=structure_type,
            compound=compound
        )
        
        print(f"✅ Success!")
        print(f"   Number of atoms: {len(atoms)}")
        print(f"   Atom types: {set(atoms.get_chemical_symbols())}")
        print(f"   All atoms: {atoms.get_chemical_symbols()}")
        print(f"   Cell: {atoms.cell}")
        
        # Test XYZ output
        xyz_buffer = io.StringIO()
        write(xyz_buffer, atoms, format="xyz")
        xyz_string = xyz_buffer.getvalue()
        xyz_lines = xyz_string.strip().split('\n')
        
        print(f"\n📄 XYZ Output:")
        print(f"   First line (atom count): {xyz_lines[0]}")
        print(f"   Total lines: {len(xyz_lines)}")
        if len(xyz_lines) > 1:
            print(f"   Comment: {xyz_lines[1]}")
        if len(xyz_lines) > 2:
            print(f"   First atom: {xyz_lines[2]}")
        if len(xyz_lines) > 3:
            print(f"   Second atom: {xyz_lines[3]}")
        
        # Verify
        try:
            num_atoms_xyz = int(xyz_lines[0].strip())
            if num_atoms_xyz != len(atoms):
                print(f"⚠️  WARNING: XYZ count ({num_atoms_xyz}) != atoms count ({len(atoms)})")
            if num_atoms_xyz == 1:
                print(f"⚠️  WARNING: Only 1 atom in structure!")
        except ValueError:
            print(f"⚠️  WARNING: Could not parse atom count from XYZ")
        
        return atoms
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("🧪 ChatMat Structure Generation Test")
    print("="*60)
    
    # Test 1: Simple element
    print("\n📋 Test 1: Simple element (Si)")
    test_structure("Si", dims=[1,1,1])
    
    # Test 2: SiO2 by name
    print("\n📋 Test 2: SiO2 by name")
    test_structure("SiO2", dims=[1,1,1])
    
    # Test 3: SiO2 with compound
    print("\n📋 Test 3: SiO2 with compound parameter")
    test_structure("SiO2", dims=[1,1,1], compound=["Si", "O"])
    
    # Test 4: Direct quartz function
    print("\n📋 Test 4: Direct quartz function")
    try:
        from chatmat.build_structures import create_quartz
        atoms = create_quartz(["Si", "O"], 4.91, 5.40)
        print(f"✅ Quartz function: {len(atoms)} atoms")
        print(f"   Atom types: {set(atoms.get_chemical_symbols())}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Check database
    print("\n📋 Test 5: Check compound database")
    from chatmat.build_structures import COMPOUND_DATABASE
    if "sio2" in COMPOUND_DATABASE:
        data = COMPOUND_DATABASE["sio2"]
        print(f"✅ Found sio2 in database:")
        print(f"   Name: {data['name']}")
        print(f"   Structure: {data['structure']}")
        print(f"   Elements: {data['elements']}")
        print(f"   Lattice a: {data.get('a', 'N/A')}")
        print(f"   Lattice c: {data.get('c', 'N/A')}")
    else:
        print("❌ sio2 NOT found in database!")
    
    # Test 6: NaCl
    print("\n📋 Test 6: NaCl (rocksalt)")
    test_structure("NaCl", dims=[1,1,1], compound=["Na", "Cl"])
    
    print("\n" + "="*60)
    print("✅ Testing complete!")
    print("="*60)

if __name__ == "__main__":
    # Run specific test
    test_structure("SiO2", dims=[1,1,1])
    
    # Or run all tests:
    # main()

