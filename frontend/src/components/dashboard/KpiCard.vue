<template>
  <div class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-100 shadow-xs hover:shadow-md hover:border-slate-200/80 transition-all duration-200 flex flex-col justify-between min-h-[116px]">
    <!-- Card Header: Title & Icon Badge -->
    <div class="flex items-center justify-between gap-2 w-full">
      <div class="min-w-0 flex-1">
        <span class="text-[11px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider block truncate" :title="description || label">
          {{ displayTitle }}
        </span>
      </div>
      <div 
        class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-2xs"
        :class="badgeColorClass"
      >
        <DollarSignIcon v-if="isUsd" class="w-4 h-4 text-emerald-600" />
        <CoinsIcon v-else-if="isKhr" class="w-4 h-4 text-amber-600" />
        <ScaleIcon v-else-if="isVolume" class="w-4 h-4 text-sky-600" />
        <GlobeIcon v-else-if="isMarkets" class="w-4 h-4 text-indigo-600" />
        <BoxesIcon v-else-if="isCommodities" class="w-4 h-4 text-purple-600" />
        <TrendingUpIcon v-else class="w-4 h-4 text-sky-600" />
      </div>
    </div>
    
    <!-- Card Body: Value & Unit Centered -->
    <div class="my-auto pt-3 pb-1 flex items-baseline justify-center gap-1.5 flex-wrap text-center">
      <span class="text-2xl sm:text-[26px] font-black text-slate-900 tracking-tight leading-none">
        {{ formattedNumber }}
      </span>
      <span 
        v-if="unitSuffix" 
        class="text-[11px] font-bold px-1.5 py-0.5 rounded-md text-slate-600 bg-slate-100/90 border border-slate-200/60 leading-none"
      >
        {{ unitSuffix }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { 
  Globe as GlobeIcon, 
  DollarSign as DollarSignIcon, 
  Coins as CoinsIcon, 
  Scale as ScaleIcon, 
  Boxes as BoxesIcon,
  TrendingUp as TrendingUpIcon 
} from 'lucide-vue-next';

const props = defineProps<{
  label: string;
  value: string;
  description?: string;
}>();

const isUsd = computed(() => props.label.includes('($)') || props.label.toLowerCase().includes('usd'));
const isKhr = computed(() => props.label.includes('(KHR)') || props.label.includes('(៛)') || props.label.toLowerCase().includes('khr'));
const isVolume = computed(() => props.label.toLowerCase().includes('volume') || props.label.toLowerCase().includes('weight'));
const isMarkets = computed(() => props.label.toLowerCase().includes('market') || props.label.toLowerCase().includes('countr') || props.label.toLowerCase().includes('destination'));
const isCommodities = computed(() => props.label.toLowerCase().includes('commodit') || props.label.toLowerCase().includes('hs8') || props.label.toLowerCase().includes('product'));

// Concise, human-friendly titles that never truncate awkwardly
const displayTitle = computed(() => {
  const lbl = props.label.trim();
  if (isUsd.value) return 'Revenue (USD)';
  if (isKhr.value) return 'Revenue (KHR)';
  if (isVolume.value) return 'Export Volume';
  if (isMarkets.value) return 'Destination Markets';
  if (isCommodities.value) return 'Total Commodities';
  return lbl;
});

// Dynamic icon background classes
const badgeColorClass = computed(() => {
  if (isUsd.value) return 'bg-emerald-50 border border-emerald-100/80';
  if (isKhr.value) return 'bg-amber-50 border border-amber-100/80';
  if (isVolume.value) return 'bg-sky-50 border border-sky-100/80';
  if (isMarkets.value) return 'bg-indigo-50 border border-indigo-100/80';
  if (isCommodities.value) return 'bg-purple-50 border border-purple-100/80';
  return 'bg-slate-50 border border-slate-100';
});

// Smart value formatting: separates long units so they display cleanly without wrapping awkwardly
const parsedValue = computed(() => {
  const val = props.value.trim();
  
  // Format: "$840.42 Million USD" -> "$840.42M", unit: "USD"
  if (val.includes('Million USD')) {
    const num = val.replace('Million USD', '').trim();
    return { number: `${num}M`, unit: 'USD' };
  }
  // Format: "3,406.24 Billion KHR" or "៛3,406.24 Billion KHR" -> "៛3,406.24B", unit: "KHR"
  if (val.includes('Billion KHR') || val.includes('B KHR')) {
    const num = val.replace(/Billion KHR|B KHR/g, '').replace('៛', '').trim();
    return { number: `៛${num}B`, unit: 'KHR' };
  }
  // Format: "3,406.24 Million KHR" or "៛3,406.24 Million KHR" -> "៛3,406.24M", unit: "KHR"
  if (val.includes('Million KHR') || val.includes('M KHR')) {
    const num = val.replace(/Million KHR|M KHR/g, '').replace('៛', '').trim();
    return { number: `៛${num}M`, unit: 'KHR' };
  }
  // Format: "0.00 KHR" or "៛0.00 KHR" -> "៛0.00", unit: "KHR"
  if (val.includes('KHR')) {
    const num = val.replace('KHR', '').replace('៛', '').trim();
    return { number: `៛${num}`, unit: 'KHR' };
  }
  // Format: "1,137,019.05 Tonnes" -> "1.14M Tonnes" or cleanly formatted
  if (val.includes('Tonnes')) {
    const raw = parseFloat(val.replace(/,/g, '').replace('Tonnes', '').trim());
    if (!isNaN(raw) && raw >= 1_000_000) {
      return { number: `${(raw / 1e6).toFixed(2)}M`, unit: 'Tonnes' };
    }
    if (!isNaN(raw) && raw >= 1000) {
      return { number: `${(raw / 1000).toFixed(1)}k`, unit: 'Tonnes' };
    }
    const num = val.replace('Tonnes', '').trim();
    return { number: num, unit: 'Tonnes' };
  }
  // Format: "41 Countries" -> "41", unit: "Markets"
  if (val.includes('Countries')) {
    const num = val.replace('Countries', '').trim();
    return { number: num, unit: 'Markets' };
  }
  // Format: "20 Commodities" -> "20", unit: "Commodities"
  if (val.includes('Commodities') || val.includes('HS8 Products')) {
    const num = val.replace(/Commodities|HS8 Products/g, '').trim();
    return { number: num, unit: 'Commodities' };
  }
  
  return { number: val, unit: '' };
});

const formattedNumber = computed(() => parsedValue.value.number);
const unitSuffix = computed(() => parsedValue.value.unit);
</script>
