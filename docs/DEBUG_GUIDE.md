# Debugging Guide for ChatMat

This guide helps you debug issues with structure generation and visualization.

## Quick Debugging Steps

### 1. Check Backend Console Output

When you run the backend (`python backend.py`), you should see debug messages:

```
📥 Received request for: SiO2 Supercell: [1, 1, 1] ...
🔍 Found sio2 in compound database: ...
✅ Generated structure with X atoms: {'Si', 'O'}
   Atom symbols: ['Si', 'O', 'O', ...]
✅ After supercell [1, 1, 1]: X atoms
📄 XYZ preview (first 5 lines):
```

**What to look for:**
- Does it find the compound in the database?
- How many atoms are generated?
- What atom types are present?
- Does the XYZ preview look correct?

### 2. Check Frontend Output

In the Streamlit app, you should see:
- Atom count message: "📊 Received structure with X atoms"
- XYZ preview code block
- Warning if only 1 atom detected

### 3. Test Structure Generation Directly

Create a test script to verify structure generation:

```python
# test_structure.py
from build_structures import create_structure

# Test SiO2
atoms = create_structure("SiO2", [1, 1, 1], compound=["Si", "O"])
print(f"SiO2 structure: {len(atoms)} atoms")
print(f"Atom types: {set(atoms.get_chemical_symbols())}")
print(f"All atoms: {atoms.get_chemical_symbols()}")

# Test XYZ output
from ase.io import write
import io
xyz_buffer = io.StringIO()
write(xyz_buffer, atoms, format="xyz")
xyz_string = xyz_buffer.getvalue()
print(f"\nXYZ output:\n{xyz_string[:500]}")  # First 500 chars
```

Run it:
```bash
python test_structure.py
```

### 4. Check XYZ Format

The XYZ format should be:
```
3                    <- Number of atoms
Comment line
Si  0.000  0.000  0.000
O   1.637  2.836  1.800
O   3.273  5.672  3.600
```

**Common issues:**
- First line should be the atom count (not 1)
- Each atom should be on its own line
- Format: `Element X Y Z`

### 5. Check Browser Console

1. Open browser developer tools (F12 or Cmd+Option+I)
2. Go to Console tab
3. Look for JavaScript errors
4. Check Network tab for API responses

### 6. Verify Structure in Visualization

The visualizer uses py3Dmol. Check:
- Is the XYZ data being passed correctly?
- Are there any JavaScript errors?
- Is the view rendering at all?

## Common Issues and Solutions

### Issue: Only 1 atom shown

**Possible causes:**
1. Structure generation failing → Check backend logs
2. XYZ format incorrect → Check XYZ preview
3. Visualization issue → Check browser console

**Solution:**
- Check backend console for atom count
- Verify XYZ format is correct
- Try a simple structure like "Si" first

### Issue: Wrong structure generated

**Possible causes:**
1. Parser not recognizing compound
2. Wrong structure type selected
3. Database lookup failing

**Solution:**
- Check parser output in backend logs
- Verify compound is in database
- Try explicit structure type

### Issue: No structure shown

**Possible causes:**
1. Backend not running
2. Connection error
3. XYZ data empty

**Solution:**
- Verify backend is running on port 8000
- Check frontend error messages
- Verify structure_xyz in response

## Debugging Tools

### Enable Verbose Logging

Add to `backend.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Print Full Structure Info

Add to backend after structure generation:
```python
print(f"Structure info:")
print(f"  Number of atoms: {len(atoms)}")
print(f"  Chemical symbols: {atoms.get_chemical_symbols()}")
print(f"  Positions shape: {atoms.positions.shape}")
print(f"  Cell: {atoms.cell}")
```

### Test Individual Functions

Test each structure creation function:
```python
from build_structures import create_quartz
atoms = create_quartz(["Si", "O"], 4.91, 5.40)
print(f"Quartz: {len(atoms)} atoms")
```

## Step-by-Step Debugging Process

1. **Start Backend**
   ```bash
   python backend.py
   ```
   - Check for any startup errors
   - Note the port (should be 8000)

2. **Start Frontend**
   ```bash
   streamlit run app.py
   ```
   - Check for any startup errors
   - Note the URL (usually http://localhost:8501)

3. **Test Simple Structure**
   - Input: "Si"
   - Should generate multiple Si atoms
   - Check backend console output

4. **Test Compound**
   - Input: "SiO2"
   - Check if compound is recognized
   - Verify atom count in backend
   - Check XYZ format

5. **Check Visualization**
   - Verify XYZ data is received
   - Check atom count in frontend
   - Look for visualization errors

6. **Compare Expected vs Actual**
   - Expected: Multiple atoms (3+ for SiO2)
   - Actual: What you see in logs/visualization
   - Identify where it diverges

## Quick Test Commands

```bash
# Test backend directly
curl -X POST http://127.0.0.1:8000/calculate/ \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "CALCULATE",
    "material_name": "SiO2",
    "structure_details": {
      "supercell_dims": [1, 1, 1],
      "compound": ["Si", "O"]
    }
  }'

# Check if backend is running
curl http://127.0.0.1:8000/docs
```

## Getting Help

When reporting issues, include:
1. Backend console output (full log)
2. Frontend atom count message
3. XYZ preview (first 10 lines)
4. Browser console errors (if any)
5. What you expected vs what you got

