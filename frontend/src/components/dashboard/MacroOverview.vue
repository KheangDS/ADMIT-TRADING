<template>
  <div v-if="store.dashboardData" class="space-y-6 sm:space-y-8">
    
    <!-- Executive Overview Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 sm:pb-4 border-b border-slate-200 gap-2 sm:gap-3">
      <div>
        <div class="flex flex-wrap items-center gap-2">
          <h2 class="text-lg sm:text-xl font-black text-slate-900 tracking-tight">Export Analytics Overview</h2>
          <span 
            v-if="liveDisplayPeriod" 
            class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-50 text-sky-700 border border-sky-200/80 shadow-2xs font-mono"
            :title="`Current reporting data period: ${liveDisplayPeriod}`"
          >
            <Calendar class="w-3 h-3 text-sky-600 flex-shrink-0" />
            <span>{{ liveDisplayPeriod }}</span>
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-0.5">High-level Cambodian agricultural trade performance & product-level insights</p>
      </div>
    </div>

    <!-- Executive KPI Cards Grid (5 Core Pillars) -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-2.5 sm:gap-3.5 lg:gap-4">
      <KpiCard
        v-for="(kpi, idx) in store.dashboardData.summary_kpis"
        :key="kpi.label"
        :label="kpi.label"
        :value="kpi.value"
        :description="kpi.description"
        :class="{ 'col-span-2 w-full max-w-[260px] sm:max-w-[280px] lg:max-w-none mx-auto lg:col-span-1': idx === 0 }"
        :is-hero="idx === 0"
      />
    </div>

    <!-- Interactive Graph Slicers & Filters Panel -->
    <GraphSlicerPanel />

    <!-- Executive Charts Grid (Powered by Interactive Chart Customizer) -->
    <div v-if="store.dashboardData.level1_charts.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
      <ChartCustomizer
        v-for="chart in store.dashboardData.level1_charts"
        :key="chart.chart_id"
        :chart-id="chart.chart_id"
        :title="chart.title"
        :chart-type="chart.chart_type"
        :data="chart.data"
        :ai-meaning="chart.ai_meaning"
      />
    </div>
    <div v-else class="bg-white p-6 sm:p-10 rounded-2xl border border-slate-200 text-center space-y-2">
      <h4 class="text-sm font-bold text-slate-700">No Export Charts Available</h4>
      <p class="text-xs text-slate-400">Charts and AI insights will automatically generate once a trade dataset is ingested from the Admin Portal.</p>
    </div>

    <!-- HS8 Commodities Summary Data Table -->
    <div class="bg-white p-4 sm:p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-slate-100 gap-2">
        <div>
          <h3 class="text-sm sm:text-base font-bold text-slate-900">Export Summary: HS 8-Digit Commodities</h3>
          <p class="text-xs text-slate-500">Comprehensive breakdown across active 8-digit tariff line commodities</p>
        </div>
        
        <!-- Table Slicers: Top 5, Top 10, All -->
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            <span class="text-[10px] text-slate-500 font-bold px-1 uppercase tracking-wider">Show:</span>
            <button
              v-for="n in [5, 10]"
              :key="n"
              @click="tableTopN = n"
              :class="[
                'cursor-pointer px-2.5 py-0.5 rounded-lg transition-all text-xs',
                tableTopN === n
                  ? 'bg-white text-sky-600 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              ]"
            >
              Top {{ n }}
            </button>
            <button
              @click="tableTopN = 999"
              :class="[
                'cursor-pointer px-2.5 py-0.5 rounded-lg transition-all text-xs',
                tableTopN === 999
                  ? 'bg-white text-sky-600 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900'
              ]"
            >
              All ({{ totalCommoditiesCount }})
            </button>
          </div>
        </div>
      </div>

      <div class="overflow-x-auto -mx-4 sm:mx-0 px-4 sm:px-0">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200 text-[11px]">
            <tr>
              <th class="p-3">HS8 Code</th>
              <th class="p-3">Commodity Product Specification</th>
              <th class="p-3">Category</th>
              <th class="p-3 text-right">Volume</th>
              <th class="p-3 text-right">Revenue</th>
              <th class="p-3 text-right">Revenue Share</th>
              <th class="p-3 text-right">Avg Unit Price</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="displayedCommodities.length === 0">
              <td colspan="7" class="p-8 text-center text-slate-400">
                No commodity records available.
              </td>
            </tr>
            <tr v-else v-for="row in displayedCommodities" :key="row.hs8_code" class="hover:bg-slate-50/80 transition-colors">
              <td class="p-3 font-mono font-bold text-sky-700">
                <router-link :to="`/compare`" class="hover:underline" title="Compare on HS8 page">
                  {{ row.hs8_code }}
                </router-link>
              </td>
              <td class="p-3">
                <span class="font-bold text-slate-900 block">{{ row.name_en }}</span>
                <span v-if="row.name_km && row.name_km !== row.name_en" class="text-[11px] text-slate-500 block truncate max-w-md">
                  {{ row.name_km }}
                </span>
              </td>
              <td class="p-3">
                <span class="inline-block px-2 py-0.5 text-[10px] font-bold rounded-md bg-slate-100 text-slate-700">
                  {{ row.category_en || 'Agricultural' }}
                </span>
              </td>
              <td class="p-3 text-right font-medium text-slate-700">
                {{ formatTableVolume(row.weight_tonnes) }}
              </td>
              <td class="p-3 text-right font-bold text-slate-900">
                {{ formatTableRevenue(row.val_usd) }}
              </td>
              <td class="p-3 text-right font-bold text-sky-600">{{ row.revenue_share_pct.toFixed(1) }}%</td>
              <td class="p-3 text-right font-mono font-bold text-slate-800">
                {{ formatUnitPrice(row) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- About This Platform: Empowering Agro-SMEs with Trade Intelligence -->
    <div class="bg-gradient-to-br from-white via-sky-50/40 to-slate-50 p-4 sm:p-6 md:p-8 rounded-2xl text-slate-900 shadow-sm border border-slate-200/90">
      <div class="flex items-center gap-2.5 text-sky-700 font-bold text-xs uppercase tracking-wider mb-6">
        <Sparkles class="w-4 h-4 text-sky-600" />
        <span>About This Platform: Empowering Agro-SMEs with Trade Intelligence</span>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Pillar 1 -->
        <div class="bg-white rounded-xl p-5 border border-slate-200/90 shadow-2xs flex flex-col justify-start">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-9 h-9 rounded-xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-600">
              <Globe class="w-4 h-4" />
            </div>
            <h4 class="font-bold text-sm text-slate-900">Democratizing Trade Intelligence for Local SMEs</h4>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed text-justify">
            Eliminates trade information asymmetry by equipping Cambodian agricultural SMEs and local producers with direct, institutional-grade visibility into global market demand, buyer destinations, and benchmark export unit prices ($/kg)—intelligence traditionally restricted to large multinational conglomerates.
          </p>
        </div>

        <!-- Pillar 2 -->
        <div class="bg-white rounded-xl p-5 border border-slate-200/90 shadow-2xs flex flex-col justify-start">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
              <TrendingUp class="w-4 h-4" />
            </div>
            <h4 class="font-bold text-sm text-slate-900">Actionable Export Strategy & Margin Optimization</h4>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed text-justify">
            Empowers agro-exporters to identify high-margin target markets, bypass intermediary markups, and strategically align harvest shipping schedules with seasonal price peaks to maximize export profitability.
          </p>
        </div>

        <!-- Pillar 3 -->
        <div class="bg-white rounded-xl p-5 border border-slate-200/90 shadow-2xs flex flex-col justify-start">
          <div class="flex items-center gap-3 mb-3">
            <div class="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
              <Cpu class="w-4 h-4" />
            </div>
            <h4 class="font-bold text-sm text-slate-900">High-Performance Analytics Powered by Grounded AI</h4>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed text-justify">
            Combines a high-performance analytical data engine with grounded conversational AI, allowing business owners and exporters to effortlessly explore complex customs records and uncover trade opportunities through natural language without requiring data science expertise.
          </p>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Sparkles, Globe, TrendingUp, Cpu, Calendar } from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';
import KpiCard from './KpiCard.vue';
import GraphSlicerPanel from './GraphSlicerPanel.vue';
import ChartCustomizer from './ChartCustomizer.vue';

const store = useDatasetStore();
const tableTopN = ref<number>(10);

function formatDisplayMonth(ym: string | undefined | null): string {
  if (!ym) return '';
  const clean = ym.trim();
  if (/^\d{4}-\d{2}$/.test(clean)) {
    const [y, m] = clean.split('-').map(Number);
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthName = monthNames[m - 1];
    if (monthName) return `${monthName} ${y}`;
  }
  return clean;
}

const liveDisplayPeriod = computed(() => {
  const pub = store.dashboardData?.publication;
  if (pub?.start_month && pub?.end_month) {
    return `${formatDisplayMonth(pub.start_month)} – ${formatDisplayMonth(pub.end_month)}`;
  }
  const begin = store.dashboardData?.begin_date;
  const end = store.dashboardData?.end_date;
  if (begin && end) {
    return `${formatDisplayMonth(begin)} – ${formatDisplayMonth(end)}`;
  }
  return '';
});

const formatTableVolume = (tonnes: number): string => {
  if (!tonnes || tonnes === 0) return '0 t';
  if (tonnes < 1) {
    const kg = Math.round(tonnes * 1000 * 100) / 100;
    const decimals = (kg < 10 && kg % 1 !== 0) ? 2 : (kg % 1 === 0 ? 0 : 1);
    return `${kg.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: 2 })} kg`;
  }
  return `${(Math.round(tonnes * 10) / 10).toLocaleString()} Tonnes`;
};

const formatTableRevenue = (valUsd: number): string => {
  if (!valUsd || valUsd === 0) return '$0';
  if (valUsd < 1_000_000) {
    const kUsd = Math.round((valUsd / 1000) * 10) / 10;
    return `$${kUsd.toLocaleString()}k USD`;
  }
  return `$${(valUsd / 1e6).toFixed(2)}M USD`;
};

const formatUnitPrice = (row: any): string => {
  const weightKg = (row.weight_kg !== undefined && row.weight_kg > 0)
    ? row.weight_kg
    : ((row.weight_tonnes !== undefined ? row.weight_tonnes : (row.weight_ton || 0)) * 1000);
  const valUsd = row.val_usd || 0;
  if (weightKg > 0 && valUsd > 0) {
    const pricePerKg = valUsd / weightKg;
    return `$${pricePerKg.toFixed(2)}/kg`;
  }
  if (row.unit_price_usd_per_kg && row.unit_price_usd_per_kg > 0) {
    return `$${row.unit_price_usd_per_kg.toFixed(2)}/kg`;
  }
  return '$0.00/kg';
};

const allCommodities = computed(() => {
  if (store.dashboardData?.hs8_commodities && store.dashboardData.hs8_commodities.length > 0) {
    return store.dashboardData.hs8_commodities;
  }
  return [];
});

const totalCommoditiesCount = computed(() => {
  return allCommodities.value.length;
});

const displayedCommodities = computed(() => {
  const list = [...allCommodities.value];
  list.sort((a, b) => b.val_usd - a.val_usd);

  if (tableTopN.value < 999) {
    return list.slice(0, tableTopN.value);
  }
  return list;
});
</script>
