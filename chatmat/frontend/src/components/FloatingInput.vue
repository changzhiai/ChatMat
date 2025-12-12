<template>
  <div class="floating-input" :style="styleObject" v-show="positionReady" ref="floatEl">
    <div v-if="showCaption" class="input-caption">Ask me anything about materials</div>
    <form @submit.prevent="submit">
      <div class="input-container">
        <div class="input-row">
          <input
            v-model="text"
            :placeholder="placeholder"
            class="input-field"
            @keydown.enter="submit"
          />
        </div>
        <div class="row-2">
          <select v-model="agent" class="agent-select">
            <option value="Agent">Agent</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="ollama">Ollama</option>
            <option value="gemini">Gemini</option>
          </select>
          <div style="flex: 1"></div>
        </div>
      </div>
      <button type="submit" class="send-btn">Send</button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue';

const props = defineProps({
  anchorRef: { type: Object, default: null },
  placeholder: { type: String, default: 'e.g., Energy of bulk Silicon' },
  isEmpty: { type: Boolean, default: false }
});

const showCaption = computed(() => props.isEmpty);

const emit = defineEmits(['send']);

const text = ref('');
const agent = ref('Agent');
const styleObject = ref({});
const positionReady = ref(false);
let retryTimer = null;

function applyAlignment() {
  try {
    // Get the left column element
    const leftColumn = document.querySelector('.left-column');
    if (!leftColumn) {
      console.log('FloatingInput: left-column not found');
      return false;
    }
    const colRect = leftColumn.getBoundingClientRect();
    const colWidth = colRect.width;
    const colCenter = colRect.left + colWidth / 2;
    
    // Calculate fixed input width (same for both centered and bottom states)
    const inputWidth = Math.min(600, colWidth * 0.85);
    const leftPos = colCenter - inputWidth / 2;

    // Only change vertical position, width stays the same
    if (props.isEmpty) {
      styleObject.value = {
        width: inputWidth + 'px',
        left: leftPos + 'px',
        transform: 'none',
        bottom: 'auto',
        top: '50%',
        marginTop: '-80px'
      };
    } else {
      styleObject.value = {
        width: inputWidth + 'px',
        left: leftPos + 'px',
        transform: 'none',
        bottom: '10px',
        top: 'auto',
        marginTop: '0'
      };
    }
    return true;
  } catch (e) {
    console.warn('FloatingInput alignment error', e);
    return false;
  }
}

function submit() {
  if (!text.value.trim()) return;
  emit('send', {
    text: text.value,
    agent: agent.value
  });
  text.value = '';
  nextTick(() => applyAlignment());
}

onMounted(() => {
  let tries = 0;
  const alignAndReady = () => {
    const ok = applyAlignment();
    if (ok) {
      positionReady.value = true;
    }
    tries++;
    if (ok || tries > 50) {
      clearInterval(retryTimer);
      if (!ok) positionReady.value = true; // Show even if alignment failed
    }
  };
  
  alignAndReady();
  retryTimer = setInterval(alignAndReady, 200);

  window.addEventListener('resize', () => {
    applyAlignment();
  });
});

onBeforeUnmount(() => {
  if (retryTimer) clearInterval(retryTimer);
  window.removeEventListener('resize', applyAlignment);
});
</script>

<style scoped>
.floating-input {
  position: fixed;
  z-index: 100;
  background: transparent;
  border: none;
  padding: 0;
  box-shadow: none;
  transition: left 120ms ease, width 120ms ease, top 150ms ease, bottom 150ms ease;
  box-sizing: border-box;
}

form {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid #d3d3d3;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.04);
  overflow: hidden;
}

.input-caption {
  height: 28px;
  line-height: 28px;
  padding: 0 12px;
  font-size: 1.3rem;
  color: #000000;
  background: transparent;
  font-weight: 600;
  margin-bottom: 12px;
  text-align: center;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.input-row {
  display: flex;
  gap: 8px;
  padding: 8px;
  border-bottom: none;
}

.input-field {
  flex: 1;
  padding: 8px 10px;
  border: none;
  border-radius: 4px;
  font-size: 1em;
  outline: none;
  box-shadow: none;
  background: transparent;
  font-family: inherit;
}

.input-field:focus {
  outline: none;
  box-shadow: none;
}

.row-2 {
  display: flex;
  gap: 8px;
  align-items: center;
  background: #ffffff;
  border: none;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  padding: 6px 8px;
  box-shadow: none;
  margin-top: 0;
}

.agent-select {
  /* Compact dropdown styling (smaller font and height) */
  padding: 4px 8px;
  height: 32px;
  line-height: 24px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.85rem;
  background: #ffffff;
  cursor: pointer;
  outline: none;
}

.agent-select:focus {
  border-color: #0f52ba;
}

.send-btn {
  padding: 10px 16px;
  border-radius: 6px;
  border: none;
  background: #0f52ba;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  transition: background 200ms ease;
}

.send-btn:hover {
  background: #0a3a8a;
}

.send-btn:active {
  transform: scale(0.98);
}

/* Hide visible Send button — form submits on Enter */
.send-btn {
  display: none !important;
}
</style>
