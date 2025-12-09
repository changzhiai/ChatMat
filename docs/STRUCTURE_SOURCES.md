# Structure Sources Guide

ChatMat now supports fetching structures from multiple external sources and loading from files.

## Available Sources

### 1. Materials Project (MP)
Fetch structures from the Materials Project database.

**Requirements:**
- Install: `pip install mp-api pymatgen`
- API Key: Get free API key from https://materialsproject.org/api
- Set environment variable: `export MP_API_KEY=your_api_key`

**Usage Examples:**
- Frontend: "Calculate energy for mp-149"
- Backend: Use `source_type="mp"` with material_id like "mp-149"

**Example:**
```python
from build_structures import get_structure

atoms = get_structure("mp-149", source_type="mp", dims=[2, 2, 2])
```

### 2. Crystallography Open Database (COD)
Fetch structures from COD - free, no API key required!

**Requirements:**
- Install: `pip install requests`
- No API key needed

**Usage Examples:**
- Frontend: "Get structure cod-2000001"
- Backend: Use `source_type="cod"` with COD ID

**Example:**
```python
from build_structures import get_structure

atoms = get_structure("2000001", source_type="cod", dims=[1, 1, 1])
```

### 3. ICSD (Inorganic Crystal Structure Database)
Fetch structures from ICSD - requires paid subscription.

**Requirements:**
- Install: `pip install pymatgen`
- ICSD credentials (paid subscription required)
- Set environment variables: `ICSD_USERNAME` and `ICSD_PASSWORD`

**Usage Examples:**
- Backend: Use `source_type="icsd"` with ICSD collection code

**Example:**
```python
from build_structures import get_structure

atoms = get_structure("12345", source_type="icsd", 
                     username="your_username", password="your_password")
```

### 4. Load from File
Load structures from local files.

**Supported Formats:**
- CIF (`.cif`)
- POSCAR/VASP (`.vasp`, `.poscar`)
- XYZ (`.xyz`)
- And all other formats supported by ASE

**Usage Examples:**
- Frontend: "Load structure from /path/to/structure.cif"
- Backend: Use `source_type="file"` with file path

**Example:**
```python
from build_structures import get_structure

atoms = get_structure("/path/to/structure.cif", source_type="file", dims=[2, 2, 2])
```

### 5. Load from URL
Fetch structures directly from URLs.

**Usage Examples:**
- Frontend: "Get structure from https://example.com/structure.cif"
- Backend: Use `source_type="url"` with URL

**Example:**
```python
from build_structures import get_structure

atoms = get_structure("https://example.com/structure.cif", 
                     source_type="url", dims=[1, 1, 1])
```

### 6. Load from String
Load structures from string content (e.g., CIF content).

**Example:**
```python
from build_structures import get_structure

cif_content = """
data_test
_cell_length_a 5.43
...
"""

atoms = get_structure("", source_type="string", 
                     content=cif_content, format="cif", dims=[1, 1, 1])
```

## Universal Function: `get_structure()`

The `get_structure()` function can auto-detect the source type:

```python
from build_structures import get_structure

# Auto-detect Materials Project
atoms = get_structure("mp-149", dims=[2, 2, 2])

# Auto-detect COD
atoms = get_structure("2000001", dims=[1, 1, 1])

# Auto-detect URL
atoms = get_structure("https://example.com/structure.cif")

# Auto-detect file
atoms = get_structure("/path/to/structure.cif")

# Explicit source type
atoms = get_structure("mp-149", source_type="mp", dims=[2, 2, 2])
```

## API Usage

### Backend Request Format

```json
{
  "intent": "CALCULATE",
  "material_name": "mp-149",
  "structure_details": {
    "supercell_dims": [2, 2, 2],
    "source_type": "mp",
    "source_params": {
      "api_key": "optional_if_env_var_set"
    }
  }
}
```

### Frontend Natural Language

The frontend parser automatically detects:
- `mp-149` → Materials Project
- `cod-2000001` or `2000001` → COD
- URLs starting with `http://` or `https://` → URL fetch
- File paths → File load

## Notes

- **Supercell dimensions** can be applied to any fetched structure
- **Auto-detection** works for most common cases
- **Error handling** provides clear error messages if sources are unavailable
- **Caching** is not implemented - each request fetches fresh data

