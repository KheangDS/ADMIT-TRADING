<template>
  <div v-if="store.dashboardData" class="space-y-8">
    
    <!-- Executive Overview Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-3">
      <div>
        <h2 class="text-xl font-black text-slate-900 tracking-tight">Macro Export Analytics Overview</h2>
        <p class="text-xs text-slate-500 mt-0.5">High-level Cambodian agricultural trade performance & market insights</p>
      </div>
    </div>

    <!-- Executive KPI Cards Grid (5 Core Pillars) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
      <KpiCard
        v-for="kpi in store.dashboardData.summary_kpis"
        :key="kpi.label"
        :label="kpi.label"
        :value="kpi.value"
        :description="kpi.description"
      />
    </div>

    <!-- High Risk Alert Banner (HHI) -->
    <div 
      v-if="store.dashboardData.is_high_risk" 
      class="bg-gradient-to-r from-rose-50 via-amber-50/40 to-white border border-rose-200/80 rounded-2xl p-4 sm:p-5 shadow-xs flex items-start gap-3.5 transition-all"
    >
      <div class="w-9 h-9 rounded-xl bg-rose-100/80 text-rose-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-2xs">
        <ShieldAlertIcon class="w-5 h-5 text-rose-600" />
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <h4 class="text-sm font-bold text-rose-950">High Export Market Concentration Risk</h4>
          <span class="text-[11px] font-mono font-extrabold px-2 py-0.5 rounded-md bg-rose-100 text-rose-800 border border-rose-200/60">
            HHI = {{ store.dashboardData.hhi_risk_score }}
          </span>
        </div>
        <p class="text-xs text-rose-800/90 mt-1 leading-relaxed">
          Over 95% of total export revenue depends on just two neighboring countries (Vietnam & Thailand). Diversification into non-regional markets is strongly recommended.
        </p>
      </div>
    </div>

    <!-- Interactive Graph Slicers & Filters Panel -->
    <GraphSlicerPanel />

    <!-- Executive Charts Grid (Powered by Interactive Chart Customizer) -->
    <div v-if="store.dashboardData.level1_charts.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
    <div v-else class="bg-white p-10 rounded-2xl border border-slate-200 text-center space-y-2">
      <h4 class="text-sm font-bold text-slate-700">No Export Charts Available</h4>
      <p class="text-xs text-slate-400">Charts and AI insights will automatically generate once a trade dataset is ingested from the Admin Portal.</p>
    </div>

    <!-- Macro Summary Data Table (All HS4 Chapters) -->
    <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
        <div>
          <h3 class="text-base font-bold text-slate-900">Macro Export Summary by HS 4-Digit Chapter</h3>
          <p class="text-xs text-slate-500">Breakdown of export revenue, weight volume, and unit prices</p>
        </div>
        <span v-if="store.filterHsCode !== 'ALL'" class="text-xs px-2.5 py-1 bg-sky-50 text-sky-700 font-semibold rounded-lg border border-sky-200">
          Showing HS {{ store.filterHsCode }} (1 of {{ store.dashboardData.hs4_categories.length }})
        </span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
            <tr>
              <th class="p-3">HS Code</th>
              <th class="p-3">Commodity Category Description</th>
              <th :class="['p-3 text-right transition-colors', store.filterMetric === 'TONNES' ? 'bg-sky-100/80 text-sky-950 font-black' : '']">
                Volume
              </th>
              <th :class="['p-3 text-right transition-colors', store.filterMetric === 'USD' ? 'bg-sky-100/80 text-sky-950 font-black' : '']">
                Revenue
              </th>
              <th class="p-3 text-right">Revenue Share</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="displayedCategories.length === 0">
              <td colspan="5" class="p-8 text-center text-slate-400">
                No commodity records matching active filter.
              </td>
            </tr>
            <tr v-else v-for="row in displayedCategories" :key="row.hs4_code" class="hover:bg-slate-50/80 transition-colors">
              <td class="p-3 font-mono font-bold text-slate-800">HS {{ row.hs4_code }}</td>
              <td class="p-3">
                <span class="font-bold text-slate-900 block">{{ row.official_title || row.hs4_desc }}</span>
                <span v-if="row.official_title && row.official_title !== row.hs4_desc" class="text-[11px] text-slate-500 block truncate max-w-md">
                  {{ row.hs4_desc }}
                </span>
              </td>
              <td :class="['p-3 text-right transition-colors', store.filterMetric === 'TONNES' ? 'bg-sky-50 font-black text-sky-900' : 'font-medium text-slate-700']">
                {{ formatTableVolume(row.weight_tonnes) }}
              </td>
              <td :class="['p-3 text-right transition-colors', store.filterMetric === 'USD' ? 'bg-sky-50 font-black text-sky-900' : 'font-bold text-slate-900']">
                {{ formatTableRevenue(row.val_usd) }}
              </td>
              <td class="p-3 text-right font-bold text-sky-600">{{ row.revenue_share_pct.toFixed(1) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Category Selection Cards Grid -->
    <CategoryCardGrid v-if="displayedCategories.length > 0" :categories="displayedCategories" />

    <!-- Executive Strategy Action Plan Cards -->
    <div v-if="store.dashboardData.executive_strategy.length > 0" class="bg-gradient-to-br from-slate-900 to-sky-950 p-6 rounded-2xl text-white shadow-lg">
      <div class="flex items-center gap-2 text-sky-400 font-bold text-xs uppercase tracking-wider mb-3">
        <TargetIcon class="w-4 h-4" />
        <span>Executive Strategy & Action Plan</span>
      </div>
      <ul class="space-y-2.5 text-sm text-slate-200">
        <li v-for="(strat, idx) in store.dashboardData.executive_strategy" :key="idx" class="flex items-start gap-2.5">
          <span class="flex-shrink-0 w-5 h-5 rounded-full bg-sky-500/20 text-sky-300 font-bold text-xs flex items-center justify-center border border-sky-400/30">
            {{ idx + 1 }}
          </span>
          <span class="leading-relaxed">{{ strat }}</span>
        </li>
      </ul>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ShieldAlert as ShieldAlertIcon, Target as TargetIcon } from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';
import KpiCard from './KpiCard.vue';
import GraphSlicerPanel from './GraphSlicerPanel.vue';
import ChartCustomizer from './ChartCustomizer.vue';
import CategoryCardGrid from './CategoryCardGrid.vue';

const store = useDatasetStore();

const formatTableVolume = (tonnes: number): string => {
  if (!tonnes || tonnes === 0) return '0 t';
  if (tonnes < 1) {
    const kg = Math.round(tonnes * 1000 * 10) / 10;
    return `${kg.toLocaleString()} kg`;
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

const displayedCategories = computed(() => {
  if (!store.dashboardData?.hs4_categories) return [];
  
  // If year or country filter is active, aggregate dynamically from chart_commodity_share data
  const commodityChart = store.dashboardData.level1_charts?.find(c => c.chart_id === 'chart_commodity_share');
  if (commodityChart && (store.filterYear !== 'ALL' || store.filterCountry !== 'ALL')) {
    let raw = [...commodityChart.data];
    if (store.filterHsCode !== 'ALL') {
      raw = raw.filter(d => d.hs4_code === store.filterHsCode);
    }
    if (store.filterYear !== 'ALL') {
      raw = raw.filter(d => !d.year || d.year.toString() === store.filterYear);
    }
    if (store.filterCountry !== 'ALL') {
      raw = raw.filter(d => !d.country || d.country.toLowerCase() === store.filterCountry.toLowerCase());
    }

    const hsMap = new Map<string, { hs4_code: string; val_usd: number; weight_tonnes: number; hs4_desc: string; official_title: string }>();
    for (const item of raw) {
      if (!item.hs4_code) continue;
      const matched = store.dashboardData.hs4_categories.find(c => c.hs4_code === item.hs4_code);
      const prev = hsMap.get(item.hs4_code) || {
        hs4_code: item.hs4_code,
        val_usd: 0,
        weight_tonnes: 0,
        hs4_desc: matched?.hs4_desc || item.label || '',
        official_title: matched?.official_title || item.label || ''
      };
      prev.val_usd += (item.val_usd || (item.value ? item.value * 1e6 : 0));
      prev.weight_tonnes += (item.weight_ton || 0);
      hsMap.set(item.hs4_code, prev);
    }

    const totalVal = Array.from(hsMap.values()).reduce((acc, c) => acc + c.val_usd, 0);
    const totalWeight = Array.from(hsMap.values()).reduce((acc, c) => acc + c.weight_tonnes, 0);
    const result = Array.from(hsMap.values()).map(c => ({
      ...c,
      val_khr: Math.round(c.val_usd * (store.exchangeRate || 4000)),
      revenue_share_pct: totalVal > 0 ? (c.val_usd / totalVal) * 100 : 0,
      volume_share_pct: totalWeight > 0 ? (c.weight_tonnes / totalWeight) * 100 : 0,
      unit_price_usd_per_kg: c.weight_tonnes > 0 ? (c.val_usd / (c.weight_tonnes * 1000)) : 0
    }));

    if (store.filterMetric === 'TONNES') {
      result.sort((a, b) => b.weight_tonnes - a.weight_tonnes);
    } else {
      result.sort((a, b) => b.val_usd - a.val_usd);
    }
    return result;
  }

  // Default global category view
  let list = [...store.dashboardData.hs4_categories];
  if (store.filterHsCode !== 'ALL') {
    list = list.filter((c) => c.hs4_code === store.filterHsCode);
  }
  if (store.filterMetric === 'TONNES') {
    list.sort((a, b) => b.weight_tonnes - a.weight_tonnes);
  } else {
    list.sort((a, b) => b.val_usd - a.val_usd);
  }
  return list;
});
</script>
