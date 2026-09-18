<template>
  <div class="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
    
    <!-- Header: Title, Active Status, and Reset Button -->
    <div class="flex items-center justify-between flex-wrap gap-2.5 pb-3 border-b border-slate-100">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center flex-shrink-0">
          <FilterIcon class="w-4 h-4" />
        </div>
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <h3 class="text-sm font-bold text-slate-900 leading-tight">Interactive Trade Slicers & Filters</h3>
            <span class="text-[10px] px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 font-bold uppercase tracking-wider">
              Live Slicing
            </span>
            <!-- Active Filter Badges -->
            <span 
              v-if="store.filterHsCode !== 'ALL'"
              class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold"
            >
              HS {{ store.filterHsCode }}
            </span>
            <span 
              v-if="store.filterYear !== 'ALL'"
              class="text-[10px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-bold"
            >
              Year {{ store.filterYear }}
            </span>
            <span 
              v-if="store.filterCountry !== 'ALL'"
              class="text-[10px] px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-bold"
            >
              {{ store.filterCountry }}
            </span>
          </div>
          <p class="text-[11px] text-slate-500 mt-0.5">Filter analytics across commodity, year, destination market, and metric dimensions</p>
        </div>
      </div>

      <!-- Reset All Filters Button -->
      <button
        v-if="store.isFiltered"
        @click="store.resetAllFilters"
        class="cursor-pointer flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 transition-all shadow-xs"
      >
        <RotateCcwIcon class="w-3.5 h-3.5 text-slate-500" />
        <span>Reset All Filters</span>
      </button>
    </div>

    <!-- 4-Pillar Slicers Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
      
      <!-- Pillar 1: Commodity Chapter Slicer -->
      <div>
        <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 flex items-center justify-between">
          <span>1. Commodity Chapter</span>
          <span v-if="store.filterHsCode !== 'ALL'" class="text-[10px] text-sky-600 font-semibold">Active</span>
        </label>
        <select
          v-model="store.filterHsCode"
          class="w-full px-3 py-2 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors"
        >
          <option value="ALL">🌐 All Commodity Chapters</option>
          <option
            v-for="cat in store.dashboardData?.hs4_categories || []"
            :key="cat.hs4_code"
            :value="cat.hs4_code"
          >
            HS {{ cat.hs4_code }} - {{ getShortCategoryName(cat) }}
          </option>
        </select>
      </div>

      <!-- Pillar 2: Time Horizon / Year Slicer -->
      <div>
        <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 flex items-center justify-between">
          <span>2. Time Horizon</span>
          <span v-if="store.filterYear !== 'ALL'" class="text-[10px] text-indigo-600 font-semibold">Active</span>
        </label>
        <select
          v-model="store.filterYear"
          class="w-full px-3 py-2 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors"
        >
          <option value="ALL">📅 All Time (All Years)</option>
          <option
            v-for="yr in availableYears"
            :key="yr"
            :value="yr.toString()"
          >
            Year {{ yr }}
          </option>
        </select>
      </div>

      <!-- Pillar 3: Destination Market Slicer -->
      <div>
        <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 flex items-center justify-between">
          <span>3. Destination Market</span>
          <span v-if="store.filterCountry !== 'ALL'" class="text-[10px] text-purple-600 font-semibold">Active</span>
        </label>
        <select
          v-model="store.filterCountry"
          class="w-full px-3 py-2 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors"
        >
          <option value="ALL">🌏 All Markets (Worldwide)</option>
          <option
            v-for="country in availableCountries"
            :key="country"
            :value="country"
          >
            {{ country }}
          </option>
        </select>
      </div>

      <!-- Pillar 4: Primary Metric Dimension Toggle -->
      <div>
        <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">
          4. Metric Dimension
        </label>
        <div class="flex bg-slate-100 p-1 rounded-xl text-xs font-semibold">
          <button
            @click="store.filterMetric = 'USD'"
            :class="[
              'cursor-pointer flex-1 py-1.5 rounded-lg transition-all text-center',
              store.filterMetric === 'USD'
                ? 'bg-white text-sky-600 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            ]"
            title="Display metrics in Dollar Value ($ USD)"
          >
            💵 Value ($USD)
          </button>
          <button
            @click="store.filterMetric = 'TONNES'"
            :class="[
              'cursor-pointer flex-1 py-1.5 rounded-lg transition-all text-center',
              store.filterMetric === 'TONNES'
                ? 'bg-white text-sky-600 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            ]"
            title="Display metrics in Export Weight Volume (Tonnes)"
          >
            ⚖️ Volume (Tonnes)
          </button>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Filter as FilterIcon, RotateCcw as RotateCcwIcon } from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';
import type { Hs4CategorySummary } from '../../types/dataset';

const store = useDatasetStore();

const availableYears = computed(() => {
  if (store.dashboardData?.available_years && store.dashboardData.available_years.length > 0) {
    return store.dashboardData.available_years;
  }
  // Fallback scan from monthly summary
  const years = new Set<number>();
  for (const item of store.dashboardData?.level1_charts?.find(c => c.chart_id === 'chart_seasonality')?.data || []) {
    if (item.name && item.name.includes('-')) {
      const yr = parseInt(item.name.split('-')[0]);
      if (!isNaN(yr)) years.add(yr);
    }
  }
  return years.size > 0 ? Array.from(years).sort() : [2023, 2024];
});

const availableCountries = computed(() => {
  if (store.dashboardData?.available_countries && store.dashboardData.available_countries.length > 0) {
    return store.dashboardData.available_countries;
  }
  // Fallback scan from market share chart
  const countries = new Set<string>();
  for (const item of store.dashboardData?.level1_charts?.find(c => c.chart_id === 'chart_market_share')?.data || []) {
    if (item.name) countries.add(item.name);
  }
  return Array.from(countries).sort();
});

function getShortCategoryName(cat: Hs4CategorySummary): string {
  if (cat.official_title) {
    return cat.official_title;
  }
  const cleanCode = cat.hs4_code.trim();
  const knownMap: Record<string, string> = {
    '0801': 'Cashew Nuts & Coconuts',
    '0804': 'Fresh & Dried Mangoes',
    '0904': 'Pepper & Chili (Capsicum)',
    '0910': 'Ginger, Turmeric & Spices',
    '1211': 'Medicinal & Perfumery Plants'
  };
  if (knownMap[cleanCode]) return knownMap[cleanCode];
  return cat.hs4_desc.split('(')[0].split(',')[0];
}
</script>

