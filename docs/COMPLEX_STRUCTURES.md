# Building Complex Structures from Descriptions

This guide explains how to build complicated crystal structures using natural language descriptions in ChatMat.

## Overview

ChatMat supports multiple methods for building complex structures:

1. **LLM-Based Generation** - Use ChatGPT/Claude to interpret complex descriptions
2. **Direct Database Access** - Fetch from Materials Project, COD, ICSD
3. **File Loading** - Load from CIF, POSCAR, or other structure files
4. **Programmatic Building** - Use Python API for precise control

## Method 1: LLM-Based Generation (Recommended for Complex Descriptions)

### Setup

```bash
# Install LLM package (choose one)
pip install openai        # For ChatGPT
pip install anthropic     # For Claude
# or use Ollama (local, free)
```

### Basic Examples

**Simple Structures:**
```
"Create a 2x2x2 supercell of diamond cubic silicon"
"Generate FCC aluminum with lattice parameter 4.05 Angstroms"
"Make a rocksalt structure of sodium chloride"
```

**Complex Structures:**
```
"Generate a 3x3x1 supercell of MoS2 monolayer with AB stacking"
"Create a heterostructure of graphene on hexagonal boron nitride"
"Build a perovskite structure of BaTiO3 with a=4.00 Angstroms"
"Generate a wurtzite GaN structure with c/a ratio of 1.63"
```

### Advanced Examples

**Layered Materials:**
```
"Create a 2D MoS2 structure with interlayer spacing of 6.15 Angstroms"
"Generate a bilayer graphene with AB stacking"
"Build a 5-layer heterostructure of MoS2/WSe2"
```

**Defects and Doping:**
```
"Create a silicon structure with a vacancy defect"
"Generate GaN with 5% magnesium doping"
"Build a TiO2 structure with oxygen vacancies"
```

**Complex Compounds:**
```
"Generate a perovskite structure of (Ba,Sr)TiO3"
"Create a spinel structure of MgAl2O4"
"Build a garnet structure of Y3Al5O12"
```

## Method 2: Using External Databases

### Materials Project

For complex structures that are already in databases:

```python
from build_structures import get_structure

# Fetch by Materials Project ID
atoms = get_structure("mp-149", source_type="mp", dims=[2, 2, 2])
```

**Frontend:**
```
"Fetch structure mp-149 from Materials Project"
"Get mp-1234 with 3x3x3 supercell"
```

### COD (Crystallography Open Database)

Free access to crystal structures:

```python
from build_structures import get_structure

# Fetch by COD ID
atoms = get_structure("2000001", source_type="cod")
```

**Frontend:**
```
"Get structure cod-2000001"
"Fetch COD entry 2000001"
```

## Method 3: Loading from Files

### CIF Files

```python
from build_structures import load_structure_from_file

# Load from CIF
atoms = load_structure_from_file("structure.cif", format="cif")
```

### POSCAR/VASP Files

```python
atoms = load_structure_from_file("POSCAR", format="vasp")
```

**Frontend:**
```
"Load structure from /path/to/structure.cif"
"Import structure from file structure.xyz"
```

## Method 4: Programmatic Building

For maximum control, use the Python API directly:

### Basic Structure

```python
from build_structures import create_structure

# Simple element
atoms = create_structure("Si", dims=[2, 2, 2], structure_type="diamond")

# Compound
atoms = create_structure("NaCl", dims=[2, 2, 2], 
                        structure_type="rocksalt", 
                        compound=["Na", "Cl"])
```

### Complex Structures

```python
from build_structures import create_structure
from ase import Atoms
from ase.build import surface, stack
import numpy as np

# 1. Create base structure
si = create_structure("Si", dims=[1, 1, 1], structure_type="diamond")

# 2. Create surface
si_surface = surface(si, (1, 1, 1), layers=5, vacuum=10.0)

# 3. Stack multiple layers
atoms = stack(si_surface, si_surface, axis=2)

# 4. Apply supercell
atoms = atoms * (2, 2, 1)
```

## Best Practices for Complex Structures

### 1. Be Specific in Descriptions

**Good:**
- "Create a 2x2x1 supercell of MoS2 monolayer with AB stacking and interlayer spacing 6.15 Angstroms"
- "Generate perovskite BaTiO3 with lattice parameter 4.00 Angstroms in a 3x3x3 supercell"

**Less Effective:**
- "Make MoS2"
- "Create perovskite"

### 2. Use Standard Terminology

**Structure Types:**
- `fcc`, `bcc`, `hcp` - Common metal structures
- `diamond` - Diamond cubic (Si, C, Ge)
- `zincblende` - ZnS structure (GaN, GaAs, etc.)
- `rocksalt` - NaCl structure
- `wurtzite` - Hexagonal ZnS structure
- `perovskite` - ABO3 structure
- `rutile` - TiO2 structure
- `quartz` - Alpha-SiO2
- `layered` - 2D materials
- `heterostructure` - Multi-material structures

### 3. Specify Lattice Parameters When Known

```
"FCC aluminum with a=4.05 Angstroms"
"Silicon diamond structure, lattice parameter 5.43"
"GaN wurtzite with a=3.19 and c=5.19"
```

### 4. For Very Complex Structures

If the structure is too complex for automatic generation:

1. **Use External Databases**: Search Materials Project or COD first
2. **Load from Files**: If you have a CIF or POSCAR file
3. **Use LLM with Detailed Description**: Provide as much detail as possible
4. **Programmatic Building**: Write custom Python code for precise control

## Examples by Complexity Level

### Level 1: Simple Elements

```
"Generate FCC copper"
"Create BCC iron"
"Make diamond silicon"
```

### Level 2: Binary Compounds

```
"Create rocksalt NaCl"
"Generate zincblende GaN"
"Build wurtzite ZnO"
```

### Level 3: Ternary Compounds

```
"Create perovskite BaTiO3"
"Generate spinel MgAl2O4"
"Build rutile TiO2"
```

### Level 4: Layered/2D Materials

```
"Generate MoS2 monolayer"
"Create graphene structure"
"Build hexagonal BN"
```

### Level 5: Heterostructures

```
"Create MoS2/WSe2 heterostructure"
"Generate graphene/hBN stack"
"Build Si/SiO2 interface"
```

### Level 6: Defects and Doping

```
"Create Si with vacancy"
"Generate GaN with Mg doping"
"Build TiO2 with oxygen vacancies"
```

## Troubleshooting

### Structure Not Generated

1. **Check Material Name**: Use standard element symbols (Si, not Silicon)
2. **Verify Structure Type**: Use recognized structure types
3. **Try LLM**: Enable LLM for complex descriptions
4. **Use Database**: Try fetching from Materials Project or COD

### Wrong Structure Generated

1. **Be More Specific**: Add structure type and lattice parameters
2. **Use LLM**: LLM can better interpret complex descriptions
3. **Check Compound**: Ensure compound elements are correct

### Complex Structure Not Supported

1. **Use File Loading**: If you have a structure file
2. **Database Lookup**: Search Materials Project for the structure
3. **Programmatic Building**: Write custom code for precise control

## Advanced: Custom Structure Building

For structures not supported by the built-in functions:

```python
from ase import Atoms
from ase.build import bulk, surface, stack
import numpy as np

# Example: Custom heterostructure
def create_custom_heterostructure():
    # Create base materials
    mos2 = create_structure("MoS2", dims=[2, 2, 1], structure_type="layered")
    wse2 = create_structure("WSe2", dims=[2, 2, 1], structure_type="layered")
    
    # Stack them
    hetero = stack(mos2, wse2, axis=2, distance=6.5)
    
    return hetero
```

## Tips for LLM Generation

1. **Use Detailed Descriptions**: More context = better results
2. **Specify All Parameters**: Lattice parameters, supercell, structure type
3. **Use Standard Terms**: Stick to recognized crystal structure names
4. **Try Different Models**: GPT-4o may handle complexity better than GPT-4o-mini
5. **Iterate**: If first attempt fails, refine the description

## Next Steps

- Check `LLM_GENERATION.md` for LLM setup and usage
- See `STRUCTURE_SOURCES.md` for database access
- Review code examples in `build_structures.py` for programmatic building

