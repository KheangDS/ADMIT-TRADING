<template>
  <div v-if="message" class="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-xl shadow-sm mb-6 flex items-start gap-3">
    <AlertTriangleIcon class="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
    <div>
      <h4 class="text-sm font-bold text-amber-900">Dataset Format Notice</h4>
      <p class="text-xs text-amber-700 mt-1 leading-relaxed">{{ message }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AlertTriangle as AlertTriangleIcon } from 'lucide-vue-next';

defineProps<{
  message?: string | null;
}>();
</script>
