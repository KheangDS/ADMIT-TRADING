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
        
          <!-- Customizer Widget Control Bar & Ask AI Button -->
          <div class="flex items-center gap-2 flex-wrap">
            <button
              @click="store.askAboutChart(title, aiMeaning?.explanation)"
              class="cursor-pointer flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-600 hover:to-indigo-700 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
              title="Ask AI to analyze this graph and give recommendations"
            >
              <SparklesIcon class="w-3.5 h-3.5" />
              <span>Ask AI</span>
            </button>

            <!-- Top-N Countries Slicer (Inside Destination Chart when All Markets is active) -->
            <div 
              v-if="chartId === 'chart_market_share' && store.filterCountry === 'ALL'" 
              class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold"
            >
              <span class="text-[10px] text-slate-500 font-bold px-1 uppercase tracking-wider">Top:</span>
              <button
                v-for="n in [3, 5, 10]"
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
          </div>
      </div>

      <!-- ECharts Rendering Container -->
      <div class="h-64 w-full relative">
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
        <v-chart v-else class="w-full h-full" :option="chartOption" autoresize />
      </div>
    </div>

    <!-- AI Meaning Container Below -->
    <AiInsightBox :meaning="aiMeaning" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Sparkles as SparklesIcon, FilterX as FilterXIcon } from 'lucide-vue-next';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, LineChart, PieChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent, ToolboxComponent, DataZoomComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import AiInsightBox from './AiInsightBox.vue';
import type { AiMeaning } from '../../types/dataset';
import { useDatasetStore } from '../../stores/datasetStore';

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
  chartType: 'HORIZONTAL_BAR' | 'DONUT' | 'LINE' | 'PAIRED_BAR';
  data: any[];
  aiMeaning?: AiMeaning;
}>();

const topNLimit = ref<number>(5);

const currentType = ref<'BAR' | 'LINE' | 'DONUT'>(
  props.chartId === 'chart_market_share' || props.chartType === 'DONUT'
    ? 'DONUT'
    : props.chartId === 'chart_commodity_share' || props.chartId === 'chart_price_jump'
      ? 'BAR'
      : 'LINE'
);

const dynamicTitle = computed(() => {
  const hsNameMap: Record<string, string> = {
    '0801': 'Cashew Nuts & Coconuts',
    '0804': 'Fresh & Dried Mangoes',
    '0904': 'Pepper & Chili',
    '0910': 'Ginger & Spices',
    '1211': 'Medicinal Plants'
  };
  const activeHsText = store.filterHsCode !== 'ALL' 
    ? ` (HS ${store.filterHsCode}${hsNameMap[store.filterHsCode] ? ' · ' + hsNameMap[store.filterHsCode] : ''})` 
    : '';
  const activeYearText = store.filterYear !== 'ALL' ? ` · ${store.filterYear}` : '';
  const activeCountryText = store.filterCountry !== 'ALL' ? ` · ${store.filterCountry}` : '';
  const filterSuffix = `${activeHsText}${activeYearText}${activeCountryText}`;
  const isTonnes = store.filterMetric === 'TONNES';
  const dataset = filteredData.value;
  const currentUnit = dataset.length > 0 && dataset[0].unitLabel ? dataset[0].unitLabel : (isTonnes ? 'Tonnes' : '$M USD');

  if (props.chartId === 'chart_commodity_share') {
    if (isTonnes) return `Export Volume by Commodity Chapter (${currentUnit})${filterSuffix}`;
    return `Export Revenue by Commodity Chapter (${currentUnit})${filterSuffix}`;
  }
  if (props.chartId === 'chart_market_share') {
    const topSuffix = (store.filterCountry === 'ALL' && topNLimit.value < 999) ? ` (Top ${topNLimit.value})` : '';
    if (isTonnes) return `Destination Country Volume Share (${currentUnit})${topSuffix}${filterSuffix}`;
    return `Destination Country Revenue Share (${currentUnit})${topSuffix}${filterSuffix}`;
  }
  if (props.chartId === 'chart_seasonality') {
    if (isTonnes) return `Monthly Export Timeline: Volume (${currentUnit})${filterSuffix}`;
    return `Monthly Export Timeline: Value (${currentUnit})${filterSuffix}`;
  }
  if (props.chartId === 'chart_price_jump') {
    if (isTonnes) return `Volume Comparison: Raw vs Processed Export Volume (${currentUnit})${filterSuffix}`;
    return `Value Comparison: Raw vs Processed Export Revenue (${currentUnit})${filterSuffix}`;
  }
  return props.title;
});

const filteredSubtitle = computed(() => {
  if (props.chartId === 'chart_market_share') {
    if (store.filterCountry !== 'ALL') {
      return `Filtered for destination: ${store.filterCountry}`;
    }
    const allUniqueCountries = new Set(props.data.map(d => d.country || d.name)).size;
    if (topNLimit.value < 999) {
      return `Showing Top ${Math.min(topNLimit.value, filteredData.value.length)} destination markets (out of ${allUniqueCountries})`;
    }
    return `Showing all ${filteredData.value.length} destination markets`;
  }
  if (props.chartId === 'chart_commodity_share') {
    return `Showing ${filteredData.value.length} commodity chapter${filteredData.value.length > 1 ? 's' : ''}`;
  }
  if (props.chartId === 'chart_seasonality') {
    return `Showing ${filteredData.value.length} monthly timeline periods`;
  }
  if (props.chartId === 'chart_price_jump') {
    return `Comparing ${filteredData.value.length} commodity categories`;
  }
  return '';
});

const filteredData = computed(() => {
  const rawList = [...props.data];
  const hsFilter = store.filterHsCode;
  const yrFilter = store.filterYear;
  const ctryFilter = store.filterCountry;
  const isTonnes = store.filterMetric === 'TONNES';

  // --- CHART 1: Commodity Category Share (HS 4-Digit Chapter Only) ---
  if (props.chartId === 'chart_commodity_share') {
    let list = rawList.filter(d => d.is_chapter || (!d.is_subproduct && (d.hs4_code || d.name?.startsWith('HS '))));
    
    // Filter by Commodity
    if (hsFilter !== 'ALL') {
      list = list.filter(d => d.hs4_code === hsFilter || d.name === `HS ${hsFilter}`);
    }
    // Filter by Year
    if (yrFilter !== 'ALL') {
      list = list.filter(d => !d.year || d.year.toString() === yrFilter);
    }
    // Filter by Country
    if (ctryFilter !== 'ALL') {
      list = list.filter(d => !d.country || d.country.toLowerCase() === ctryFilter.toLowerCase());
    }

    // Dynamic Aggregation by hs4_code
    const hsMap = new Map<string, { hs4_code: string; val_usd: number; weight_ton: number; label: string }>();
    for (const item of list) {
      const code = item.hs4_code || (item.name && item.name.startsWith('HS ') ? item.name.replace('HS ', '').trim() : null);
      if (!code) continue;
      const matched = store.dashboardData?.hs4_categories?.find(c => c.hs4_code === code);
      const prev = hsMap.get(code) || { 
        hs4_code: code, 
        val_usd: 0, 
        weight_ton: 0, 
        label: item.label || matched?.official_title || matched?.hs4_desc || '' 
      };
      
      const vUsd = item.val_usd !== undefined ? item.val_usd : (item.value ? item.value * 1e6 : (matched?.val_usd || 0));
      const wTon = item.weight_ton !== undefined ? item.weight_ton : (matched?.weight_tonnes || 0);
      
      prev.val_usd += vUsd;
      prev.weight_ton += wTon;
      hsMap.set(code, prev);
    }

    const aggregated = Array.from(hsMap.values());
    const maxValUsd = aggregated.reduce((max, c) => Math.max(max, c.val_usd), 0);
    const maxWeightTon = aggregated.reduce((max, c) => Math.max(max, c.weight_ton), 0);
    const useK = !isTonnes && maxValUsd < 1_000_000;
    const useKg = isTonnes && maxWeightTon < 1;
    const unitLabel = isTonnes ? (useKg ? 'kg' : 'Tonnes') : (useK ? '$k USD' : '$M USD');

    return aggregated.map(c => {
      let displayVal: number;
      if (isTonnes) {
        displayVal = useKg ? Math.round(c.weight_ton * 1000 * 10) / 10 : Math.round(c.weight_ton * 10) / 10;
      } else {
        displayVal = useK ? Math.round((c.val_usd / 1000) * 10) / 10 : Math.round((c.val_usd / 1e6) * 100) / 100;
      }
      return {
        name: `HS ${c.hs4_code}`,
        hs4_code: c.hs4_code,
        value: displayVal,
        displayValue: displayVal,
        val_usd: c.val_usd,
        weight_ton: c.weight_ton,
        label: c.label,
        unitLabel
      };
    }).sort((a, b) => b.displayValue - a.displayValue);
  }

  // --- CHART 2: Destination Market Share ---
  if (props.chartId === 'chart_market_share') {
    let list = rawList;

    // Filter by Commodity
    if (hsFilter !== 'ALL') {
      list = list.filter(d => !d.hs4_code || d.hs4_code === hsFilter);
    }
    // Filter by Year
    if (yrFilter !== 'ALL') {
      list = list.filter(d => !d.year || d.year.toString() === yrFilter);
    }
    // Filter by Country
    if (ctryFilter !== 'ALL') {
      list = list.filter(d => (d.country || d.name || '').toLowerCase() === ctryFilter.toLowerCase());
    }

    // Dynamic Aggregation by Country
    const countryMap = new Map<string, { country: string; val_usd: number; weight_ton: number }>();
    for (const item of list) {
      const cname = item.country || item.name;
      if (!cname) continue;
      const prev = countryMap.get(cname) || { country: cname, val_usd: 0, weight_ton: 0 };
      const vUsd = item.val_usd !== undefined ? item.val_usd : (item.value ? item.value * 1e6 : 0);
      const wTon = item.weight_ton !== undefined ? item.weight_ton : 0;
      prev.val_usd += vUsd;
      prev.weight_ton += wTon;
      countryMap.set(cname, prev);
    }

    const aggregated = Array.from(countryMap.values());
    const totalVal = aggregated.reduce((acc, c) => acc + (isTonnes ? c.weight_ton : c.val_usd), 0);
    const maxValUsd = aggregated.reduce((max, c) => Math.max(max, c.val_usd), 0);
    const maxWeightTon = aggregated.reduce((max, c) => Math.max(max, c.weight_ton), 0);
    const useK = !isTonnes && maxValUsd < 1_000_000;
    const useKg = isTonnes && maxWeightTon < 1;
    const unitLabel = isTonnes ? (useKg ? 'kg' : 'Tonnes') : (useK ? '$k USD' : '$M USD');

    const sortedList = aggregated.map(c => {
      let displayVal: number;
      if (isTonnes) {
        displayVal = useKg ? Math.round(c.weight_ton * 1000 * 10) / 10 : Math.round(c.weight_ton * 10) / 10;
      } else {
        displayVal = useK ? Math.round((c.val_usd / 1000) * 10) / 10 : Math.round((c.val_usd / 1e6) * 100) / 100;
      }
      const sharePct = totalVal > 0 ? ((isTonnes ? c.weight_ton : c.val_usd) / totalVal) * 100 : 0;
      return {
        name: c.country,
        country: c.country,
        value: displayVal,
        displayValue: displayVal,
        val_usd: c.val_usd,
        weight_ton: c.weight_ton,
        worldSharePct: Math.round(sharePct * 10) / 10,
        unitLabel
      };
    }).sort((a, b) => b.displayValue - a.displayValue);

    // Apply Top N slicing if 'ALL' markets is selected and topNLimit is active
    if (ctryFilter === 'ALL' && topNLimit.value < 999) {
      return sortedList.slice(0, topNLimit.value);
    }

    return sortedList;
  }

  // --- CHART 3: Raw vs Processed Comparison (Metric Dimension & Slicers Dynamic) ---
  if (props.chartId === 'chart_price_jump' || props.chartType === 'PAIRED_BAR' || (rawList.length > 0 && (rawList[0].Raw_Value !== undefined || rawList[0].Raw_Val !== undefined || rawList[0].raw_val_usd !== undefined || rawList[0].Raw_Price !== undefined))) {
    const HS8_PAIR_DEFS: Record<string, { rawCodes: string[]; procCodes: string[]; label: string }> = {
      '0801': { rawCodes: ['08013100'], procCodes: ['08013200'], label: 'HS 0801 - Cashew Nuts & Coconuts' },
      '0804': { rawCodes: ['08045021'], procCodes: ['08045022'], label: 'HS 0804 - Fresh & Dried Mangoes' },
      '0904': { rawCodes: ['09041120', '09041110', '09041190', '09042110'], procCodes: ['09041220', '09041210', '09041290', '09042210'], label: 'HS 0904 - Pepper & Chili (Capsicum)' },
      '0910': { rawCodes: ['09101100'], procCodes: ['09101200'], label: 'HS 0910 - Ginger, Turmeric & Spices' }
    };

    let list = rawList;
    if (hsFilter !== 'ALL') {
      list = list.filter(d => {
        if (d.hs4_code) return d.hs4_code === hsFilter;
        const catName = (d.category || d.name || '').toLowerCase();
        return catName.includes(hsFilter);
      });
    }

    const hasMultiDims = list.some(d => d.year !== undefined || d.country !== undefined);

    if (hasMultiDims) {
      if (yrFilter !== 'ALL') {
        list = list.filter(d => d.year && d.year.toString() === yrFilter);
      }
      if (ctryFilter !== 'ALL') {
        list = list.filter(d => d.country && d.country.toLowerCase() === ctryFilter.toLowerCase());
      }
    }

    // Dynamic aggregation by hs4_code / category
    const catMap = new Map<string, any>();
    for (const item of list) {
      const code = item.hs4_code || (item.category && item.category.match(/\d{4}/) ? item.category.match(/\d{4}/)[0] : null);
      if (!code) continue;

      const def = HS8_PAIR_DEFS[code];
      const categoryLabel = item.category || def?.label || `HS ${code}`;

      const prev = catMap.get(code) || {
        hs4_code: code,
        category: categoryLabel,
        raw_label: item.raw_label || 'Raw Commodity',
        processed_label: item.processed_label || 'Processed Product',
        raw_val_usd: 0,
        raw_weight_ton: 0,
        proc_val_usd: 0,
        proc_weight_ton: 0
      };

      const rVal = item.raw_val_usd !== undefined ? item.raw_val_usd : (item.Raw_Val ? item.Raw_Val * 1e6 : 0);
      const rTon = item.raw_weight_ton !== undefined ? item.raw_weight_ton : (item.Raw_Tonnes || 0);
      const pVal = item.proc_val_usd !== undefined ? item.proc_val_usd : (item.Processed_Val ? item.Processed_Val * 1e6 : 0);
      const pTon = item.proc_weight_ton !== undefined ? item.proc_weight_ton : (item.Processed_Tonnes || 0);

      prev.raw_val_usd += rVal;
      prev.raw_weight_ton += rTon;
      prev.proc_val_usd += pVal;
      prev.proc_weight_ton += pTon;
      catMap.set(code, prev);
    }

    // Fallback ONLY when NO filters are active (global unfiltered view)
    if (catMap.size === 0 && !store.isFiltered && store.dashboardData?.category_details) {
      for (const [code, def] of Object.entries(HS8_PAIR_DEFS)) {
        const subProducts = store.dashboardData.category_details[code]?.sub_products || [];
        let rVal = 0, rTon = 0, pVal = 0, pTon = 0;
        for (const sp of subProducts) {
          const spCode = String(sp.hs8_code || '').replace('.0', '').padStart(8, '0');
          if (def.rawCodes.includes(spCode)) {
            rVal += sp.val_usd || 0;
            rTon += sp.weight_tonnes || 0;
          } else if (def.procCodes.includes(spCode)) {
            pVal += sp.val_usd || 0;
            pTon += sp.weight_tonnes || 0;
          }
        }
        if (rVal > 0 || pVal > 0 || rTon > 0 || pTon > 0) {
          catMap.set(code, {
            hs4_code: code,
            category: def.label,
            raw_label: 'Raw Commodity',
            processed_label: 'Processed Product',
            raw_val_usd: rVal,
            raw_weight_ton: rTon,
            proc_val_usd: pVal,
            proc_weight_ton: pTon
          });
        }
      }
    }

    // Slicer Scaling ONLY if rawList did not have year/country rows and filters are active
    if (!hasMultiDims && (yrFilter !== 'ALL' || ctryFilter !== 'ALL')) {
      const commodityChart = store.dashboardData?.level1_charts?.find(c => c.chart_id === 'chart_commodity_share');
      if (commodityChart && commodityChart.data) {
        for (const [code, valObj] of catMap.entries()) {
          const catRows = commodityChart.data.filter((d: any) => d.hs4_code === code || d.name === `HS ${code}`);
          const totalUsd = catRows.reduce((sum: number, d: any) => sum + (d.val_usd || 0), 0);
          const totalTon = catRows.reduce((sum: number, d: any) => sum + (d.weight_ton || 0), 0);

          let filteredRows = catRows;
          if (yrFilter !== 'ALL') {
            filteredRows = filteredRows.filter((d: any) => !d.year || d.year.toString() === yrFilter);
          }
          if (ctryFilter !== 'ALL') {
            filteredRows = filteredRows.filter((d: any) => !d.country || d.country.toLowerCase() === ctryFilter.toLowerCase());
          }
          const filteredUsd = filteredRows.reduce((sum: number, d: any) => sum + (d.val_usd || 0), 0);
          const filteredTon = filteredRows.reduce((sum: number, d: any) => sum + (d.weight_ton || 0), 0);

          const ratioVal = totalUsd > 0 ? (filteredUsd / totalUsd) : 0;
          const ratioTon = totalTon > 0 ? (filteredTon / totalTon) : 0;

          valObj.raw_val_usd *= ratioVal;
          valObj.proc_val_usd *= ratioVal;
          valObj.raw_weight_ton *= ratioTon;
          valObj.proc_weight_ton *= ratioTon;
        }
      }
    }

    let aggregated = Array.from(catMap.values());
    if (store.isFiltered) {
      aggregated = aggregated.filter(c => (c.raw_val_usd > 0 || c.proc_val_usd > 0 || c.raw_weight_ton > 0 || c.proc_weight_ton > 0));
    }

    const maxValUsd = aggregated.reduce((max, c) => Math.max(max, c.raw_val_usd, c.proc_val_usd), 0);
    const maxWeightTon = aggregated.reduce((max, c) => Math.max(max, c.raw_weight_ton, c.proc_weight_ton), 0);
    const useK = !isTonnes && maxValUsd < 1_000_000;
    const useKg = isTonnes && maxWeightTon < 1;
    const unitLabel = isTonnes ? (useKg ? 'kg' : 'Tonnes') : (useK ? '$k USD' : '$M USD');

    return aggregated.map(c => {
      let rawDisplay: number;
      let procDisplay: number;
      if (isTonnes) {
        rawDisplay = useKg ? Math.round(c.raw_weight_ton * 1000 * 10) / 10 : Math.round(c.raw_weight_ton * 10) / 10;
        procDisplay = useKg ? Math.round(c.proc_weight_ton * 1000 * 10) / 10 : Math.round(c.proc_weight_ton * 10) / 10;
      } else {
        rawDisplay = useK ? Math.round((c.raw_val_usd / 1000) * 10) / 10 : Math.round((c.raw_val_usd / 1e6) * 100) / 100;
        procDisplay = useK ? Math.round((c.proc_val_usd / 1000) * 10) / 10 : Math.round((c.proc_val_usd / 1e6) * 100) / 100;
      }
      return {
        hs4_code: c.hs4_code,
        category: c.category,
        name: c.category,
        raw_label: c.raw_label,
        processed_label: c.processed_label,
        raw_val_usd: c.raw_val_usd,
        raw_weight_ton: c.raw_weight_ton,
        proc_val_usd: c.proc_val_usd,
        proc_weight_ton: c.proc_weight_ton,
        Raw_Value: rawDisplay,
        Processed_Value: procDisplay,
        unitLabel
      };
    });
  }

  // --- CHART 4: Seasonality Monthly Timeline Dynamics ---
  if (props.chartId === 'chart_seasonality') {
    let list = rawList;

    // Filter by Commodity
    if (hsFilter !== 'ALL') {
      list = list.filter(d => !d.hs4_code || d.hs4_code === hsFilter);
    }
    // Filter by Year
    if (yrFilter !== 'ALL') {
      list = list.filter(d => (!d.year && !d.name) || (d.year && d.year.toString() === yrFilter) || (d.name && d.name.startsWith(`${yrFilter}-`)));
    }
    // Filter by Country
    if (ctryFilter !== 'ALL') {
      list = list.filter(d => !d.country || d.country.toLowerCase() === ctryFilter.toLowerCase());
    }

    // Dynamic Aggregation by Month (yyyy_mm)
    const monthMap = new Map<string, { yyyy_mm: string; val_usd: number; weight_ton: number; weight_kton: number; val_million_usd: number }>();
    for (const item of list) {
      const yyyymm = item.yyyy_mm || item.name;
      if (!yyyymm || !/^\d{4}-\d{2}$/.test(yyyymm)) continue;
      const prev = monthMap.get(yyyymm) || { yyyy_mm: yyyymm, val_usd: 0, weight_ton: 0, weight_kton: 0, val_million_usd: 0 };
      const vUsd = item.val_usd !== undefined ? item.val_usd : ((item.value_m_usd || item.val_million_usd || 0) * 1e6);
      const wTon = item.weight_ton !== undefined ? item.weight_ton : ((item.weight_kton || 0) * 1000);
      prev.val_usd += vUsd;
      prev.weight_ton += wTon;
      prev.val_million_usd += vUsd / 1e6;
      prev.weight_kton += wTon / 1000;
      monthMap.set(yyyymm, prev);
    }

    const sortedMonths = Array.from(monthMap.values()).sort((a, b) => a.yyyy_mm.localeCompare(b.yyyy_mm));
    const maxValUsd = sortedMonths.reduce((max, m) => Math.max(max, m.val_usd), 0);
    const maxWeightTon = sortedMonths.reduce((max, m) => Math.max(max, m.weight_ton), 0);
    const useK = !isTonnes && maxValUsd < 1_000_000;
    const useKg = isTonnes && maxWeightTon < 1;
    const unitLabel = isTonnes ? (useKg ? 'kg' : 'Tonnes') : (useK ? '$k USD' : '$M USD');

    return sortedMonths.map(m => {
      let displayVal: number;
      if (isTonnes) {
        displayVal = useKg ? Math.round(m.weight_ton * 1000 * 10) / 10 : Math.round(m.weight_ton * 10) / 10;
      } else {
        displayVal = useK ? Math.round((m.val_usd / 1000) * 10) / 10 : Math.round(m.val_million_usd * 100) / 100;
      }
      return {
        name: m.yyyy_mm,
        yyyy_mm: m.yyyy_mm,
        value: displayVal,
        displayValue: displayVal,
        val_million_usd: Math.round(m.val_million_usd * 100) / 100,
        weight_kton: Math.round(m.weight_kton * 100) / 100,
        weight_ton: Math.round(m.weight_ton * 10) / 10,
        val_usd: m.val_usd,
        unitLabel
      };
    });
  }

  return rawList;
});

const chartOption = computed(() => {
  const dataset = filteredData.value;
  const isTonnes = store.filterMetric === 'TONNES';
  const currentUnit = dataset.length > 0 && dataset[0].unitLabel ? dataset[0].unitLabel : (isTonnes ? 'Tonnes' : '$M USD');
  const isK = currentUnit === '$k USD';
  const isM = currentUnit === '$M USD';
  const isKg = currentUnit === 'kg';

  const toolbox = {
    show: true,
    right: '2%',
    top: '2%',
    feature: {
      saveAsImage: { title: 'Save Image' },
      restore: { title: 'Reset Zoom' }
    }
  };

  // Special Handling for PAIRED_BAR Raw vs Processed Comparison Chart
  const isPairedBar = props.chartId === 'chart_price_jump' || props.chartType === 'PAIRED_BAR' || (dataset.length > 0 && (dataset[0].Raw_Value !== undefined || dataset[0].Raw_Price !== undefined));

  if (isPairedBar && currentType.value === 'BAR') {
    const rawLegend = isTonnes ? `Raw Commodity (${currentUnit})` : (isK ? 'Raw Commodity ($k USD)' : 'Raw Commodity ($M USD)');
    const procLegend = isTonnes ? `Processed Product (${currentUnit})` : (isK ? 'Processed Product ($k USD)' : 'Processed Product ($M USD)');

    const formatVal = (v: number): string => {
      if (isKg) {
        return `${v.toLocaleString()} kg`;
      } else if (isTonnes) {
        if (v === 0) return '0 t';
        if (v < 1) {
          const kg = Math.round(v * 1000 * 10) / 10;
          return `${kg.toLocaleString()} kg`;
        }
        if (v >= 1000) return `${(v / 1000).toFixed(1)}k t`;
        return `${v.toLocaleString()} t`;
      } else if (isK) {
        if (v === 0) return '$0k';
        return `$${v.toLocaleString()}k`;
      } else {
        if (v === 0) return '$0M';
        if (v < 1) {
          const kUsd = Math.round(v * 1000 * 10) / 10;
          return `$${kUsd.toLocaleString()}k`;
        }
        return `$${v.toLocaleString()}M`;
      }
    };

    const categories = dataset.map(d => d.category || d.name);
    const rawValues = dataset.map(d => d.Raw_Value !== undefined ? d.Raw_Value : (isTonnes ? (d.Raw_Tonnes || 0) : ((d.raw_val_usd ? d.raw_val_usd / (isK ? 1000 : 1e6) : (d.Raw_Val ? d.Raw_Val * (isK ? 1000 : 1) : (d.Raw_Price || 0))))));
    const procValues = dataset.map(d => d.Processed_Value !== undefined ? d.Processed_Value : (isTonnes ? (d.Processed_Tonnes || 0) : ((d.proc_val_usd ? d.proc_val_usd / (isK ? 1000 : 1e6) : (d.Processed_Val ? d.Processed_Val * (isK ? 1000 : 1) : (d.Processed_Price || 0))))));

    return {
      toolbox,
      legend: {
        data: [rawLegend, procLegend],
        bottom: '0%',
        textStyle: { fontSize: 11, fontWeight: 'bold', color: '#334155' }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any[]) => {
          const rawItem = params.find(p => p.seriesName === rawLegend);
          const procItem = params.find(p => p.seriesName === procLegend);
          const rawVal = rawItem ? rawItem.value : 0;
          const procVal = procItem ? procItem.value : 0;
          const totalCat = rawVal + procVal;
          const procShare = totalCat > 0 ? ((procVal / totalCat) * 100).toFixed(1) : '0';
          const ratio = rawVal > 0 ? (procVal / rawVal).toFixed(2) : 'N/A';

          return `
            <div style="font-weight:bold;color:#0f172a;margin-bottom:4px;">${params[0].name}</div>
            <div style="color:#0284c7;font-size:12px;">🔵 Raw Commodity: <strong>${formatVal(rawVal)}</strong></div>
            <div style="color:#059669;font-size:12px;margin-top:2px;">🟢 Processed Product: <strong>${formatVal(procVal)}</strong></div>
            <div style="margin-top:6px;padding-top:4px;border-top:1px solid #e2e8f0;color:#0369a1;font-weight:bold;font-size:11px;">
              📊 Processed Share: ${procShare}% of category total (${ratio}x of Raw)
            </div>
          `;
        }
      },
      grid: { left: '3%', right: '12%', bottom: '14%', top: '8%', containLabel: true },
      xAxis: { 
        type: 'value', 
        splitNumber: 4,
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
        axisLabel: { 
          fontSize: 10,
          color: '#64748b',
          formatter: (v: number) => formatVal(v)
        }
      },
      yAxis: { 
        type: 'category', 
        data: categories.slice().reverse(),
        axisLabel: { 
          fontWeight: 'bold', 
          fontSize: 11, 
          color: '#1e293b',
          formatter: (val: string) => {
            if (val.length > 28) {
              return val.substring(0, 26) + '...';
            }
            return val;
          }
        }
      },
      series: [
        {
          name: rawLegend,
          type: 'bar',
          data: rawValues.slice().reverse(),
          itemStyle: { color: '#0284c7', borderRadius: [0, 4, 4, 0] },
          label: {
            show: true,
            position: 'right',
            formatter: (p: any) => formatVal(p.value),
            fontSize: 10,
            color: '#0284c7',
            fontWeight: 'bold'
          }
        },
        {
          name: procLegend,
          type: 'bar',
          data: procValues.slice().reverse(),
          itemStyle: { color: '#10b981', borderRadius: [0, 4, 4, 0] },
          label: {
            show: true,
            position: 'right',
            formatter: (p: any) => formatVal(p.value),
            fontSize: 10,
            color: '#059669',
            fontWeight: 'bold'
          }
        }
      ]
    };
  }

  const names = dataset.map(d => d.name || d.category || d.yyyy_mm);
  const values = dataset.map(d => d.displayValue !== undefined ? d.displayValue : (d.value !== undefined ? d.value : d.Raw_Price));

  if (currentType.value === 'DONUT') {
    return {
      toolbox,
      color: ['#0284c7', '#10b981', '#6366f1', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6', '#f97316'],
      tooltip: { 
        trigger: 'item', 
        formatter: (params: any) => {
          const raw = dataset.find(d => (d.name || d.country || d.category) === params.name);
          const fullLabel = raw?.label ? `<div style="color:#64748b;font-size:11px;">${raw.label}</div>` : '';
          let valFormatted = '';
          if (isK) {
            valFormatted = `$${params.value.toLocaleString()}k USD`;
          } else if (isM) {
            if (params.value < 1 && params.value > 0) {
              valFormatted = `$${(Math.round(params.value * 1000 * 10) / 10).toLocaleString()}k USD`;
            } else {
              valFormatted = `$${params.value.toLocaleString()}M USD`;
            }
          } else if (isKg) {
            valFormatted = `${params.value.toLocaleString()} kg`;
          } else if (isTonnes) {
            if (params.value < 1 && params.value > 0) {
              valFormatted = `${(Math.round(params.value * 1000 * 10) / 10).toLocaleString()} kg`;
            } else {
              valFormatted = `${params.value.toLocaleString()} Tonnes`;
            }
          } else {
            valFormatted = `${params.value.toLocaleString()} ${currentUnit}`;
          }
          const globalShareText = raw?.worldSharePct !== undefined 
            ? `<div style="color:#0284c7;font-size:11px;font-weight:600;margin-top:2px;">🌍 Worldwide Share: ${raw.worldSharePct}%</div>` 
            : '';
          return `
            <div style="font-weight:bold;color:#0f172a;">${params.name}</div>
            ${fullLabel}
            <div style="font-weight:bold;color:#0369a1;margin-top:2px;">
              ${valFormatted} (${params.percent}%)
            </div>
            ${globalShareText}
          `;
        } 
      },
      legend: {
        type: 'scroll',
        orient: 'horizontal',
        bottom: 0,
        textStyle: { fontSize: 11, color: '#334155', fontWeight: '500' }
      },
      series: [
        {
          type: 'pie',
          radius: ['44%', '68%'],
          center: ['50%', '46%'],
          minAngle: 12,
          avoidLabelOverlap: true,
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: {
            show: true,
            formatter: '{b}: {d}%',
            fontSize: 11,
            fontWeight: 'bold',
            color: '#1e293b'
          },
          labelLine: {
            show: true,
            length: 12,
            length2: 10,
            smooth: true
          },
          data: dataset.map(d => ({ 
            name: d.name || d.country || d.category, 
            value: d.displayValue !== undefined ? d.displayValue : (d.value || d.Raw_Price) 
          }))
        }
      ]
    };
  }

  if (currentType.value === 'LINE') {
    return {
      toolbox,
      tooltip: { 
        trigger: 'axis', 
        formatter: (params: any) => {
          const p = params[0];
          let formatted = '';
          if (isK) {
            formatted = `$${p.value.toLocaleString()}k USD`;
          } else if (isM) {
            if (p.value < 1 && p.value > 0) {
              formatted = `$${(Math.round(p.value * 1000 * 10) / 10).toLocaleString()}k USD`;
            } else {
              formatted = `$${p.value.toLocaleString()}M USD`;
            }
          } else if (isKg) {
            formatted = `${p.value.toLocaleString()} kg`;
          } else if (isTonnes) {
            if (p.value < 1 && p.value > 0) {
              formatted = `${(Math.round(p.value * 1000 * 10) / 10).toLocaleString()} kg`;
            } else {
              formatted = `${p.value.toLocaleString()} Tonnes`;
            }
          } else {
            formatted = `${p.value.toLocaleString()} ${currentUnit}`;
          }
          return `<div><strong style="color:#0f172a;">${p.name}</strong><div style="color:#0284c7;font-weight:bold;margin-top:4px;">${formatted}</div></div>`;
        }
      },
      grid: { left: '3%', right: '4%', bottom: '14%', top: '10%', containLabel: true },
      dataZoom: [{ type: 'inside' }, { type: 'slider', height: 16, bottom: '1%' }],
      xAxis: { type: 'category', data: names, boundaryGap: false, axisLabel: { fontSize: 10, rotate: 30 } },
      yAxis: { 
        type: 'value', 
        name: currentUnit, 
        splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
        axisLabel: {
          fontSize: 10,
          color: '#64748b',
          formatter: (v: number) => {
            if (isK) return `$${v.toLocaleString()}k`;
            if (isM) return `$${v}M`;
            if (isKg) return `${v.toLocaleString()} kg`;
            if (isTonnes) {
              if (v >= 1000) return `${(v / 1000).toFixed(1)}k t`;
              return `${v.toLocaleString()} t`;
            }
            return `${v.toLocaleString()}`;
          }
        }
      },
      series: [
        {
          data: values,
          type: 'line',
          smooth: true,
          lineStyle: { width: 3, color: '#0284c7' },
          itemStyle: { color: '#0284c7' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(2, 132, 199, 0.35)' },
                { offset: 1, color: 'rgba(2, 132, 199, 0.02)' }
              ]
            }
          }
        }
      ]
    };
  }

  // BAR (Default)
  return {
    toolbox,
    tooltip: { 
      trigger: 'axis', 
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const p = params[0];
        const rawData = dataset.find(d => (d.name || d.category) === p.name);
        const descLabel = rawData?.label ? `<div style="color:#475569;font-size:11px;margin-top:2px;">${rawData.label}</div>` : '';
        let formatted = '';
        if (isK) {
          formatted = `$${p.value.toLocaleString()}k USD`;
        } else if (isM) {
          if (p.value < 1 && p.value > 0) {
            formatted = `$${(Math.round(p.value * 1000 * 10) / 10).toLocaleString()}k USD`;
          } else {
            formatted = `$${p.value.toLocaleString()}M USD`;
          }
        } else if (isKg) {
          formatted = `${p.value.toLocaleString()} kg`;
        } else if (isTonnes) {
          if (p.value < 1 && p.value > 0) {
            formatted = `${(Math.round(p.value * 1000 * 10) / 10).toLocaleString()} kg`;
          } else {
            formatted = `${p.value.toLocaleString()} Tonnes`;
          }
        } else {
          formatted = `${p.value.toLocaleString()} ${currentUnit}`;
        }
        return `<div><strong style="color:#0f172a;">${p.name}</strong>${descLabel}<div style="color:#0284c7;font-weight:bold;margin-top:4px;">${formatted}</div></div>`;
      }
    },
    xAxis: { 
      type: 'value', 
      splitNumber: 4,
      splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } },
      axisLabel: { 
        fontSize: 10,
        color: '#64748b',
        formatter: (v: number) => {
          if (isK) return `$${v.toLocaleString()}k`;
          if (isM) return `$${v}M`;
          if (isKg) return `${v.toLocaleString()} kg`;
          if (isTonnes) {
            if (v >= 1000) return `${(v / 1000).toFixed(1)}k t`;
            return `${v.toLocaleString()} t`;
          }
          return `${v.toLocaleString()} t`;
        }
      }
    },
    yAxis: { 
      type: 'category', 
      data: names.slice(0, 10).reverse(),
      axisLabel: { fontSize: 11, fontWeight: 'bold', color: '#334155' }
    },
    series: [
      {
        data: values.slice(0, 10).reverse(),
        type: 'bar',
        itemStyle: { 
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#0284c7' },
              { offset: 1, color: '#38bdf8' }
            ]
          },
          borderRadius: [0, 6, 6, 0] 
        },
        label: {
          show: true,
          position: 'right',
          formatter: (p: any) => {
            if (isK) return `$${p.value}k`;
            if (isM) {
              if (p.value < 1 && p.value > 0) return `$${Math.round(p.value * 1000 * 10) / 10}k`;
              return `$${p.value}M`;
            }
            if (isKg) return `${p.value} kg`;
            if (isTonnes) {
              if (p.value < 1 && p.value > 0) return `${Math.round(p.value * 1000 * 10) / 10} kg`;
              if (p.value >= 1000) return `${(p.value / 1000).toFixed(1)}k t`;
              return `${p.value} t`;
            }
            return `${p.value}`;
          },
          fontSize: 10,
          fontWeight: 'bold',
          color: '#0369a1'
        }
      }
    ]
  };
});
</script>
