<template>
  <div v-if="meaning" class="mt-4 p-4 bg-sky-50/80 rounded-xl border border-sky-100 text-xs text-slate-700 space-y-2">
    <div class="flex items-center gap-2 text-sky-800 font-bold text-xs uppercase tracking-wider">
      <BotIcon class="w-4 h-4 text-sky-600" />
      <span>AI Graph Insights</span>
    </div>
    <p class="leading-relaxed"><strong>Meaning:</strong> {{ meaning.explanation }}</p>
    <p class="leading-relaxed text-slate-900 font-medium"><strong>Key Takeaway:</strong> {{ meaning.key_takeaway }}</p>
    <p class="leading-relaxed text-emerald-800 font-semibold"><strong>Recommended Strategy:</strong> {{ meaning.action }}</p>
  </div>
</template>

<script setup lang="ts">
import { Bot as BotIcon } from 'lucide-vue-next';
import type { AiMeaning } from '../../types/dataset';

defineProps<{
  meaning?: AiMeaning;
}>();
</script>
