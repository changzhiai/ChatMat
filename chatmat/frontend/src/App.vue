<template>
  <div id="app" class="app-container">
    <Sidebar v-model:debugMode="debugMode" />
    <div class="main-layout">
      <section class="left-column">
        <div class="header">ChatMat</div>
        <ChatHistory :messages="messages" ref="chatHistory" :isEmpty="messages.length === 0" />
      </section>
      <aside class="right-column">
        <Visualizer3D :xyzData="lastXYZ" :debugMode="debugMode" />
      </aside>
    </div>
    <FloatingInput :anchorRef="$refs.chatHistory" @send="onSend" :isEmpty="messages.length === 0" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ChatHistory from './components/ChatHistory.vue';
import FloatingInput from './components/FloatingInput.vue';
import Visualizer3D from './components/Visualizer3D.vue';
import Sidebar from './components/Sidebar.vue';
import { parseMaterialRequest } from './utils/parseRequest.js';
import { sendCalculationRequest } from './api/backend.js';

const messages = ref([]);
const lastXYZ = ref(null);
const debugMode = ref(false);

async function onSend(payload) {
  const { text, agent } = payload;
  
  if (!text.trim()) return;

  // Add user message
  messages.value.push(['user', text]);

  // Parse request
  const parsed = parseMaterialRequest(text);

  // Determine if using LLM
  const useLLM = agent !== 'Agent';
  const llmProvider = useLLM ? agent : null;

  // Add loading message
  const loadingIdx = messages.value.length;
  messages.value.push(['bot', '⏳ Calculating... Please wait.']);

  try {
    const result = await sendCalculationRequest(parsed, useLLM, llmProvider, text);

    if (result.success) {
      const data = result.data;
      const material = data.material || parsed.material_name;
      const nAtoms = data.n_atoms || 'N/A';
      const supercellStr = `${parsed.supercell_dims[0]}×${parsed.supercell_dims[1]}×${parsed.supercell_dims[2]}`;
      const structInfo = parsed.structure_type ? ` (${parsed.structure_type.toUpperCase()})` : '';

      const resultMsg = `
<strong>Structure:</strong> ${material}${structInfo}<br/>
<br/>
📦 <strong>Supercell:</strong> ${supercellStr}<br/>
🔢 <strong>Atoms:</strong> ${nAtoms}<br/>
<br/>
⚡ <strong>Total Energy:</strong> ${data.energy ? data.energy.toFixed(4) : 'N/A'} eV
      `.trim();

      messages.value[loadingIdx] = ['bot', resultMsg];

      // Save XYZ data
      if (data.structure_xyz) {
        lastXYZ.value = data.structure_xyz;

        // Parse atom count for debugging
        const lines = data.structure_xyz.split('\n');
        if (lines.length > 0) {
          try {
            const atomCount = parseInt(lines[0]);
            if (debugMode.value && atomCount === 1) {
              messages.value.push(['bot', '⚠️ <strong>Warning:</strong> Only 1 atom in structure. Check backend logs.']);
            }
          } catch (e) {
            // Silent fail on atom count parsing
          }
        }
      }
    } else {
      messages.value[loadingIdx] = ['bot', `❌ <strong>Error:</strong> ${result.error}`];
    }
  } catch (error) {
    messages.value[loadingIdx] = ['bot', `❌ <strong>Error:</strong> ${String(error)}`];
  }
}
</script>

<style scoped>
#app {
  width: 100%;
  height: 100vh;
  display: flex;
  background: white;
}

.app-container {
  display: flex;
  flex-direction: row;
  height: 100vh;
  width: 100%;
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.header {
  padding: 16px 20px;
  font-size: 1.5em;
  font-weight: 700;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
  background: white;
}

.left-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 60%;
  background: #ffffff;
  border-right: 1px solid #e0e0e0;
  box-sizing: border-box;
}

.right-column {
  flex: 0 0 40%;
  padding: 20px;
  background: white;
  overflow-y: auto;
  box-sizing: border-box;
}

@media (max-width: 1024px) {
  .left-column {
    max-width: 70%;
  }

  .right-column {
    flex: 0 0 30%;
  }
}

@media (max-width: 800px) {
  .main-layout {
    flex-direction: column;
  }

  .left-column {
    max-width: 100%;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }

  .right-column {
    flex: 0 0 40vh;
    border-right: none;
  }
}
</style>
