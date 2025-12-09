# LLM-Based Structure Generation Guide

ChatMat now supports generating crystal structures using Large Language Models (LLMs) like ChatGPT, Claude, and Ollama to interpret natural language descriptions.

## Supported LLM Providers

### 1. OpenAI (ChatGPT)
Use OpenAI's GPT models to generate structures from natural language.

**Setup:**
```bash
# Install package
pip install openai

# Set API key
export OPENAI_API_KEY=your_api_key_here
```

**Usage:**
- Frontend: Check "Use LLM" checkbox and select "openai"
- Backend: Use `use_llm=True` with `llm_provider="openai"`

**Available Models:**
- `gpt-4o-mini` (default, cost-effective)
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

**Example:**
```python
from build_structures import generate_structure_with_llm

atoms = generate_structure_with_llm(
    "Create a 2x2x2 supercell of diamond cubic silicon",
    provider="openai",
    model="gpt-4o-mini"
)
```

### 2. Anthropic (Claude)
Use Anthropic's Claude models for structure generation.

**Setup:**
```bash
# Install package
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY=your_api_key_here
```

**Usage:**
- Frontend: Check "Use LLM" checkbox and select "anthropic"
- Backend: Use `use_llm=True` with `llm_provider="anthropic"`

**Available Models:**
- `claude-3-haiku-20240307` (default, fast and cost-effective)
- `claude-3-sonnet-20240229`
- `claude-3-opus-20240229`

**Example:**
```python
from build_structures import generate_structure_with_llm

atoms = generate_structure_with_llm(
    "Generate FCC aluminum with lattice parameter 4.05 Angstroms",
    provider="anthropic",
    model="claude-3-haiku-20240307"
)
```

### 3. Ollama (Local LLM)
Use local Ollama models - free, runs on your machine, no API key needed!

**Setup:**
```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama3
# or
ollama pull mistral
```

**Usage:**
- Frontend: Check "Use LLM" checkbox and select "ollama"
- Backend: Use `use_llm=True` with `llm_provider="ollama"`

**Available Models:**
- `llama3` (default)
- `mistral`
- `codellama`
- Any model you have installed in Ollama

**Example:**
```python
from build_structures import generate_structure_with_llm

atoms = generate_structure_with_llm(
    "Make a rocksalt structure of sodium chloride",
    provider="ollama",
    model="llama3",
    base_url="http://localhost:11434"  # Default Ollama URL
)
```

## How It Works

1. **Natural Language Input**: User provides a description like "Create a 2x2x2 supercell of diamond cubic silicon"

2. **LLM Processing**: The LLM receives a structured prompt asking it to extract:
   - Material name (e.g., "Si")
   - Structure type (e.g., "diamond")
   - Lattice parameter (if specified)
   - Supercell dimensions (e.g., [2, 2, 2])
   - Compound elements (if applicable)

3. **JSON Response**: LLM returns structured JSON with these parameters

4. **Structure Generation**: The system uses the extracted parameters to generate the actual crystal structure using ASE

## Frontend Usage

### Automatic Detection
The frontend automatically uses LLM for complex descriptions (longer than 10 words without specific identifiers).

### Manual Selection
1. Check the "Use LLM for complex descriptions" checkbox
2. Select your preferred LLM provider
3. Enter your natural language description
4. Click "Generate & Calculate"

### Example Prompts
- "Create a 2x2x2 supercell of diamond cubic silicon"
- "Generate FCC aluminum with lattice parameter 4.05 Angstroms"
- "Make a rocksalt structure of sodium chloride"
- "I need a 3x3x3 supercell of BCC iron"
- "Generate zincblende GaN structure"

## Backend API Usage

### Request Format
```json
{
  "intent": "CALCULATE",
  "material_name": "Si",
  "user_input": "Create a 2x2x2 supercell of diamond cubic silicon",
  "structure_details": {
    "use_llm": true,
    "llm_provider": "openai",
    "llm_params": {
      "model": "gpt-4o-mini"
    },
    "supercell_dims": [1, 1, 1]
  }
}
```

### Python API
```python
from build_structures import generate_structure_with_llm

# Simple usage
atoms = generate_structure_with_llm(
    "Create a 2x2x2 supercell of diamond cubic silicon",
    provider="openai"
)

# With custom parameters
atoms = generate_structure_with_llm(
    "Generate FCC aluminum with lattice parameter 4.05",
    provider="anthropic",
    model="claude-3-sonnet-20240229",
    api_key="your_key"  # Optional if env var is set
)

# Apply supercell after generation
atoms = atoms * (2, 2, 2)
```

## Response Parsing

The system uses intelligent parsing to extract structure parameters from LLM responses:

1. **JSON Extraction**: First tries to extract valid JSON from the response
2. **Regex Fallback**: If JSON parsing fails, uses regex patterns to extract:
   - Element symbols
   - Structure type keywords
   - Lattice parameters
   - Supercell dimensions

## Error Handling

- **Missing API Key**: Clear error message with setup instructions
- **Invalid Response**: Falls back to regex parsing
- **Unsupported Provider**: Lists available providers
- **Network Issues**: Provides timeout and connection error details

## Tips for Best Results

1. **Be Specific**: Include structure type, material name, and dimensions
   - ✅ "Create a 2x2x2 supercell of diamond cubic silicon"
   - ❌ "Make silicon"

2. **Use Standard Terms**: Use common crystal structure names
   - ✅ "FCC", "BCC", "HCP", "diamond", "zincblende", "rocksalt"
   - ❌ "face centered cubic" (works but less efficient)

3. **Specify Lattice Parameters**: If you know the lattice parameter, include it
   - ✅ "FCC aluminum with a=4.05"
   - ✅ "Silicon diamond structure, lattice parameter 5.43 Angstroms"

4. **For Compounds**: Clearly specify both elements
   - ✅ "Sodium chloride rocksalt structure"
   - ✅ "GaN zincblende"

## Cost Considerations

- **OpenAI**: Pay per token (~$0.15-0.60 per 1M input tokens, ~$0.60-2.00 per 1M output tokens)
- **Anthropic**: Pay per token (~$0.25-3.00 per 1M input tokens, ~$0.75-15.00 per 1M output tokens)
- **Ollama**: Free! Runs locally on your machine

## Privacy

- **OpenAI/Anthropic**: Data is sent to their servers (check their privacy policies)
- **Ollama**: Completely local, no data leaves your machine

