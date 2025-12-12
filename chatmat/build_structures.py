"""
Structure building module for ChatMat.

This module contains functions and databases for generating crystal structures
using the Atomic Simulation Environment (ASE). It also supports fetching structures
from external databases like Materials Project, COD, and loading from files.
It also supports LLM-based structure generation from natural language descriptions.
"""

import io
import os
import json
import re
import numpy as np
from typing import List, Optional, Dict, Union, Any

# Optional FastAPI import (only needed when used as API backend)
try:
    from fastapi import HTTPException
except ImportError:
    # Fallback for when fastapi is not installed (e.g., during testing)
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = ""):
            self.status_code = status_code
            self.detail = detail if detail else f"HTTP {status_code} error"
            super().__init__(f"{status_code}: {self.detail}")

# --- ASE Imports for Structure Generation ---
from ase.build import bulk
from ase import Atoms
from ase.spacegroup import crystal
from ase.io import read, write

# --- Material Database: Common crystal structures and lattice parameters ---
MATERIAL_DATABASE: Dict[str, Dict[str, any]] = {
    # Elements - FCC
    "al": {"structure": "fcc", "a": 4.05, "name": "Aluminum"},
    "ag": {"structure": "fcc", "a": 4.09, "name": "Silver"},
    "au": {"structure": "fcc", "a": 4.08, "name": "Gold"},
    "cu": {"structure": "fcc", "a": 3.61, "name": "Copper"},
    "ni": {"structure": "fcc", "a": 3.52, "name": "Nickel"},
    "pd": {"structure": "fcc", "a": 3.89, "name": "Palladium"},
    "pt": {"structure": "fcc", "a": 3.92, "name": "Platinum"},
    
    # Elements - BCC
    "fe": {"structure": "bcc", "a": 2.87, "name": "Iron"},
    "cr": {"structure": "bcc", "a": 2.88, "name": "Chromium"},
    "mo": {"structure": "bcc", "a": 3.15, "name": "Molybdenum"},
    "w": {"structure": "bcc", "a": 3.16, "name": "Tungsten"},
    "v": {"structure": "bcc", "a": 3.02, "name": "Vanadium"},
    "nb": {"structure": "bcc", "a": 3.30, "name": "Niobium"},
    "ta": {"structure": "bcc", "a": 3.31, "name": "Tantalum"},
    
    # Elements - HCP
    "mg": {"structure": "hcp", "a": 3.21, "c": 5.21, "name": "Magnesium"},
    "ti": {"structure": "hcp", "a": 2.95, "c": 4.68, "name": "Titanium"},
    "zn": {"structure": "hcp", "a": 2.66, "c": 4.95, "name": "Zinc"},
    "co": {"structure": "hcp", "a": 2.51, "c": 4.07, "name": "Cobalt"},
    "zr": {"structure": "hcp", "a": 3.23, "c": 5.15, "name": "Zirconium"},
    "be": {"structure": "hcp", "a": 2.29, "c": 3.58, "name": "Beryllium"},
    
    # Elements - Diamond
    "si": {"structure": "diamond", "a": 5.43, "name": "Silicon"},
    "ge": {"structure": "diamond", "a": 5.66, "name": "Germanium"},
    "c": {"structure": "diamond", "a": 3.57, "name": "Carbon (Diamond)"},
    "sn": {"structure": "diamond", "a": 6.49, "name": "Tin"},
    
    # Elements - Simple Cubic (rare)
    "po": {"structure": "sc", "a": 3.35, "name": "Polonium"},
}

# Compound database
COMPOUND_DATABASE: Dict[str, Dict[str, any]] = {
    # Rocksalt (NaCl structure)
    "nacl": {"structure": "rocksalt", "elements": ["Na", "Cl"], "a": 5.64, "name": "Sodium Chloride"},
    "mgo": {"structure": "rocksalt", "elements": ["Mg", "O"], "a": 4.21, "name": "Magnesium Oxide"},
    "lif": {"structure": "rocksalt", "elements": ["Li", "F"], "a": 4.03, "name": "Lithium Fluoride"},
    
    # Zincblende (ZnS structure)
    "zns": {"structure": "zincblende", "elements": ["Zn", "S"], "a": 5.41, "name": "Zinc Sulfide"},
    "gan": {"structure": "zincblende", "elements": ["Ga", "N"], "a": 4.52, "name": "Gallium Nitride"},
    "gap": {"structure": "zincblende", "elements": ["Ga", "P"], "a": 5.45, "name": "Gallium Phosphide"},
    "inas": {"structure": "zincblende", "elements": ["In", "As"], "a": 6.06, "name": "Indium Arsenide"},
    "cdte": {"structure": "zincblende", "elements": ["Cd", "Te"], "a": 6.48, "name": "Cadmium Telluride"},
    
    # Wurtzite (ZnS wurtzite structure)
    "zns_w": {"structure": "wurtzite", "elements": ["Zn", "S"], "a": 3.82, "c": 6.26, "name": "Zinc Sulfide (Wurtzite)"},
    
    # Perovskite (CaTiO3 structure)
    "catio3": {"structure": "perovskite", "elements": ["Ca", "Ti", "O"], "a": 3.84, "name": "Calcium Titanate"},
    "batio3": {"structure": "perovskite", "elements": ["Ba", "Ti", "O"], "a": 4.00, "name": "Barium Titanate"},
    
    # Rutile (TiO2 structure)
    "tio2": {"structure": "rutile", "elements": ["Ti", "O"], "a": 4.59, "c": 2.96, "name": "Titanium Dioxide"},
    
    # Quartz (SiO2 alpha-quartz structure - most common form)
    "sio2": {"structure": "quartz", "elements": ["Si", "O"], "a": 4.91, "c": 5.40, "name": "Silicon Dioxide (Quartz)"},
    "sio2_quartz": {"structure": "quartz", "elements": ["Si", "O"], "a": 4.91, "c": 5.40, "name": "Silicon Dioxide (Quartz)"},
    "sio2_cristobalite": {"structure": "cristobalite", "elements": ["Si", "O"], "a": 7.16, "name": "Silicon Dioxide (Cristobalite)"},
}


def create_rocksalt(elements: List[str], a: float) -> Atoms:
    """Create rocksalt (NaCl) structure using crystal() with spacegroup."""
    if len(elements) < 2:
        raise ValueError(f"Rocksalt structure requires 2 elements, got {len(elements)}")
    
    try:
        # Rocksalt: spacegroup 225 (Fm-3m)
        atoms = crystal(elements, 
                      basis=[(0, 0, 0), (0.5, 0.5, 0.5)],
                      spacegroup=225,
                      cellpar=[a, a, a, 90, 90, 90],
                      size=(1, 1, 1))
        # Verify we got a proper structure
        if len(atoms) > 0:
            return atoms
    except Exception as e:
        print(f"⚠️ Warning: crystal() failed for rocksalt: {e}, using fallback")
    
    # Fallback: create proper rocksalt structure manually
    # Rocksalt has 8 atoms per conventional cell (4 of each element)
    positions = [
        # Element 1 (e.g., Na)
        [0, 0, 0],
        [a/2, a/2, 0],
        [a/2, 0, a/2],
        [0, a/2, a/2],
        # Element 2 (e.g., Cl)
        [a/2, a/2, a/2],
        [0, 0, a/2],
        [0, a/2, 0],
        [a/2, 0, 0],
    ]
    symbols = [elements[0], elements[0], elements[0], elements[0],
              elements[1], elements[1], elements[1], elements[1]]
    return Atoms(symbols, positions=positions, cell=[a, a, a])


def create_zincblende(elements: List[str], a: float) -> Atoms:
    """Create zincblende (ZnS) structure."""
    if len(elements) < 2:
        raise ValueError(f"Zincblende structure requires 2 elements, got {len(elements)}")
    
    try:
        # Zincblende: spacegroup 216 (F-43m)
        atoms = crystal(elements,
                      basis=[(0, 0, 0), (0.25, 0.25, 0.25)],
                      spacegroup=216,
                      cellpar=[a, a, a, 90, 90, 90],
                      size=(1, 1, 1))
        # Verify we got a proper structure
        if len(atoms) > 0:
            return atoms
    except Exception as e:
        print(f"⚠️ Warning: crystal() failed for zincblende: {e}, using fallback")
    
    # Fallback: create proper zincblende structure manually
    # Zincblende has 2 atoms per primitive cell, 8 atoms per conventional cell
    positions = [
        [0, 0, 0],  # Element 1 at origin
        [a/4, a/4, a/4],  # Element 2 at (1/4, 1/4, 1/4)
        # Add more atoms for conventional cell
        [a/2, a/2, 0],  # Element 1
        [3*a/4, 3*a/4, a/4],  # Element 2
        [a/2, 0, a/2],  # Element 1
        [3*a/4, a/4, 3*a/4],  # Element 2
        [0, a/2, a/2],  # Element 1
        [a/4, 3*a/4, 3*a/4],  # Element 2
    ]
    symbols = [elements[0], elements[1], elements[0], elements[1], 
              elements[0], elements[1], elements[0], elements[1]]
    return Atoms(symbols, positions=positions, cell=[a, a, a])


def create_wurtzite(elements: List[str], a: float, c: float) -> Atoms:
    """Create wurtzite structure."""
    if len(elements) < 2:
        raise ValueError(f"Wurtzite structure requires 2 elements, got {len(elements)}")
    
    try:
        # Wurtzite: spacegroup 186 (P63mc)
        atoms = crystal(elements,
                      basis=[(0, 0, 0), (1/3, 2/3, 0.375)],
                      spacegroup=186,
                      cellpar=[a, a, c, 90, 90, 120],
                      size=(1, 1, 1))
        # Verify we got a proper structure
        if len(atoms) > 0:
            return atoms
    except Exception as e:
        print(f"⚠️ Warning: crystal() failed for wurtzite: {e}, using fallback")
    
    # Fallback: create proper wurtzite structure manually
    # Wurtzite has 4 atoms per unit cell (2 of each element)
    positions = [
        [0, 0, 0],  # Element 1
        [a/3, 2*a/3, c*0.375],  # Element 2
        [a/2, a*np.sqrt(3)/6, c/2],  # Element 1
        [5*a/6, a*np.sqrt(3)/2, c*0.875],  # Element 2
    ]
    symbols = [elements[0], elements[1], elements[0], elements[1]]
    cell = [[a, 0, 0], [-a/2, a*np.sqrt(3)/2, 0], [0, 0, c]]
    return Atoms(symbols, positions=positions, cell=cell)


def create_perovskite(elements: List[str], a: float) -> Atoms:
    """Create perovskite (ABO3) structure - simplified version."""
    # Perovskite has A, B, and 3 O atoms per unit cell
    if len(elements) < 3:
        # If we don't have enough elements, create a simple structure
        # A at corners, B at center, O at face centers
        positions = [
            [0, 0, 0],  # A
            [a/2, a/2, a/2],  # B
            [a/2, a/2, 0],  # O1
            [a/2, 0, a/2],  # O2
            [0, a/2, a/2],  # O3
        ]
        symbols = [elements[0] if len(elements) > 0 else "A",
                  elements[1] if len(elements) > 1 else "B",
                  elements[2] if len(elements) > 2 else "O",
                  elements[2] if len(elements) > 2 else "O",
                  elements[2] if len(elements) > 2 else "O"]
        return Atoms(symbols, positions=positions, cell=[a, a, a])
    else:
        # Proper perovskite: A, B, and 3 O
        positions = [
            [0, 0, 0],  # A
            [a/2, a/2, a/2],  # B
            [a/2, a/2, 0],  # O1
            [a/2, 0, a/2],  # O2
            [0, a/2, a/2],  # O3
        ]
        symbols = [elements[0], elements[1], elements[2], elements[2], elements[2]]
        return Atoms(symbols, positions=positions, cell=[a, a, a])


def create_rutile(elements: List[str], a: float, c: float) -> Atoms:
    """Create rutile (TiO2) structure - simplified version."""
    # Rutile structure: 2 Ti and 4 O atoms per unit cell
    if len(elements) < 2:
        raise ValueError(f"Rutile structure requires 2 elements, got {len(elements)}")
    
    ti_element = elements[0]  # Should be "Ti"
    o_element = elements[1]   # Should be "O"
    
    # Simplified rutile structure with proper Ti:O = 1:2 ratio
    # 2 Ti atoms and 4 O atoms
    positions = [
        # Ti atoms
        [0, 0, 0],  # Ti1
        [a/2, a/2, c/2],  # Ti2
        # O atoms
        [0.31*a, 0.31*a, 0],  # O1
        [0.69*a, 0.69*a, 0],  # O2
        [0.31*a, 0.31*a, c],  # O3
        [0.69*a, 0.69*a, c],  # O4
    ]
    symbols = [ti_element, ti_element, o_element, o_element, o_element, o_element]
    return Atoms(symbols, positions=positions, cell=[a, a, c])


def create_quartz(elements: List[str], a: float, c: float) -> Atoms:
    """Create quartz (alpha-SiO2) structure - hexagonal."""
    # Ensure we have both elements
    if len(elements) < 2:
        raise ValueError(f"Quartz structure requires 2 elements, got {len(elements)}")
    
    si_element = elements[0]  # Should be "Si"
    o_element = elements[1]   # Should be "O"
    
    # Create a simplified quartz structure with proper Si:O = 1:2 ratio
    # Using a minimal unit cell with 1 Si and 2 O atoms
    try:
        positions = [
            [0, 0, 0],  # Si at origin
            [a/3, a*np.sqrt(3)/3, c/3],  # O1
            [2*a/3, 2*a*np.sqrt(3)/3, 2*c/3],  # O2
        ]
        symbols = [si_element, o_element, o_element]
        
        # Create hexagonal cell
        cell = [[a, 0, 0], [-a/2, a*np.sqrt(3)/2, 0], [0, 0, c]]
        atoms = Atoms(symbols, positions=positions, cell=cell)
        
        # Verify the structure
        if len(atoms) != 3:
            raise ValueError(f"Expected 3 atoms, got {len(atoms)}")
        if set(atoms.get_chemical_symbols()) != {si_element, o_element}:
            raise ValueError(f"Structure contains wrong elements: {set(atoms.get_chemical_symbols())}")
        
        return atoms
        
    except Exception as e:
        # Fallback: create a very simple structure but ensure correct elements
        print(f"⚠️ Warning: Quartz creation had issue: {e}, using fallback")
        positions = [
            [0, 0, 0],  # Si
            [a/4, a*np.sqrt(3)/4, c/4],  # O
            [a/2, a*np.sqrt(3)/2, c/2],  # O
        ]
        symbols = [si_element, o_element, o_element]
        cell = [[a, 0, 0], [-a/2, a*np.sqrt(3)/2, 0], [0, 0, c]]
        return Atoms(symbols, positions=positions, cell=cell)


def create_cristobalite(elements: List[str], a: float) -> Atoms:
    """Create cristobalite (SiO2) structure - cubic."""
    # Cristobalite: spacegroup 227 (Fd-3m) - simplified cubic structure
    # For SiO2, create structure with proper Si:O = 1:2 ratio
    if len(elements) < 2:
        raise ValueError(f"Cristobalite structure requires 2 elements, got {len(elements)}")
    
    si_element = elements[0]  # Should be "Si"
    o_element = elements[1]    # Should be "O"
    
    # Simplified cristobalite: 2 Si and 4 O atoms per unit cell
    positions = [
        # Si atoms
        [0, 0, 0],  # Si1
        [a/4, a/4, a/4],  # Si2
        # O atoms
        [a/8, a/8, a/8],  # O1
        [3*a/8, 3*a/8, 3*a/8],  # O2
        [a/2, a/4, a/4],  # O3
        [a/4, a/2, a/4],  # O4
    ]
    symbols = [si_element, si_element, o_element, o_element, o_element, o_element]
    return Atoms(symbols, positions=positions, cell=[a, a, a])


def create_structure(name: str, dims: List[int], structure_type: Optional[str] = None, 
                    lattice_param: Optional[float] = None, compound: Optional[List[str]] = None) -> Atoms:
    """
    Enhanced structure generator supporting many materials and crystal structures.
    
    Args:
        name: Material name (element symbol or compound name)
        dims: Supercell dimensions [nx, ny, nz]
        structure_type: Optional crystal structure type (fcc, bcc, hcp, diamond, etc.)
        lattice_param: Optional custom lattice parameter
        compound: Optional list of element symbols for compounds
        
    Returns:
        Atoms object representing the crystal structure
        
    Raises:
        HTTPException: If structure cannot be generated
    """
    name_lower = name.lower().strip()
    
    # First, check if the name itself is in the compound database (e.g., "sio2", "tio2")
    if name_lower in COMPOUND_DATABASE:
        data = COMPOUND_DATABASE[name_lower]
        struct_type = structure_type or data["structure"]
        a = lattice_param or data.get("a", 5.0)
        
        print(f"🔍 Found {name_lower} in compound database: {data['name']}, structure={struct_type}, elements={data['elements']}")
        
        try:
            if struct_type == "rocksalt":
                atoms = create_rocksalt(data["elements"], a)
            elif struct_type == "zincblende":
                atoms = create_zincblende(data["elements"], a)
            elif struct_type == "wurtzite":
                c = data.get("c", a * 1.63)
                atoms = create_wurtzite(data["elements"], a, c)
            elif struct_type == "perovskite":
                atoms = create_perovskite(data["elements"], a)
            elif struct_type == "rutile":
                c = data.get("c", a * 0.64)
                atoms = create_rutile(data["elements"], a, c)
            elif struct_type == "quartz":
                c = data.get("c", a * 1.10) if "c" in data else a * 1.10
                atoms = create_quartz(data["elements"], a, c)
            elif struct_type == "cristobalite":
                atoms = create_cristobalite(data["elements"], a)
            else:
                atoms = create_zincblende(data["elements"], a)
            
            print(f"✅ Generated structure with {len(atoms)} atoms: {set(atoms.get_chemical_symbols())}")
            print(f"   Atom symbols: {atoms.get_chemical_symbols()}")
            
            # Verify structure has multiple atoms
            if len(atoms) < 2:
                raise ValueError(f"Structure has only {len(atoms)} atom(s), expected multiple atoms")
            
            atoms = atoms * tuple(dims)
            print(f"✅ After supercell {dims}: {len(atoms)} atoms")
            return atoms
            
        except Exception as e:
            print(f"❌ Error creating {struct_type} structure: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create {struct_type} structure for {name_lower}: {str(e)}"
            )
    
    # Check if it's a compound
    if compound and len(compound) >= 2:
        compound_key = "".join(sorted([e.lower() for e in compound]))
        # Also create a direct compound name (e.g., "sio" from ["Si", "O"])
        compound_name = "".join([e.lower() for e in compound])
        # For binary compounds, try common patterns: "sio2", "tio2", etc.
        compound_name_with_num = None
        if len(compound) == 2:
            compound_name_with_num = f"{compound[0].lower()}{compound[1].lower()}2"
        
        # Try to find in compound database
        for key, data in COMPOUND_DATABASE.items():
            # Check multiple matching strategies
            matches = (compound_key in key or 
                      all(e.lower() in key for e in compound) or
                      compound_name in key or
                      name_lower in key)
            
            # For binary compounds, also check with number suffix
            if compound_name_with_num:
                matches = matches or compound_name_with_num in key
            
            if matches:
                struct_type = structure_type or data["structure"]
                a = lattice_param or data.get("a", 5.0)
                
                if struct_type == "rocksalt":
                    atoms = create_rocksalt(data["elements"], a)
                elif struct_type == "zincblende":
                    atoms = create_zincblende(data["elements"], a)
                elif struct_type == "wurtzite":
                    c = data.get("c", a * 1.63)
                    atoms = create_wurtzite(data["elements"], a, c)
                elif struct_type == "perovskite":
                    atoms = create_perovskite(data["elements"], a)
                elif struct_type == "rutile":
                    c = data.get("c", a * 0.64)
                    atoms = create_rutile(data["elements"], a, c)
                elif struct_type == "quartz":
                    c = data.get("c", a * 1.10)  # Default c/a ratio for quartz
                    atoms = create_quartz(data["elements"], a, c)
                elif struct_type == "cristobalite":
                    atoms = create_cristobalite(data["elements"], a)
                else:
                    # Default to zincblende for binary compounds
                    atoms = create_zincblende(data["elements"], a)
                
                atoms = atoms * tuple(dims)
                return atoms
        
        # If not found, try to create a simple binary structure
        try:
            atoms = bulk(compound[0], "fcc", a=lattice_param or 4.0)
            atoms = atoms * tuple(dims)
            return atoms
        except:
            pass
    
    # Check element database
    if name_lower in MATERIAL_DATABASE:
        data = MATERIAL_DATABASE[name_lower]
        struct_type = structure_type or data["structure"]
        a = lattice_param or data["a"]
        
        # Capitalize element symbol for ASE (e.g., "au" -> "Au")
        element_symbol = name_lower.capitalize() if len(name_lower) <= 2 else name_lower
        
        # Use cubic=True to get conventional cell with multiple atoms instead of primitive cell
        if struct_type == "hcp":
            c = data.get("c", a * 1.633)  # Default c/a ratio
            atoms = bulk(element_symbol, "hcp", a=a, c=c, cubic=False)
        elif struct_type == "diamond":
            atoms = bulk(element_symbol, "diamond", a=a, cubic=True)
        elif struct_type == "bcc":
            atoms = bulk(element_symbol, "bcc", a=a, cubic=True)
        elif struct_type == "fcc":
            atoms = bulk(element_symbol, "fcc", a=a, cubic=True)
        elif struct_type == "sc":
            atoms = bulk(element_symbol, "sc", a=a, cubic=True)
        else:
            # Default based on database - use cubic=True for cubic structures
            if data["structure"] in ["fcc", "bcc", "sc", "diamond"]:
                atoms = bulk(element_symbol, data["structure"], a=a, cubic=True)
            else:
                atoms = bulk(element_symbol, data["structure"], a=a)
    else:
        # Try to guess structure type or use default
        struct_type = structure_type or "fcc"
        a = lattice_param or 4.0
        
        # Capitalize element symbol for ASE
        element_symbol = name_lower.capitalize() if len(name_lower) <= 2 else name_lower
        
        try:
            if struct_type == "hcp":
                atoms = bulk(element_symbol, "hcp", a=a, c=a*1.633, cubic=False)
            elif struct_type == "diamond":
                atoms = bulk(element_symbol, "diamond", a=a, cubic=True)
            elif struct_type == "bcc":
                atoms = bulk(element_symbol, "bcc", a=a, cubic=True)
            elif struct_type == "sc":
                atoms = bulk(element_symbol, "sc", a=a, cubic=True)
            else:
                atoms = bulk(element_symbol, "fcc", a=a, cubic=True)
        except Exception as e:
            # Last resort: try with default parameters
            try:
                atoms = bulk(element_symbol, "fcc", a=4.0)
            except Exception as e2:
                raise HTTPException(status_code=400, 
                    detail=f"Could not generate structure for '{name}'. Error: {str(e2)}. Please specify a valid element or compound.")
    
    # Apply Supercell
    atoms = atoms * tuple(dims)
    return atoms


# ============================================================================
# External Structure Fetching Functions
# ============================================================================

def fetch_from_materials_project(material_id: str, api_key: Optional[str] = None) -> Atoms:
    """
    Fetch structure from Materials Project database.
    
    Args:
        material_id: Materials Project ID (e.g., "mp-149", "mp-1234")
        api_key: Optional API key. If not provided, checks MP_API_KEY environment variable.
        
    Returns:
        Atoms object from Materials Project
        
    Raises:
        HTTPException: If structure cannot be fetched
    """
    try:
        from mp_api.client import MPRester
        
        api_key = api_key or os.getenv("MP_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Materials Project API key required. Set MP_API_KEY environment variable or provide api_key parameter."
            )
        
        with MPRester(api_key) as mpr:
            structure = mpr.get_structure_by_material_id(material_id)
            # Convert pymatgen Structure to ASE Atoms
            from pymatgen.io.ase import AseAtomsAdaptor
            adaptor = AseAtomsAdaptor()
            atoms = adaptor.get_atoms(structure)
            return atoms
            
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="mp-api package not installed. Install with: pip install mp-api pymatgen"
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch structure '{material_id}' from Materials Project: {str(e)}"
        )


def fetch_from_cod(cod_id: Union[str, int]) -> Atoms:
    """
    Fetch structure from Crystallography Open Database (COD).
    
    Args:
        cod_id: COD entry ID (e.g., "2000001" or 2000001)
        
    Returns:
        Atoms object from COD
        
    Raises:
        HTTPException: If structure cannot be fetched
    """
    try:
        import requests
        
        cod_id_str = str(cod_id).zfill(9)  # COD IDs are 9 digits
        url = f"http://www.crystallography.net/cod/{cod_id_str}.cif"
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise HTTPException(
                status_code=404,
                detail=f"COD entry {cod_id} not found. Check if the ID is correct."
            )
        
        # Read CIF from string
        cif_string = response.text
        atoms = read(io.StringIO(cif_string), format="cif")
        return atoms
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="requests package not installed. Install with: pip install requests"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching structure from COD: {str(e)}"
        )


def fetch_from_icsd(icsd_id: Union[str, int], username: Optional[str] = None, 
                    password: Optional[str] = None) -> Atoms:
    """
    Fetch structure from ICSD (Inorganic Crystal Structure Database).
    Note: ICSD requires a paid subscription and credentials.
    
    Args:
        icsd_id: ICSD collection code
        username: ICSD username
        password: ICSD password
        
    Returns:
        Atoms object from ICSD
        
    Raises:
        HTTPException: If structure cannot be fetched
    """
    try:
        from pymatgen.ext.icsd import ICSSD
        
        username = username or os.getenv("ICSD_USERNAME")
        password = password or os.getenv("ICSD_PASSWORD")
        
        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="ICSD credentials required. Set ICSD_USERNAME and ICSD_PASSWORD environment variables."
            )
        
        icsd = ICSSD(username, password)
        structure = icsd.get_structure(icsd_id)
        
        # Convert pymatgen Structure to ASE Atoms
        from pymatgen.io.ase import AseAtomsAdaptor
        adaptor = AseAtomsAdaptor()
        atoms = adaptor.get_atoms(structure)
        return atoms
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="pymatgen package not installed. Install with: pip install pymatgen"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching structure from ICSD: {str(e)}"
        )


def load_structure_from_file(file_path: str, format: Optional[str] = None) -> Atoms:
    """
    Load structure from a file.
    
    Supported formats: CIF, POSCAR, XYZ, VASP, etc. (ASE auto-detects format)
    
    Args:
        file_path: Path to structure file
        format: Optional format specification (e.g., "cif", "vasp", "xyz")
                 If None, ASE will auto-detect from file extension
        
    Returns:
        Atoms object loaded from file
        
    Raises:
        HTTPException: If file cannot be loaded
    """
    try:
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {file_path}"
            )
        
        if format:
            atoms = read(file_path, format=format)
        else:
            atoms = read(file_path)  # Auto-detect format
        
        if atoms is None:
            raise HTTPException(
                status_code=400,
                detail=f"Could not parse structure from file: {file_path}"
            )
        
        return atoms
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading structure from file: {str(e)}"
        )


def load_structure_from_string(content: str, format: str) -> Atoms:
    """
    Load structure from a string (e.g., CIF content, POSCAR content).
    
    Args:
        content: String containing structure data
        format: Format of the structure data (e.g., "cif", "vasp", "xyz")
        
    Returns:
        Atoms object loaded from string
        
    Raises:
        HTTPException: If structure cannot be loaded
    """
    try:
        atoms = read(io.StringIO(content), format=format)
        if atoms is None:
            raise HTTPException(
                status_code=400,
                detail=f"Could not parse structure from string (format: {format})"
            )
        return atoms
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading structure from string: {str(e)}"
        )


def fetch_structure_from_url(url: str, format: Optional[str] = None) -> Atoms:
    """
    Fetch structure from a URL (e.g., direct link to CIF file).
    
    Args:
        url: URL to structure file
        format: Optional format specification. If None, tries to detect from URL or content
        
    Returns:
        Atoms object fetched from URL
        
    Raises:
        HTTPException: If structure cannot be fetched
    """
    try:
        import requests
        
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch structure from URL: {url}"
            )
        
        content = response.text
        
        # Try to detect format from URL extension if not specified
        if not format:
            if url.endswith('.cif'):
                format = 'cif'
            elif url.endswith('.xyz'):
                format = 'xyz'
            elif 'poscar' in url.lower() or url.endswith('.vasp'):
                format = 'vasp'
            else:
                format = 'cif'  # Default to CIF
        
        atoms = read(io.StringIO(content), format=format)
        if atoms is None:
            raise HTTPException(
                status_code=400,
                detail=f"Could not parse structure from URL (format: {format})"
            )
        return atoms
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="requests package not installed. Install with: pip install requests"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching structure from URL: {str(e)}"
        )


def get_structure(source: str, source_type: str = "auto", **kwargs) -> Atoms:
    """
    Universal function to get structure from various sources.
    
    Args:
        source: Source identifier (material_id, cod_id, file_path, URL, etc.)
        source_type: Type of source. Options:
            - "auto": Try to auto-detect source type
            - "mp": Materials Project (requires material_id like "mp-149")
            - "cod": Crystallography Open Database (requires cod_id)
            - "icsd": ICSD database (requires icsd_id and credentials)
            - "file": Local file path
            - "url": URL to structure file
            - "string": Structure data as string (requires format parameter)
        **kwargs: Additional parameters:
            - For "mp": api_key (optional)
            - For "icsd": username, password (optional, can use env vars)
            - For "file": format (optional)
            - For "url": format (optional)
            - For "string": format (required), content (required)
            - dims: Supercell dimensions to apply [nx, ny, nz] (optional)
        
    Returns:
        Atoms object
        
    Raises:
        HTTPException: If structure cannot be fetched/generated
    """
    # Auto-detect source type
    if source_type == "auto":
        if source.startswith("mp-"):
            source_type = "mp"
        elif source.startswith("http://") or source.startswith("https://"):
            source_type = "url"
        elif os.path.exists(source):
            source_type = "file"
        elif source.isdigit() or (source.startswith("cod-") and source[4:].isdigit()):
            source_type = "cod"
            if source.startswith("cod-"):
                source = source[4:]
        else:
            # Try to use built-in create_structure
            try:
                dims = kwargs.get("dims", [1, 1, 1])
                structure_type = kwargs.get("structure_type")
                lattice_param = kwargs.get("lattice_param")
                compound = kwargs.get("compound")
                return create_structure(source, dims, structure_type, lattice_param, compound)
            except:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not auto-detect source type for '{source}'. Please specify source_type."
                )
    
    # Fetch based on source type
    if source_type == "mp":
        atoms = fetch_from_materials_project(source, kwargs.get("api_key"))
    elif source_type == "cod":
        atoms = fetch_from_cod(source)
    elif source_type == "icsd":
        atoms = fetch_from_icsd(source, kwargs.get("username"), kwargs.get("password"))
    elif source_type == "file":
        atoms = load_structure_from_file(source, kwargs.get("format"))
    elif source_type == "url":
        atoms = fetch_structure_from_url(source, kwargs.get("format"))
    elif source_type == "string":
        if "content" not in kwargs or "format" not in kwargs:
            raise HTTPException(
                status_code=400,
                detail="For 'string' source_type, both 'content' and 'format' parameters are required."
            )
        atoms = load_structure_from_string(kwargs["content"], kwargs["format"])
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source_type: {source_type}. Valid options: mp, cod, icsd, file, url, string, auto"
        )
    
    # Apply supercell if specified
    if "dims" in kwargs:
        dims = kwargs["dims"]
        if isinstance(dims, list) and len(dims) == 3:
            atoms = atoms * tuple(dims)
    
    return atoms


# ============================================================================
# LLM-Based Structure Generation
# ============================================================================

def parse_llm_structure_response(llm_response: str) -> Dict[str, Any]:
    """
    Parse LLM response to extract structure parameters.
    
    Expected JSON format:
    {
        "material_name": "Si",
        "structure_type": "diamond",
        "lattice_parameter": 5.43,
        "supercell_dims": [2, 2, 2],
        "compound": null
    }
    
    Args:
        llm_response: LLM response text (may contain JSON or natural language)
        
    Returns:
        Dictionary with structure parameters
    """
    # Try to extract JSON from the response
    json_match = re.search(r'\{[^{}]*\}', llm_response, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            # Validate and set defaults
            result = {
                "material_name": parsed.get("material_name", "Si"),
                "structure_type": parsed.get("structure_type"),
                "lattice_parameter": parsed.get("lattice_parameter"),
                "supercell_dims": parsed.get("supercell_dims", [1, 1, 1]),
                "compound": parsed.get("compound")
            }
            return result
        except json.JSONDecodeError:
            pass
    
    # Fallback: try to extract information using regex patterns
    result = {
        "material_name": "Si",
        "structure_type": None,
        "lattice_parameter": None,
        "supercell_dims": [1, 1, 1],
        "compound": None
    }
    
    # Extract material name
    element_pattern = r'\b([A-Z][a-z]?)\b'
    elements = re.findall(element_pattern, llm_response)
    if elements:
        # Filter out common words
        common_words = {"The", "For", "Get", "Calculate", "Energy", "Force", "Structure"}
        valid_elements = [e for e in elements if e not in common_words]
        if valid_elements:
            result["material_name"] = valid_elements[0]
    
    # Extract structure type
    structure_keywords = {
        "fcc": ["fcc", "face-centered cubic", "face centered cubic"],
        "bcc": ["bcc", "body-centered cubic", "body centered cubic"],
        "hcp": ["hcp", "hexagonal close-packed"],
        "diamond": ["diamond", "diamond cubic"],
        "zincblende": ["zincblende", "zinc blende"],
        "rocksalt": ["rocksalt", "rock salt", "nacl structure"]
    }
    
    text_lower = llm_response.lower()
    for struct_type, keywords in structure_keywords.items():
        if any(kw in text_lower for kw in keywords):
            result["structure_type"] = struct_type
            break
    
    # Extract lattice parameter
    lattice_match = re.search(r'[al]\s*[=:]\s*([\d.]+)', text_lower)
    if lattice_match:
        result["lattice_parameter"] = float(lattice_match.group(1))
    
    # Extract supercell
    supercell_match = re.search(r'(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)', text_lower)
    if supercell_match:
        result["supercell_dims"] = [
            int(supercell_match.group(1)),
            int(supercell_match.group(2)),
            int(supercell_match.group(3))
        ]
    
    return result


def generate_structure_with_openai(description: str, api_key: Optional[str] = None, 
                                   model: str = "gpt-4o-mini") -> Atoms:
    """
    Generate structure using OpenAI's ChatGPT.
    
    Args:
        description: Natural language description of the structure
        api_key: OpenAI API key (or use OPENAI_API_KEY env var)
        model: Model to use (gpt-4, gpt-4o-mini, gpt-3.5-turbo, etc.)
        
    Returns:
        Atoms object
        
    Raises:
        HTTPException: If structure cannot be generated
    """
    try:
        from openai import OpenAI
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key required. Set OPENAI_API_KEY environment variable or provide api_key parameter."
            )
        
        client = OpenAI(api_key=api_key)
        
        # Create a prompt for structure generation
        system_prompt = """You are a materials science expert. Given a description of a crystal structure, 
extract the following information and return it as JSON:
- material_name: Element symbol or compound name (e.g., "Si", "NaCl", "GaN", "MoS2", "Graphene")
- structure_type: Crystal structure type (fcc, bcc, hcp, diamond, zincblende, rocksalt, wurtzite, perovskite, rutile, quartz, cristobalite, layered, 2d) or null
- lattice_parameter: Lattice parameter in Angstroms (float) or null. For 2D materials, this is the in-plane lattice parameter.
- supercell_dims: Supercell dimensions as [nx, ny, nz] (default: [1, 1, 1])
- compound: List of element symbols for compounds (e.g., ["Na", "Cl"], ["Mo", "S"], ["C"]) or null for elements

For complex structures, extract as much information as possible. If the structure description is too complex, 
suggest the closest simple structure that can be generated. For layered/2D materials, use structure_type "layered" or "2d".

Return ONLY valid JSON, no additional text."""

        user_prompt = f"Extract structure parameters from this description: {description}"
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for more deterministic output
            response_format={"type": "json_object"} if "gpt-4" in model or "gpt-3.5-turbo" in model else None
        )
        
        llm_response = response.choices[0].message.content
        
        # Parse the response
        params = parse_llm_structure_response(llm_response)
        
        # Generate structure
        atoms = create_structure(
            params["material_name"],
            params["supercell_dims"],
            structure_type=params["structure_type"],
            lattice_param=params["lattice_parameter"],
            compound=params["compound"]
        )
        
        return atoms
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openai package not installed. Install with: pip install openai"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating structure with OpenAI: {str(e)}"
        )


def generate_structure_with_anthropic(description: str, api_key: Optional[str] = None,
                                      model: str = "claude-3-haiku-20240307") -> Atoms:
    """
    Generate structure using Anthropic's Claude.
    
    Args:
        description: Natural language description of the structure
        api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
        model: Model to use (claude-3-opus, claude-3-sonnet, claude-3-haiku, etc.)
        
    Returns:
        Atoms object
        
    Raises:
        HTTPException: If structure cannot be generated
    """
    try:
        from anthropic import Anthropic
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or provide api_key parameter."
            )
        
        client = Anthropic(api_key=api_key)
        
        system_prompt = """You are a materials science expert. Given a description of a crystal structure, 
extract the following information and return it as JSON:
- material_name: Element symbol or compound name (e.g., "Si", "NaCl", "GaN", "MoS2", "Graphene")
- structure_type: Crystal structure type (fcc, bcc, hcp, diamond, zincblende, rocksalt, wurtzite, perovskite, rutile, quartz, cristobalite, layered, 2d) or null
- lattice_parameter: Lattice parameter in Angstroms (float) or null. For 2D materials, this is the in-plane lattice parameter.
- supercell_dims: Supercell dimensions as [nx, ny, nz] (default: [1, 1, 1])
- compound: List of element symbols for compounds (e.g., ["Na", "Cl"], ["Mo", "S"], ["C"]) or null for elements

For complex structures, extract as much information as possible. If the structure description is too complex, 
suggest the closest simple structure that can be generated. For layered/2D materials, use structure_type "layered" or "2d".

Return ONLY valid JSON, no additional text."""

        user_prompt = f"Extract structure parameters from this description: {description}"
        
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        llm_response = message.content[0].text
        
        # Parse the response
        params = parse_llm_structure_response(llm_response)
        
        # Generate structure
        atoms = create_structure(
            params["material_name"],
            params["supercell_dims"],
            structure_type=params["structure_type"],
            lattice_param=params["lattice_parameter"],
            compound=params["compound"]
        )
        
        return atoms
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="anthropic package not installed. Install with: pip install anthropic"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating structure with Anthropic: {str(e)}"
        )


def generate_structure_with_llm(description: str, provider: str = "openai", 
                                 api_key: Optional[str] = None, **kwargs) -> Atoms:
    """
    Universal function to generate structure using any LLM provider.
    
    Args:
        description: Natural language description of the structure
        provider: LLM provider ("openai", "anthropic", "ollama", etc.)
        api_key: API key for the provider
        **kwargs: Additional provider-specific parameters (model, etc.)
        
    Returns:
        Atoms object
        
    Raises:
        HTTPException: If structure cannot be generated
    """
    if provider.lower() == "openai":
        model = kwargs.get("model", "gpt-4o-mini")
        return generate_structure_with_openai(description, api_key, model)
    
    elif provider.lower() == "anthropic":
        model = kwargs.get("model", "claude-3-haiku-20240307")
        return generate_structure_with_anthropic(description, api_key, model)
    
    elif provider.lower() == "ollama":
        # Support for local Ollama models
        return generate_structure_with_ollama(description, **kwargs)
    
    elif provider.lower() == "gemini":
        model = kwargs.get("model", "gemini-default-model")
        return generate_structure_with_gemini(description, api_key, model)
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown LLM provider: {provider}. Supported: openai, anthropic, ollama, gemini"
        )


def generate_structure_with_ollama(description: str, model: str = "llama3", 
                                   base_url: str = "http://localhost:11434") -> Atoms:
    """
    Generate structure using Ollama (local LLM).
    
    Args:
        description: Natural language description of the structure
        model: Ollama model name (llama3, mistral, etc.)
        base_url: Ollama API base URL
        
    Returns:
        Atoms object
        
    Raises:
        HTTPException: If structure cannot be generated
    """
    try:
        import requests
        
        system_prompt = """You are a materials science expert. Given a description of a crystal structure, 
extract the following information and return it as JSON:
- material_name: Element symbol or compound name (e.g., "Si", "NaCl", "GaN", "MoS2", "Graphene")
- structure_type: Crystal structure type (fcc, bcc, hcp, diamond, zincblende, rocksalt, wurtzite, perovskite, rutile, quartz, cristobalite, layered, 2d) or null
- lattice_parameter: Lattice parameter in Angstroms (float) or null. For 2D materials, this is the in-plane lattice parameter.
- supercell_dims: Supercell dimensions as [nx, ny, nz] (default: [1, 1, 1])
- compound: List of element symbols for compounds (e.g., ["Na", "Cl"], ["Mo", "S"], ["C"]) or null for elements

For complex structures, extract as much information as possible. If the structure description is too complex, 
suggest the closest simple structure that can be generated. For layered/2D materials, use structure_type "layered" or "2d".

Return ONLY valid JSON, no additional text."""

        user_prompt = f"Extract structure parameters from this description: {description}"
        
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Ollama API error: {response.status_code}"
            )
        
        llm_response = response.json()["message"]["content"]
        
        # Parse the response
        params = parse_llm_structure_response(llm_response)
        
        # Generate structure
        atoms = create_structure(
            params["material_name"],
            params["supercell_dims"],
            structure_type=params["structure_type"],
            lattice_param=params["lattice_parameter"],
            compound=params["compound"]
        )
        
        return atoms
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="requests package not installed. Install with: pip install requests"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating structure with Ollama: {str(e)}"
        )


def generate_structure_with_gemini(description: str, api_key: str, model: str) -> Atoms:
    """
    Generate structure using Gemini API.

    Args:
        description: Natural language description of the structure
        api_key: Gemini API key
        model: Gemini model name

    Returns:
        Atoms object

    Raises:
        HTTPException: If structure cannot be generated
    """
    try:
        import requests
        import json
        from ase import Atoms

        if not api_key:
            api_key = 'AIzaSyC2OrwSSymjjq2RVHxrKjvLkRYu7xFA2pw' # ChatMat api key from Google AI studio

        # Define the Gemini API endpoint
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
        
        print('User input:', description)
        description = "Provide the crystal structure parameters in JSON format: symbols, positions, cell: " + description

        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": description
                        }
                    ]
                }
            ]
        }

        # Send the request to the Gemini API
        response = requests.post(
            gemini_url,
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": api_key
            },
            data=json.dumps(payload),
            timeout=30
        )

        # Check for errors in the response
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Gemini API error: {response.text}"
            )

        # Parse the response JSON
        response_data = response.json()
        print('description of LLM input:', description)
        print('response_data of LLM model:', response_data)

        # candidates -> index 0 -> content -> parts -> index 0 -> text
        raw_text = response_data['candidates'][0]['content']['parts'][0]['text']
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        structure_data = json.loads(clean_text)

        # Extract structure parameters
        # structure_data = response_data.get("structure")
        # if not structure_data:
        #     raise HTTPException(
        #         status_code=500,
        #         detail="Invalid response from Gemini API: Missing structure data"
        #     )

        # Convert the structure data to an Atoms object
        try:
            atoms = Atoms(
                symbols=structure_data["symbols"],
                positions=structure_data["positions"],
                cell=structure_data["cell"],
                pbc=True
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error constructing Atoms object from Gemini response: {str(e)}"
            )

        return atoms

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="requests package not installed. Install with: pip install requests"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating structure with Gemini: {str(e)}"
        )

