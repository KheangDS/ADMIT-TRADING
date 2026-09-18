<template>
  <div class="mt-8">
    <div class="flex items-center justify-between mb-4">
      <div>
        <h2 class="text-xl font-bold text-slate-900 tracking-tight">Explore Major Commodity Categories</h2>
        <p class="text-xs text-slate-500 mt-0.5">Click any category card below to drill-down into 8-digit sub-products & category analytics.</p>
      </div>
      <span class="text-xs font-semibold text-sky-700 bg-sky-50 px-2.5 py-1 rounded-lg border border-sky-100">
        {{ categories.length }} HS4 Chapters · {{ totalHs8CommoditiesCount }} HS8 Commodities Total
      </span>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <!-- 5 Chapter Cards -->
      <div
        v-for="cat in categories"
        :key="cat.hs4_code"
        @click="goToCategory(cat.hs4_code)"
        class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md cursor-pointer transition-all hover:border-sky-300 group flex flex-col justify-between"
      >
        <div>
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-mono">
                HS {{ cat.hs4_code }}
              </span>
              <span class="text-[11px] font-semibold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded-md border border-purple-100/60">
                {{ getSubProductCount(cat.hs4_code) }} HS8 Products
              </span>
            </div>
            <span class="text-xs font-black text-sky-600">
              {{ cat.revenue_share_pct.toFixed(1) }}% Share
            </span>
          </div>

          <!-- English Title -->
          <h3 class="text-base font-bold text-slate-900 group-hover:text-sky-600 transition-colors line-clamp-1">
            {{ cat.title_en || cat.official_title || cat.hs4_desc }}
          </h3>
          <!-- Khmer Title -->
          <p class="text-xs font-medium text-slate-500 mt-0.5 line-clamp-1 font-sans">
            {{ cat.title_km || cat.hs4_desc }}
          </p>

          <div class="mt-4 space-y-1.5 text-xs text-slate-600">
            <div class="flex justify-between">
              <span class="text-slate-500">Revenue:</span>
              <strong class="text-slate-900">{{ formatRevenue(cat.val_usd) }}</strong>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Volume:</span>
              <strong class="text-slate-900">{{ formatVolume(cat.weight_tonnes) }}</strong>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Avg Price:</span>
              <strong class="text-emerald-600">${{ cat.unit_price_usd_per_kg.toFixed(2) }} / kg</strong>
            </div>
          </div>
        </div>

        <div class="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-sky-600 group-hover:translate-x-1 transition-transform">
          <span>Explore Category Details</span>
          <ArrowRightIcon class="w-4 h-4" />
        </div>
      </div>

      <!-- 6th Card: Compare Commodities across Chapters -->
      <div
        @click="goToCompare"
        class="bg-gradient-to-br from-indigo-50/70 via-sky-50/50 to-white p-5 rounded-2xl border-2 border-dashed border-sky-300 shadow-sm hover:shadow-md cursor-pointer transition-all hover:border-sky-500 group flex flex-col justify-between"
      >
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-bold px-2 py-0.5 rounded-md bg-sky-100 text-sky-800 font-mono">
              TOOL
            </span>
            <span class="text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
              Cross-Chapter
            </span>
          </div>

          <h3 class="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition-colors flex items-center gap-2">
            <span>⚖️ Compare Commodities</span>
          </h3>
          <p class="text-xs font-medium text-slate-600 mt-0.5 font-sans">
            ប្រៀបធៀបទំនិញកូដ ៨ខ្ទង់
          </p>

          <p class="mt-3 text-xs text-slate-600 leading-relaxed">
            Select any two 8-digit HS commodities across chapters to compare price trajectories, monthly export volumes, and international market penetration side-by-side.
          </p>
        </div>

        <div class="mt-5 pt-3 border-t border-sky-100 flex items-center justify-between text-xs font-bold text-indigo-600 group-hover:translate-x-1 transition-transform">
          <span>Launch Comparison Tool</span>
          <ArrowRightIcon class="w-4 h-4" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { ArrowRight as ArrowRightIcon } from 'lucide-vue-next';
import type { Hs4CategorySummary } from '../../types/dataset';
import { useDatasetStore } from '../../stores/datasetStore';

const store = useDatasetStore();
const router = useRouter();

defineProps<{
  categories: Hs4CategorySummary[];
}>();

const goToCategory = (hs4Code: string) => {
  store.selectCategory(hs4Code);
  router.push(`/category/${hs4Code}`);
};

const goToCompare = () => {
  router.push('/compare');
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

const totalHs8CommoditiesCount = computed(() => {
  if (store.dashboardData?.commodity_list?.length) {
    return store.dashboardData.commodity_list.length;
  }
  const kpi = store.dashboardData?.summary_kpis?.find(k => k.label.includes('Commodit'));
  if (kpi && kpi.numeric_val) return kpi.numeric_val;
  return 20;
});

const getSubProductCount = (hs4Code: string): number => {
  if (store.dashboardData?.category_details?.[hs4Code]?.sub_products) {
    return store.dashboardData.category_details[hs4Code].sub_products.length;
  }
  const knownCounts: Record<string, number> = {
    '0801': 2,
    '0804': 2,
    '0904': 9,
    '0910': 6,
    '1211': 1
  };
  return knownCounts[hs4Code] || 1;
};
</script>
