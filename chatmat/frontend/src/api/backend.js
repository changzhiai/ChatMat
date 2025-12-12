/**
 * Backend API connector for FastAPI server
 */

const BACKEND_URL = "http://127.0.0.1:8000/calculate/";

export async function sendCalculationRequest(parsed, useGPU = false, llmProvider = null, userInput = '') {
  // Ensure all values are properly typed
  const latticeParam = parsed.lattice_parameter !== null ? parseFloat(parsed.lattice_parameter) : null;

  const payload = {
    intent: "CALCULATE",
    material_name: String(parsed.material_name || "Si"),
    user_input: String(userInput || parsed.user_input || ""),
    structure_details: {
      supercell_dims: parsed.supercell_dims.map(x => parseInt(x)),
      structure_type: parsed.structure_type ? String(parsed.structure_type) : null,
      lattice_parameter: latticeParam,
      compound: parsed.compound ? parsed.compound.map(x => String(x)) : null,
      source_type: parsed.source_type ? String(parsed.source_type) : null,
      source_params: parsed.source_params || {},
      use_llm: Boolean(useGPU),
      llm_provider: llmProvider || null,
      llm_params: useGPU && llmProvider ? {
        model: llmProvider === "openai" ? "gpt-4o-mini" :
               llmProvider === "anthropic" ? "claude-3-haiku-20240307" :
               llmProvider === "ollama" ? "llama3" : null
      } : {}
    }
  };

  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      const data = await response.json();
      return { success: true, data };
    } else {
      const errorData = await response.json().catch(() => ({}));
      const errorDetail = errorData.detail ? 
        (Array.isArray(errorData.detail) ? errorData.detail[0]?.msg : errorData.detail) :
        `HTTP ${response.status}`;
      return { success: false, error: errorDetail };
    }
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
      return { 
        success: false, 
        error: `Connection Failed: Cannot connect to backend at ${BACKEND_URL}` 
      };
    }
    return { success: false, error: String(error) };
  }
}
