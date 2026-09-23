<template>
  <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
    <!-- Header with Metric Toggle & Unit Scale -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-100">
      <div>
        <div class="flex items-center gap-2">
          <span class="p-1.5 rounded-lg bg-sky-50 text-sky-600">
            <GlobeIcon class="w-4 h-4" />
          </span>
          <h3 class="text-base font-bold text-slate-900">{{ title || 'Global Export Destination Map' }}</h3>
        </div>
        <p class="text-xs text-slate-500 mt-0.5 font-sans">
          ផែនទីលំហូរពាណិជ្ជកម្មនាំចេញ និងទីផ្សារគោលដៅអន្តរជាតិពីកម្ពុជា (Cambodia)
        </p>
      </div>

      <!-- Metric Switcher: Volume vs Revenue with Unit Scales -->
      <div class="flex items-center bg-slate-100 p-1 rounded-xl self-start sm:self-auto">
        <button
          @click="activeMetric = 'VOLUME'"
          class="px-3 py-1 text-xs font-bold rounded-lg transition-all"
          :class="activeMetric === 'VOLUME' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          title="Scale: kg / Metric Tonnes"
        >
          📦 Volume (Tonnes/kg)
        </button>
        <button
          @click="activeMetric = 'REVENUE'"
          class="px-3 py-1 text-xs font-bold rounded-lg transition-all"
          :class="activeMetric === 'REVENUE' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
          title="Scale: $k / $M USD"
        >
          💰 Revenue ($USD)
        </button>
      </div>
    </div>

    <!-- ECharts Container -->
    <div class="relative w-full h-[420px] sm:h-[500px] rounded-xl overflow-hidden bg-slate-950 border border-slate-800">
      <!-- Cambodia Hub Badge -->
      <div class="absolute top-3 left-3 z-10 bg-slate-900/90 backdrop-blur-xs px-3 py-1.5 rounded-xl border border-slate-700 text-xs text-slate-200 flex items-center gap-2 shadow-md">
        <span class="relative flex h-2.5 w-2.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
        </span>
        <span class="font-bold text-white">Origin: Cambodia 🇰🇭</span>
        <span class="text-slate-400 text-[11px] font-sans">(កម្ពុជា)</span>
      </div>

      <!-- Active Metric Legend Badge -->
      <div class="absolute top-3 right-3 z-10 bg-slate-900/90 backdrop-blur-xs px-3 py-1.5 rounded-xl border border-slate-700 text-xs text-slate-300 shadow-md">
        <span class="text-slate-400">Scale: </span>
        <strong :class="activeMetric === 'VOLUME' ? 'text-sky-400' : 'text-amber-400'">
          {{ activeMetric === 'VOLUME' ? '📦 Volume (kg / Tonnes)' : '💰 Value ($k / $M USD)' }}
        </strong>
      </div>

      <!-- In-Map Country Intelligence Floating Card (Triggered by Map Click) -->
      <div
        v-if="selectedCountry"
        class="absolute bottom-4 left-4 z-20 bg-slate-900/95 backdrop-blur-md border border-slate-700 p-4 rounded-xl shadow-2xl text-white max-w-xs w-full transition-all animate-in fade-in"
      >
        <div class="flex items-center justify-between pb-2 border-b border-slate-800 mb-2.5">
          <div class="flex items-center gap-2">
            <span class="text-xl">{{ getCountryFlag(selectedCountry.country) }}</span>
            <div>
              <h4 class="font-bold text-sm text-white leading-tight">
                {{ getDisplayCountryName(selectedCountry.country) }}
              </h4>
              <span class="text-[10px] text-slate-400 font-sans">Destination Partner</span>
            </div>
          </div>
          <button
            @click="selectedCountry = null"
            class="w-6 h-6 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center text-xs font-bold"
            title="Close country details"
          >
            ✕
          </button>
        </div>

        <div class="space-y-2 text-xs">
          <div class="flex items-center justify-between bg-slate-800/60 p-2 rounded-lg border border-slate-700/50">
            <span class="text-slate-400">Export Revenue:</span>
            <div class="text-right">
              <strong class="text-amber-400 font-bold block">{{ formatRevenueUsd(selectedCountry.val_usd) }}</strong>
              <span class="text-[10px] text-emerald-400 font-semibold">{{ countrySharePct(selectedCountry) }}% Share</span>
            </div>
          </div>

          <div class="flex items-center justify-between bg-slate-800/60 p-2 rounded-lg border border-slate-700/50">
            <span class="text-slate-400">Export Volume:</span>
            <strong class="text-sky-300 font-bold">{{ formatVolumeKg(selectedCountry.weight_kg) }}</strong>
          </div>

          <!-- Country-Specific Average Price -->
          <div class="flex items-center justify-between bg-emerald-950/40 p-2 rounded-lg border border-emerald-800/40">
            <span class="text-emerald-300 font-semibold">Country Avg Price:</span>
            <div class="text-right">
              <strong class="text-emerald-400 font-mono font-bold block">
                ${{ countryAvgPriceUsd(selectedCountry) }}/kg
              </strong>
              <span class="text-[10px] text-slate-400">
                ({{ countryAvgPriceKhr(selectedCountry) }} ៛/kg)
              </span>
            </div>
          </div>
        </div>
      </div>

      <v-chart
        ref="chartRef"
        class="w-full h-full cursor-pointer"
        :option="mapChartOption"
        @click="onMapClick"
        autoresize
      />
    </div>

    <!-- Bottom Destination Market Summary Pills -->
    <div class="mt-4 pt-3 border-t border-slate-100">
      <div class="flex items-center justify-between text-xs text-slate-500 mb-2">
        <span class="font-semibold text-slate-700">Top Destination Markets ({{ marketData.length }} countries):</span>
        <span class="text-[11px] text-slate-400">Click country to view inside-map intelligence</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="mkt in marketData.slice(0, 10)"
          :key="mkt.country"
          @click="selectedCountry = mkt"
          class="cursor-pointer flex items-center gap-1.5 px-2.5 py-1 rounded-lg border transition-all text-xs text-left"
          :class="selectedCountry?.country === mkt.country ? 'bg-sky-50 border-sky-300 ring-2 ring-sky-400/30' : 'bg-slate-50 border-slate-200/80 hover:bg-slate-100'"
        >
          <span class="font-bold text-slate-800">{{ getCountryFlag(mkt.country) }} {{ getDisplayCountryName(mkt.country) }}</span>
          <span class="text-slate-400">|</span>
          <span class="font-semibold" :class="activeMetric === 'VOLUME' ? 'text-sky-700' : 'text-amber-700'">
            {{ activeMetric === 'VOLUME' ? formatVolumeKg(mkt.weight_kg) : formatRevenueUsd(mkt.val_usd) }}
          </span>
          <span class="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
            {{ countrySharePct(mkt) }}%
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { MapChart, ScatterChart, EffectScatterChart, LinesChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GeoComponent,
  VisualMapComponent,
  GridComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { Globe as GlobeIcon } from 'lucide-vue-next';
import worldGeoJson from '../../assets/world.json';
import type { MarketBreakdownItem } from '../../types/dataset';
import {
  getCountryMeta,
  getCountryFlag,
  getDisplayCountryName,
  CAMBODIA_COORDS
} from '../../utils/countryRegistry';

// Register standard Apache ECharts world map GeoJSON
echarts.registerMap('world', worldGeoJson as any);

echarts.use([
  CanvasRenderer,
  MapChart,
  ScatterChart,
  EffectScatterChart,
  LinesChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GeoComponent,
  VisualMapComponent,
  GridComponent,
]);

const props = defineProps<{
  title?: string;
  marketData: MarketBreakdownItem[];
  exchangeRate?: number;
}>();

const activeMetric = ref<'VOLUME' | 'REVENUE'>('VOLUME');
const selectedCountry = ref<MarketBreakdownItem | null>(null);



const totalValUsd = computed(() => {
  return (props.marketData || []).reduce((acc, m) => acc + (m.val_usd || 0), 0);
});

const countrySharePct = (m: MarketBreakdownItem): string => {
  if (m.share_pct) return m.share_pct.toFixed(1);
  return ((m.val_usd / Math.max(1, totalValUsd.value)) * 100).toFixed(1);
};

const countryAvgPriceUsd = (m: MarketBreakdownItem): string => {
  if (!m || !m.weight_kg || m.weight_kg <= 0) return '0.00';
  return (m.val_usd / m.weight_kg).toFixed(2);
};

const countryAvgPriceKhr = (m: MarketBreakdownItem): string => {
  if (!m || !m.weight_kg || m.weight_kg <= 0) return '0';
  const rate = props.exchangeRate || 4000;
  const khr = m.val_khr ? (m.val_khr / m.weight_kg) : ((m.val_usd * rate) / m.weight_kg);
  return Math.round(khr).toLocaleString();
};

const formatRevenueUsd = (valUsd: number): string => {
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

const onMapClick = (params: any) => {
  if (params.data?.rawMarket) {
    selectedCountry.value = params.data.rawMarket;
  } else if (params.name) {
    const matched = props.marketData.find(m => {
      const meta = getCountryMeta(m.country);
      return m.country === params.name || 
             meta.en.toLowerCase() === params.name.toLowerCase() ||
             params.name.includes(meta.en) ||
             params.name.includes(m.country);
    });
    if (matched) {
      selectedCountry.value = matched;
    }
  }
};

// Compute ECharts Option with registered 'world' GeoJSON
const mapChartOption = computed(() => {
  const mktList = props.marketData || [];

  const cambodiaHub = {
    name: 'Cambodia (Origin / ប្រទេសដើមកំណើត)',
    value: [...CAMBODIA_COORDS, 100],
    itemStyle: { color: '#10b981' }
  };

  const maxVal = Math.max(
    1,
    ...mktList.map(m => (activeMetric.value === 'VOLUME' ? m.weight_kg : m.val_usd))
  );

  // Scatter points for destination countries
  const scatterPoints = mktList
    .map(m => {
      const meta = getCountryMeta(m.country);
      const val = activeMetric.value === 'VOLUME' ? m.weight_kg : m.val_usd;
      const size = Math.max(14, Math.min(42, Math.sqrt(val / maxVal) * 38));
      return {
        name: `${meta.flag} ${meta.en} (${m.country})`,
        value: [meta.coords[0], meta.coords[1], val],
        symbolSize: size,
        rawMarket: m,
        meta,
        label: {
          show: true,
          formatter: () => `${meta.flag} ${meta.en}`,
          position: 'top',
          color: '#f8fafc',
          fontSize: 10,
          fontWeight: 'bold',
          textBorderColor: '#090d16',
          textBorderWidth: 3,
          distance: 6,
        },
        itemStyle: {
          color: activeMetric.value === 'VOLUME' ? '#38bdf8' : '#fbbf24',
          borderColor: '#ffffff',
          borderWidth: 1.5,
          shadowBlur: 14,
          shadowColor: activeMetric.value === 'VOLUME' ? 'rgba(56, 189, 248, 0.8)' : 'rgba(251, 191, 36, 0.8)',
        },
      };
    });

  // Animated Trade Flow Lines from Phnom Penh Cambodia to Destinations
  const flowLines = mktList
    .map(m => {
      const meta = getCountryMeta(m.country);
      return {
        fromName: 'Cambodia',
        toName: meta.en,
        coords: [CAMBODIA_COORDS, meta.coords],
      };
    });

  return {
    backgroundColor: '#090d16',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: '#334155',
      borderWidth: 1,
      padding: [10, 14],
      textStyle: { color: '#f8fafc', fontSize: 12 },
      formatter: (params: any) => {
        if (params.seriesType === 'lines') {
          return `<div class="font-bold text-sky-400">✈️ Trade Flow: Cambodia 🇰🇭 → ${params.data.toName}</div>`;
        }
        if (params.data?.name && params.data.name.includes('Cambodia (Origin')) {
          return `<div class="p-1">
            <div class="font-bold text-emerald-400 text-sm">🇰🇭 Cambodia (Origin Country)</div>
            <div class="text-xs text-slate-300 mt-0.5">Agricultural Trade Hub (ភ្នំពេញ)</div>
          </div>`;
        }
        const m = params.data?.rawMarket;
        const meta = params.data?.meta;
        if (!m) return params.name;
        const flag = meta?.flag || '🌐';
        const enName = meta?.en || m.country;
        const share = countrySharePct(m);
        const unitPriceUsd = countryAvgPriceUsd(m);
        const unitPriceKhr = countryAvgPriceKhr(m);

        return `
          <div class="p-1 space-y-1.5 min-w-[220px]">
            <div class="flex items-center justify-between border-b border-slate-700 pb-1.5">
              <div>
                <span class="font-black text-sm text-white">${flag} ${enName}</span>
                <span class="text-xs text-slate-400 font-sans block">${m.country}</span>
              </div>
              <span class="text-xs font-black text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800/50">${share}% Share</span>
            </div>
            <div class="text-xs space-y-1 pt-0.5">
              <div class="flex justify-between">
                <span class="text-slate-400">Volume (បរិមាណ):</span>
                <strong class="text-sky-300 font-bold">${formatVolumeKg(m.weight_kg)}</strong>
              </div>
              <div class="flex justify-between">
                <span class="text-slate-400">Revenue (ចំណូល $):</span>
                <strong class="text-amber-300 font-bold">${formatRevenueUsd(m.val_usd)}</strong>
              </div>
              <div class="flex justify-between border-t border-slate-800 pt-1">
                <span class="text-slate-400">Country Avg Price:</span>
                <strong class="text-emerald-400 font-mono font-bold">$${unitPriceUsd}/kg <span class="text-[11px] text-slate-400 font-sans">(${unitPriceKhr} ៛)</span></strong>
              </div>
            </div>
          </div>
        `;
      }
    },
    geo: {
      map: 'world',
      roam: true,
      zoom: 1.18,
      center: [55, 20],
      label: {
        show: false,
        emphasis: {
          show: true,
          color: '#ffffff',
          fontSize: 10,
        }
      },
      itemStyle: {
        areaColor: '#1e293b',
        borderColor: '#334155',
        borderWidth: 0.8,
      },
      emphasis: {
        itemStyle: {
          areaColor: '#0284c7',
          borderColor: '#38bdf8',
          borderWidth: 1.5,
        }
      }
    },
    series: [
      // Animated Flight / Trade Lines from Cambodia
      {
        name: 'Export Routes',
        type: 'lines',
        coordinateSystem: 'geo',
        zlevel: 1,
        effect: {
          show: true,
          period: 4,
          trailLength: 0.25,
          symbol: 'arrow',
          symbolSize: 6,
          color: activeMetric.value === 'VOLUME' ? '#38bdf8' : '#fbbf24',
        },
        lineStyle: {
          color: activeMetric.value === 'VOLUME' ? 'rgba(56, 189, 248, 0.45)' : 'rgba(251, 191, 36, 0.45)',
          width: 1.8,
          curveness: 0.22,
        },
        data: flowLines,
      },
      // Destination Bubbles
      {
        name: 'Destination Markets',
        type: 'scatter',
        coordinateSystem: 'geo',
        zlevel: 2,
        data: scatterPoints,
      },
      // Pulsing Cambodia Origin Hub
      {
        name: 'Cambodia Hub',
        type: 'effectScatter',
        coordinateSystem: 'geo',
        zlevel: 3,
        rippleEffect: {
          brushType: 'stroke',
          scale: 4,
          period: 3,
        },
        symbolSize: 16,
        data: [cambodiaHub],
      },
    ],
  };
});
</script>
