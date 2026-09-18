<template>
  <div>
    <!-- Floating Chat Trigger Button -->
    <button
      @click="store.toggleChat()"
      class="fixed bottom-6 right-6 z-40 w-14 h-14 bg-gradient-to-tr from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-full shadow-xl flex items-center justify-center transition-all hover:scale-105 focus:outline-none"
    >
      <MessageSquareIcon v-if="!store.isChatOpen" class="w-6 h-6" />
      <XIcon v-else class="w-6 h-6" />
    </button>

    <!-- Floating Chatbot Drawer Panel -->
    <div
      v-if="store.isChatOpen"
      class="fixed bottom-24 right-6 z-40 w-96 max-w-[calc(100vw-3rem)] h-[520px] bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col justify-between overflow-hidden animate-in fade-in slide-in-from-bottom-5"
    >
      <!-- Chat Header -->
      <div class="p-4 bg-gradient-to-r from-sky-600 to-indigo-600 text-white flex items-center justify-between">
        <div class="flex items-center gap-2">
          <BotIcon class="w-5 h-5 text-sky-200" />
          <div>
            <h3 class="text-sm font-bold leading-tight">Dataset AI Assistant</h3>
            <p class="text-[10px] text-sky-200">Grounded strictly in uploaded Excel file</p>
          </div>
        </div>
        <button @click="store.toggleChat()" class="text-sky-200 hover:text-white">
          <XIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- Messages Body -->
      <div ref="chatContainer" class="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50 text-xs">
        <div
          v-for="msg in store.chatMessages"
          :key="msg.id"
          :class="['flex flex-col', msg.sender === 'user' ? 'items-end' : 'items-start']"
        >
          <div
            :class="[
              'p-3 rounded-2xl max-w-[85%] leading-relaxed shadow-sm',
              msg.sender === 'user'
                ? 'bg-sky-600 text-white rounded-tr-none'
                : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none'
            ]"
          >
            <p v-html="formatMarkdown(msg.text)"></p>
            
            <!-- SQL Execution Tag if available -->
            <div v-if="msg.sql" class="mt-2 pt-1.5 border-t border-slate-100 text-[10px] font-mono text-slate-500">
              ⚡ DuckDB Query executed
            </div>
          </div>
          <span class="text-[10px] text-slate-400 mt-1 px-1">{{ msg.timestamp }}</span>
        </div>

        <!-- Animated AI Processing / Thinking Indicator -->
        <div v-if="store.isChatProcessing" class="flex flex-col items-start space-y-1">
          <div class="p-3 bg-white text-slate-700 border border-slate-200 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-2">
            <div class="flex items-center gap-1">
              <span class="w-2 h-2 rounded-full bg-sky-500 animate-pulse"></span>
              <span class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse [animation-delay:0.2s]"></span>
              <span class="w-2 h-2 rounded-full bg-sky-600 animate-pulse [animation-delay:0.4s]"></span>
            </div>
            <span class="text-xs font-semibold text-slate-600 ml-1">AI is thinking & analyzing dataset...</span>
          </div>
        </div>
      </div>

      <!-- Chat Input Footer -->
      <form @submit.prevent="handleSend" class="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
        <input
          type="text"
          v-model="inputQuery"
          :disabled="store.isChatProcessing"
          placeholder="Ask a question about your dataset..."
          class="flex-1 px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 disabled:opacity-60"
        />
        <button
          type="submit"
          :disabled="!inputQuery.trim() || store.isChatProcessing"
          class="p-2 bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white rounded-xl transition-colors flex items-center justify-center"
        >
          <Loader2Icon v-if="store.isChatProcessing" class="w-4 h-4 animate-spin" />
          <SendIcon v-else class="w-4 h-4" />
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { MessageSquare as MessageSquareIcon, X as XIcon, Bot as BotIcon, Send as SendIcon, Loader2 as Loader2Icon } from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';

const store = useDatasetStore();
const inputQuery = ref<string>('');
const chatContainer = ref<HTMLDivElement | null>(null);

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
}

watch(() => store.chatMessages.length, () => scrollToBottom());
watch(() => store.isChatProcessing, () => scrollToBottom());

function handleSend() {
  if (inputQuery.value.trim() && !store.isChatProcessing) {
    store.postChatMessage(inputQuery.value.trim());
    inputQuery.value = '';
    scrollToBottom();
  }
}

function formatMarkdown(text: string): string {
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}
</script>
