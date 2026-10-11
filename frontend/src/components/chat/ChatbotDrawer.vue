<template>
  <div>
    <!-- Floating Chat Trigger Button -->
    <button
      @click="store.toggleChat()"
      class="fixed bottom-6 right-6 z-40 w-14 h-14 bg-gradient-to-tr from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-full shadow-2xl flex items-center justify-center transition-all hover:scale-105 focus:outline-none cursor-pointer group"
      title="Open Dataset AI Assistant (Coming Soon)"
    >
      <div class="relative flex items-center justify-center">
        <MessageSquareIcon v-if="!store.isChatOpen" class="w-6 h-6" />
        <XIcon v-else class="w-6 h-6" />
        <span 
          v-if="!store.isChatOpen" 
          class="absolute -top-3.5 -right-3 px-1.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-amber-400 text-slate-950 border border-white shadow-xs"
        >
          Soon
        </span>
      </div>
    </button>

    <!-- Floating Chatbot Drawer Panel (Coming Soon Experience) -->
    <div
      v-if="store.isChatOpen"
      class="fixed bottom-20 sm:bottom-24 inset-x-3 sm:inset-x-auto sm:right-6 z-40 sm:w-[460px] md:w-[490px] h-[calc(100vh-6.5rem)] sm:h-[600px] max-h-[85vh] bg-white rounded-2xl sm:rounded-3xl shadow-2xl border border-slate-200/90 flex flex-col justify-between overflow-hidden animate-in fade-in slide-in-from-bottom-4"
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
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30">
                Coming Soon
              </span>
            </div>
            <p class="text-[11px] text-slate-300">Agricultural data assistant</p>
          </div>
        </div>
        <button
          @click="store.toggleChat()"
          class="cursor-pointer p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          title="Close"
        >
          <XIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- Main Coming Soon Showcase Body -->
      <div class="flex-1 p-5 sm:p-6 overflow-y-auto space-y-5 bg-gradient-to-b from-slate-50 via-white to-slate-50 text-slate-700">
        <!-- Hero Graphic & Badge -->
        <div class="text-center space-y-3 pt-2">
          <div class="relative w-16 h-16 mx-auto">
            <div class="absolute inset-0 bg-sky-500/20 rounded-2xl blur-lg animate-pulse"></div>
            <div class="relative w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white flex items-center justify-center shadow-lg border border-sky-300/30">
              <SparklesIcon class="w-8 h-8 text-sky-200" />
            </div>
          </div>

          <div class="space-y-1.5">
            <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-200 text-xs font-bold">
              <ClockIcon class="w-3.5 h-3.5 text-sky-600" />
              <span>Feature in Active Development</span>
            </div>
            <h4 class="text-lg font-black text-slate-900 tracking-tight">
              AI Trade Assistant is Coming Soon
            </h4>
            <p class="text-xs text-slate-500 leading-relaxed max-w-sm mx-auto">
              We are currently fine-tuning our domain-specific agricultural trade models to ensure verified accuracy and institutional-grade reasoning before public launch.
            </p>
          </div>
        </div>

        <!-- What to Expect Feature Cards -->
        <div class="space-y-2.5 pt-1">
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            What to expect when it launches:
          </p>

          <!-- Feature 1 -->
          <div class="p-3 rounded-xl bg-white border border-slate-200/80 shadow-2xs flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center shrink-0 border border-sky-100 mt-0.5">
              <TrendingUpIcon class="w-4 h-4" />
            </div>
            <div class="space-y-0.5">
              <h5 class="text-xs font-bold text-slate-800">Natural-Language Trade Insights</h5>
              <p class="text-[11px] text-slate-500 leading-normal">
                Ask questions about export volume peaks, monthly growth, and commodity market share in plain English or Khmer.
              </p>
            </div>
          </div>

          <!-- Feature 2 -->
          <div class="p-3 rounded-xl bg-white border border-slate-200/80 shadow-2xs flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 border border-indigo-100 mt-0.5">
              <SparklesIcon class="w-4 h-4" />
            </div>
            <div class="space-y-0.5">
              <h5 class="text-xs font-bold text-slate-800">Contextual Chart Explanations</h5>
              <p class="text-[11px] text-slate-500 leading-normal">
                Click "Ask AI" on any macro chart or compare view to receive an analytical synthesis of that exact dataset.
              </p>
            </div>
          </div>

          <!-- Feature 3 -->
          <div class="p-3 rounded-xl bg-white border border-slate-200/80 shadow-2xs flex items-start gap-3">
            <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-100 mt-0.5">
              <DatabaseIcon class="w-4 h-4" />
            </div>
            <div class="space-y-0.5">
              <h5 class="text-xs font-bold text-slate-800">DuckDB SQL Verification</h5>
              <p class="text-[11px] text-slate-500 leading-normal">
                Every calculation is mathematically computed and grounded directly in published customs dataset records.
              </p>
            </div>
          </div>
        </div>

        <!-- Development Progress Status Box -->
        <div class="p-3 rounded-xl bg-slate-100/90 border border-slate-200 text-xs space-y-1">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-slate-600">Current Phase:</span>
            <span class="text-[10px] font-mono font-bold text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
              Model Calibration
            </span>
          </div>
          <p class="text-[11px] text-slate-500">
            Testing query accuracy and analytical consistency across all Cambodian agricultural HS codes.
          </p>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="p-3.5 bg-white border-t border-slate-200/90 flex items-center justify-between gap-3">
        <span class="text-[11px] text-slate-400 font-medium">
          Stay tuned for upcoming updates
        </span>
        <button
          type="button"
          @click="store.toggleChat()"
          class="cursor-pointer px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-xs"
        >
          Got it
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  MessageSquare as MessageSquareIcon,
  X as XIcon,
  Bot as BotIcon,
  Sparkles as SparklesIcon,
  Clock as ClockIcon,
  TrendingUp as TrendingUpIcon,
  Database as DatabaseIcon
} from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';

const store = useDatasetStore();
</script>
