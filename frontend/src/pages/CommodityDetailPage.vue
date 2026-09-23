<template>
  <div v-if="commodity" class="space-y-8">
    
    <!-- Top Navigation & Header -->
    <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center gap-2 mb-2 flex-wrap">
          <button
            @click="goBack"
            class="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-colors shadow-xs"
          >
            <ArrowLeftIcon class="w-3.5 h-3.5" />
            <span>Back to Overview</span>
          </button>
          <span class="text-xs font-mono font-black px-2.5 py-1 rounded-lg bg-sky-100 text-sky-800">
            HS {{ commodity.hs8_code }}
          </span>
          <span class="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600">
            Chapter {{ commodity.hs4_code }}
          </span>
        </div>

        <!-- Bilingual Product Title -->
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">
          {{ commodity.name_en }}
        </h1>
        <p v-if="commodity.name_km" class="text-sm font-semibold text-slate-500 font-sans mt-0.5">
          {{ commodity.name_km }}
        </p>
      </div>

      <!-- Header Action Buttons -->
      <div class="flex items-center gap-2 self-stretch md:self-auto justify-end">
        <button
          @click="goToCompare"
          class="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white font-bold text-xs rounded-xl shadow-sm hover:shadow transition-all"
        >
          <span>⚖️ Compare with Another HS8</span>
          <ArrowRightIcon class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- 4 Core KPI Metric Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Total Revenue -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between text-slate-500 text-xs mb-1">
          <span class="font-semibold uppercase tracking-wider">Total Export Value</span>
          <span class="p-1.5 rounded-lg bg-amber-50 text-amber-600">💰</span>
        </div>
        <div class="text-2xl font-black text-slate-900">
          {{ formatRevenue(commodity.total_val_usd) }}
        </div>
        <p class="text-xs text-slate-500 mt-1 font-mono">
          ≈ {{ formatKhrBillions(commodity.total_val_khr) }}
        </p>
      </div>

      <!-- Total Volume -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between text-slate-500 text-xs mb-1">
          <span class="font-semibold uppercase tracking-wider">Total Export Volume</span>
          <span class="p-1.5 rounded-lg bg-sky-50 text-sky-600">📦</span>
        </div>
        <div class="text-2xl font-black text-slate-900">
          {{ formatVolumeKg(commodity.total_weight_kg) }}
        </div>
        <p class="text-xs text-slate-500 mt-1">
          {{ commodity.total_weight_ton.toLocaleString(undefined, { maximumFractionDigits: 1 }) }} Tonnes total
        </p>
      </div>

      <!-- Unit Price -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between text-slate-500 text-xs mb-1">
          <span class="font-semibold uppercase tracking-wider">Average Unit Price</span>
          <span class="p-1.5 rounded-lg bg-emerald-50 text-emerald-600">🏷️</span>
        </div>
        <div class="text-2xl font-black text-emerald-600">
          ${{ commodity.avg_price_usd_per_kg.toFixed(2) }} <span class="text-xs text-slate-500 font-normal">/ kg</span>
        </div>
        <p class="text-xs text-slate-500 mt-1 font-mono">
          {{ Math.round(commodity.avg_price_khr_per_kg).toLocaleString() }} ៛ / kg
        </p>
      </div>

      <!-- Export Markets Count -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <div class="flex items-center justify-between text-slate-500 text-xs mb-1">
          <span class="font-semibold uppercase tracking-wider">Destination Markets</span>
          <span class="p-1.5 rounded-lg bg-indigo-50 text-indigo-600">🌏</span>
        </div>
        <div class="text-2xl font-black text-indigo-600">
          {{ commodity.num_markets }} <span class="text-xs text-slate-500 font-normal">Countries</span>
        </div>
        <p class="text-xs text-slate-500 mt-1 truncate">
          Top: <strong>{{ topMarketName }}</strong>
        </p>
      </div>
    </div>

    <!-- World Map of Destination Markets -->
    <WorldExportMap
      :title="`Export Destination Map — HS ${commodity.hs8_code} (${commodity.name_en})`"
      :market-data="commodity.market_breakdown"
      :exchange-rate="store.exchangeRate"
    />

    <!-- Monthly Trend & Price Evolution Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Chart 1: Monthly Export Timeline (Revenue or Volume) -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-900">Monthly Export Timeline</h3>
            <p class="text-xs text-slate-500 mt-0.5">Historical seasonality and shipping dynamics</p>
          </div>
          <div class="flex items-center bg-slate-100 p-1 rounded-xl">
            <button
              @click="trendMetric = 'USD'"
              class="px-2.5 py-1 text-xs font-bold rounded-lg transition-all"
              :class="trendMetric === 'USD' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600'"
            >
              Revenue ($)
            </button>
            <button
              @click="trendMetric = 'VOLUME'"
              class="px-2.5 py-1 text-xs font-bold rounded-lg transition-all"
              :class="trendMetric === 'VOLUME' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600'"
            >
              Volume
            </button>
          </div>
        </div>

        <div class="h-72 w-full">
          <v-chart class="w-full h-full" :option="monthlyTrendOption" autoresize />
        </div>
      </div>

      <!-- Chart 2: Unit Price Trend (USD/kg and KHR/kg) -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-900">Unit Price Evolution</h3>
            <p class="text-xs text-slate-500 mt-0.5">Export price per kg trajectory over time ($/kg & ៛/kg)</p>
          </div>
          <span class="text-xs font-semibold px-2 py-1 bg-emerald-50 text-emerald-700 rounded-lg">
            Dual Currency
          </span>
        </div>

        <div class="h-72 w-full">
          <v-chart class="w-full h-full" :option="priceTrendOption" autoresize />
        </div>
      </div>

    </div>

    <!-- Raw vs Processed Comparison Section (Conditional) -->
    <div
      v-if="commodity.raw_vs_processed"
      class="bg-gradient-to-br from-white via-indigo-50/30 to-slate-50 p-6 sm:p-8 rounded-2xl text-slate-900 shadow-sm border border-slate-200/90"
    >
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-200">
        <div>
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 font-mono text-xs font-bold border border-amber-200">
              VALUE CHAIN ANALYSIS
            </span>
            <span class="text-xs text-slate-500">Chapter HS {{ commodity.hs4_code }}</span>
          </div>
          <h3 class="text-xl font-black text-slate-900 mt-1">
            Processing Value Jump: Raw vs Processed
          </h3>
          <p class="text-xs text-slate-600 mt-0.5">
            Economic premium gained by domestic value-added processing before export.
          </p>
        </div>

        <div class="px-4 py-2 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-extrabold flex items-center gap-2 self-start sm:self-auto shadow-2xs">
          <span>⚡ Value Multiplier:</span>
          <span class="text-sm font-black text-emerald-700">
            {{ (commodity.raw_vs_processed.proc_price_usd_per_kg / Math.max(0.01, commodity.raw_vs_processed.raw_price_usd_per_kg)).toFixed(1) }}x
          </span>
        </div>
      </div>

      <!-- Side-by-side Raw vs Processed Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Raw Form Card -->
        <div class="bg-white p-5 rounded-2xl border border-amber-200/80 shadow-2xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                HS {{ commodity.raw_vs_processed.raw_hs8 }}
              </span>
              <span class="text-xs font-bold text-amber-800 bg-amber-100 border border-amber-200 px-2 py-0.5 rounded">
                Raw / Unprocessed
              </span>
            </div>
            <h4 class="text-base font-bold text-slate-900">{{ commodity.raw_vs_processed.raw_name_en }}</h4>
            <p class="text-xs text-slate-500 font-sans mt-0.5">{{ commodity.raw_vs_processed.raw_name_km }}</p>

            <div class="mt-4 space-y-2 text-xs">
              <div class="flex justify-between py-1 border-b border-slate-100">
                <span class="text-slate-500">Unit Price ($/kg):</span>
                <strong class="text-amber-700 font-bold">${{ commodity.raw_vs_processed.raw_price_usd_per_kg.toFixed(2) }}/kg</strong>
              </div>
              <div class="flex justify-between py-1 border-b border-slate-100">
                <span class="text-slate-500">Unit Price (KHR/kg):</span>
                <strong class="text-slate-700">{{ Math.round(commodity.raw_vs_processed.raw_price_khr_per_kg).toLocaleString() }} ៛/kg</strong>
              </div>
              <div class="flex justify-between py-1 border-b border-slate-100">
                <span class="text-slate-500">Total Volume:</span>
                <strong class="text-slate-700">{{ formatVolumeKg(commodity.raw_vs_processed.raw_weight_kg) }}</strong>
              </div>
              <div class="flex justify-between py-1">
                <span class="text-slate-500">Total Export Value:</span>
                <strong class="text-slate-900 font-bold">{{ formatRevenue(commodity.raw_vs_processed.raw_val_usd) }}</strong>
              </div>
            </div>
          </div>

          <router-link
            :to="`/commodity/${commodity.raw_vs_processed.raw_hs8}`"
            class="mt-4 text-center text-xs font-bold text-amber-800 hover:text-amber-900 py-2 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 transition-colors"
          >
            View Raw Commodity Detail →
          </router-link>
        </div>

        <!-- Processed Form Card -->
        <div class="bg-white p-5 rounded-2xl border border-indigo-200/80 shadow-2xs flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between mb-2">
              <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                HS {{ commodity.raw_vs_processed.processed_hs8 }}
              </span>
              <span class="text-xs font-bold text-emerald-800 bg-emerald-100 border border-emerald-200 px-2 py-0.5 rounded">
                Processed / Value-Added
              </span>
            </div>
            <h4 class="text-base font-bold text-slate-900">{{ commodity.raw_vs_processed.processed_name_en }}</h4>
            <p class="text-xs text-indigo-700 font-sans mt-0.5">{{ commodity.raw_vs_processed.processed_name_km }}</p>

            <div class="mt-4 space-y-2 text-xs">
              <div class="flex justify-between py-1 border-b border-slate-100">
                <span class="text-slate-500">Unit Price ($/kg):</span>
                <strong class="text-emerald-700 font-bold">${{ commodity.raw_vs_processed.proc_price_usd_per_kg.toFixed(2) }}/kg</strong>
              </div>
              <div class="flex justify-between py-1 border-b border-slate-100">
                <span class="text-slate-500">Unit Price (KHR/kg):</span>
                <strong class="text-slate-700">{{ Math.round(commodity.raw_vs_processed.proc_price_khr_per_kg).toLocaleString() }} ៛/kg</strong>
              </div>
              <div class="flex justify-between py-1 border-b border-slate-100">
                <span class="text-slate-500">Total Volume:</span>
                <strong class="text-slate-700">{{ formatVolumeKg(commodity.raw_vs_processed.proc_weight_kg) }}</strong>
              </div>
              <div class="flex justify-between py-1">
                <span class="text-slate-500">Total Export Value:</span>
                <strong class="text-slate-900 font-bold">{{ formatRevenue(commodity.raw_vs_processed.proc_val_usd) }}</strong>
              </div>
            </div>
          </div>

          <router-link
            :to="`/commodity/${commodity.raw_vs_processed.processed_hs8}`"
            class="mt-4 text-center text-xs font-bold text-indigo-800 hover:text-indigo-900 py-2 rounded-xl bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition-colors"
          >
            View Processed Commodity Detail →
          </router-link>
        </div>
      </div>
    </div>

    <!-- Top Export Markets Table -->
    <div class="bg-white p-4 sm:p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-sm sm:text-base font-bold text-slate-900">Destination Markets Breakdown</h3>
          <p class="text-xs text-slate-500 mt-0.5">International buyers ranked by total export revenue and volume</p>
        </div>
        <span class="text-xs font-semibold text-slate-500 bg-slate-50 px-2.5 py-1 rounded-lg">
          {{ commodity.market_breakdown.length }} Markets
        </span>
      </div>

      <div class="overflow-x-auto -mx-4 sm:mx-0 px-4 sm:px-0">
        <table class="w-full text-left text-xs whitespace-nowrap">
          <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
            <tr>
              <th class="p-3 w-12 text-center">Rank</th>
              <th class="p-3">Country</th>
              <th class="p-3 text-right">Volume</th>
              <th class="p-3 text-right">Revenue ($USD)</th>
              <th class="p-3 text-right">Revenue (KHR)</th>
              <th class="p-3 text-right">Market Share</th>
              <th class="p-3 text-right">Avg Unit Price</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="(m, idx) in commodity.market_breakdown" :key="m.country" class="hover:bg-slate-50 transition-colors">
              <td class="p-3 text-center font-bold text-slate-400">{{ idx + 1 }}</td>
              <td class="p-3 font-bold text-slate-900">{{ getCountryFlag(m.country) }} {{ m.country }}</td>
              <td class="p-3 text-right font-medium text-slate-700">{{ formatVolumeKg(m.weight_kg) }}</td>
              <td class="p-3 text-right font-bold text-slate-900">{{ formatRevenue(m.val_usd) }}</td>
              <td class="p-3 text-right font-mono text-slate-500">{{ formatKhrBillions(m.val_khr) }}</td>
              <td class="p-3 text-right">
                <span class="px-2 py-0.5 rounded-md font-bold text-[11px] bg-sky-50 text-sky-700">
                  {{ m.share_pct ? m.share_pct.toFixed(1) : ((m.val_usd / Math.max(1, commodity.total_val_usd)) * 100).toFixed(1) }}%
                </span>
              </td>
              <td class="p-3 text-right font-bold text-emerald-600">
                ${{ (m.val_usd / Math.max(1, m.weight_kg)).toFixed(2) }} / kg
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
  
  <!-- Not Found / Loading State -->
  <div v-else class="text-center py-24 bg-white rounded-2xl border border-slate-100 p-8">
    <p class="text-base font-bold text-slate-700">Commodity not found</p>
    <p class="text-xs text-slate-500 mt-1">The requested 8-digit HS commodity was not found in the current dataset.</p>
    <button
      @click="goBack"
      class="mt-4 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white font-semibold text-xs rounded-xl transition-colors"
    >
      Return to Overview
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { ArrowLeft as ArrowLeftIcon, ArrowRight as ArrowRightIcon } from 'lucide-vue-next';
import { useDatasetStore } from '../stores/datasetStore';
import WorldExportMap from '../components/dashboard/WorldExportMap.vue';
import type { CommodityDetail } from '../types/dataset';

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const route = useRoute();
const router = useRouter();
const store = useDatasetStore();

const trendMetric = ref<'USD' | 'VOLUME'>('USD');

const currentHs8Code = computed(() => {
  return (route.params.hs8code as string) || '';
});

const commodity = computed<CommodityDetail | null>(() => {
  if (!store.dashboardData?.commodity_details) return null;
  return store.dashboardData.commodity_details[currentHs8Code.value] || null;
});

const topMarketName = computed(() => {
  if (!commodity.value?.market_breakdown?.length) return 'None';
  return commodity.value.market_breakdown[0].country;
});

const goBack = () => {
  router.push('/');
};

const goToCompare = () => {
  router.push(`/compare?a=${currentHs8Code.value}`);
};

const COUNTRY_FLAGS: Record<string, string> = {
  'Vietnam': '🇻🇳', 'China': '🇨🇳', 'Thailand': '🇹🇭', 'Japan': '🇯🇵',
  'United States': '🇺🇸', 'USA': '🇺🇸', 'France': '🇫🇷', 'South Korea': '🇰🇷',
  'Taiwan': '🇹🇼', 'India': '🇮🇳', 'Malaysia': '🇲🇾', 'Singapore': '🇸🇬',
  'Germany': '🇩🇪', 'Netherlands': '🇳🇱', 'Italy': '🇮🇹', 'United Kingdom': '🇬🇧',
};

const getCountryFlag = (name: string): string => {
  return COUNTRY_FLAGS[name] || '🌐';
};

const formatRevenue = (valUsd: number): string => {
  if (!valUsd || valUsd === 0) return '$0 USD';
  if (valUsd < 1_000_000) {
    const kUsd = Math.round((valUsd / 1000) * 10) / 10;
    return `$${kUsd.toLocaleString()}k USD`;
  }
  return `$${(valUsd / 1e6).toFixed(2)}M USD`;
};

const formatVolumeKg = (kg: number): string => {
  if (!kg || kg === 0) return '0 kg';
  const tonnes = kg / 1000.0;
  if (tonnes < 1) {
    return `${Math.round(kg).toLocaleString()} kg`;
  }
  return `${(Math.round(tonnes * 10) / 10).toLocaleString()} Tonnes`;
};

const formatKhrBillions = (khr: number): string => {
  if (!khr || khr === 0) return '៛0 KHR';
  if (khr >= 1e9) {
    return `៛${(khr / 1e9).toFixed(2)}B KHR`;
  }
  if (khr >= 1e6) {
    return `៛${(khr / 1e6).toFixed(2)}M KHR`;
  }
  return `៛${Math.round(khr).toLocaleString()} KHR`;
};

// Monthly Trend Chart Option (Revenue or Volume with dynamic units)
const monthlyTrendOption = computed(() => {
  if (!commodity.value?.monthly_trend?.length) return {};
  const data = commodity.value.monthly_trend;
  const xLabels = data.map(d => d.yyyy_mm);

  if (trendMetric.value === 'USD') {
    const maxVal = Math.max(...data.map(d => d.val_usd));
    const useK = maxVal < 1_000_000;
    const yValues = data.map(d => (useK ? d.val_usd / 1000.0 : d.val_usd / 1e6));
    const unit = useK ? '$k USD' : '$M USD';

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const p = params[0];
          const rawUsd = data[p.dataIndex]?.val_usd || 0;
          return `<strong>${p.name}</strong><br/>Revenue: <strong>${formatRevenue(rawUsd)}</strong>`;
        }
      },
      grid: { top: 25, right: 20, bottom: 25, left: 55 },
      xAxis: { type: 'category', data: xLabels, axisLabel: { fontSize: 11 } },
      yAxis: {
        type: 'value',
        name: unit,
        nameTextStyle: { fontSize: 10, color: '#64748b' },
        axisLabel: { formatter: (v: number) => (useK ? `$${v.toFixed(0)}k` : `$${v.toFixed(2)}M`) }
      },
      series: [
        {
          name: 'Export Revenue',
          type: 'line',
          data: yValues,
          smooth: true,
          symbolSize: 6,
          itemStyle: { color: '#0284c7' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(2, 132, 199, 0.3)' },
                { offset: 1, color: 'rgba(2, 132, 199, 0.0)' }
              ]
            }
          }
        }
      ]
    };
  } else {
    // Volume metric (Tonnes or kg)
    const maxKg = Math.max(...data.map(d => d.weight_kg));
    const useKg = maxKg < 1000;
    const yValues = data.map(d => (useKg ? d.weight_kg : d.weight_kg / 1000.0));
    const unit = useKg ? 'kg' : 'Tonnes';

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const p = params[0];
          const rawKg = data[p.dataIndex]?.weight_kg || 0;
          return `<strong>${p.name}</strong><br/>Volume: <strong>${formatVolumeKg(rawKg)}</strong>`;
        }
      },
      grid: { top: 25, right: 20, bottom: 25, left: 55 },
      xAxis: { type: 'category', data: xLabels, axisLabel: { fontSize: 11 } },
      yAxis: {
        type: 'value',
        name: unit,
        nameTextStyle: { fontSize: 10, color: '#64748b' },
        axisLabel: { formatter: (v: number) => (useKg ? `${v.toFixed(0)}kg` : `${v.toFixed(1)}t`) }
      },
      series: [
        {
          name: 'Export Volume',
          type: 'line',
          data: yValues,
          smooth: true,
          symbolSize: 6,
          itemStyle: { color: '#10b981' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(16, 185, 129, 0.3)' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.0)' }
              ]
            }
          }
        }
      ]
    };
  }
});

// Price Evolution Chart Option (USD/kg and KHR/kg)
const priceTrendOption = computed(() => {
  if (!commodity.value?.monthly_trend?.length) return {};
  const data = commodity.value.monthly_trend;
  const xLabels = data.map(d => d.yyyy_mm);
  const usdPrices = data.map(d => Number(d.price_usd_per_kg.toFixed(3)));
  const khrPrices = data.map(d => Math.round(d.price_khr_per_kg));

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex;
        const d = data[idx];
        return `
          <strong>${d.yyyy_mm}</strong><br/>
          Price: <strong class="text-emerald-500">$${d.price_usd_per_kg.toFixed(2)}/kg</strong><br/>
          Price: <strong class="text-amber-500">${Math.round(d.price_khr_per_kg).toLocaleString()} ៛/kg</strong>
        `;
      }
    },
    legend: { data: ['USD/kg ($)', 'KHR/kg (៛)'], top: 0, textStyle: { fontSize: 11 } },
    grid: { top: 35, right: 65, bottom: 25, left: 50 },
    xAxis: { type: 'category', data: xLabels, axisLabel: { fontSize: 11 } },
    yAxis: [
      {
        type: 'value',
        name: 'USD/kg ($)',
        nameTextStyle: { fontSize: 10, color: '#0284c7' },
        axisLabel: { formatter: '${value}' }
      },
      {
        type: 'value',
        name: 'KHR/kg (៛)',
        nameTextStyle: { fontSize: 10, color: '#f59e0b' },
        axisLabel: { formatter: '{value}៛' }
      }
    ],
    series: [
      {
        name: 'USD/kg ($)',
        type: 'line',
        yAxisIndex: 0,
        data: usdPrices,
        smooth: true,
        symbolSize: 6,
        itemStyle: { color: '#0284c7' },
        lineStyle: { width: 2.5 }
      },
      {
        name: 'KHR/kg (៛)',
        type: 'line',
        yAxisIndex: 1,
        data: khrPrices,
        smooth: true,
        symbolSize: 6,
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 2, type: 'dashed' }
      }
    ]
  };
});
</script>

