import io
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- ASE Imports ---
from ase.io import write
from ase import Atoms

# --- Structure Building Module ---
try:
    # Try relative import first (when used as a package)
    from .build_structures import create_structure, get_structure, generate_structure_with_llm
except ImportError:
    # Fallback to absolute import (when run as a script)
    from build_structures import create_structure, get_structure, generate_structure_with_llm

# --- 1. App Configuration ---
app = FastAPI(title="ChatMat Backend")

# ⚠️ CORS Policy: Essential to allow the Streamlit frontend (port 8501) 
# to talk to this backend (port 8000).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Data Models (Input/Output Contract) ---
class StructureDetails(BaseModel):
    supercell_dims: List[int] = [1, 1, 1]
    structure_type: Optional[str] = None  # e.g., "fcc", "bcc", "hcp", "diamond", "zincblende", etc.
    lattice_parameter: Optional[float] = None  # Custom lattice parameter
    compound: Optional[List[str]] = None  # For compounds like ["Na", "Cl"]
    source_type: Optional[str] = None  # "mp", "cod", "icsd", "file", "url", "string", "auto", "llm"
    source_params: Optional[dict] = None  # Additional parameters for external sources
    use_llm: Optional[bool] = False  # Use LLM to interpret natural language
    llm_provider: Optional[str] = None  # "openai", "anthropic", "ollama"
    llm_params: Optional[dict] = None  # LLM-specific parameters (model, api_key, etc.)

class CalculationRequest(BaseModel):
    intent: str
    material_name: str
    structure_details: StructureDetails
    user_input: Optional[str] = None  # Original user input for LLM processing

# --- 3. The "Mock" Foundation Model ---
# 🛠️ REAL WORLD INTEGRATION: Replace this function with your actual model call.
def run_foundation_model(atoms: Atoms):
    """
    Simulates a foundation model calculation.
    Returns: Energy (eV) and Forces (eV/A)
    """
    # Simulate processing time or model loading
    n_atoms = len(atoms)
    
    # Generate dummy data that looks realistic
    # Energy: Rough approximation (e.g., -5 eV per atom) plus some noise
    total_energy = -5.0 * n_atoms + np.random.normal(0, 0.1)
    
    # Forces: Random small vectors for each atom
    forces = np.random.normal(0, 0.05, (n_atoms, 3))
    
    # Calculate Max Force (scalar)
    max_force = np.max(np.linalg.norm(forces, axis=1))
    
    return total_energy, max_force

# --- 4. API Endpoints ---
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "ChatMat Backend is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/calculate/")
async def calculate(request: CalculationRequest):
    try:
        details = request.structure_details
        print(f"📥 Received request for: {request.material_name} "
              f"Supercell: {details.supercell_dims} "
              f"Structure: {details.structure_type} "
              f"Compound: {details.compound} "
              f"Source: {details.source_type}")
        
        # A. Generate or Fetch Structure
        if details.use_llm or (details.source_type == "llm"):
            # Use LLM to interpret natural language and generate structure
            llm_params = details.llm_params or {}
            provider = details.llm_provider or "openai"
            
            # Use the full user input as description, fallback to material_name
            description = request.user_input if request.user_input else request.material_name
            
            atoms = generate_structure_with_llm(
                description,
                provider=provider,
                **llm_params
            )
            
            # Apply supercell if specified
            if details.supercell_dims != [1, 1, 1]:
                atoms = atoms * tuple(details.supercell_dims)
                
        elif details.source_type and details.source_type != "auto":
            # Fetch from external source
            source_params = details.source_params or {}
            source_params["dims"] = details.supercell_dims
            
            atoms = get_structure(
                request.material_name,
                source_type=details.source_type,
                **source_params
            )
        else:
            # Use built-in structure generator
            atoms = create_structure(
                request.material_name,
                details.supercell_dims,
                structure_type=details.structure_type,
                lattice_param=details.lattice_parameter,
                compound=details.compound
            )
        
        print(f"✅ Generated structure with {len(atoms)} atoms")
        print(f"   Atom types: {set(atoms.get_chemical_symbols())}")
        print(f"   First few atoms: {atoms.get_chemical_symbols()[:10]}")
        
        # Verify structure
        if len(atoms) == 0:
            raise HTTPException(status_code=500, detail="Generated structure has no atoms!")
        if len(atoms) == 1:
            print(f"⚠️ WARNING: Structure has only 1 atom! This might be an error.")
        
        # B. Run Calculation (The Foundation Model)
        energy, max_force = run_foundation_model(atoms)
        
        # C. Convert Structure to XYZ String (for Visualization)
        # We write to a string buffer to send it over JSON
        xyz_buffer = io.StringIO()
        write(xyz_buffer, atoms, format="xyz")
        xyz_string = xyz_buffer.getvalue()
        
        # Debug: Print first few lines of XYZ
        xyz_lines = [line for line in xyz_string.split('\n') if line.strip()][:10]
        print(f"📄 XYZ preview (first 10 non-empty lines):")
        for i, line in enumerate(xyz_lines, 1):
            print(f"   {i}: {line}")
        
        # Verify XYZ format
        xyz_lines_all = xyz_string.strip().split('\n')
        if len(xyz_lines_all) > 0:
            try:
                num_atoms_xyz = int(xyz_lines_all[0].strip())
                print(f"📊 XYZ contains {num_atoms_xyz} atoms (structure has {len(atoms)} atoms)")
                if num_atoms_xyz != len(atoms):
                    print(f"⚠️ WARNING: Mismatch! XYZ says {num_atoms_xyz} but structure has {len(atoms)}")
                if num_atoms_xyz == 1:
                    print(f"❌ ERROR: XYZ only has 1 atom! This is wrong!")
            except ValueError:
                print(f"⚠️ WARNING: Could not parse atom count from XYZ first line: '{xyz_lines_all[0] if xyz_lines_all else 'empty'}'")

        # D. Return Response
        return {
            "status": "success",
            "material": request.material_name,
            "n_atoms": len(atoms),
            "energy": energy,
            "max_force": max_force,
            "structure_xyz": xyz_string
        }

    except HTTPException as e:
        # Re-raise HTTPException with proper detail
        detail = getattr(e, 'detail', str(e)) if hasattr(e, 'detail') else str(e)
        if not detail:
            detail = f"HTTP {getattr(e, 'status_code', 500)}: {type(e).__name__}"
        print(f"❌ HTTPException: {detail}")
        raise HTTPException(status_code=getattr(e, 'status_code', 500), detail=detail)
    except Exception as e:
        import traceback
        error_msg = str(e) if str(e) else repr(e)
        if not error_msg or error_msg == "":
            error_msg = f"{type(e).__name__}: {repr(e)}"
        print(f"❌ Error: {error_msg}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Full traceback:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg or f"Unknown error: {type(e).__name__}")

# --- 6. Server Startup ---
if __name__ == "__main__":
    import uvicorn
    # Run on localhost port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)