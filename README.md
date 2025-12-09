# ChatMat

A tool for generating and calculating crystal structures using foundation models.

## Project Structure

```
ChatMat/
├── chatmat/              # Main application code
│   ├── __init__.py       # Package initialization
│   ├── app.py            # Streamlit frontend
│   ├── backend.py        # FastAPI backend
│   └── build_structures.py  # Structure generation module
├── docs/                 # Documentation
│   ├── STRUCTURE_SOURCES.md
│   ├── COMPLEX_STRUCTURES.md
│   ├── LLM_GENERATION.md
│   └── DEBUG_GUIDE.md
├── test/                 # Test scripts
│   ├── test_structure.py
│   ├── test_backend_flow.py
│   └── test_xyz_output.py
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. For LLM support (optional):
```bash
pip install openai        # For ChatGPT
# or
pip install anthropic     # For Claude
```

3. Set API keys (if using LLMs):
```bash
export OPENAI_API_KEY=your_key_here
# or
export ANTHROPIC_API_KEY=your_key_here
```

## Running the Application

### Start the Backend

**Option 1: Using the run script (recommended)**
```bash
./run_backend.sh
```

**Option 2: Manual**
```bash
cd chatmat
python backend.py
```

**Option 3: As a Python module**
```bash
python -m chatmat.backend
```

The backend will run on `http://127.0.0.1:8000`

### Start the Frontend

**Option 1: Using the run script (recommended)**
```bash
./run_frontend.sh
```

**Option 2: Manual**
```bash
cd chatmat
streamlit run app.py
```

**Option 3: As a Python module**
```bash
streamlit run chatmat/app.py
```

The frontend will open in your browser at `http://localhost:8501`

## Usage

1. **Simple Structures**: Input material names like "Si", "Au", "Fe"
2. **Compounds**: Input "SiO2", "NaCl", "GaN", etc.
3. **With Supercells**: "2x2x2 supercell of Silicon"
4. **LLM Generation**: Enable "Use LLM" checkbox for complex descriptions
5. **External Sources**: Use "mp-149" for Materials Project, "cod-2000001" for COD

## Testing

Run test scripts to verify structure generation:

```bash
python test/test_structure.py
python test/test_backend_flow.py
python test/test_xyz_output.py
```

## Documentation

- **Structure Sources**: `docs/STRUCTURE_SOURCES.md` - How to fetch from databases
- **Complex Structures**: `docs/COMPLEX_STRUCTURES.md` - Building complex structures
- **LLM Generation**: `docs/LLM_GENERATION.md` - Using LLMs for structure generation
- **Debugging**: `docs/DEBUG_GUIDE.md` - Debugging guide

## Features

- ✅ Generate structures for 20+ elements
- ✅ Support for compounds (NaCl, GaN, SiO2, TiO2, etc.)
- ✅ Multiple crystal structures (FCC, BCC, HCP, Diamond, Zincblende, Rocksalt, etc.)
- ✅ Fetch from Materials Project, COD, ICSD
- ✅ Load from files (CIF, POSCAR, XYZ, etc.)
- ✅ LLM-based structure generation (ChatGPT, Claude, Ollama)
- ✅ 3D visualization with py3Dmol
- ✅ Energy and force calculations

## Development

The code is organized as a Python package:
- `chatmat/` - Main package
- `test/` - Test scripts
- `docs/` - Documentation

Import from the package:
```python
from chatmat.build_structures import create_structure
from chatmat.backend import app
```

