<template>
  <div class="space-y-8">
    
    <!-- Top Navigation & Header -->
    <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div>
        <button
          @click="goBack"
          class="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-colors shadow-xs mb-2"
        >
          <ArrowLeftIcon class="w-3.5 h-3.5" />
          <span>Back to Overview</span>
        </button>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
          <span>⚖️ 8-Digit Commodity Comparison</span>
        </h1>
        <p class="text-xs text-slate-500 mt-1 font-sans">
          ប្រៀបធៀបទំនិញកូដ ៨ខ្ទង់ — Cross-chapter analysis of prices, export volumes, and international markets.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold px-3 py-1 bg-sky-50 text-sky-700 rounded-lg">
          {{ store.dashboardData?.commodity_list?.length || 0 }} Commodities Available
        </span>
      </div>
    </div>

    <!-- Dual Commodity Pickers -->
    <div class="grid grid-cols-1 md:grid-cols-11 gap-4 items-center">
      
      <!-- Picker A (Commodity 1) -->
      <div class="md:col-span-5 bg-white p-5 rounded-2xl border-2 border-sky-300 shadow-sm relative">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold uppercase tracking-wider text-sky-700 flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-sky-500"></span>
            Commodity A (ទំនិញ ទី១)
          </span>
          <span v-if="commA" class="text-xs font-mono font-bold text-sky-600 bg-sky-50 px-2 py-0.5 rounded">
            HS {{ commA.hs8_code }}
          </span>
        </div>

        <select
          v-model="selectedCodeA"
          class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-sky-500 focus:outline-hidden"
        >
          <option v-for="item in commodityOptions" :key="`a-${item.hs8_code}`" :value="item.hs8_code">
            [HS {{ item.hs8_code }}] {{ item.name_en }} {{ item.name_km ? `(${item.name_km})` : '' }}
          </option>
        </select>

        <div v-if="commA" class="mt-3 text-xs text-slate-500 flex items-center justify-between">
          <span class="truncate font-sans font-medium text-slate-700">{{ commA.name_km }}</span>
          <router-link :to="`/commodity/${commA.hs8_code}`" class="text-sky-600 font-bold hover:underline ml-2 whitespace-nowrap">
            View Detail →
          </router-link>
        </div>
      </div>

      <!-- Swap Button (Center) -->
      <div class="md:col-span-1 flex justify-center">
        <button
          @click="swapCommodities"
          title="Swap Commodities A and B"
          class="p-3 bg-slate-100 hover:bg-sky-100 text-slate-700 hover:text-sky-700 rounded-full transition-all shadow-xs border border-slate-200"
        >
          <ArrowLeftRightIcon class="w-4 h-4" />
        </button>
      </div>

      <!-- Picker B (Commodity 2) -->
      <div class="md:col-span-5 bg-white p-5 rounded-2xl border-2 border-amber-300 shadow-sm relative">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
            Commodity B (ទំនិញ ទី២)
          </span>
          <span v-if="commB" class="text-xs font-mono font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
            HS {{ commB.hs8_code }}
          </span>
        </div>

        <select
          v-model="selectedCodeB"
          class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-amber-500 focus:outline-hidden"
        >
          <option v-for="item in commodityOptions" :key="`b-${item.hs8_code}`" :value="item.hs8_code">
            [HS {{ item.hs8_code }}] {{ item.name_en }} {{ item.name_km ? `(${item.name_km})` : '' }}
          </option>
        </select>

        <div v-if="commB" class="mt-3 text-xs text-slate-500 flex items-center justify-between">
          <span class="truncate font-sans font-medium text-slate-700">{{ commB.name_km }}</span>
          <router-link :to="`/commodity/${commB.hs8_code}`" class="text-amber-600 font-bold hover:underline ml-2 whitespace-nowrap">
            View Detail →
          </router-link>
        </div>
      </div>

    </div>

    <!-- Side-by-Side KPI Comparison Cards (4 Pillars) -->
    <div v-if="commA && commB" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- KPI 1: Export Revenue -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-3">
          Total Export Value ($USD)
        </span>
        <div class="space-y-2 text-xs">
          <div class="flex items-center justify-between p-2 rounded-xl bg-sky-50/70 border border-sky-100">
            <span class="font-bold text-sky-800 truncate max-w-[120px]">A: {{ commA.name_en }}</span>
            <strong class="text-slate-900 text-sm font-black">{{ formatRevenue(commA.total_val_usd) }}</strong>
          </div>
          <div class="flex items-center justify-between p-2 rounded-xl bg-amber-50/70 border border-amber-100">
            <span class="font-bold text-amber-800 truncate max-w-[120px]">B: {{ commB.name_en }}</span>
            <strong class="text-slate-900 text-sm font-black">{{ formatRevenue(commB.total_val_usd) }}</strong>
          </div>
        </div>
        <div class="mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Ratio (A / B):</span>
          <strong class="text-slate-800 font-mono">{{ (commA.total_val_usd / Math.max(1, commB.total_val_usd)).toFixed(2) }}x</strong>
        </div>
      </div>

      <!-- KPI 2: Export Volume -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-3">
          Total Export Volume
        </span>
        <div class="space-y-2 text-xs">
          <div class="flex items-center justify-between p-2 rounded-xl bg-sky-50/70 border border-sky-100">
            <span class="font-bold text-sky-800 truncate max-w-[120px]">A: {{ commA.name_en }}</span>
            <strong class="text-slate-900 text-sm font-black">{{ formatVolumeKg(commA.total_weight_kg) }}</strong>
          </div>
          <div class="flex items-center justify-between p-2 rounded-xl bg-amber-50/70 border border-amber-100">
            <span class="font-bold text-amber-800 truncate max-w-[120px]">B: {{ commB.name_en }}</span>
            <strong class="text-slate-900 text-sm font-black">{{ formatVolumeKg(commB.total_weight_kg) }}</strong>
          </div>
        </div>
        <div class="mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Ratio (A / B):</span>
          <strong class="text-slate-800 font-mono">{{ (commA.total_weight_kg / Math.max(1, commB.total_weight_kg)).toFixed(2) }}x</strong>
        </div>
      </div>

      <!-- KPI 3: Unit Price -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-3">
          Avg Unit Price ($/kg)
        </span>
        <div class="space-y-2 text-xs">
          <div class="flex items-center justify-between p-2 rounded-xl bg-sky-50/70 border border-sky-100">
            <span class="font-bold text-sky-800 truncate max-w-[120px]">A: {{ commA.name_en }}</span>
            <strong class="text-sky-700 text-sm font-black">${{ commA.avg_price_usd_per_kg.toFixed(2) }}/kg</strong>
          </div>
          <div class="flex items-center justify-between p-2 rounded-xl bg-amber-50/70 border border-amber-100">
            <span class="font-bold text-amber-800 truncate max-w-[120px]">B: {{ commB.name_en }}</span>
            <strong class="text-amber-700 text-sm font-black">${{ commB.avg_price_usd_per_kg.toFixed(2) }}/kg</strong>
          </div>
        </div>
        <div class="mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Price Premium:</span>
          <strong class="text-emerald-600 font-bold">
            {{ commA.avg_price_usd_per_kg >= commB.avg_price_usd_per_kg ? 'A is ' + (commA.avg_price_usd_per_kg / Math.max(0.01, commB.avg_price_usd_per_kg)).toFixed(1) + 'x higher' : 'B is ' + (commB.avg_price_usd_per_kg / Math.max(0.01, commA.avg_price_usd_per_kg)).toFixed(1) + 'x higher' }}
          </strong>
        </div>
      </div>

      <!-- KPI 4: Destination Markets -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-3">
          Destination Markets
        </span>
        <div class="space-y-2 text-xs">
          <div class="flex items-center justify-between p-2 rounded-xl bg-sky-50/70 border border-sky-100">
            <span class="font-bold text-sky-800 truncate max-w-[120px]">A: {{ commA.name_en }}</span>
            <strong class="text-slate-900 text-sm font-black">{{ commA.num_markets }} countries</strong>
          </div>
          <div class="flex items-center justify-between p-2 rounded-xl bg-amber-50/70 border border-amber-100">
            <span class="font-bold text-amber-800 truncate max-w-[120px]">B: {{ commB.name_en }}</span>
            <strong class="text-slate-900 text-sm font-black">{{ commB.num_markets }} countries</strong>
          </div>
        </div>
        <div class="mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Shared Markets:</span>
          <strong class="text-slate-800 font-mono">{{ sharedMarketsCount }} countries</strong>
        </div>
      </div>

    </div>

    <!-- Comparative Charts Row -->
    <div v-if="commA && commB" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
      <!-- Chart 1: Unit Price ($/kg) Historical Trajectory Comparison -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
        <div class="pb-3 mb-3 border-b border-slate-100">
          <h3 class="text-base font-bold text-slate-900">Unit Price ($/kg) Trend Comparison</h3>
          <p class="text-xs text-slate-500 mt-0.5">Monthly price trajectory for Commodity A vs Commodity B</p>
        </div>

        <div class="h-80 w-full">
          <v-chart class="w-full h-full" :option="priceCompareChartOption" autoresize />
        </div>
      </div>

      <!-- Chart 2: Export Performance (Volume or Revenue) Comparison -->
      <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
        <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-900">Export Volume & Value Comparison</h3>
            <p class="text-xs text-slate-500 mt-0.5">Side-by-side monthly shipping dynamics</p>
          </div>

          <div class="flex items-center bg-slate-100 p-1 rounded-xl">
            <button
              @click="compareMetric = 'USD'"
              class="px-2.5 py-1 text-xs font-bold rounded-lg transition-all"
              :class="compareMetric === 'USD' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600'"
            >
              Revenue ($)
            </button>
            <button
              @click="compareMetric = 'VOLUME'"
              class="px-2.5 py-1 text-xs font-bold rounded-lg transition-all"
              :class="compareMetric === 'VOLUME' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600'"
            >
              Volume
            </button>
          </div>
        </div>

        <div class="h-80 w-full">
          <v-chart class="w-full h-full" :option="volumeCompareChartOption" autoresize />
        </div>
      </div>

    </div>

    <!-- Comparative Market Overlap Table -->
    <div v-if="commA && commB" class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-base font-bold text-slate-900">Market Overlap & Destination Penetration</h3>
          <p class="text-xs text-slate-500 mt-0.5">Compare export market distribution between Commodity A and Commodity B</p>
        </div>
        <span class="text-xs font-semibold text-slate-500 bg-slate-50 px-2.5 py-1 rounded-lg">
          {{ combinedMarkets.length }} Total Markets
        </span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
            <tr>
              <th class="p-3">Destination Country</th>
              <th class="p-3 text-right text-sky-800 bg-sky-50/50">A: {{ commA.name_en }} (Vol)</th>
              <th class="p-3 text-right text-sky-800 bg-sky-50/50">A: Revenue ($)</th>
              <th class="p-3 text-right text-amber-800 bg-amber-50/50">B: {{ commB.name_en }} (Vol)</th>
              <th class="p-3 text-right text-amber-800 bg-amber-50/50">B: Revenue ($)</th>
              <th class="p-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="m in combinedMarkets" :key="m.country" class="hover:bg-slate-50 transition-colors">
              <td class="p-3 font-bold text-slate-900">
                {{ getCountryFlag(m.country) }} {{ m.country }}
              </td>
              <td class="p-3 text-right font-medium text-slate-700 bg-sky-50/20">
                {{ m.valA ? formatVolumeKg(m.valA.weight_kg) : '—' }}
              </td>
              <td class="p-3 text-right font-bold text-sky-900 bg-sky-50/20">
                {{ m.valA ? formatRevenue(m.valA.val_usd) : '—' }}
              </td>
              <td class="p-3 text-right font-medium text-slate-700 bg-amber-50/20">
                {{ m.valB ? formatVolumeKg(m.valB.weight_kg) : '—' }}
              </td>
              <td class="p-3 text-right font-bold text-amber-900 bg-amber-50/20">
                {{ m.valB ? formatRevenue(m.valB.val_usd) : '—' }}
              </td>
              <td class="p-3 text-center">
                <span
                  v-if="m.valA && m.valB"
                  class="px-2 py-0.5 rounded-full font-bold text-[10px] bg-emerald-100 text-emerald-800"
                >
                  Both Markets
                </span>
                <span
                  v-else-if="m.valA"
                  class="px-2 py-0.5 rounded-full font-bold text-[10px] bg-sky-100 text-sky-800"
                >
                  A Only
                </span>
                <span
                  v-else
                  class="px-2 py-0.5 rounded-full font-bold text-[10px] bg-amber-100 text-amber-800"
                >
                  B Only
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
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
import { ArrowLeft as ArrowLeftIcon, ArrowLeftRight as ArrowLeftRightIcon } from 'lucide-vue-next';
import { useDatasetStore } from '../stores/datasetStore';
import type { CommodityDetail, CommodityListItem } from '../types/dataset';

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

const selectedCodeA = ref<string>('08013100');
const selectedCodeB = ref<string>('08013200');
const compareMetric = ref<'USD' | 'VOLUME'>('USD');

onMounted(() => {
  const queryA = route.query.a as string;
  const queryB = route.query.b as string;
  const list = store.dashboardData?.commodity_list || [];

  if (queryA && list.some(c => c.hs8_code === queryA)) {
    selectedCodeA.value = queryA;
  } else if (list.length > 0) {
    selectedCodeA.value = list[0].hs8_code;
  }

  if (queryB && list.some(c => c.hs8_code === queryB)) {
    selectedCodeB.value = queryB;
  } else if (list.length > 1) {
    selectedCodeB.value = list[1].hs8_code;
  }
});

const commodityOptions = computed<CommodityListItem[]>(() => {
  return store.dashboardData?.commodity_list || [];
});

const commA = computed<CommodityDetail | null>(() => {
  if (!store.dashboardData?.commodity_details) return null;
  return store.dashboardData.commodity_details[selectedCodeA.value] || null;
});

const commB = computed<CommodityDetail | null>(() => {
  if (!store.dashboardData?.commodity_details) return null;
  return store.dashboardData.commodity_details[selectedCodeB.value] || null;
});

const swapCommodities = () => {
  const temp = selectedCodeA.value;
  selectedCodeA.value = selectedCodeB.value;
  selectedCodeB.value = temp;
};

const goBack = () => {
  router.push('/');
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

// Combined Markets computation
const combinedMarkets = computed(() => {
  if (!commA.value || !commB.value) return [];
  const mapA = new Map(commA.value.market_breakdown.map(m => [m.country, m]));
  const mapB = new Map(commB.value.market_breakdown.map(m => [m.country, m]));
  const allCountries = Array.from(new Set([...mapA.keys(), ...mapB.keys()]));

  return allCountries.map(country => ({
    country,
    valA: mapA.get(country) || null,
    valB: mapB.get(country) || null,
  })).sort((a, b) => {
    const totA = (a.valA?.val_usd || 0) + (a.valB?.val_usd || 0);
    const totB = (b.valA?.val_usd || 0) + (b.valB?.val_usd || 0);
    return totB - totA;
  });
});

const sharedMarketsCount = computed(() => {
  return combinedMarkets.value.filter(m => m.valA && m.valB).length;
});

// Price Compare Line Chart Option
const priceCompareChartOption = computed(() => {
  if (!commA.value || !commB.value) return {};
  const monthsA = new Map(commA.value.monthly_trend.map(m => [m.yyyy_mm, m.price_usd_per_kg]));
  const monthsB = new Map(commB.value.monthly_trend.map(m => [m.yyyy_mm, m.price_usd_per_kg]));
  const allMonths = Array.from(new Set([...monthsA.keys(), ...monthsB.keys()])).sort();

  const seriesA = allMonths.map(m => monthsA.has(m) ? Number(monthsA.get(m)!.toFixed(3)) : null);
  const seriesB = allMonths.map(m => monthsB.has(m) ? Number(monthsB.get(m)!.toFixed(3)) : null);

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let res = `<strong>${params[0].name}</strong><br/>`;
        for (const p of params) {
          if (p.value !== null && p.value !== undefined) {
            res += `<span style="color:${p.color};font-weight:bold;">${p.seriesName}:</span> $${Number(p.value).toFixed(2)}/kg<br/>`;
          }
        }
        return res;
      }
    },
    legend: {
      data: [commA.value.name_en, commB.value.name_en],
      top: 0,
      textStyle: { fontSize: 11 }
    },
    grid: { top: 35, right: 20, bottom: 25, left: 55 },
    xAxis: { type: 'category', data: allMonths, axisLabel: { fontSize: 11 } },
    yAxis: {
      type: 'value',
      name: 'USD / kg ($)',
      nameTextStyle: { fontSize: 10, color: '#64748b' },
      axisLabel: { formatter: '${value}' }
    },
    series: [
      {
        name: commA.value.name_en,
        type: 'line',
        data: seriesA,
        smooth: true,
        symbolSize: 6,
        itemStyle: { color: '#0284c7' },
        lineStyle: { width: 2.5 }
      },
      {
        name: commB.value.name_en,
        type: 'line',
        data: seriesB,
        smooth: true,
        symbolSize: 6,
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 2.5 }
      }
    ]
  };
});

// Volume / Revenue Compare Chart Option
const volumeCompareChartOption = computed(() => {
  if (!commA.value || !commB.value) return {};

  const mapDataA = new Map(
    commA.value.monthly_trend.map(m => [
      m.yyyy_mm,
      compareMetric.value === 'USD' ? m.val_usd : m.weight_kg
    ])
  );
  const mapDataB = new Map(
    commB.value.monthly_trend.map(m => [
      m.yyyy_mm,
      compareMetric.value === 'USD' ? m.val_usd : m.weight_kg
    ])
  );
  const allMonths = Array.from(new Set([...mapDataA.keys(), ...mapDataB.keys()])).sort();

  if (compareMetric.value === 'USD') {
    const maxVal = Math.max(
      ...Array.from(mapDataA.values()),
      ...Array.from(mapDataB.values())
    );
    const useK = maxVal < 1_000_000;
    const seriesA = allMonths.map(m => {
      const v = mapDataA.get(m);
      return v !== undefined ? (useK ? v / 1000.0 : v / 1e6) : 0;
    });
    const seriesB = allMonths.map(m => {
      const v = mapDataB.get(m);
      return v !== undefined ? (useK ? v / 1000.0 : v / 1e6) : 0;
    });
    const unit = useK ? '$k USD' : '$M USD';

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let res = `<strong>${params[0].name}</strong><br/>`;
          for (const p of params) {
            const rawVal = useK ? p.value * 1000 : p.value * 1e6;
            res += `<span style="color:${p.color};font-weight:bold;">${p.seriesName}:</span> ${formatRevenue(rawVal)}<br/>`;
          }
          return res;
        }
      },
      legend: {
        data: [commA.value.name_en, commB.value.name_en],
        top: 0,
        textStyle: { fontSize: 11 }
      },
      grid: { top: 35, right: 20, bottom: 25, left: 55 },
      xAxis: { type: 'category', data: allMonths, axisLabel: { fontSize: 11 } },
      yAxis: {
        type: 'value',
        name: unit,
        nameTextStyle: { fontSize: 10, color: '#64748b' },
        axisLabel: { formatter: (v: number) => (useK ? `$${v.toFixed(0)}k` : `$${v.toFixed(2)}M`) }
      },
      series: [
        {
          name: commA.value.name_en,
          type: 'bar',
          data: seriesA,
          itemStyle: { color: '#0284c7', borderRadius: [4, 4, 0, 0] }
        },
        {
          name: commB.value.name_en,
          type: 'bar',
          data: seriesB,
          itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] }
        }
      ]
    };
  } else {
    // Volume metric
    const maxKg = Math.max(
      ...Array.from(mapDataA.values()),
      ...Array.from(mapDataB.values())
    );
    const useKg = maxKg < 1000;
    const seriesA = allMonths.map(m => {
      const v = mapDataA.get(m);
      return v !== undefined ? (useKg ? v : v / 1000.0) : 0;
    });
    const seriesB = allMonths.map(m => {
      const v = mapDataB.get(m);
      return v !== undefined ? (useKg ? v : v / 1000.0) : 0;
    });
    const unit = useKg ? 'kg' : 'Tonnes';

    return {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let res = `<strong>${params[0].name}</strong><br/>`;
          for (const p of params) {
            const rawKg = useKg ? p.value : p.value * 1000;
            res += `<span style="color:${p.color};font-weight:bold;">${p.seriesName}:</span> ${formatVolumeKg(rawKg)}<br/>`;
          }
          return res;
        }
      },
      legend: {
        data: [commA.value.name_en, commB.value.name_en],
        top: 0,
        textStyle: { fontSize: 11 }
      },
      grid: { top: 35, right: 20, bottom: 25, left: 55 },
      xAxis: { type: 'category', data: allMonths, axisLabel: { fontSize: 11 } },
      yAxis: {
        type: 'value',
        name: unit,
        nameTextStyle: { fontSize: 10, color: '#64748b' },
        axisLabel: { formatter: (v: number) => (useKg ? `${v.toFixed(0)}kg` : `${v.toFixed(1)}t`) }
      },
      series: [
        {
          name: commA.value.name_en,
          type: 'bar',
          data: seriesA,
          itemStyle: { color: '#0284c7', borderRadius: [4, 4, 0, 0] }
        },
        {
          name: commB.value.name_en,
          type: 'bar',
          data: seriesB,
          itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] }
        }
      ]
    };
  }
});
</script>

