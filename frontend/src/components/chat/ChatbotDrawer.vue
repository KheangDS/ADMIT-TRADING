<template>
  <div>
    <!-- Floating Chat Trigger Button -->
    <button
      @click="store.toggleChat()"
      class="fixed bottom-6 right-6 z-40 w-14 h-14 bg-gradient-to-tr from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-full shadow-2xl flex items-center justify-center transition-all hover:scale-105 focus:outline-none cursor-pointer"
      title="Open Dataset AI Assistant"
    >
      <MessageSquareIcon v-if="!store.isChatOpen" class="w-6 h-6" />
      <XIcon v-else class="w-6 h-6" />
    </button>

    <!-- Floating Chatbot Drawer Panel -->
    <div
      v-if="store.isChatOpen"
      class="fixed bottom-24 right-4 sm:right-6 z-40 w-[420px] sm:w-[480px] md:w-[520px] max-w-[calc(100vw-2rem)] h-[620px] max-h-[82vh] bg-white rounded-3xl shadow-2xl border border-slate-200/90 flex flex-col justify-between overflow-hidden animate-in fade-in slide-in-from-bottom-4"
    >
      <!-- Chat Header -->
      <div class="px-5 py-3.5 bg-gradient-to-r from-slate-900 via-sky-950 to-indigo-950 text-white flex items-center justify-between border-b border-slate-800 shadow-sm">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-sky-500/20 border border-sky-400/30 flex items-center justify-center text-sky-300">
            <BotIcon class="w-5 h-5" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-sm font-black tracking-tight text-white">Trade AI Intelligence</h3>
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </div>
            <p class="text-[11px] text-slate-300">Grounded strictly in active trade dataset</p>
          </div>
        </div>
        <div class="flex items-center gap-1">
          <button
            @click="clearChat"
            class="cursor-pointer p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
            title="Clear Chat History"
          >
            <RotateCcwIcon class="w-3.5 h-3.5" />
          </button>
          <button
            @click="store.toggleChat()"
            class="cursor-pointer p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
            title="Close Assistant"
          >
            <XIcon class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Quick Suggestion Chips (Shown on Start) -->
      <div v-if="store.chatMessages.length <= 1" class="px-4 py-2.5 bg-sky-50/70 border-b border-sky-100 flex items-center gap-1.5 overflow-x-auto text-[11px]">
        <span class="text-slate-500 font-semibold shrink-0">Suggestions:</span>
        <button
          v-for="chip in quickChips"
          :key="chip"
          @click="sendPrompt(chip)"
          class="cursor-pointer shrink-0 px-2.5 py-1 rounded-full bg-white text-sky-800 border border-sky-200/80 hover:bg-sky-100/60 transition-all font-medium"
        >
          {{ chip }}
        </button>
      </div>

      <!-- Messages Body -->
      <div ref="chatContainer" class="flex-1 p-4 sm:p-5 overflow-y-auto space-y-4 bg-slate-50/70 text-xs">
        <div
          v-for="msg in store.chatMessages"
          :key="msg.id"
          :class="['flex flex-col', msg.sender === 'user' ? 'items-end' : 'items-start']"
        >
          <!-- User Message Bubble -->
          <div
            v-if="msg.sender === 'user'"
            class="p-3.5 px-4 rounded-2xl rounded-tr-none bg-gradient-to-r from-sky-600 to-indigo-600 text-white max-w-[88%] leading-relaxed shadow-sm font-medium"
          >
            <p class="whitespace-pre-wrap">{{ msg.text }}</p>
          </div>

          <!-- AI Message Card (Structured & Formatted) -->
          <div
            v-else
            class="p-4 sm:p-5 rounded-2xl rounded-tl-none bg-white text-slate-800 border border-slate-200/80 max-w-[94%] shadow-sm space-y-2 relative group"
          >
            <!-- Formatted Markdown Content -->
            <div
              class="ai-response-content text-slate-700 leading-relaxed space-y-2.5"
              v-html="renderFormattedResponse(msg.text)"
            ></div>

            <!-- Card Action Footer (Copy & SQL Tag) -->
            <div class="pt-2 mt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
              <div class="flex items-center gap-1.5">
                <span v-if="msg.sql" class="inline-flex items-center gap-1 font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded-md border border-sky-100">
                  ⚡ DuckDB Verified
                </span>
                <span v-else class="text-slate-400">Dataset Grounded</span>
              </div>

              <button
                @click="copyToClipboard(msg.text, msg.id)"
                class="cursor-pointer inline-flex items-center gap-1 text-slate-400 hover:text-sky-600 transition-colors px-1.5 py-0.5 rounded"
                title="Copy Answer"
              >
                <CheckIcon v-if="copiedId === msg.id" class="w-3 h-3 text-emerald-600" />
                <CopyIcon v-else class="w-3 h-3" />
                <span>{{ copiedId === msg.id ? 'Copied' : 'Copy' }}</span>
              </button>
            </div>
          </div>

          <span class="text-[10px] text-slate-400 mt-1 px-1.5">{{ msg.timestamp }}</span>
        </div>

        <!-- Animated AI Thinking Indicator -->
        <div v-if="store.isChatProcessing" class="flex flex-col items-start space-y-1">
          <div class="p-4 bg-white text-slate-700 border border-slate-200/90 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-3">
            <div class="w-6 h-6 rounded-lg bg-sky-50 flex items-center justify-center">
              <Loader2Icon class="w-4 h-4 text-sky-600 animate-spin" />
            </div>
            <div>
              <p class="text-xs font-bold text-slate-800">Synthesizing dataset intelligence...</p>
              <p class="text-[10px] text-slate-400">Querying DuckDB analytical engine & Gemini LLM</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Input Footer -->
      <form @submit.prevent="handleSend" class="p-3 sm:p-3.5 bg-white border-t border-slate-200/90 flex items-center gap-2">
        <input
          type="text"
          v-model="inputQuery"
          :disabled="store.isChatProcessing"
          placeholder="Ask anything about commodities, prices, or destinations..."
          class="flex-1 px-3.5 py-2.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500 disabled:opacity-60 transition-all font-medium text-slate-800 placeholder:text-slate-400"
        />
        <button
          type="submit"
          :disabled="!inputQuery.trim() || store.isChatProcessing"
          class="cursor-pointer px-3.5 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 disabled:opacity-40 text-white rounded-xl transition-all shadow-xs flex items-center justify-center shrink-0 font-bold"
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
import {
  MessageSquare as MessageSquareIcon,
  X as XIcon,
  Bot as BotIcon,
  Send as SendIcon,
  Loader2 as Loader2Icon,
  Copy as CopyIcon,
  Check as CheckIcon,
  RotateCcw as RotateCcwIcon
} from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';

const store = useDatasetStore();
const inputQuery = ref<string>('');
const chatContainer = ref<HTMLDivElement | null>(null);
const copiedId = ref<string | null>(null);

const quickChips = [
  'Top export commodities by revenue',
  'Destination market concentration',
  'Monthly export timeline & peak season',
  'Highest unit price HS8 commodities'
];

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
}

watch(() => store.chatMessages.length, () => scrollToBottom());
watch(() => store.isChatProcessing, () => scrollToBottom());

function sendPrompt(prompt: string) {
  if (!store.isChatProcessing) {
    store.postChatMessage(prompt);
    scrollToBottom();
  }
}

function handleSend() {
  if (inputQuery.value.trim() && !store.isChatProcessing) {
    store.postChatMessage(inputQuery.value.trim());
    inputQuery.value = '';
    scrollToBottom();
  }
}

function clearChat() {
  store.chatMessages = [
    {
      id: 'welcome',
      sender: 'ai',
      text: 'Hello! 👋 I am your AI Agricultural Trade Assistant. Ask me any question grounded strictly in your uploaded trade dataset!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ];
}

async function copyToClipboard(text: string, id: string) {
  try {
    await navigator.clipboard.writeText(text);
    copiedId.value = id;
    setTimeout(() => {
      if (copiedId.value === id) copiedId.value = null;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy message:', err);
  }
}

/**
 * Structured Markdown Parser
 * Converts raw LLM output (### Headings, Bullet Lists, Numbered Lists, Dividers, Bold Text)
 * into rich, visually structured HTML with clear visual hierarchy.
 */
function renderFormattedResponse(rawText: string): string {
  if (!rawText) return '';

  let text = rawText.trim();

  // 1. Format Section Dividers
  text = text.replace(/^(?:---|___|\*\*\*)\s*$/gm, '<hr class="my-3 border-slate-200" />');

  // 1.5 Format Markdown Tables
  text = text.replace(/((?:\|[^\n]+\|\r?\n)+)/g, (tableMatch) => {
    const rows = tableMatch.trim().split('\n').map(r => r.trim()).filter(Boolean);
    if (rows.length < 2) return tableMatch;
    let html = '<div class="overflow-x-auto my-2.5 rounded-xl border border-slate-200 shadow-xs"><table class="w-full text-left text-xs border-collapse">';
    let isHeader = true;
    for (const row of rows) {
      if (/^\|[\s\-:|]+\|$/.test(row)) {
        isHeader = false;
        continue;
      }
      const cells = row.split('|').slice(1, -1).map(c => c.trim());
      if (isHeader) {
        html += '<thead class="bg-slate-100 text-slate-700 font-bold uppercase text-[10px] tracking-wider border-b border-slate-200"><tr>';
        cells.forEach(c => { html += `<th class="py-2 px-3">${c}</th>`; });
        html += '</tr></thead><tbody>';
        isHeader = false;
      } else {
        html += '<tr class="border-b border-slate-100 hover:bg-slate-50 transition-colors">';
        cells.forEach(c => { html += `<td class="py-2 px-3 text-slate-700">${c}</td>`; });
        html += '</tr>';
      }
    }
    html += '</tbody></table></div>';
    return html;
  });

  // 2. Format Headings (### 1. Key Insights -> Styled Badge Heading)
  text = text.replace(/^###\s*(?:(\d+)\.\s*)?([^\n]+)/gm, (_match, num, title) => {
    const numBadge = num
      ? `<span class="w-5 h-5 rounded-md bg-sky-100 text-sky-800 font-extrabold text-[11px] flex items-center justify-center shrink-0 border border-sky-200">${num}</span>`
      : `<span class="w-2 h-3.5 bg-gradient-to-b from-sky-500 to-indigo-600 rounded-full shrink-0"></span>`;
    return `
      <div class="flex items-center gap-2 pt-2.5 pb-1 mt-1 border-b border-slate-100">
        ${numBadge}
        <h4 class="text-xs font-black uppercase tracking-wider text-slate-900">${title.trim()}</h4>
      </div>
    `;
  });

  // 3. Format Subheadings (## Subtitle)
  text = text.replace(/^##\s*([^\n]+)/gm, `
    <h4 class="text-xs font-bold text-slate-800 mt-2 mb-1">$1</h4>
  `);

  // 4. Format Numbered Lists (1. Item -> Styled Step)
  text = text.replace(/^(\d+)\.\s+([^\n]+)/gm, `
    <div class="flex items-start gap-2.5 my-1.5 pl-1">
      <span class="w-4 h-4 rounded-full bg-slate-100 text-slate-700 font-bold text-[10px] flex items-center justify-center shrink-0 mt-0.5 border border-slate-200">$1</span>
      <div class="flex-1 text-slate-700 leading-relaxed">$2</div>
    </div>
  `);

  // 5. Format Bullet Points (* Item or - Item -> Clean Dot List)
  text = text.replace(/^[\*\-]\s+([^\n]+)/gm, `
    <div class="flex items-start gap-2 my-1 pl-1">
      <span class="text-sky-600 font-black text-sm leading-none shrink-0 mt-0.5">•</span>
      <div class="flex-1 text-slate-700 leading-relaxed">$1</div>
    </div>
  `);

  // 6. Format Bold Text (**text**)
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-black text-slate-900">$1</strong>');

  // 7. Format Inline Code (`code`)
  text = text.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 text-[11px] font-mono font-bold bg-slate-100 text-sky-700 rounded border border-slate-200">$1</code>');

  // 8. Format Italic / Notes (*Note: ...*)
  text = text.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<span class="italic text-slate-500 text-[11px]">$1</span>');

  // 9. Split remaining blocks into clean paragraphs
  const paragraphs = text.split(/\n{2,}/);
  return paragraphs
    .map(p => {
      const trimmed = p.trim();
      if (
        trimmed.startsWith('<div class="flex') ||
        trimmed.startsWith('<div class="overflow-x-auto') ||
        trimmed.startsWith('<hr') ||
        trimmed.startsWith('<h4')
      ) {
        return trimmed;
      }
      return `<p class="leading-relaxed mb-1.5 text-slate-700">${trimmed.replace(/\n/g, '<br/>')}</p>`;
    })
    .join('');
}
</script>

<style scoped>
:deep(.ai-response-content strong) {
  color: #0f172a;
}
:deep(.ai-response-content h4) {
  letter-spacing: 0.025em;
}
:deep(.ai-response-content hr) {
  border-color: #e2e8f0;
}
</style>
