<template>
  <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
    <div>
      <!-- Header with Customizer Bar & Slicers -->
      <div class="flex items-center justify-between mb-4 gap-2 flex-wrap">
        <div>
          <h3 class="text-base font-bold text-slate-800 tracking-tight">{{ dynamicTitle }}</h3>
          <span v-if="filteredSubtitle" class="text-[11px] font-semibold text-sky-600">
            {{ filteredSubtitle }}
          </span>
        </div>
        
        <!-- Controls Bar: Ask AI + Top-N + Unit Selector -->
        <div class="flex items-center gap-2 flex-wrap">
          <button
            @click="store.askAboutChart(title, aiMeaning?.explanation)"
            class="cursor-pointer flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-600 hover:to-indigo-700 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
            title="Ask AI to analyze this graph (Coming Soon)"
          >
            <SparklesIcon class="w-3.5 h-3.5" />
            <span>Ask AI</span>
          </button>

          <!-- Top-N Slicer for Commodity Donut or Country Bar Charts -->
          <div 
            v-if="chartId === 'chart_commodity_share' || chartId === 'chart_market_share'" 
            class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold"
          >
            <span class="text-[10px] text-slate-500 font-bold px-1 uppercase tracking-wider">Top:</span>
            <button
              v-for="n in [5, 10]"
              :key="n"
              @click="topNLimit = n"
              :class="[
                'cursor-pointer px-2 py-0.5 rounded-lg transition-all text-xs',
                topNLimit === n
                  ? 'bg-white text-sky-600 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              ]"
            >
              {{ n }}
            </button>
            <button
              @click="topNLimit = 999"
              :class="[
                'cursor-pointer px-2 py-0.5 rounded-lg transition-all text-xs',
                topNLimit === 999
                  ? 'bg-white text-sky-600 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              ]"
            >
              All
            </button>
          </div>

          <!-- For Table Charts (which display both Volume and Revenue simultaneously) -->
          <template v-if="chartId === 'chart_market_share_table' || chartType === 'TABLE'">
            <div class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
              <span class="text-[10px] text-slate-500 font-bold px-1 uppercase tracking-wider">Vol:</span>
              <select
                v-model="volumeUnit"
                class="bg-white text-slate-700 text-xs font-bold rounded-lg px-2 py-0.5 border border-slate-200/60 shadow-xs focus:ring-1 focus:ring-sky-500 cursor-pointer outline-none"
                title="Select Table Volume Display Unit"
              >
                <option value="AUTO">Auto ({{ autoVolumeLabel }})</option>
                <option value="MT">Million Tonnes (Mt)</option>
                <option value="KT">Kilo Tonnes (kT)</option>
                <option value="T">Tonnes (t)</option>
                <option value="KG">Kilograms (kg)</option>
              </select>
            </div>

            <div class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
              <span class="text-[10px] text-slate-500 font-bold px-1 uppercase tracking-wider">Rev:</span>
              <select
                v-model="revenueUnit"
                class="bg-white text-slate-700 text-xs font-bold rounded-lg px-2 py-0.5 border border-slate-200/60 shadow-xs focus:ring-1 focus:ring-sky-500 cursor-pointer outline-none"
                title="Select Table Revenue Display Unit"
              >
                <option value="AUTO">Auto ({{ autoRevenueLabel }})</option>
                <option value="T">Trillions ($T)</option>
                <option value="B">Billions ($B)</option>
                <option value="M">Millions ($M)</option>
                <option value="K">Thousands ($k)</option>
                <option value="EXACT">Exact ($)</option>
              </select>
            </div>
          </template>

          <!-- For Single-Metric Charts (Donut, Bar, Line) toggled by global metric slicer -->
          <div v-else class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <span class="text-[10px] text-slate-500 font-bold px-1 uppercase tracking-wider">Unit:</span>
            <!-- Revenue Unit Dropdown -->
            <select
              v-if="store.filterMetric !== 'TONNES'"
              v-model="revenueUnit"
              class="bg-white text-slate-700 text-xs font-bold rounded-lg px-2 py-0.5 border border-slate-200/60 shadow-xs focus:ring-1 focus:ring-sky-500 cursor-pointer outline-none"
              title="Select Revenue Display Unit"
            >
              <option value="AUTO">Auto ({{ autoRevenueLabel }})</option>
              <option value="T">Trillions ($T)</option>
              <option value="B">Billions ($B)</option>
              <option value="M">Millions ($M)</option>
              <option value="K">Thousands ($k)</option>
              <option value="EXACT">Exact ($)</option>
            </select>
            <!-- Volume Unit Dropdown -->
            <select
              v-else
              v-model="volumeUnit"
              class="bg-white text-slate-700 text-xs font-bold rounded-lg px-2 py-0.5 border border-slate-200/60 shadow-xs focus:ring-1 focus:ring-sky-500 cursor-pointer outline-none"
              title="Select Volume Display Unit"
            >
              <option value="AUTO">Auto ({{ autoVolumeLabel }})</option>
              <option value="MT">Million Tonnes (Mt)</option>
              <option value="KT">Kilo Tonnes (kT)</option>
              <option value="T">Tonnes (t)</option>
              <option value="KG">Kilograms (kg)</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Content Container -->
      <div class="h-72 sm:h-80 w-full relative">
        <!-- Empty State -->
        <div 
          v-if="filteredData.length === 0" 
          class="h-full w-full flex flex-col items-center justify-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200 text-center p-4"
        >
          <div class="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-2">
            <FilterXIcon class="w-5 h-5 text-slate-400" />
          </div>
          <p class="text-xs font-bold text-slate-700">No Export Records Found</p>
          <p class="text-[11px] text-slate-400 mt-0.5 max-w-xs">
            No trade activity recorded for the active chapter, time period, or destination market.
          </p>
        </div>

        <!-- Render Table (if chart_type === 'TABLE' or chartId === 'chart_market_share_table') -->
        <div 
          v-else-if="chartId === 'chart_market_share_table' || chartType === 'TABLE'" 
          class="h-full w-full overflow-y-auto overflow-x-auto rounded-xl border border-slate-100 text-xs"
        >
          <table class="w-full text-left border-collapse">
            <thead class="bg-slate-50 text-slate-600 font-bold uppercase text-[10px] tracking-wider sticky top-0 z-10 border-b border-slate-200">
              <tr>
                <th class="py-2 px-3">Rank</th>
                <th class="py-2 px-3">Destination Market</th>
                <th class="py-2 px-3 text-right">Volume ({{ activeVolumeMeta.suffix.trim() || 't' }})</th>
                <th class="py-2 px-3 text-right">Volume %</th>
                <th class="py-2 px-3 text-right">Revenue ({{ activeRevenueMeta.label }})</th>
                <th class="py-2 px-3 text-right">Revenue %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 text-slate-800">
              <tr 
                v-for="(row, idx) in tableRows" 
                :key="row.country || idx" 
                class="hover:bg-slate-50/80 transition-colors"
              >
                <td class="py-2 px-3 font-mono font-bold text-slate-500">#{{ row.rank || (idx + 1) }}</td>
                <td class="py-2 px-3 font-semibold text-slate-900 flex items-center gap-1.5">
                  <span>{{ row.country_en || row.country }}</span>
                  <span v-if="row.country_kh && row.country_kh !== row.country_en" class="text-[10px] text-slate-400">({{ row.country_kh }})</span>
                </td>
                <td class="py-2 px-3 text-right font-medium text-slate-700">
                  {{ formatVolumeCell(row.weight_ton) }}
                </td>
                <td class="py-2 px-3 text-right font-bold text-sky-700">
                  {{ (row.volume_share_pct || 0) > 0 && (row.volume_share_pct || 0) < 0.05 ? '<0.1%' : `${(row.volume_share_pct || 0).toFixed(1)}%` }}
                </td>
                <td class="py-2 px-3 text-right font-bold text-slate-900">
                  {{ formatRevenueCell(row.val_usd) }}
                </td>
                <td class="py-2 px-3 text-right font-black text-emerald-600">
                  {{ (row.revenue_share_pct || 0) > 0 && (row.revenue_share_pct || 0) < 0.05 ? '<0.1%' : `${(row.revenue_share_pct || 0).toFixed(1)}%` }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Render EChart -->
        <v-chart v-else class="w-full h-full" :option="chartOption" autoresize />
      </div>

      <!-- Touch-Scrollable Mobile-Responsive Legend for Pie / Donut Charts -->
      <div 
        v-if="(chartId === 'chart_commodity_share' || chartType === 'DONUT') && pieLegendItems.length > 0 && filteredData.length > 0"
        class="mt-2.5 pt-2 border-t border-slate-100"
      >
        <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 snap-x scroll-smooth -mx-1 px-1">
          <button
            v-for="item in pieLegendItems"
            :key="item.name"
            @click="togglePieLegendItem(item.name)"
            type="button"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-xl border text-xs font-semibold whitespace-nowrap transition-all flex-shrink-0 cursor-pointer snap-start"
            :class="item.visible 
              ? 'bg-slate-50 border-slate-200/90 text-slate-700 shadow-2xs hover:bg-slate-100 hover:border-slate-300' 
              : 'bg-slate-100/50 border-dashed border-slate-200 text-slate-400 opacity-60 line-through'"
            :title="`Click to toggle ${item.name} in chart`"
          >
            <span 
              class="w-2.5 h-2.5 rounded-full flex-shrink-0 transition-transform"
              :style="{ backgroundColor: item.visible ? item.color : '#cbd5e1' }"
            ></span>
            <span class="text-[11px] font-medium max-w-[130px] sm:max-w-[160px] truncate">{{ item.name }}</span>
            <span class="text-[10px] font-bold text-slate-500 font-mono">{{ item.sharePct }}%</span>
          </button>
        </div>
      </div>
    </div>

    <!-- AI Meaning Container Below -->
    <AiInsightBox :meaning="aiMeaning" />
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';

const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024);
const updateWidth = () => {
  if (typeof window !== 'undefined') {
    windowWidth.value = window.innerWidth;
  }
};

onMounted(() => {
  updateWidth();
  window.addEventListener('resize', updateWidth);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);
});

const isMobile = computed(() => windowWidth.value < 640);
import { Sparkles as SparklesIcon, FilterX as FilterXIcon } from 'lucide-vue-next';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, LineChart, PieChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent, ToolboxComponent, DataZoomComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import AiInsightBox from './AiInsightBox.vue';
import type { AiMeaning } from '../../types/dataset';
import { useDatasetStore } from '../../stores/datasetStore';
import { matchesHsSelection } from '../../utils/analyticsFilters';

use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent
]);

const store = useDatasetStore();

const props = defineProps<{
  chartId?: string;
  title: string;
  chartType: 'HORIZONTAL_BAR' | 'DONUT' | 'LINE' | 'TABLE' | 'PAIRED_BAR';
  data: any[];
  aiMeaning?: AiMeaning;
}>();

const topNLimit = ref<number>(5);

// Independent Unit Selector State per Chart
export type RevenueUnit = 'AUTO' | 'T' | 'B' | 'M' | 'K' | 'EXACT';
export type VolumeUnit = 'AUTO' | 'MT' | 'KT' | 'T' | 'KG';

const revenueUnit = ref<RevenueUnit>('AUTO');
const volumeUnit = ref<VolumeUnit>('AUTO');

const pieColors = [
  '#0284c7', '#10b981', '#6366f1', '#f59e0b', '#ec4899',
  '#8b5cf6', '#14b8a6', '#f97316', '#3b82f6', '#84cc16'
];

const hiddenPieItemNames = ref<string[]>([]);

const pieLegendItems = computed(() => {
  if (props.chartId !== 'chart_commodity_share' && props.chartType !== 'DONUT') return [];
  const data = filteredData.value;
  const sliced = (topNLimit.value < 999 && (props.chartId === 'chart_commodity_share' || props.chartId === 'chart_market_share'))
    ? data.slice(0, topNLimit.value)
    : data;
  return sliced.map((d, idx) => ({
    name: d.name,
    hs8_code: d.hs8_code,
    sharePct: d.sharePct,
    val_usd: d.val_usd,
    weight_ton: d.weight_ton,
    color: pieColors[idx % pieColors.length],
    visible: !hiddenPieItemNames.value.includes(d.name)
  }));
});

function togglePieLegendItem(name: string) {
  if (hiddenPieItemNames.value.includes(name)) {
    hiddenPieItemNames.value = hiddenPieItemNames.value.filter(n => n !== name);
  } else {
    if (hiddenPieItemNames.value.length < pieLegendItems.value.length - 1) {
      hiddenPieItemNames.value.push(name);
    }
  }
}

// Processed and sliced data based on active filters (clean aggregate without unit dependencies)
const filteredData = computed(() => {
  const rawList = props.data ? [...props.data] : [];
  const hsFilters = store.selectedHsCodes;
  const yrFilter = store.filterYear;
  const ctryFilter = store.filterCountry;
  const isTonnes = store.filterMetric === 'TONNES';

  // 1. Commodity Share (Donut Chart of HS8 Commodities)
  if (props.chartId === 'chart_commodity_share') {
    let list = rawList;
    list = list.filter(d => matchesHsSelection(d, hsFilters));
    if (yrFilter !== 'ALL') {
      list = list.filter(d => !d.year || d.year.toString() === yrFilter);
    }
    if (ctryFilter !== 'ALL') {
      list = list.filter(d => !d.country || d.country === 'ALL' || d.country.toLowerCase() === ctryFilter.toLowerCase());
    }

    const commMap = new Map<string, any>();
    for (const item of list) {
      const code = item.hs8_code || item.name;
      if (!code) continue;
      const prev = commMap.get(code) || {
        hs8_code: code,
        hs4_code: item.hs4_code,
        name: item.name || item.name_en || code,
        name_en: item.name_en || item.name || code,
        name_km: item.name_km,
        category_en: item.category_en,
        val_usd: 0,
        weight_ton: 0
      };
      prev.val_usd += (item.val_usd || (item.value ? item.value * 1e6 : 0));
      prev.weight_ton += (item.weight_ton ?? (item.weight_kg ? item.weight_kg / 1000 : 0));
      commMap.set(code, prev);
    }

    const aggregated = Array.from(commMap.values());
    const totalVal = aggregated.reduce((acc, c) => acc + (isTonnes ? c.weight_ton : c.val_usd), 0);

    return aggregated.map(c => {
      const rawVal = isTonnes ? c.weight_ton : c.val_usd;
      const share = totalVal > 0 ? (rawVal / totalVal) * 100 : 0;
      return {
        name: c.name_en || c.name,
        hs8_code: c.hs8_code,
        hs4_code: c.hs4_code,
        val_usd: c.val_usd,
        weight_ton: c.weight_ton,
        unit_price_usd_per_kg: c.weight_ton > 0 ? (c.val_usd / (c.weight_ton * 1000)) : 0,
        sharePct: Math.round(share * 10) / 10
      };
    }).sort((a, b) => (isTonnes ? b.weight_ton - a.weight_ton : b.val_usd - a.val_usd));
  }

  // 2. Destination Countries (Horizontal Bar Chart)
  if (props.chartId === 'chart_market_share') {
    let list = rawList.filter(d => matchesHsSelection(d, hsFilters));
    if (yrFilter !== 'ALL') {
      list = list.filter(d => !d.year || d.year.toString() === yrFilter);
    }
    if (ctryFilter !== 'ALL') {
      list = list.filter(d => (d.country || d.name || '').toLowerCase() === ctryFilter.toLowerCase());
    }

    const countryMap = new Map<string, any>();
    for (const item of list) {
      const cname = item.country_en || item.country || item.name;
      if (!cname) continue;
      const prev = countryMap.get(cname) || {
        country: cname,
        country_en: cname,
        country_kh: item.country_kh,
        val_usd: 0,
        weight_ton: 0
      };
      prev.val_usd += (item.val_usd || (item.value ? item.value * 1e6 : 0));
      prev.weight_ton += (item.weight_ton ?? (item.weight_kg ? item.weight_kg / 1000 : 0));
      countryMap.set(cname, prev);
    }

    const aggregated = Array.from(countryMap.values());
    const totalVal = aggregated.reduce((acc, c) => acc + (isTonnes ? c.weight_ton : c.val_usd), 0);

    return aggregated.map(c => {
      const rawVal = isTonnes ? c.weight_ton : c.val_usd;
      const share = totalVal > 0 ? (rawVal / totalVal) * 100 : 0;
      return {
        name: c.country_en,
        country: c.country_en,
        val_usd: c.val_usd,
        weight_ton: c.weight_ton,
        sharePct: Math.round(share * 10) / 10
      };
    }).sort((a, b) => (isTonnes ? b.weight_ton - a.weight_ton : b.val_usd - a.val_usd));
  }

  // 3. Monthly Seasonality Line Chart
  if (props.chartId === 'chart_seasonality') {
    let list = rawList.filter(d => matchesHsSelection(d, hsFilters));
    if (yrFilter !== 'ALL') {
      list = list.filter(d => !d.year || d.year.toString() === yrFilter);
    }
    if (ctryFilter !== 'ALL') {
      list = list.filter(d => !d.country || d.country.toLowerCase() === ctryFilter.toLowerCase());
    }

    const monthMap = new Map<string, any>();
    for (const item of list) {
      const ym = item.yyyy_mm || item.name;
      if (!ym || !/^\d{4}-\d{2}$/.test(ym)) continue;
      const prev = monthMap.get(ym) || { yyyy_mm: ym, val_usd: 0, weight_ton: 0 };
      prev.val_usd += (item.val_usd || (item.val_million_usd ? item.val_million_usd * 1e6 : 0));
      prev.weight_ton += (item.weight_ton ?? (item.weight_kton ? item.weight_kton * 1000 : (item.weight_kg ? item.weight_kg / 1000 : 0)));
      monthMap.set(ym, prev);
    }

    return Array.from(monthMap.values()).sort((a, b) => a.yyyy_mm.localeCompare(b.yyyy_mm));
  }

  return rawList;
});

// Table rows for Market Share Table widget (dynamically responds to Year and Country slicers with True Ranking)
const tableRows = computed(() => {
  const rawList = (props.data || store.dashboardData?.market_share_table || []).filter(d => matchesHsSelection(d, store.selectedHsCodes));
  const yrFilter = store.filterYear;
  const ctryFilter = store.filterCountry;

  // 1. Filter by Year (if active)
  let yearFiltered = rawList;
  if (yrFilter !== 'ALL') {
    yearFiltered = yearFiltered.filter(d => !d.year || d.year.toString() === yrFilter);
  }

  // 2. Aggregate by Country across the active year scope
  const countryMap = new Map<string, any>();
  for (const item of yearFiltered) {
    const cname = item.country_en || item.country || item.name;
    if (!cname) continue;
    const prev = countryMap.get(cname) || {
      country: cname,
      country_en: cname,
      country_kh: item.country_kh || cname,
      country_iso3: item.country_iso3 || 'OTH',
      val_usd: 0,
      weight_ton: 0
    };
    prev.val_usd += (item.val_usd || (item.value ? item.value * 1e6 : 0));
    prev.weight_ton += (item.weight_ton ?? (item.weight_kg ? item.weight_kg / 1000 : 0));
    countryMap.set(cname, prev);
  }

  const allAggregated = Array.from(countryMap.values());
  const totalScopeValUSD = allAggregated.reduce((sum, c) => sum + c.val_usd, 0);
  const totalScopeWeightTon = allAggregated.reduce((sum, c) => sum + c.weight_ton, 0);

  // 3. Sort all countries descending by export revenue to establish TRUE RANK
  const allRanked = allAggregated
    .sort((a, b) => b.val_usd - a.val_usd)
    .map((c, idx) => ({
      ...c,
      rank: idx + 1, // True Rank (#1, #2, #3... #14)
      revenue_share_pct: totalScopeValUSD > 0 ? (c.val_usd / totalScopeValUSD) * 100 : 0,
      volume_share_pct: totalScopeWeightTon > 0 ? (c.weight_ton / totalScopeWeightTon) * 100 : 0,
    }));

  // 4. Apply Country filter (if active)
  if (ctryFilter !== 'ALL') {
    return allRanked.filter(c => (c.country_en || c.country || '').toLowerCase() === ctryFilter.toLowerCase());
  }

  // If All Markets, return Top 10
  return allRanked.slice(0, 10);
});

// Auto unit detection based on max values
const autoRevenueUnit = computed<RevenueUnit>(() => {
  let maxVal = 0;
  if (props.chartId === 'chart_market_share_table' || props.chartType === 'TABLE') {
    const rows = tableRows.value || [];
    if (rows.length > 0) {
      maxVal = Math.max(...rows.map(r => r.val_usd || 0), 0);
    }
  } else {
    const data = filteredData.value || [];
    if (data.length > 0) {
      maxVal = Math.max(...data.map(d => d.val_usd || (d.value ? d.value * 1e6 : 0)), 0);
    }
  }
  if (maxVal >= 1e12) return 'T';
  if (maxVal >= 1e9) return 'B';
  if (maxVal >= 1e6) return 'M';
  if (maxVal >= 1e3) return 'K';
  return 'EXACT';
});

const autoVolumeUnit = computed<VolumeUnit>(() => {
  let maxWeight = 0;
  if (props.chartId === 'chart_market_share_table' || props.chartType === 'TABLE') {
    const rows = tableRows.value || [];
    if (rows.length > 0) {
      maxWeight = Math.max(...rows.map(r => r.weight_ton || 0), 0);
    }
  } else {
    const data = filteredData.value || [];
    if (data.length > 0) {
      maxWeight = Math.max(...data.map(d => d.weight_ton || 0), 0);
    }
  }
  if (maxWeight >= 1e6) return 'MT';
  if (maxWeight >= 1e3) return 'KT';
  if (maxWeight >= 1) return 'T';
  return 'KG';
});

const autoRevenueLabel = computed(() => {
  switch (autoRevenueUnit.value) {
    case 'T': return '$T';
    case 'B': return '$B';
    case 'M': return '$M';
    case 'K': return '$k';
    case 'EXACT': default: return '$';
  }
});

const autoVolumeLabel = computed(() => {
  switch (autoVolumeUnit.value) {
    case 'MT': return 'Mt';
    case 'KT': return 'kT';
    case 'T': return 't';
    case 'KG': default: return 'kg';
  }
});

const activeRevenueMeta = computed(() => {
  const unit = revenueUnit.value === 'AUTO' ? autoRevenueUnit.value : revenueUnit.value;
  switch (unit) {
    case 'T': return { divisor: 1e12, suffix: 'T', prefix: '$', label: '$T USD', fullUnit: 'Trillion USD ($T)' };
    case 'B': return { divisor: 1e9, suffix: 'B', prefix: '$', label: '$B USD', fullUnit: 'Billion USD ($B)' };
    case 'M': return { divisor: 1e6, suffix: 'M', prefix: '$', label: '$M USD', fullUnit: 'Million USD ($M)' };
    case 'K': return { divisor: 1e3, suffix: 'k', prefix: '$', label: '$k USD', fullUnit: 'Thousand USD ($k)' };
    case 'EXACT': default: return { divisor: 1, suffix: '', prefix: '$', label: '$ USD', fullUnit: 'Exact USD ($)' };
  }
});

const activeVolumeMeta = computed(() => {
  const unit = volumeUnit.value === 'AUTO' ? autoVolumeUnit.value : volumeUnit.value;
  switch (unit) {
    case 'MT': return { divisor: 1e6, suffix: ' Mt', prefix: '', label: 'Million Tonnes (Mt)', fullUnit: 'Million Tonnes (Mt)' };
    case 'KT': return { divisor: 1e3, suffix: ' kT', prefix: '', label: 'Kilo Tonnes (kT)', fullUnit: 'Kilo Tonnes (kT)' };
    case 'T': return { divisor: 1, suffix: ' t', prefix: '', label: 'Tonnes (t)', fullUnit: 'Tonnes (t)' };
    case 'KG': default: return { divisor: 0.001, suffix: ' kg', prefix: '', label: 'Kilograms (kg)', fullUnit: 'Kilograms (kg)' };
  }
});

const unitMeta = computed(() => {
  return store.filterMetric === 'TONNES' ? activeVolumeMeta.value : activeRevenueMeta.value;
});

const formatRevenueCell = (rawUSD?: number): string => {
  if (rawUSD === undefined || rawUSD === null || isNaN(rawUSD)) return '$0';
  const meta = activeRevenueMeta.value;
  const scaled = rawUSD / meta.divisor;
  if (meta.divisor === 1) {
    return `$${Math.round(scaled).toLocaleString()}`;
  }
  const formatted = scaled.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
  return `$${formatted}${meta.suffix}`;
};

const formatVolumeCell = (rawTonnes?: number): string => {
  if (rawTonnes === undefined || rawTonnes === null || isNaN(rawTonnes)) return '0 t';
  const meta = activeVolumeMeta.value;
  const scaled = rawTonnes / meta.divisor;
  if (meta.divisor === 0.001) {
    const decimals = (scaled < 10 && scaled % 1 !== 0) ? 2 : (scaled % 1 === 0 ? 0 : 1);
    return `${scaled.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: 2 })} kg`;
  }
  const maxDecimals = scaled === 0 ? 0 : (scaled < 0.1 ? 4 : (scaled < 10 && scaled % 1 !== 0 ? 2 : (scaled % 1 === 0 ? 0 : 1)));
  const minDecimals = scaled % 1 === 0 ? 0 : 1;
  const formatted = scaled.toLocaleString(undefined, {
    minimumFractionDigits: minDecimals,
    maximumFractionDigits: maxDecimals
  });
  return `${formatted}${meta.suffix}`;
};

const dynamicTitle = computed(() => {
  const code = store.selectedSingleHsCode;
  const selectedComm = store.dashboardData?.hs8_commodities?.find(c => c.hs8_code === code)
    || store.dashboardData?.commodity_list?.find(c => c.hs8_code === code);
  const commName = selectedComm ? selectedComm.name_en : '';
  const activeHsText = code ? ` (HS ${code}${commName ? ' · ' + commName : ''})`
    : store.selectedHsCodes.length ? ` (${store.selectedHsCodes.length} commodities)` : '';
  const activeYearText = store.filterYear !== 'ALL' ? ` · ${store.filterYear}` : '';
  const activeCountryText = store.filterCountry !== 'ALL' ? ` · ${store.filterCountry}` : '';
  const filterSuffix = `${activeHsText}${activeYearText}${activeCountryText}`;
  const isTonnes = store.filterMetric === 'TONNES';
  const topSuffix = topNLimit.value < 999 ? ` (Top ${topNLimit.value})` : '';
  const activeUnitLabel = isTonnes ? activeVolumeMeta.value.label : activeRevenueMeta.value.label;

  if (props.chartId === 'chart_commodity_share') {
    if (isTonnes) return `Commodities Export Volume Share${topSuffix}${filterSuffix}`;
    return `Commodities Export Revenue Share${topSuffix}${filterSuffix}`;
  }
  if (props.chartId === 'chart_market_share') {
    if (isTonnes) return `Top Destination Countries Volume (${activeUnitLabel})${topSuffix}${filterSuffix}`;
    return `Top Destination Countries Revenue (${activeUnitLabel})${topSuffix}${filterSuffix}`;
  }
  if (props.chartId === 'chart_market_share_table') {
    const yearText = store.filterYear !== 'ALL' ? ` · Year ${store.filterYear}` : '';
    const countryText = store.filterCountry !== 'ALL' ? ` · ${store.filterCountry}` : '';
    const baseTitle = store.filterCountry !== 'ALL' ? 'Market Share Summary' : 'Top 10 Market Share Summary';
    return `${baseTitle}${countryText}${yearText}`;
  }
  if (props.chartId === 'chart_seasonality') {
    if (isTonnes) return `Export Volume by Months (${activeUnitLabel})${filterSuffix}`;
    return `Export Revenue by Months (${activeUnitLabel})${filterSuffix}`;
  }
  return props.title;
});

const filteredSubtitle = computed(() => {
  if (props.chartId === 'chart_commodity_share') {
    return `Showing ${Math.min(topNLimit.value, filteredData.value.length)} of ${filteredData.value.length} HS8 commodities`;
  }
  if (props.chartId === 'chart_market_share') {
    return `Showing ${Math.min(topNLimit.value, filteredData.value.length)} partner markets`;
  }
  if (props.chartId === 'chart_market_share_table') {
    const yearScope = store.filterYear !== 'ALL' ? `in Year ${store.filterYear}` : 'across all reporting periods';
    if (store.filterCountry !== 'ALL') {
      return `Market share, export volume, and national rank position for ${store.filterCountry} ${yearScope}`;
    }
    return `Export volume and revenue breakdown across top destination partner markets ${yearScope}`;
  }
  if (props.chartId === 'chart_seasonality') {
    const isTonnes = store.filterMetric === 'TONNES';
    if (isTonnes) return `Monthly export volume trajectory in ${activeVolumeMeta.value.fullUnit}`;
    return `Monthly export revenue trajectory in ${activeRevenueMeta.value.fullUnit}`;
  }
  return '';
});

// ECharts Options Generator
const chartOption = computed(() => {
  const isTonnes = store.filterMetric === 'TONNES';
  const data = filteredData.value;
  const slicedData = (topNLimit.value < 999 && (props.chartId === 'chart_commodity_share' || props.chartId === 'chart_market_share'))
    ? data.slice(0, topNLimit.value)
    : data;

  const toolbox = {
    show: true,
    right: '1%',
    top: '0%',
    itemSize: 12,
    itemGap: 8,
    feature: {
      saveAsImage: { title: 'Save Image' },
      restore: { title: 'Reset' }
    }
  };

  // 1. DONUT CHART (for HS8 Commodities)
  if (props.chartId === 'chart_commodity_share' || props.chartType === 'DONUT') {
    const pieData = slicedData
      .filter(d => !hiddenPieItemNames.value.includes(d.name))
      .map((d) => {
        const itemIdx = slicedData.findIndex(s => s.name === d.name);
        const raw = (isTonnes ? d.weight_ton : d.val_usd) / unitMeta.value.divisor;
        const rounded = raw < 1 ? Math.round(raw * 1000) / 1000 : Math.round(raw * 100) / 100;
        return {
          name: d.name,
          value: rounded,
          val_usd: d.val_usd,
          weight_ton: d.weight_ton,
          sharePct: d.sharePct,
          itemStyle: {
            color: pieColors[itemIdx % pieColors.length]
          }
        };
      });

    return {
      toolbox,
      tooltip: {
        trigger: 'item',
        confine: true,
        extraCssText: 'max-width: 240px; white-space: normal; word-break: break-word; border-radius: 10px; padding: 8px 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15); z-index: 50;',
        formatter: (params: any) => {
          const item = params.data;
          const valText = isTonnes 
            ? `<strong>${formatVolumeCell(item.weight_ton)}</strong>` 
            : `<strong>${formatRevenueCell(item.val_usd)}</strong>`;
          return `
            <div style="font-weight:bold;color:#0f172a;margin-bottom:2px;line-height:1.3;">${params.name}</div>
            <div style="font-size:12px;color:#334155;">${valText} <span style="color:#0284c7;font-weight:600;">(${params.percent}%)</span></div>
          `;
        }
      },

      legend: {
        show: false
      },
      series: [
        {
          name: 'Commodity Share',
          type: 'pie',
          radius: isMobile.value ? ['48%', '76%'] : ['45%', '72%'],
          center: ['50%', '50%'],
          minAngle: 8,
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: !isMobile.value,
            formatter: '{b}: {d}%',
            fontSize: 9.5,
            color: '#334155',
            overflow: 'truncate',
            width: 80
          },
          labelLine: {
            show: !isMobile.value,
            length: 8,
            length2: 8
          },
          data: pieData
        }
      ]
    };
  }

  // 2. HORIZONTAL BAR CHART (for Destination Countries)
  if (props.chartId === 'chart_market_share' || props.chartType === 'HORIZONTAL_BAR') {
    const categories = slicedData.map(d => d.name).reverse();
    const values = slicedData.map(d => {
      const raw = (isTonnes ? d.weight_ton : d.val_usd) / unitMeta.value.divisor;
      return raw < 1 ? Math.round(raw * 1000) / 1000 : Math.round(raw * 100) / 100;
    }).reverse();

    return {
      toolbox,
      grid: { left: '2%', right: isMobile.value ? '14%' : '18%', bottom: '4%', top: 32, containLabel: true },
      tooltip: {
        trigger: 'axis',
        confine: true,
        extraCssText: 'max-width: 260px; white-space: normal; word-break: break-word; border-radius: 10px; padding: 8px 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15); z-index: 50;',
        axisPointer: { type: 'shadow' },
        formatter: (params: any[]) => {
          const p = params[0];
          const raw = slicedData.find(d => d.name === p.name);
          const rawValUSD = raw?.val_usd ?? (isTonnes ? 0 : p.value * unitMeta.value.divisor);
          const rawWeightTon = raw?.weight_ton ?? (isTonnes ? p.value * unitMeta.value.divisor : 0);
          const valText = isTonnes 
            ? `<strong>${formatVolumeCell(rawWeightTon)}</strong>` 
            : `<strong>${formatRevenueCell(rawValUSD)}</strong>`;
          const shareText = raw?.sharePct ? `<span style="color:#0284c7;font-weight:bold;"> (${raw.sharePct}% share)</span>` : '';
          return `
            <div style="font-weight:bold;color:#0f172a;line-height:1.3;">${p.name}</div>
            <div style="font-size:12px;color:#334155;margin-top:2px;">${valText}${shareText}</div>
          `;
        }
      },
      xAxis: {
        type: 'value',
        splitNumber: 3,
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
        axisLabel: {
          fontSize: 9.5,
          color: '#64748b',
          hideOverlap: true,
          formatter: (v: number) => isTonnes ? formatVolumeCell(v * unitMeta.value.divisor) : `${unitMeta.value.prefix}${v.toLocaleString()}${unitMeta.value.suffix}`
        }
      },
      yAxis: {
        type: 'category',
        data: categories,
        axisLabel: {
          fontWeight: 'bold',
          fontSize: 10.5,
          color: '#1e293b',
          width: 70,
          overflow: 'truncate'
        }
      },
      series: [
        {
          name: 'Export Metric',
          type: 'bar',
          data: values,
          barMaxWidth: 22,
          itemStyle: {
            color: '#0284c7',
            borderRadius: [0, 6, 6, 0]
          },
          label: {
            show: true,
            position: 'right',
            offset: [4, 0],
            formatter: (p: any) => isTonnes ? formatVolumeCell(p.value * unitMeta.value.divisor) : `${unitMeta.value.prefix}${p.value.toLocaleString()}${unitMeta.value.suffix}`,
            fontSize: 9.5,
            fontWeight: 'bold',
            color: '#0369a1'
          }
        }
      ]
    };
  }

  // 3. MONTHLY TIMELINE SINGLE-LINE CHART (controlled by Revenue vs. Volume slicer)
  if (props.chartId === 'chart_seasonality' || props.chartType === 'LINE') {
    const xDates = data.map(d => d.yyyy_mm);
    const values = data.map(d => {
      const rawVal = isTonnes ? (d.weight_ton || 0) : (d.val_usd || 0);
      const raw = rawVal / unitMeta.value.divisor;
      return raw < 1 ? Math.round(raw * 1000) / 1000 : Math.round(raw * 100) / 100;
    });
    const metricName = isTonnes ? 'Export Volume' : 'Export Revenue';
    const yAxisLabel = (v: number) => `${unitMeta.value.prefix}${v.toLocaleString()}${unitMeta.value.suffix}`;
    const yAxisName = isTonnes ? `Volume (${unitMeta.value.suffix.trim()})` : `Revenue (${unitMeta.value.label})`;

    return {
      toolbox: {
        show: true,
        right: '1%',
        top: '0%',
        itemSize: 12,
        itemGap: 8,
        feature: {
          dataZoom: {
            yAxisIndex: 'none',
            title: {
              zoom: 'Zoom Area',
              back: 'Reset'
            }
          },
          saveAsImage: { title: 'Save Image' },
          restore: { title: 'Reset' }
        }
      },
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: 0,
          zoomOnMouseWheel: true,
          moveOnMouseMove: true,
          moveOnMouseWheel: true
        },
        {
          type: 'slider',
          xAxisIndex: 0,
          height: 16,
          bottom: 2,
          borderColor: 'transparent',
          backgroundColor: '#f8fafc',
          fillerColor: 'rgba(2, 132, 199, 0.15)',
          handleStyle: {
            color: '#0284c7',
            borderColor: '#0284c7',
            shadowBlur: 2,
            shadowColor: 'rgba(0, 0, 0, 0.15)'
          },
          textStyle: {
            color: '#64748b',
            fontSize: 9
          },
          brushSelect: false
        }
      ],
      grid: { left: '2%', right: '4%', bottom: 28, top: 32, containLabel: true },
      tooltip: {
        trigger: 'axis',
        confine: true,
        extraCssText: 'max-width: 240px; white-space: normal; word-break: break-word; border-radius: 10px; padding: 8px 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15); z-index: 50;',
        axisPointer: { type: 'line', lineStyle: { color: '#0284c7', type: 'dashed' } },
        formatter: (params: any[]) => {
          const p = params[0];
          const date = p.name;
          const raw = data.find(d => d.yyyy_mm === date);
          const rawValUSD = raw?.val_usd ?? (isTonnes ? 0 : p.value * unitMeta.value.divisor);
          const rawWeightTon = raw?.weight_ton ?? (isTonnes ? p.value * unitMeta.value.divisor : 0);
          const valDisplay = isTonnes ? formatVolumeCell(rawWeightTon) : formatRevenueCell(rawValUSD);
          return `
            <div style="font-weight:bold;color:#0f172a;margin-bottom:3px;line-height:1.3;">${date}</div>
            <div style="font-size:12px;color:#334155;">${metricName}: <strong>${valDisplay}</strong></div>
          `;
        }
      },

      xAxis: {
        type: 'category',
        data: xDates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisLabel: { fontSize: 9.5, color: '#64748b', hideOverlap: true }
      },
      yAxis: {
        type: 'value',
        name: yAxisName,
        nameTextStyle: { fontSize: 10, color: '#64748b', fontWeight: 'bold' },
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
        axisLabel: { fontSize: 9.5, color: '#64748b', formatter: yAxisLabel }
      },
      series: [
        {
          name: metricName,
          type: 'line',
          data: values,
          smooth: true,
          showSymbol: true,
          symbolSize: 6,
          itemStyle: { color: '#0284c7' },
          lineStyle: { width: 3, color: '#0284c7' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(2, 132, 199, 0.25)' },
                { offset: 1, color: 'rgba(2, 132, 199, 0.01)' }
              ]
            }
          }
        }
      ]
    };
  }

  return {};
});
</script>
