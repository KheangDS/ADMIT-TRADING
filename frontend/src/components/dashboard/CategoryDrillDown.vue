<template>
  <div v-if="detail" class="space-y-8">
    
    <!-- Navigation Back Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
      <button
        @click="goBack"
        class="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-xl transition-colors shadow-xs"
      >
        <ArrowLeftIcon class="w-4 h-4" />
        <span>Back to Macro Overview</span>
      </button>

      <div class="text-left sm:text-right">
        <div class="flex items-center sm:justify-end gap-2">
          <span class="text-xs font-mono font-extrabold px-2.5 py-0.5 rounded-md bg-sky-100 text-sky-800">
            HS {{ detail.hs4_code }}
          </span>
          <span class="text-xs font-semibold text-slate-500">Chapter Detail</span>
        </div>
        <h2 class="text-lg font-bold text-slate-900 leading-tight mt-1">
          {{ hs4Category?.title_en || hs4Category?.official_title || detail.hs4_desc }}
        </h2>
        <p v-if="hs4Category?.title_km" class="text-xs font-medium text-slate-500 mt-0.5 font-sans">
          {{ hs4Category.title_km }}
        </p>
      </div>
    </div>

    <!-- Sub-Products Breakdown Table (8-Digit HS Codes) -->
    <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 class="text-base font-bold text-slate-900">Sub-Products Breakdown (8-Digit HS Codes)</h3>
          <p class="text-xs text-slate-500 mt-0.5">Click any commodity row below to open its dedicated HS8 Analytics page with World Map.</p>
        </div>
        <span class="text-xs font-semibold text-sky-700 bg-sky-50 px-3 py-1 rounded-lg self-start">
          {{ detail.sub_products.length }} Commodities
        </span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
            <tr>
              <th class="p-3">HS 8-Digit Code</th>
              <th class="p-3">Product Name (English / ភាសាខ្មែរ)</th>
              <th class="p-3 text-right">Volume</th>
              <th class="p-3 text-right">Revenue</th>
              <th class="p-3 text-right">Avg Unit Price</th>
              <th class="p-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr 
              v-for="sp in detail.sub_products" 
              :key="sp.hs8_code" 
              @click="goToCommodity(sp.hs8_code)"
              class="hover:bg-sky-50/60 transition-colors cursor-pointer group"
            >
              <td class="p-3 font-mono font-bold text-sky-700 group-hover:underline">
                {{ sp.hs8_code }}
              </td>
              <td class="p-3">
                <span class="font-bold text-slate-900 block group-hover:text-sky-700 transition-colors">
                  {{ sp.name_en || sp.product_name || sp.hs8_desc }}
                </span>
                <span v-if="sp.name_km" class="text-[11px] text-slate-500 block font-sans mt-0.5">
                  {{ sp.name_km }}
                </span>
                <span v-else-if="sp.product_name && sp.product_name !== sp.hs8_desc" class="text-[11px] text-slate-400 block truncate max-w-md mt-0.5">
                  {{ sp.hs8_desc }}
                </span>
              </td>
              <td class="p-3 text-right text-slate-700 font-medium">{{ formatVolume(sp.weight_tonnes) }}</td>
              <td class="p-3 text-right font-bold text-slate-900">{{ formatRevenue(sp.val_usd) }}</td>
              <td class="p-3 text-right font-bold text-emerald-600">
                ${{ sp.unit_price_usd_per_kg.toFixed(2) }} / kg
              </td>
              <td class="p-3 text-center">
                <span class="inline-flex items-center gap-1 text-[11px] font-bold text-sky-600 group-hover:text-sky-800 bg-sky-50 group-hover:bg-sky-100 px-2.5 py-1 rounded-lg transition-colors">
                  <span>View HS8</span>
                  <ArrowRightIcon class="w-3.5 h-3.5" />
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Category Specific Charts Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ChartCustomizer
        v-for="chart in detail.charts"
        :key="chart.chart_id"
        :title="chart.title"
        :chart-type="chart.chart_type"
        :data="chart.data"
        :ai-meaning="chart.ai_meaning"
      />
    </div>

    <!-- Category AI Strategy Card -->
    <div v-if="detail.ai_strategy" class="p-5 bg-sky-50 rounded-2xl border border-sky-100 text-xs text-sky-900 flex items-start gap-3 shadow-xs">
      <TargetIcon class="w-5 h-5 text-sky-600 flex-shrink-0 mt-0.5" />
      <div>
        <h4 class="font-bold text-sky-900 uppercase text-xs tracking-wider">Category Strategic Recommendation</h4>
        <p class="mt-1 text-slate-700 leading-relaxed">{{ detail.ai_strategy }}</p>
      </div>
    </div>

  </div>
  <div v-else class="text-center py-20 bg-white rounded-2xl border border-slate-100 p-8">
    <p class="text-sm font-semibold text-slate-600">Category not found or dataset is not loaded yet.</p>
    <button
      @click="goBack"
      class="mt-4 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs rounded-xl transition-colors"
    >
      Return to Overview
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft as ArrowLeftIcon, ArrowRight as ArrowRightIcon, Target as TargetIcon } from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';
import ChartCustomizer from './ChartCustomizer.vue';

const route = useRoute();
const router = useRouter();
const store = useDatasetStore();

const currentHs4Code = computed(() => {
  return (route.params.hs4code as string) || store.activeCategory || '0801';
});

onMounted(() => {
  if (route.params.hs4code) {
    store.selectCategory(route.params.hs4code as string);
  }
});

const detail = computed(() => {
  if (!store.dashboardData || !store.dashboardData.category_details) return null;
  return store.dashboardData.category_details[currentHs4Code.value] || null;
});

const hs4Category = computed(() => {
  if (!store.dashboardData || !store.dashboardData.hs4_categories) return null;
  return store.dashboardData.hs4_categories.find(c => c.hs4_code === currentHs4Code.value) || null;
});

const goBack = () => {
  store.selectCategory(null);
  router.push('/');
};

const goToCommodity = (hs8Code: string) => {
  router.push(`/commodity/${hs8Code}`);
};

const formatRevenue = (valUsd: number): string => {
  if (!valUsd || valUsd === 0) return '$0 USD';
  if (valUsd < 1_000_000) {
    const kUsd = Math.round((valUsd / 1000) * 10) / 10;
    return `$${kUsd.toLocaleString()}k USD`;
  }
  return `$${(valUsd / 1e6).toFixed(2)}M USD`;
};

const formatVolume = (tonnes: number): string => {
  if (!tonnes || tonnes === 0) return '0 Tonnes';
  if (tonnes < 1) {
    const kg = Math.round(tonnes * 1000 * 10) / 10;
    return `${kg.toLocaleString()} kg`;
  }
  return `${(Math.round(tonnes * 10) / 10).toLocaleString()} Tonnes`;
};
</script>
