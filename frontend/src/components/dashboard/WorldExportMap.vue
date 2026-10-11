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

      <!-- Metric Switcher & Theme Toggle -->
      <div class="flex items-center gap-2 self-start sm:self-auto">
        <div class="flex items-center bg-slate-100 p-1 rounded-xl">
          <button
            @click="activeMetric = 'VOLUME'"
            class="px-3 py-1 text-xs font-bold rounded-lg transition-all"
            :class="activeMetric === 'VOLUME' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            title="Scale: kg / Metric Tonnes"
          >
            Volume (Tonnes/kg)
          </button>
          <button
            @click="activeMetric = 'REVENUE'"
            class="px-3 py-1 text-xs font-bold rounded-lg transition-all"
            :class="activeMetric === 'REVENUE' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            title="Scale: $k / $M USD"
          >
            Revenue ($USD)
          </button>
        </div>

        <!-- Map Theme Toggle -->
        <button
          @click="isDarkTheme = !isDarkTheme"
          class="flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-xl border transition-all"
          :class="isDarkTheme 
            ? 'bg-slate-800 border-slate-700 text-amber-400 hover:bg-slate-700' 
            : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 shadow-2xs'"
          :title="isDarkTheme ? 'Switch to Light Theme' : 'Switch to Dark Theme'"
        >
          <span>{{ isDarkTheme ? 'Dark Theme' : 'Light Theme' }}</span>
        </button>
      </div>
    </div>

    <!-- ECharts Container -->
    <div 
      class="relative w-full h-[420px] sm:h-[500px] rounded-xl overflow-hidden border transition-colors select-none cursor-grab active:cursor-grabbing"
      :class="isDarkTheme ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'"
      style="touch-action: none; -webkit-user-select: none; user-select: none;"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseUp"
      @wheel.prevent="handleWheel"
      @touchstart="handleTouchStart"
      @touchmove.prevent="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <!-- Cambodia Hub Badge -->
      <div 
        class="absolute top-3 left-3 z-10 backdrop-blur-xs px-3 py-1.5 rounded-xl border text-xs flex items-center gap-2 shadow-xs transition-colors"
        :class="isDarkTheme ? 'bg-slate-900/90 border-slate-700 text-slate-200' : 'bg-white/95 border-slate-200 text-slate-800'"
      >
        <span class="relative flex h-2.5 w-2.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
        </span>
        <span class="font-bold" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">Origin: Cambodia</span>
        <span class="text-slate-400 text-[11px] font-sans">(កម្ពុជា)</span>
      </div>

      <!-- Active Metric Legend Badge -->
      <div 
        class="absolute top-3 right-3 z-10 backdrop-blur-xs px-3 py-1.5 rounded-xl border text-xs shadow-xs transition-colors"
        :class="isDarkTheme ? 'bg-slate-900/90 border-slate-700 text-slate-300' : 'bg-white/95 border-slate-200 text-slate-700'"
      >
        <span class="text-slate-400">Scale: </span>
        <strong :class="activeMetric === 'VOLUME' ? (isDarkTheme ? 'text-sky-400' : 'text-sky-600') : (isDarkTheme ? 'text-amber-400' : 'text-amber-600')">
          {{ activeMetric === 'VOLUME' ? 'Volume (kg / Tonnes)' : 'Value ($k / $M USD)' }}
        </strong>
      </div>


      <!-- In-Map Country Intelligence Floating Card (Triggered by Map Click) -->
      <div
        v-if="selectedCountry"
        class="absolute bottom-4 left-4 z-20 backdrop-blur-md border p-4 rounded-xl shadow-xl max-w-xs w-full transition-all animate-in fade-in"
        :class="isDarkTheme ? 'bg-slate-900/95 border-slate-700 text-white' : 'bg-white/98 border-slate-200 text-slate-900'"
      >
        <div class="flex items-center justify-between pb-2 border-b mb-2.5" :class="isDarkTheme ? 'border-slate-800' : 'border-slate-100'">
          <div class="flex items-center gap-2">
            <span class="text-xl">{{ getCountryFlag(selectedCountry.country) }}</span>
            <div>
              <h4 class="font-bold text-sm leading-tight" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
                {{ getDisplayCountryName(selectedCountry.country) }}
              </h4>
              <span class="text-[10px] text-slate-400 font-sans">Destination Partner</span>
            </div>
          </div>
          <button
            @click="closeSelectedCountry"
            class="w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold transition-colors"
            :class="isDarkTheme ? 'bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white' : 'bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900'"
            title="Close country details"
          >
            ✕
          </button>
        </div>

        <div class="space-y-2 text-xs">
          <div class="flex items-center justify-between p-2 rounded-lg border" :class="isDarkTheme ? 'bg-slate-800/60 border-slate-700/50' : 'bg-slate-50 border-slate-100'">
            <span class="text-slate-500">Export Revenue:</span>
            <div class="text-right">
              <strong class="font-bold block" :class="isDarkTheme ? 'text-amber-400' : 'text-amber-600'">{{ formatRevenueUsd(selectedCountry.val_usd) }}</strong>
              <span class="text-[10px] font-semibold" :class="isDarkTheme ? 'text-emerald-400' : 'text-emerald-600'">{{ countrySharePct(selectedCountry) }}% Share</span>
            </div>
          </div>

          <div class="flex items-center justify-between p-2 rounded-lg border" :class="isDarkTheme ? 'bg-slate-800/60 border-slate-700/50' : 'bg-slate-50 border-slate-100'">
            <span class="text-slate-500">Export Volume:</span>
            <strong class="font-bold" :class="isDarkTheme ? 'text-sky-300' : 'text-sky-700'">{{ formatVolumeKg(selectedCountry.weight_kg) }}</strong>
          </div>

          <!-- Country-Specific Average Price -->
          <div class="flex items-center justify-between p-2 rounded-lg border" :class="isDarkTheme ? 'bg-emerald-950/40 border-emerald-800/40' : 'bg-emerald-50 border-emerald-200'">
            <span class="font-semibold" :class="isDarkTheme ? 'text-emerald-300' : 'text-emerald-800'">Country Avg Price:</span>
            <div class="text-right">
              <strong class="font-mono font-bold block" :class="isDarkTheme ? 'text-emerald-400' : 'text-emerald-700'">
                ${{ countryAvgPriceUsd(selectedCountry) }}/kg
              </strong>
              <span class="text-[10px]" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
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
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
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
import {
  Globe as GlobeIcon,
} from 'lucide-vue-next';
import worldGeoJson from '../../assets/world.json';
import type { MarketBreakdownItem } from '../../types/dataset';
import {
  getCountryMeta,
  getCountryFlag,
  getDisplayCountryName,
  isSameCountry,
  CAMBODIA_COORDS
} from '../../utils/countryRegistry';

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

// Register standard Apache ECharts world map GeoJSON
echarts.registerMap('world', worldGeoJson as any);

const props = defineProps<{
  title?: string;
  marketData: MarketBreakdownItem[];
  exchangeRate?: number;
}>();

const chartRef = ref<any>(null);
const activeMetric = ref<'VOLUME' | 'REVENUE'>('VOLUME');
const isDarkTheme = ref<boolean>(false);
const selectedCountry = ref<MarketBreakdownItem | null>(null);

// Interactive Drag / Pan & Touch Handling
const isDragging = ref<boolean>(false);
const hasMoved = ref<boolean>(false);
let startX = 0;
let startY = 0;
let lastX = 0;
let lastY = 0;

let touchStartX = 0;
let touchStartY = 0;
let touchLastX = 0;
let touchLastY = 0;
let touchStartDist = 0;

let resizeObserver: ResizeObserver | null = null;

const getChartInstance = () => {
  if (!chartRef.value) return null;
  return (chartRef.value as any).chart || chartRef.value;
};

const resizeChart = () => {
  const inst = getChartInstance();
  if (inst && typeof inst.resize === 'function') {
    inst.resize();
  }
};

onMounted(() => {
  window.addEventListener('resize', resizeChart);
  nextTick(() => {
    resizeChart();
  });
  setTimeout(resizeChart, 50);
  setTimeout(resizeChart, 200);
  setTimeout(resizeChart, 500);
});

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart);
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
});

const panMap = (dx: number, dy: number) => {
  const inst = getChartInstance();
  if (!inst || typeof inst.dispatchAction !== 'function') return;
  inst.dispatchAction({
    type: 'geoRoam',
    componentType: 'geo',
    dx,
    dy,
  });
};

const handleMouseDown = (e: MouseEvent) => {
  if (e.button !== 0) return;
  isDragging.value = true;
  hasMoved.value = false;
  startX = e.clientX;
  startY = e.clientY;
  lastX = e.clientX;
  lastY = e.clientY;
};

const handleMouseMove = (e: MouseEvent) => {
  if (!isDragging.value) return;
  const dx = e.clientX - lastX;
  const dy = e.clientY - lastY;
  if (Math.hypot(e.clientX - startX, e.clientY - startY) > 4) {
    hasMoved.value = true;
  }
  lastX = e.clientX;
  lastY = e.clientY;
  panMap(dx, dy);
};

const handleMouseUp = () => {
  isDragging.value = false;
  setTimeout(() => {
    hasMoved.value = false;
  }, 50);
};

const handleWheel = (e: WheelEvent) => {
  const inst = getChartInstance();
  if (!inst || typeof inst.dispatchAction !== 'function') return;
  const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
  const rect = (e.currentTarget as HTMLElement)?.getBoundingClientRect?.() || { left: 0, top: 0 };
  const originX = e.clientX - rect.left;
  const originY = e.clientY - rect.top;
  inst.dispatchAction({
    type: 'geoRoam',
    componentType: 'geo',
    zoom: zoomFactor,
    originX,
    originY,
  });
};

const handleTouchStart = (e: TouchEvent) => {
  if (e.touches.length === 1) {
    hasMoved.value = false;
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
    touchLastX = touchStartX;
    touchLastY = touchStartY;
  } else if (e.touches.length === 2) {
    const dx = e.touches[0].clientX - e.touches[1].clientX;
    const dy = e.touches[0].clientY - e.touches[1].clientY;
    touchStartDist = Math.hypot(dx, dy);
  }
};

const handleTouchMove = (e: TouchEvent) => {
  const inst = getChartInstance();
  if (!inst || typeof inst.dispatchAction !== 'function') return;
  if (e.touches.length === 1) {
    const curX = e.touches[0].clientX;
    const curY = e.touches[0].clientY;
    const dx = curX - touchLastX;
    const dy = curY - touchLastY;
    if (Math.hypot(curX - touchStartX, curY - touchStartY) > 6) {
      hasMoved.value = true;
    }
    touchLastX = curX;
    touchLastY = curY;
    panMap(dx, dy);
  } else if (e.touches.length === 2) {
    const dx = e.touches[0].clientX - e.touches[1].clientX;
    const dy = e.touches[0].clientY - e.touches[1].clientY;
    const dist = Math.hypot(dx, dy);
    if (touchStartDist > 0 && dist > 0) {
      const zoom = dist / touchStartDist;
      const midX = (e.touches[0].clientX + e.touches[1].clientX) / 2;
      const midY = (e.touches[0].clientY + e.touches[1].clientY) / 2;
      const rect = (e.currentTarget as HTMLElement)?.getBoundingClientRect?.() || { left: 0, top: 0 };
      inst.dispatchAction({
        type: 'geoRoam',
        componentType: 'geo',
        zoom: zoom > 1 ? 1.05 : 0.95,
        originX: midX - rect.left,
        originY: midY - rect.top,
      });
      touchStartDist = dist;
    }
  }
};

const handleTouchEnd = () => {
  touchStartDist = 0;
  setTimeout(() => {
    hasMoved.value = false;
  }, 50);
};

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

const closeSelectedCountry = () => {
  selectedCountry.value = null;
  const inst = getChartInstance();
  if (inst && typeof inst.dispatchAction === 'function') {
    inst.dispatchAction({ type: 'hideTip' });
  }
};

const onMapClick = (params: any) => {
  if (hasMoved.value) return;

  const inst = getChartInstance();
  if (inst && typeof inst.dispatchAction === 'function') {
    inst.dispatchAction({ type: 'hideTip' });
  }

  if (params.data?.rawMarket) {
    selectedCountry.value = params.data.rawMarket;
  } else if (params.name) {
    const matched = props.marketData.find(m => isSameCountry(m.country, params.name));
    if (matched) {
      selectedCountry.value = matched;
    }
  }
};

// Compute ECharts Option with registered 'world' GeoJSON
const mapChartOption = computed(() => {
  const mktList = props.marketData || [];
  const isDark = isDarkTheme.value;

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
          color: isDark ? '#f8fafc' : '#0f172a',
          fontSize: 10,
          fontWeight: 'bold',
          textBorderColor: isDark ? '#090d16' : '#ffffff',
          textBorderWidth: 3,
          distance: 6,
        },
        itemStyle: {
          color: activeMetric.value === 'VOLUME'
            ? (isDark ? '#38bdf8' : '#0284c7')
            : (isDark ? '#fbbf24' : '#d97706'),
          borderColor: '#ffffff',
          borderWidth: 1.5,
          shadowBlur: isDark ? 14 : 6,
          shadowColor: activeMetric.value === 'VOLUME' 
            ? (isDark ? 'rgba(56, 189, 248, 0.8)' : 'rgba(2, 132, 199, 0.4)')
            : (isDark ? 'rgba(251, 191, 36, 0.8)' : 'rgba(217, 119, 6, 0.4)'),
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
    backgroundColor: isDark ? '#090d16' : '#f8fafc',
    tooltip: {
      show: false,
    },
    geo: {
      map: 'world',
      roam: true,
      scaleLimit: { min: 0.8, max: 15 },
      zoom: 1.18,
      center: [55, 20],
      label: {
        show: false,
        emphasis: {
          show: true,
          color: isDark ? '#ffffff' : '#0f172a',
          fontSize: 10,
        }
      },
      itemStyle: {
        areaColor: isDark ? '#1e293b' : '#e2e8f0',
        borderColor: isDark ? '#334155' : '#cbd5e1',
        borderWidth: 0.8,
      },
      emphasis: {
        itemStyle: {
          areaColor: isDark ? '#0284c7' : '#bae6fd',
          borderColor: isDark ? '#38bdf8' : '#0284c7',
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
        z: 2,
        silent: true,
        effect: {
          show: true,
          period: 4,
          trailLength: 0.25,
          symbol: 'arrow',
          symbolSize: 6,
          color: activeMetric.value === 'VOLUME'
            ? (isDark ? '#38bdf8' : '#0284c7')
            : (isDark ? '#fbbf24' : '#d97706'),
        },
        lineStyle: {
          color: activeMetric.value === 'VOLUME'
            ? (isDark ? 'rgba(56, 189, 248, 0.45)' : 'rgba(2, 132, 199, 0.45)')
            : (isDark ? 'rgba(251, 191, 36, 0.45)' : 'rgba(217, 119, 6, 0.45)'),
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
        z: 3,
        data: scatterPoints,
      },
      // Pulsing Cambodia Origin Hub
      {
        name: 'Cambodia Hub',
        type: 'effectScatter',
        coordinateSystem: 'geo',
        z: 4,
        silent: true,
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
