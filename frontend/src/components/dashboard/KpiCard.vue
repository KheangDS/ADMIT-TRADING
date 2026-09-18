<template>
  <div class="bg-white p-4 sm:p-5 rounded-2xl border border-slate-100 shadow-xs hover:shadow-md hover:border-slate-200/80 transition-all duration-200 flex flex-col justify-between min-h-[128px]">
    <!-- Card Header: Label & Icon Badge -->
    <div class="flex items-start justify-between gap-2">
      <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider line-clamp-1">
        {{ label }}
      </span>
      <div 
        class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-2xs"
        :class="badgeColorClass"
      >
        <DollarSignIcon v-if="label.includes('($)')" class="w-4 h-4 text-emerald-600" />
        <CoinsIcon v-else-if="label.includes('(KHR)')" class="w-4 h-4 text-amber-600" />
        <ScaleIcon v-else-if="label.includes('Volume')" class="w-4 h-4 text-sky-600" />
        <GlobeIcon v-else-if="label.includes('Markets') || label.includes('Countries')" class="w-4 h-4 text-indigo-600" />
        <BoxesIcon v-else-if="label.includes('Commodit') || label.includes('HS8')" class="w-4 h-4 text-purple-600" />
        <TrendingUpIcon v-else class="w-4 h-4 text-sky-600" />
      </div>
    </div>
    
    <!-- Card Body: Value & Unit -->
    <div class="mt-2.5">
      <div class="flex items-baseline gap-1.5 flex-wrap">
        <span class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight leading-none">
          {{ formattedNumber }}
        </span>
        <span v-if="unitSuffix" class="text-xs font-bold text-slate-500">
          {{ unitSuffix }}
        </span>
      </div>
      <p class="text-[11px] text-slate-400 mt-1.5 font-medium leading-tight line-clamp-1">
        {{ description }}
      </p>
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
  description: string;
}>();

// Dynamic icon background classes
const badgeColorClass = computed(() => {
  if (props.label.includes('($)')) return 'bg-emerald-50 border border-emerald-100/80';
  if (props.label.includes('(KHR)') || props.label.includes('(៛)')) return 'bg-amber-50 border border-amber-100/80';
  if (props.label.includes('Volume')) return 'bg-sky-50 border border-sky-100/80';
  if (props.label.includes('Markets') || props.label.includes('Countries')) return 'bg-indigo-50 border border-indigo-100/80';
  if (props.label.includes('Commodit') || props.label.includes('HS8')) return 'bg-purple-50 border border-purple-100/80';
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
  // Format: "41 Countries" -> "41", unit: "Countries"
  if (val.includes('Countries')) {
    const num = val.replace('Countries', '').trim();
    return { number: num, unit: 'Countries' };
  }
  // Format: "20 Commodities" -> "20", unit: "HS8 Products"
  if (val.includes('Commodities')) {
    const num = val.replace('Commodities', '').trim();
    return { number: num, unit: 'HS8 Products' };
  }
  
  return { number: val, unit: '' };
});

const formattedNumber = computed(() => parsedValue.value.number);
const unitSuffix = computed(() => parsedValue.value.unit);
</script>
