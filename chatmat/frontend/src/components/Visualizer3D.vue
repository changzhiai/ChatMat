<template>
  <div class="visualizer-container">
    <h3>🧊 Visualizer</h3>
    <div v-if="!xyzData" class="placeholder">
      <p>Generate a structure to see it here.</p>
      <p style="font-size: 0.9em; color: #999;">(Example: Diamond structure)</p>
    </div>
    <div v-else class="viz-content">
      <div ref="molViewerContainer" class="mol-viewer"></div>
      <div v-if="atomCount" class="info">
        <p>📊 <strong>Atoms:</strong> {{ atomCount }}</p>
        <p v-if="debugInfo" style="font-size: 0.85em; color: #666;">{{ debugInfo }}</p>
        <div v-for="(line, index) in xyzLines" :key="index" class="xyz-coordinates">
          <p v-if="index >= 2">{{ line }}</p>
        </div>
      </div>
      <div class="controls-row">
        <button @click="resetStructure" class="control-btn">🔄 Reset</button>
        <button @click="downloadXYZ" class="control-btn">⬇️ Download XYZ</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue';

const props = defineProps({
  xyzData: String,
  debugMode: { type: Boolean, default: false }
});

const molViewerContainer = ref(null);
const atomCount = ref(0);
const debugInfo = ref('');
const xyzLines = ref([]);
let viewerLoaded = false;

function parseXYZ() {
  if (!props.xyzData) {
    atomCount.value = 0;
    debugInfo.value = '';
    return;
  }

  const lines = props.xyzData.trim().split('\n').filter(l => l.trim());
  if (lines.length > 0) {
    try {
      atomCount.value = parseInt(lines[0].trim());
      if (props.debugMode && atomCount.value > 0) {
        const elements = new Set();
        for (let i = 2; i < Math.min(2 + atomCount.value, lines.length); i++) {
          const parts = lines[i].split(/\s+/);
          if (parts.length > 0) {
            elements.add(parts[0]);
          }
        }
        debugInfo.value = `Elements: ${Array.from(elements).join(', ')}`;
      }
    } catch (e) {
      if (props.debugMode) {
        debugInfo.value = `Parse error: ${e.message}`;
      }
    }
  }
}

function load3DmolScript() {
  return new Promise((resolve, reject) => {
    if (window.$3Dmol) {
      resolve();
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://3Dmol.org/build/3Dmol-min.js';
    script.async = true;
    script.onerror = () => {
      console.error('Failed to load 3Dmol library');
      reject(new Error('Failed to load 3Dmol'));
    };
    script.onload = () => {
      // Wait for the library to be ready
      setTimeout(() => resolve(), 100);
    };
    document.head.appendChild(script);
  });
}

async function renderMolecule() {
  // Ensure DOM updates have completed so ref is populated
  await nextTick();

  if (!props.xyzData) {
    console.log('Skipping render: no xyzData');
    return;
  }

  if (!molViewerContainer.value) {
    console.log('Skipping render: container not yet available');
    // try once more shortly after
    setTimeout(() => {
      renderMolecule();
    }, 150);
    return;
  }

  try {
    // Load the 3Dmol library if not already loaded
    if (!viewerLoaded) {
      await load3DmolScript();
      viewerLoaded = true;
    }

    // Wait for DOM to be ready
    await nextTick();

    if (!window.$3Dmol) {
      console.error('3Dmol library not available');
      debugInfo.value = '3Dmol viewer unavailable';
      return;
    }

    const viewerId = molViewerContainer.value.id;
    console.log('Creating viewer for container:', viewerId);

    // Clear previous viewer if exists
    if (window.currentViewer) {
      window.currentViewer.clear();
    }

    // Create viewer with explicit config
    const viewer = window.$3Dmol.createViewer(molViewerContainer.value, {
      backgroundColor: 'white',
      antialias: true
    });

    if (!viewer) {
      console.error('Failed to create viewer');
      debugInfo.value = 'Failed to create viewer';
      return;
    }

    console.log('Viewer created, adding model...');

    // Add model
    viewer.addModel(props.xyzData, 'xyz');

    // Set style
    viewer.setStyle({}, {
      sphere: { colorscheme: 'Jmol', scale: 0.25 },
      stick: { colorscheme: 'Jmol', radius: 0.15 }
    });

    // Add thin arrows for x, y, z axes at the bottom-left corner
    viewer.addArrow({ start: { x: -1, y: -1, z: -1 }, end: { x: 0, y: -1, z: -1 }, color: 'red', radius: 0.02 }); // Thin X-axis
    viewer.addArrow({ start: { x: -1, y: -1, z: -1 }, end: { x: -1, y: 0, z: -1 }, color: 'green', radius: 0.02 }); // Thin Y-axis
    viewer.addArrow({ start: { x: -1, y: -1, z: -1 }, end: { x: -1, y: -1, z: 0 }, color: 'blue', radius: 0.02 }); // Thin Z-axis

    // Relocate labels to match the new arrowhead positions
    // Update labels to set the background to white
    viewer.addLabel('x', { position: { x: 0, y: -1, z: -1 }, fontColor: 'red', fontSize: 12, backgroundColor: 'white' });
    viewer.addLabel('y', { position: { x: -1., y: 0, z: -1.2 }, fontColor: 'green', fontSize: 12, backgroundColor: 'white' });
    viewer.addLabel('z', { position: { x: -1, y: -1, z: 0 }, fontColor: 'blue', fontSize: 12, backgroundColor: 'white' });

    // Axes labels removed per user request (show axes glyphs only)

    // Set background and render
    viewer.setBackgroundColor('white');
    viewer.zoomTo();
    viewer.render();

    console.log('Molecule rendered successfully');
    window.currentViewer = viewer;
    debugInfo.value = '✓ Rendered';
  } catch (e) {
    console.error('Visualization error:', e);
    debugInfo.value = `Error: ${e.message}`;
  }
}

function downloadXYZ() {
  if (!props.xyzData) return;
  const blob = new Blob([props.xyzData], { type: 'chemical/x-xyz' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'structure.xyz';
  a.click();
  URL.revokeObjectURL(url);
}

// Add a reset button to control the structure
const resetStructure = () => {
  if (window.currentViewer) {
    window.currentViewer.zoomTo(); // Reset the zoom and orientation
    window.currentViewer.render();
  }
};

/* Ensure renderMolecule is called after xyzData changes */
watch(
  () => props.xyzData,
  async (newVal) => {
    console.log('XYZ data changed, new length:', newVal?.length);
    parseXYZ();
    if (newVal) {
      await nextTick(); // Ensure DOM updates are complete
      renderMolecule();
    }
  },
  { immediate: true }
);

onMounted(() => {
  console.log('Visualizer mounted');
  parseXYZ();

  if (molViewerContainer.value && !molViewerContainer.value.id) {
    molViewerContainer.value.id = 'mol-viewer-' + Date.now();
  }

  if (props.xyzData) {
    renderMolecule();
  }
});
</script>

<style scoped>
.visualizer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}

.visualizer-container h3 {
  margin: 0;
  color: black; /* Change the heading color to black */
}

.placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  text-align: center;
}

.placeholder p {
  margin: 5px 0;
}

.viz-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mol-viewer {
  flex: 1;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #f9f9f9;
  min-height: 300px;
  width: 100%;
  height: 100%;
  position: relative;
}

.info {
  padding: 10px;
  background: #f0f8ff;
  border-left: 4px solid #0f52ba;
  border-radius: 4px;
  font-size: 0.9em;
}

.info p {
  margin: 4px 0;
}

.controls-row {
  display: flex;
  gap: 10px;
  justify-content: flex-start;
  margin-top: 10px;
}

.control-btn {
  padding: 8px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: background 200ms ease;
  width: 150px; /* Ensure both buttons have the same width */
  text-align: center;
}

.control-btn:hover {
  background: #0056b3;
}

.xyz-coordinates {
  font-size: 0.85em;
  color: #444;
  margin-left: 10px;
}
</style>
