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
              v-if="store.isSingleCommoditySelected && singleSelectedCommodity"
              class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold"
            >
              HS {{ singleSelectedCommodity.hs8_code }} · {{ singleSelectedCommodity.name_en }} (1 Selected)
            </span>
            <span 
              v-else-if="store.filterHsCodes.length > 1"
              class="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold"
            >
              {{ store.filterHsCodes.length }} Commodities Selected (Multi-Crop)
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
          <p class="text-[11px] text-slate-500 mt-0.5">
            Filter analytics across commodities, years, destinations, and scale dimensions
          </p>
        </div>
      </div>

      <!-- Reset All Filters Button -->
      <button
        v-if="store.isFiltered"
        @click="resetFilters"
        class="cursor-pointer flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 transition-all shadow-xs"
      >
        <RotateCcwIcon class="w-3.5 h-3.5 text-slate-500" />
        <span>Reset All Filters</span>
      </button>
    </div>

    <!-- 4-Pillar Slicers Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
      
      <!-- Pillar 1: Multi-Commodity HS8 Slicer -->
      <div class="relative">
        <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 flex items-center justify-between">
          <span>1. Commodities (Multi-Select)</span>
          <span v-if="store.filterHsCodes.length > 0" class="text-[10px] text-sky-600 font-semibold">
            {{ store.filterHsCodes.length }} Active
          </span>
        </label>
        
        <!-- Multi-select trigger button -->
        <button
          type="button"
          @click="isDropdownOpen = !isDropdownOpen"
          class="w-full px-3 py-2 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 flex items-center justify-between focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors"
        >
          <span class="truncate text-left">
            {{ commodityDisplayLabel }}
          </span>
          <ChevronDownIcon class="w-4 h-4 text-slate-500 flex-shrink-0 ml-1.5 transition-transform" :class="{ 'rotate-180': isDropdownOpen }" />
        </button>

        <!-- Dropdown Menu / Checklist -->
        <div
          v-if="isDropdownOpen"
          class="absolute left-0 right-0 top-full mt-1.5 z-40 bg-white rounded-xl border border-slate-200 shadow-xl p-3 space-y-2.5 max-h-72 flex flex-col"
        >
          <!-- Search & Select All Controls -->
          <div class="flex items-center gap-2">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search commodity or HS code..."
              class="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
          <div class="flex items-center justify-between text-[11px] pb-1.5 border-b border-slate-100">
            <button
              type="button"
              @click="selectAllCommodities"
              class="text-sky-600 font-bold hover:underline"
            >
              Select All ({{ availableHs8Commodities.length }})
            </button>
            <button
              type="button"
              @click="clearCommoditySelection"
              class="text-slate-500 font-semibold hover:text-slate-800"
            >
              Clear Selection
            </button>
          </div>

          <!-- Commodity Checkbox List -->
          <div class="overflow-y-auto space-y-1 pr-1 flex-1">
            <label
              v-for="comm in filteredCommodityOptions"
              :key="comm.hs8_code"
              class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer text-xs"
            >
              <input
                type="checkbox"
                :value="comm.hs8_code"
                v-model="store.filterHsCodes"
                class="rounded border-slate-300 text-sky-600 focus:ring-sky-500"
              />
              <span class="font-mono text-slate-500 font-bold text-[11px]">HS {{ comm.hs8_code }}</span>
              <span class="text-slate-800 font-medium truncate flex-1">{{ comm.name_en }}</span>
            </label>
            <div v-if="filteredCommodityOptions.length === 0" class="text-center py-4 text-xs text-slate-400">
              No matching commodities
            </div>
          </div>

          <!-- Bottom Close / Done -->
          <div class="pt-1.5 border-t border-slate-100 flex justify-end">
            <button
              type="button"
              @click="isDropdownOpen = false"
              class="px-3 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-bold"
            >
              Done
            </button>
          </div>
        </div>
      </div>

      <!-- Pillar 2: Year Slicer -->
      <div>
        <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 flex items-center justify-between">
          <span>2. Year</span>
          <span v-if="store.filterYear !== 'ALL'" class="text-[10px] text-indigo-600 font-semibold">Active</span>
        </label>
        <select
          v-model="store.filterYear"
          class="w-full px-3 py-2 bg-slate-50 hover:bg-slate-100/80 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-colors"
        >
          <option value="ALL">All Years</option>
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
          <option value="ALL">All Markets (Worldwide)</option>
          <option
            v-for="country in availableCountries"
            :key="country"
            :value="country"
          >
            {{ country }}
          </option>
        </select>
      </div>

      <!-- Pillar 4: Primary Metric Dimension & Unit Scale -->
      <div>
        <label class="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5 flex items-center justify-between">
          <span>4. Metric & Unit Scale</span>
          <span class="text-[10px] text-slate-400 font-normal">
            {{ store.filterMetric === 'USD' ? 'Scale: $k / $M USD' : 'Scale: kg / Tonnes' }}
          </span>
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
            title="Display metrics in Dollar Value ($ USD / Thousands / Millions)"
          >
            Value ($USD)
          </button>
          <button
            @click="store.filterMetric = 'TONNES'"
            :class="[
              'cursor-pointer flex-1 py-1.5 rounded-lg transition-all text-center',
              store.filterMetric === 'TONNES'
                ? 'bg-white text-sky-600 shadow-xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            ]"
            title="Display metrics in Export Volume (Kilograms / Metric Tonnes)"
          >
            Volume (Tonnes)
          </button>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { Filter as FilterIcon, RotateCcw as RotateCcwIcon, ChevronDown as ChevronDownIcon } from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';
import { allowedYears } from '../../utils/analyticsFilters';

const store = useDatasetStore();
const isDropdownOpen = ref<boolean>(false);
const searchQuery = ref<string>('');

const availableHs8Commodities = computed(() => {
  if (store.dashboardData?.hs8_commodities && store.dashboardData.hs8_commodities.length > 0) {
    return store.dashboardData.hs8_commodities;
  }
  if (store.dashboardData?.commodity_list && store.dashboardData.commodity_list.length > 0) {
    return store.dashboardData.commodity_list;
  }
  return [];
});

const filteredCommodityOptions = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  if (!query) return availableHs8Commodities.value;
  return availableHs8Commodities.value.filter(c => 
    c.hs8_code.includes(query) || (c.name_en && c.name_en.toLowerCase().includes(query))
  );
});

const singleSelectedCommodity = computed(() => {
  if (store.filterHsCodes.length === 1) {
    return availableHs8Commodities.value.find(c => c.hs8_code === store.filterHsCodes[0]) || null;
  }
  return null;
});

const commodityDisplayLabel = computed(() => {
  const total = availableHs8Commodities.value.length;
  const count = store.filterHsCodes.length;
  if (count === 0 || count === total) {
    return `All HS8 Commodities (${total})`;
  }
  if (count === 1) {
    const item = availableHs8Commodities.value.find(c => c.hs8_code === store.filterHsCodes[0]);
    return item ? `HS ${item.hs8_code} · ${item.name_en}` : '1 Commodity Selected';
  }
  return `${count} Commodities Selected`;
});


const selectAllCommodities = () => {
  store.filterHsCodes = availableHs8Commodities.value.map(c => c.hs8_code);
};

const clearCommoditySelection = () => {
  store.filterHsCodes = [];
};

const resetFilters = () => {
  store.resetAllFilters();
  isDropdownOpen.value = false;
};

const availableYears = computed(() => allowedYears(store.dashboardData));
watch(availableYears, years => {
  if (store.filterYear !== 'ALL' && !years.includes(Number(store.filterYear))) store.filterYear = 'ALL';
}, { immediate: true });

const availableCountries = computed(() => {
  if (store.dashboardData?.available_countries && store.dashboardData.available_countries.length > 0) {
    return store.dashboardData.available_countries;
  }
  const countries = new Set<string>();
  for (const item of store.dashboardData?.level1_charts?.find(c => c.chart_id === 'chart_market_share')?.data || []) {
    if (item.name) countries.add(item.name);
  }
  return Array.from(countries).sort();
});
</script>
