<template>
  <div class="chat-history-wrapper" :class="{ 'empty-centered': isEmpty }" ref="wrapper">
    <div v-if="messages.length > 0">
      <div v-for="(msg, idx) in messages" :key="idx" class="chat-container" :class="msg[0] === 'user' ? 'user-msg' : 'bot-msg'">
        <span v-if="msg[0] !== 'user'">🤖 </span>
        <span v-html="msg[1]"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';

const props = defineProps({
  messages: {
    type: Array,
    required: true
  },
  isEmpty: {
    type: Boolean,
    default: false
  }
});

const wrapper = ref(null);

// Auto-scroll to bottom when messages change
watch(() => props.messages, async () => {
  await nextTick();
  if (wrapper.value) {
    wrapper.value.scrollTop = wrapper.value.scrollHeight;
  }
}, { deep: true });
</script>

<style scoped>
.chat-history-wrapper {
  /* Let this component take remaining space inside the left column (below header) */
  flex: 1 1 auto;
  min-height: 0; /* allow proper flex children scrolling */
  overflow-y: auto;
  padding: 0 20px 120px 20px;
  background: #ffffff;
  border-radius: 8px;
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
  margin-top: 10px; /* Added 10px margin to the top of the chat history block */
}

/* When empty/centered: center content and limit height */
.chat-history-wrapper.empty-centered {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  /* Use full available height inside the column so centering is between header and bottom */
  height: 100%;
}

.centered-prompt {
  text-align: center;
  font-size: 1.2em;
  color: #999;
  padding: 40px 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #ffffff;
  text-align: center;
  padding: 40px 20px;
}

.empty-state h2 {
  margin: 20px 0 10px;
  font-size: 2em;
  color: #333;
}

.empty-state p {
  font-size: 1.1em;
  color: #666;
}

.chat-container {
  padding: 12px 15px;
  margin-bottom: 12px;
  border-radius: 8px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-msg {
  text-align: left;
  background: #e3f2fd;
  color: #0f52ba;
  font-weight: 600;
  border-left: 4px solid #0f52ba;
}

.bot-msg {
  text-align: left;
  background: #f5f5f5;
  color: #333;
  border-left: 4px solid #4caf50;
  line-height: 1.6;
}

.bot-msg :deep(strong) {
  color: #0f52ba;
}

.bot-msg :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}
</style>
