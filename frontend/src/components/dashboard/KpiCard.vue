<template>
  <div 
    class="bg-white p-3.5 sm:p-4 lg:p-5 rounded-2xl border border-slate-100 shadow-xs hover:shadow-md hover:border-slate-200/80 transition-all duration-200 flex flex-col justify-between items-center text-center"
    :class="[
      isHero ? 'min-h-[96px] sm:min-h-[116px] bg-gradient-to-br from-white via-white to-emerald-50/30 border-emerald-100/80' : 'min-h-[90px] sm:min-h-[116px]'
    ]"
  >
    <!-- Card Header: Title & Icon Badge (Centered) -->
    <div class="flex items-center justify-center gap-1.5 w-full text-center">
      <div 
        class="rounded-lg flex items-center justify-center flex-shrink-0"
        :class="[
          badgeColorClass,
          isHero ? 'w-5 h-5 sm:w-6 sm:h-6' : 'w-4 h-4 sm:w-5 sm:h-5'
        ]"
      >
        <DollarSignIcon v-if="isUsd" class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-emerald-600" />
        <ArrowLeftRightIcon v-else-if="isTransactions" class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-amber-600" />
        <ScaleIcon v-else-if="isVolume" class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-sky-600" />
        <GlobeIcon v-else-if="isMarkets" class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-indigo-600" />
        <BoxesIcon v-else-if="isCommodities" class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-purple-600" />
        <TrendingUpIcon v-else class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-sky-600" />
      </div>
      <span 
        class="font-bold text-slate-500 uppercase tracking-tight leading-tight truncate" 
        :class="isHero ? 'text-[11px] sm:text-xs text-slate-600' : 'text-[9px] sm:text-[11px]'"
        :title="description || label"
      >
        {{ displayTitle }}
      </span>
    </div>
    
    <!-- Card Body: Value & Unit (Centered) -->
    <div class="my-auto pt-2 sm:pt-2.5 pb-0.5 sm:pb-1 flex items-baseline justify-center gap-1.5 flex-wrap text-center w-full">
      <span 
        class="font-black text-slate-900 tracking-tight leading-none"
        :class="isHero ? 'text-2xl sm:text-[28px]' : 'text-xl sm:text-[24px] lg:text-[26px]'"
      >
        {{ formattedNumber }}
      </span>
      <span 
        v-if="unitSuffix" 
        class="font-bold px-1.5 py-0.5 rounded-md text-slate-600 bg-slate-100/90 border border-slate-200/60 leading-none"
        :class="isHero ? 'text-[10px] sm:text-[11px]' : 'text-[9px] sm:text-[11px]'"
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
  ArrowLeftRight as ArrowLeftRightIcon, 
  Scale as ScaleIcon, 
  Boxes as BoxesIcon, 
  TrendingUp as TrendingUpIcon 
} from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    label: string;
    value: string;
    description?: string;
    isHero?: boolean;
  }>(),
  {
    isHero: false,
  }
);

const isUsd = computed(() => props.label.includes('($)') || props.label.toLowerCase().includes('usd') || props.label.toLowerCase().includes('revenue (usd)'));
const isTransactions = computed(() => props.label.toLowerCase().includes('transaction') || props.label.toLowerCase().includes('record') || props.label.toLowerCase().includes('declaration'));
const isVolume = computed(() => props.label.toLowerCase().includes('volume') || props.label.toLowerCase().includes('weight'));
const isMarkets = computed(() => props.label.toLowerCase().includes('market') || props.label.toLowerCase().includes('countr') || props.label.toLowerCase().includes('destination'));
const isCommodities = computed(() => props.label.toLowerCase().includes('commodit') || props.label.toLowerCase().includes('hs8') || props.label.toLowerCase().includes('product'));

// Concise, human-friendly titles that never truncate awkwardly
const displayTitle = computed(() => {
  const lbl = props.label.trim();
  if (isUsd.value) return 'Revenue (USD)';
  if (isTransactions.value) return 'Total Transactions';
  if (isVolume.value) return 'Export Volume';
  if (isMarkets.value) return 'Destination Markets';
  if (isCommodities.value) return 'Total Commodities';
  return lbl;
});

// Dynamic icon background classes
const badgeColorClass = computed(() => {
  if (isUsd.value) return 'bg-emerald-50 border border-emerald-100/80';
  if (isTransactions.value) return 'bg-amber-50 border border-amber-100/80';
  if (isVolume.value) return 'bg-sky-50 border border-sky-100/80';
  if (isMarkets.value) return 'bg-indigo-50 border border-indigo-100/80';
  if (isCommodities.value) return 'bg-purple-50 border border-purple-100/80';
  return 'bg-slate-50 border border-slate-100';
});

// Smart value formatting: separates long units so they display cleanly without wrapping awkwardly
const parsedValue = computed(() => {
  const val = props.value.trim();
  
  // Format: "$840.42 Million USD" -> "$840.42M", unit: "USD"
  if (val.includes('Million USD') || val.includes('M USD')) {
    const num = val.replace(/Million USD|M USD/g, '').trim();
    return { number: `${num}M`, unit: 'USD' };
  }
  // Format: "625 Records" or "625 Transactions" -> "625", unit: "Records"
  if (val.includes('Records') || val.includes('Transactions') || val.includes('Declarations')) {
    const num = val.replace(/Records|Transactions|Declarations/g, '').trim();
    return { number: num, unit: 'Records' };
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
  if (val.includes('Countries') || val.includes('Markets')) {
    const num = val.replace(/Countries|Markets/g, '').trim();
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
