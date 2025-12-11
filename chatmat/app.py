import streamlit as st
import streamlit.components.v1 as components
import requests
import py3Dmol
import re
from stmol import showmol
from streamlit_float import float_init, float_parent

# --- Configuration ---
# ⚠️ This must match the address where your FastAPI backend is running
BACKEND_URL = "http://127.0.0.1:8000/calculate/"

st.set_page_config(page_title="ChatMat", layout="wide", page_icon="⚛️")

# Initialize streamlit-float for floating elements
float_init()

# --- Custom CSS for Chat Styling ---
st.markdown("""
<style>
    /* Hide the submit button */
    form[data-testid="stForm"] button[type="submit"],
    button[data-testid="stBaseButton-secondaryFormSubmit"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        opacity: 0 !important;
    }
    
    /* Remove specific element container */
    div.stElementContainer.element-container.st-emotion-cache-e6st4z.e196pkbe0,
    div[data-testid="stElementContainer"].element-container.st-emotion-cache-e6st4z.e196pkbe0 {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
    }
    
    /* Remove border from vertical block */
    div.stVerticalBlock.st-emotion-cache-1n6tfoc.e196pkbe2,
    div[data-testid="stVerticalBlock"].st-emotion-cache-1n6tfoc.e196pkbe2,
    form[data-testid="stForm"] div[data-testid="stVerticalBlock"] {
        border: none !important;
        border-width: 0 !important;
        border-style: none !important;
        border-color: transparent !important;
        box-shadow: none !important;
    }
    

    /* Input styling - no borders, no outlines */
    input,
    input[type="text"],
    div[data-testid="stTextInput"] input,
    div[data-baseweb="input"] input,
    div[data-baseweb="input"],
    div[data-baseweb="input"] > div,
    div[data-testid="stTextInput"] {
        border: none !important;
        background-color: #ffffff !important;
        outline: none !important;
        box-shadow: none !important;
    }
    input:focus,
    input:focus-visible,
    div[data-baseweb="input"]:focus,
    div[data-baseweb="input"]:focus-within {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    
    .chat-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .user-msg {
        text-align: right;
        color: #0f52ba;
        font-weight: bold;
    }
    .bot-msg {
        text-align: left;
        color: #333;
    }
</style>
            
<script>
    // Get the element
    const wrapper = document.querySelector('.chat-history-wrapper');

    if (wrapper) {
        // Get the exact width in pixels
        const width = wrapper.getBoundingClientRect().width;
        console.log("Wrapper width is:", width);
    }
        
</script>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = []
if "last_structure_xyz" not in st.session_state:
    st.session_state.last_structure_xyz = None

# --- Sidebar: Instructions ---
with st.sidebar:
    st.header("⚛️ ChatMat Control")
    st.write("This tool uses a foundation model to calculate energy and forces for material structures.")
    
    # Debug Mode Toggle
    debug_mode = st.checkbox("🐛 Debug Mode", value=False, help="Show detailed debugging information")
    st.markdown("### Try these prompts:")
    st.code("Calculate energy for a 2x2x2 supercell of Silicon")
    st.code("Get forces for bulk Gold (Au)")
    st.code("Generate FCC Aluminum with 3x3x3 supercell")
    st.code("Create BCC Iron structure")
    st.code("Calculate energy for NaCl (rocksalt)")
    st.code("Generate GaN zincblende structure")
    st.code("Create HCP Titanium with a=2.95")
    st.divider()
    st.markdown("**Supported:** Elements (Si, Al, Au, Fe, Ti, Mg, etc.), Compounds (NaCl, GaN, TiO2, etc.)")
    st.markdown("**Structures:** FCC, BCC, HCP, Diamond, Zincblende, Rocksalt, Wurtzite, Perovskite")
    st.divider()
    st.markdown("### External Sources:")
    st.code("Fetch from Materials Project: mp-149")
    st.code("Fetch from COD: cod-2000001")
    st.code("Load from URL: https://example.com/structure.cif")
    st.code("Load from file: /path/to/structure.cif")
    st.divider()
    st.markdown("### LLM Generation:")
    st.code("Create a 2x2x2 supercell of diamond cubic silicon")
    st.code("Generate FCC aluminum with lattice parameter 4.05")
    st.code("Make a rocksalt structure of sodium chloride")
    st.code("Generate MoS2 monolayer with AB stacking")
    st.code("Create perovskite BaTiO3 with a=4.00")
    st.info("💡 Enable 'Use LLM' checkbox for complex natural language descriptions")
    st.markdown("**See COMPLEX_STRUCTURES.md for advanced examples**")
    st.divider()
    
    # Debugging Section
    if debug_mode:
        st.markdown("### 🐛 Debug Tools")
        st.markdown("**Backend Console:** Check terminal where `python backend.py` is running")
        st.markdown("**Test Script:** Run `python test_structure.py`")
        st.markdown("**Guide:** See `DEBUG_GUIDE.md`")
        st.divider()
    
    st.info("Ensure your FastAPI backend is running on port 8000.")

# --- Main Layout ---
col1, col2 = st.columns([3, 2])

# === COLUMN 1: Chat Interface ===
with col1:
    st.markdown("<h1 style='text-align: center;'>ChatMat</h1>", unsafe_allow_html=True)
    
    # 1. Chat History Display
    st.markdown('<div class="chat-history-wrapper">', unsafe_allow_html=True)
    for role, text in st.session_state.history:
        if role == "user":
            st.markdown(f'<div class="chat-container user-msg">👤 You: {text}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-container bot-msg">🤖 ChatMat: {text}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Input Area - Conditional rendering based on history
    is_empty = len(st.session_state.history) == 0
    
    if is_empty:
        # Start: Render form in center with vertical spacers
        st.markdown("<br><br><br>", unsafe_allow_html=True)  # Top spacer
        with st.form(key="chat_form", clear_on_submit=True):
            # First row: Input field
            user_input = st.text_input("", placeholder="e.g., Energy of bulk Silicon", label_visibility="collapsed", autocomplete="off")
            
            # Second row: Agent dropdown and space for other elements (like Cursor)
            col_dropdown, col_other = st.columns([1, 4])
            with col_dropdown:
                if "agent_option" not in st.session_state:
                    st.session_state.agent_option = "Agent"
                agent_options = ["Agent", "openai", "anthropic", "ollama"]
                current_index = agent_options.index(st.session_state.agent_option) if st.session_state.agent_option in agent_options else 0
                agent_option = st.selectbox(
                    "Agent",
                    options=agent_options,
                    index=current_index,
                    label_visibility="collapsed"
                )
                st.session_state.agent_option = agent_option
            with col_other:
                pass  # Space for other elements
            
            use_llm = (agent_option != "Agent")
            llm_provider = agent_option if (use_llm and agent_option in ["openai", "anthropic", "ollama"]) else None
            
            # Form submits on Enter key press - button is hidden
            submit_button = st.form_submit_button(use_container_width=True, label="", help="Press Enter to submit")
        st.markdown("<br><br><br>", unsafe_allow_html=True)  # Bottom spacer
    else:
        # Active: Render form at bottom using streamlit-float
        with st.container():
            float_parent(css="""
                    position: fixed !important;
                    z-index: 100 !important;
                    bottom: 10px !important;
                    background-color: #ffffff !important;
                    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1) !important;
                    border: 1px solid #d3d3d3 !important;
                    border-radius: 5px !important;
                    padding: 5px !important;
                    box-sizing: border-box !important;
                    width: auto !important;
                    # width: 100% !important;
                    # max-width: 1000px !important;
                    """)
            
            # left: unset !important;
            # right: unset !important;
            # width: auto !important;
            # max-width: none !important;
            with st.form(key="chat_form", clear_on_submit=True):
                # First row: Input field
                user_input = st.text_input("", placeholder="e.g., Energy of bulk Silicon", label_visibility="collapsed", autocomplete="off")
                
                # Second row: Agent dropdown and space for other elements
                col_dropdown, col_other = st.columns([1, 4])
                with col_dropdown:
                    if "agent_option" not in st.session_state:
                        st.session_state.agent_option = "Agent"
                    agent_options = ["Agent", "openai", "anthropic", "ollama"]
                    current_index = agent_options.index(st.session_state.agent_option) if st.session_state.agent_option in agent_options else 0
                    agent_option = st.selectbox(
                        "Agent",
                        options=agent_options,
                        index=current_index,
                        label_visibility="collapsed"
                    )
                    st.session_state.agent_option = agent_option
                with col_other:
                    pass  # Space for other elements
                
                use_llm = (agent_option != "Agent")
                llm_provider = agent_option if (use_llm and agent_option in ["openai", "anthropic", "ollama"]) else None
                
                # Form submits on Enter key press - button is hidden
                submit_button = st.form_submit_button(use_container_width=True, label="", help="Press Enter to submit")

    # 3. Enhanced Natural Language Parser
    def parse_material_request(text: str) -> dict:
        """Parse natural language input to extract material, supercell, structure type, etc."""
        text_lower = text.lower()
        
        # Initialize defaults
        result = {
            "material_name": "Si",
            "supercell_dims": [1, 1, 1],
            "structure_type": None,
            "lattice_parameter": None,
            "compound": None,
            "source_type": None,
            "source_params": {},
            "use_llm": False,
            "llm_provider": None,
            "llm_params": {}
        }
        
        # Extract supercell dimensions (e.g., "2x2x2", "3x3x3", "2 2 2")
        supercell_patterns = [
            r'(\d+)\s*[x×]\s*(\d+)\s*[x×]\s*(\d+)',  # 2x2x2, 3×3×3
            r'supercell\s*[:\s]+(\d+)\s*[x×,]\s*(\d+)\s*[x×,]\s*(\d+)',  # supercell: 2x2x2
            r'(\d+)\s+(\d+)\s+(\d+)',  # 2 2 2 (if near "supercell")
        ]
        
        for pattern in supercell_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result["supercell_dims"] = [int(match.group(1)), int(match.group(2)), int(match.group(3))]
                break
        
        # Extract structure types
        structure_keywords = {
            "fcc": ["fcc", "face-centered cubic", "face centered cubic"],
            "bcc": ["bcc", "body-centered cubic", "body centered cubic"],
            "hcp": ["hcp", "hexagonal close-packed", "hexagonal close packed"],
            "diamond": ["diamond", "diamond cubic"],
            "sc": ["sc", "simple cubic"],
            "zincblende": ["zincblende", "zinc blende", "sphalerite"],
            "rocksalt": ["rocksalt", "rock salt", "nacl structure"],
            "wurtzite": ["wurtzite"],
            "perovskite": ["perovskite"],
            "rutile": ["rutile"],
        }
        
        for struct_type, keywords in structure_keywords.items():
            if any(kw in text_lower for kw in keywords):
                result["structure_type"] = struct_type
                break
        
        # Extract lattice parameter (e.g., "a=5.43", "lattice 4.08")
        lattice_patterns = [
            r'[al]\s*=\s*([\d.]+)',
            r'lattice\s*(?:parameter|constant)?\s*[:=]?\s*([\d.]+)',
            r'a\s*=\s*([\d.]+)'
        ]
        for pattern in lattice_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result["lattice_parameter"] = float(match.group(1))
                break
        
        # Define common words to filter out (used in multiple places)
        common_words = {"The", "For", "Get", "Calculate", "Energy", "Force", "Structure", 
                      "Supercell", "Bulk", "Of", "A", "An", "In", "On", "At"}
        
        # IMPORTANT: Check compounds FIRST before elements to avoid false matches
        # Extract compounds (e.g., "NaCl", "GaN", "TiO2", "sodium chloride")
        compound_map = {
            "nacl": {"name": "NaCl", "compound": ["Na", "Cl"]},
            "sodium chloride": {"name": "NaCl", "compound": ["Na", "Cl"]},
            "mgo": {"name": "MgO", "compound": ["Mg", "O"]},
            "magnesium oxide": {"name": "MgO", "compound": ["Mg", "O"]},
            "gan": {"name": "GaN", "compound": ["Ga", "N"]},
            "gallium nitride": {"name": "GaN", "compound": ["Ga", "N"]},
            "gap": {"name": "GaP", "compound": ["Ga", "P"]},
            "gallium phosphide": {"name": "GaP", "compound": ["Ga", "P"]},
            "zns": {"name": "ZnS", "compound": ["Zn", "S"]},
            "zinc sulfide": {"name": "ZnS", "compound": ["Zn", "S"]},
            "tio2": {"name": "TiO2", "compound": ["Ti", "O"]},
            "titanium dioxide": {"name": "TiO2", "compound": ["Ti", "O"]},
            "sio2": {"name": "SiO2", "compound": ["Si", "O"], "structure_type": "quartz"},
            "silicon dioxide": {"name": "SiO2", "compound": ["Si", "O"], "structure_type": "quartz"},
            "quartz": {"name": "SiO2", "compound": ["Si", "O"], "structure_type": "quartz"},
            "catio3": {"name": "CaTiO3", "compound": ["Ca", "Ti", "O"]},
            "calcium titanate": {"name": "CaTiO3", "compound": ["Ca", "Ti", "O"]},
        }
        
        for key, value in compound_map.items():
            if key in text_lower:
                result["material_name"] = value["name"]
                result["compound"] = value["compound"]
                # Set structure type if specified in compound_map
                if "structure_type" in value:
                    result["structure_type"] = value["structure_type"]
                break
        
        # Check for compound formulas (e.g., "NaCl", "GaN", "SiO2")
        # Only do this if we haven't already found a compound
        if not result.get("compound"):
            compound_pattern = r'\b([A-Z][a-z]?[A-Z]?[a-z]?\d*)\b'
            compound_matches = re.findall(compound_pattern, text)
            for match in compound_matches:
                if len(match) >= 2 and match not in common_words:
                    # Try to parse as compound (simple heuristic)
                    if any(c.isdigit() for c in match):  # Has numbers, likely compound (e.g., SiO2, TiO2)
                        result["material_name"] = match
                        # Try to extract elements (simplified)
                        elements = re.findall(r'[A-Z][a-z]?', match)
                        if len(elements) >= 2:
                            result["compound"] = elements
                            break  # Found a compound, stop looking
                    elif len(match) == 2 and match[0].isupper() and match[1].isupper():  # Like "GaN"
                        result["material_name"] = match
                        result["compound"] = [match[0], match[1]]
                        break  # Found a compound, stop looking
        
        # Only check for elements if we haven't found a compound
        if not result.get("compound"):
            # Extract material names (elements)
            # Common element names
            element_map = {
                "silicon": "Si", "si": "Si",
                "aluminum": "Al", "aluminium": "Al", "al": "Al",
                "gold": "Au", "au": "Au",
                "copper": "Cu", "cu": "Cu",
                "iron": "Fe", "fe": "Fe",
                "titanium": "Ti", "ti": "Ti",
                "magnesium": "Mg", "mg": "Mg",
                "nickel": "Ni", "ni": "Ni",
                "zinc": "Zn", "zn": "Zn",
                "carbon": "C", "c": "C",
                "germanium": "Ge", "ge": "Ge",
                "chromium": "Cr", "cr": "Cr",
                "molybdenum": "Mo", "mo": "Mo",
                "tungsten": "W", "w": "W",
                "vanadium": "V", "v": "V",
                "cobalt": "Co", "co": "Co",
                "palladium": "Pd", "pd": "Pd",
                "platinum": "Pt", "pt": "Pt",
                "silver": "Ag", "ag": "Ag",
                "beryllium": "Be", "be": "Be",
                "zirconium": "Zr", "zr": "Zr",
            }
            
            # Check for element names
            for name, symbol in element_map.items():
                if name in text_lower:
                    result["material_name"] = symbol
                    break
            
            # Check for chemical symbols directly (e.g., "Si", "Au", "Fe")
            # Only if we still don't have a material name
            if result["material_name"] == "Si":  # Still default
                element_symbols = r'\b([A-Z][a-z]?)\b'
                matches = re.findall(element_symbols, text)
                if matches:
                    # Filter out common words that aren't elements
                    potential_elements = [m for m in matches if m not in common_words and len(m) <= 2]
                    if potential_elements:
                        result["material_name"] = potential_elements[0]
        
        # Detect external source types (check after compounds to avoid conflicts)
        # Materials Project (mp-XXXX)
        if re.search(r'\bmp-\d+\b', text, re.IGNORECASE):
            match = re.search(r'\b(mp-\d+)\b', text, re.IGNORECASE)
            if match:
                result["material_name"] = match.group(1)
                result["source_type"] = "mp"
        
        # COD database (cod-XXXXXXX or just numbers)
        elif re.search(r'\bcod-?\d+\b', text, re.IGNORECASE):
            match = re.search(r'\bcod-?(\d+)\b', text, re.IGNORECASE)
            if match:
                result["material_name"] = match.group(1)
                result["source_type"] = "cod"
        
        # URL detection
        elif re.search(r'https?://\S+', text):
            match = re.search(r'(https?://\S+)', text)
            if match:
                result["material_name"] = match.group(1)
                result["source_type"] = "url"
        
        # File path detection (if it looks like a path)
        elif re.search(r'[/\\]', text) or text.endswith(('.cif', '.xyz', '.vasp', '.poscar')):
            result["material_name"] = text.strip()
            result["source_type"] = "file"
        
        return result
    
    # 3. Logic Handling
    if submit_button and user_input:
        # Add user message to history
        st.session_state.history.append(("user", user_input))
        
        # Parse the user input
        parsed = parse_material_request(user_input)
        
        # Determine if we should use LLM
        # Use LLM if checkbox is checked OR if the description is complex (long, contains multiple clauses)
        should_use_llm = use_llm or (len(user_input.split()) > 10 and not parsed.get("source_type"))
        
        agent_option_safe = st.session_state.get("agent_option", "Agent")
        if not isinstance(agent_option_safe, str):
            agent_option_safe = "Agent"
        
        llm_provider_str = None
        if should_use_llm:
            # Use the safe agent option from session state
            if agent_option_safe in ["openai", "anthropic", "ollama"]:
                llm_provider_str = agent_option_safe
            else:
                # Fallback: try to extract from llm_provider if it's a string
                if isinstance(llm_provider, str) and llm_provider in ["openai", "anthropic", "ollama"]:
                    llm_provider_str = llm_provider
                else:
                    llm_provider_str = None
        
        # Ensure all values are JSON-serializable (no Streamlit objects)
        lattice_param = None
        if parsed["lattice_parameter"] is not None:
            try:
                lattice_param = float(parsed["lattice_parameter"])
            except (ValueError, TypeError):
                lattice_param = None
        
        payload = {
            "intent": "CALCULATE",
            "material_name": str(parsed["material_name"]) if parsed["material_name"] else "Si",
            "user_input": str(user_input) if user_input else None,
            "structure_details": {
                "supercell_dims": [int(x) for x in parsed["supercell_dims"]],
                "structure_type": str(parsed["structure_type"]) if parsed["structure_type"] else None,
                "lattice_parameter": lattice_param,
                "compound": [str(x) for x in parsed["compound"]] if parsed["compound"] else None,
                "source_type": str(parsed.get("source_type")) if parsed.get("source_type") else None,
                "source_params": {str(k): str(v) if not isinstance(v, (dict, list)) else v 
                                 for k, v in parsed.get("source_params", {}).items()} if parsed.get("source_params") else {},
                "use_llm": bool(should_use_llm),
                "llm_provider": llm_provider_str,
                "llm_params": {
                    "model": "gpt-4o-mini" if llm_provider_str == "openai" else 
                            "claude-3-haiku-20240307" if llm_provider_str == "anthropic" else
                            "llama3" if llm_provider_str == "ollama" else None
                } if should_use_llm and llm_provider_str else {}
            }
        }

        with st.spinner("Synthesizing structure and calculating physics..."):
            try:
                response = requests.post(BACKEND_URL, json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the result message
                    material_display = data.get('material', parsed["material_name"])
                    n_atoms = data.get('n_atoms', 'N/A')
                    supercell_str = f"{parsed['supercell_dims'][0]}×{parsed['supercell_dims'][1]}×{parsed['supercell_dims'][2]}"
                    structure_info = f" ({parsed['structure_type'].upper()})" if parsed['structure_type'] else ""
                    
                    result_msg = (
                        f"**Structure:** {material_display}{structure_info}\n\n"
                        f"📦 **Supercell:** {supercell_str}\n"
                        f"🔢 **Atoms:** {n_atoms}\n\n"
                        f"⚡ **Total Energy:** {'test'*100} {data.get('energy', 'N/A'):.4f} eV\n\n"
                        f"💪 **Max Force:** {data.get('max_force', 'N/A'):.4f} eV/Å"
                    )
                    
                    st.session_state.history.append(("bot", result_msg))
                    
                    # Save XYZ data for visualization
                    if "structure_xyz" in data:
                        xyz_data = data["structure_xyz"]
                        # Debug: Check XYZ data
                        xyz_lines = [line for line in xyz_data.strip().split('\n') if line.strip()]
                        if len(xyz_lines) > 0:
                            try:
                                num_atoms = int(xyz_lines[0].strip())
                                backend_atoms = data.get('n_atoms', 'N/A')
                                
                                if debug_mode:
                                    st.info(f"📊 **Debug Info:**")
                                    st.write(f"- Received structure with **{num_atoms} atoms** (backend: {backend_atoms})")
                                    st.write(f"- Material: {data.get('material', 'N/A')}")
                                    st.write(f"- Energy: {data.get('energy', 'N/A'):.4f} eV")
                                    
                                    if num_atoms == 1:
                                        st.error("⚠️ **WARNING: Structure has only 1 atom!** Check backend logs.")
                                    
                                    # Show XYZ preview
                                    with st.expander("🔍 View XYZ Data"):
                                        st.code(xyz_data[:1000], language=None)  # First 1000 chars
                                    
                                    # Show parsed request
                                    with st.expander("🔍 View Parsed Request"):
                                        st.json(parsed)
                                    
                                    # Show full response
                                    with st.expander("🔍 View Full Response"):
                                        st.json(data)
                                else:
                                    if num_atoms == 1:
                                        st.warning("⚠️ Only 1 atom detected. Enable Debug Mode for details.")
                                    
                            except ValueError:
                                if debug_mode:
                                    st.warning(f"⚠️ Could not parse atom count. First line: {xyz_lines[0]}")
                        st.session_state.last_structure_xyz = xyz_data
                        
                else:
                    # Try to get error details from response
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", f"HTTP {response.status_code}")
                        if isinstance(error_detail, list) and len(error_detail) > 0:
                            error_detail = error_detail[0].get("msg", str(error_detail[0]))
                    except:
                        error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                    st.error(f"Backend Error: {error_detail}")
                    st.session_state.history.append(("bot", f"❌ Error: {error_detail}"))
            
            except requests.exceptions.ConnectionError as e:
                st.error(f"Connection Failed: Cannot connect to backend at {BACKEND_URL}")
                st.session_state.history.append(("bot", "❌ Backend is offline. Please ensure the backend is running on port 8000."))
            except requests.exceptions.Timeout as e:
                st.error(f"Request Timeout: Backend took too long to respond")
                st.session_state.history.append(("bot", "❌ Request timeout. The backend may be overloaded."))
            except requests.exceptions.RequestException as e:
                st.error(f"Request Error: {e}")
                st.session_state.history.append(("bot", f"❌ Request Error: {str(e)}"))
            except Exception as e:
                st.error(f"Unexpected Error: {e}")
                if debug_mode:
                    import traceback
                    st.code(traceback.format_exc())
                st.session_state.history.append(("bot", f"❌ Error: {str(e)}"))
        
        # Rerun to update chat history immediately
        st.rerun()

# === COLUMN 2: 3D Visualization ===
with col2:
    # st.subheader("🧊 Structure Visualizer")
    st.subheader("🧊 Visualizer")

    if st.session_state.last_structure_xyz:
        # Create a 3D view using py3Dmol
        xyz_data = st.session_state.last_structure_xyz
        
        # Debug: Show XYZ info
        xyz_lines = [line for line in xyz_data.strip().split('\n') if line.strip()]
        if len(xyz_lines) > 0:
            try:
                num_atoms_xyz = int(xyz_lines[0].strip())
                if debug_mode:
                    st.caption(f"📊 **Visualizer Debug:** XYZ file contains {num_atoms_xyz} atoms")
                    if num_atoms_xyz == 1:
                        st.error("⚠️ **CRITICAL: Only 1 atom in XYZ!** Structure generation failed.")
                    # Count unique elements
                    if len(xyz_lines) > 2:
                        elements_in_xyz = set()
                        for line in xyz_lines[2:2+num_atoms_xyz]:
                            if line.strip():
                                parts = line.split()
                                if len(parts) > 0:
                                    elements_in_xyz.add(parts[0])
                        st.caption(f"   Elements found: {elements_in_xyz}")
                else:
                    if num_atoms_xyz == 1:
                        st.warning("⚠️ Only 1 atom detected. Enable Debug Mode for details.")
            except Exception as e:
                if debug_mode:
                    st.warning(f"⚠️ Could not parse XYZ: {e}")
        
        # Debug: Verify XYZ data before visualization
        if debug_mode:
            xyz_preview = xyz_data[:500] if len(xyz_data) > 500 else xyz_data
            with st.expander("🔍 XYZ Data for Visualization"):
                st.code(xyz_preview, language=None)
                st.write(f"Total length: {len(xyz_data)} characters")
        
        try:
            view = py3Dmol.view(width=400, height=400)
            view.addModel(xyz_data, "xyz")
            view.setStyle({'sphere': {'scale': 0.3}, 'stick': {}})
            view.zoomTo()
            view.setBackgroundColor('white')
            
            # Render the molecule
            showmol(view, height=400, width=400)
            
            if debug_mode:
                st.success("✅ Visualization rendered successfully")
        except Exception as e:
            st.error(f"❌ Visualization error: {e}")
            if debug_mode:
                st.code(f"XYZ data that failed:\n{xyz_data[:500]}", language=None)
        
        st.caption("Interactive 3D View: Click and drag to rotate.")
        
        # Download Button
        st.download_button(
            label="Download .XYZ File",
            data=xyz_data,
            file_name="structure.xyz",
            mime="chemical/x-xyz"
        )
    else:
        st.info("Generate a structure to see it here.")
        # Placeholder image for visual appeal before generation
        st.markdown("*(Example: Diamond structure)*") 