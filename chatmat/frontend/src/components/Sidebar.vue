<template>
  <aside class="sidebar">
    <div class="sidebar-content">
      <h2>⚛️ ChatMat Control</h2>
      <p>Calculate energy and forces for material structures.</p>

      <div class="section">
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            :checked="debugMode"
            @change="$emit('update:debugMode', $event.target.checked)"
          />
          <span>🐛 Debug Mode</span>
        </label>
      </div>

      <div class="section">
        <h3>Try these prompts:</h3>
        <div class="prompts">
          <code>Calculate energy for a 2x2x2 supercell of Silicon</code>
          <code>Get forces for bulk Gold (Au)</code>
          <code>Generate FCC Aluminum with 3x3x3 supercell</code>
          <code>Create BCC Iron structure</code>
          <code>Calculate energy for NaCl (rocksalt)</code>
          <code>Generate GaN zincblende structure</code>
          <code>Create HCP Titanium with a=2.95</code>
        </div>
      </div>

      <hr />

      <div class="section">
        <h3>Supported:</h3>
        <p><strong>Elements:</strong> Si, Al, Au, Fe, Ti, Mg, Ni, Zn, C, Ge, etc.</p>
        <p><strong>Compounds:</strong> NaCl, GaN, TiO2, SiO2, etc.</p>
        <p><strong>Structures:</strong> FCC, BCC, HCP, Diamond, Zincblende, Rocksalt, Wurtzite, Perovskite</p>
      </div>

      <hr />

      <div class="section">
        <h3>External Sources:</h3>
        <div class="prompts">
          <code>Fetch from Materials Project: mp-149</code>
          <code>Fetch from COD: cod-2000001</code>
          <code>Load from URL: https://example.com/structure.cif</code>
          <code>Load from file: /path/to/structure.cif</code>
        </div>
      </div>

      <hr />

      <div class="section">
        <h3>LLM Generation:</h3>
        <div class="prompts">
          <code>Create a 2x2x2 supercell of diamond cubic silicon</code>
          <code>Generate FCC aluminum with lattice parameter 4.05</code>
          <code>Make a rocksalt structure of sodium chloride</code>
        </div>
        <p style="font-size: 0.9em; margin-top: 10px;"><strong>💡 Tip:</strong> Select an LLM provider (OpenAI, Anthropic, Ollama) for complex descriptions.</p>
      </div>

      <hr />

      <div class="section info-box">
        <p>📌 Ensure FastAPI backend is running on port 8000.</p>
        <p>📌 See docs/ folder for advanced examples.</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  debugMode: { type: Boolean, required: true }
});

defineEmits(['update:debugMode']);
</script>

<style scoped>
.sidebar {
  width: 280px;
  padding: 20px;
  background: #f5f5f5;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  max-height: 100vh;
  box-sizing: border-box;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sidebar h2 {
  margin: 0 0 5px 0;
  font-size: 1.3em;
  color: #333;
}

.sidebar > .sidebar-content > p {
  margin: 0;
  font-size: 0.9em;
  color: #666;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section h3 {
  margin: 10px 0 8px 0;
  font-size: 0.95em;
  color: #333;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.section p {
  margin: 5px 0;
  font-size: 0.85em;
  line-height: 1.4;
  color: #555;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  cursor: pointer;
}

.checkbox-label span {
  font-weight: 600;
}

.prompts {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prompts code {
  display: block;
  padding: 8px;
  background: #ffffff;
  border-left: 3px solid #0f52ba;
  border-radius: 4px;
  font-size: 0.8em;
  color: #333;
  font-family: 'Courier New', monospace;
  word-break: break-word;
  cursor: pointer;
  transition: background 150ms ease;
}

.prompts code:hover {
  background: #e3f2fd;
}

hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 10px 0;
}

.info-box {
  background: #fff9e6;
  border-left: 4px solid #ff9800;
  padding: 10px;
  border-radius: 4px;
}

.info-box p {
  margin: 4px 0;
  font-size: 0.85em;
}

@media (max-width: 1200px) {
  .sidebar {
    width: 250px;
  }
}

@media (max-width: 900px) {
  .sidebar {
    display: none;
  }
}
</style>
