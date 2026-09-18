<template>
  <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col justify-between">
    <!-- Header with Metric Toggle -->
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

      <!-- Metric Switcher: Volume vs Revenue -->
      <div class="flex items-center bg-slate-100 p-1 rounded-xl self-start sm:self-auto">
        <button
          @click="activeMetric = 'VOLUME'"
          class="px-3 py-1 text-xs font-bold rounded-lg transition-all"
          :class="activeMetric === 'VOLUME' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
        >
          📦 Volume (បរិមាណ)
        </button>
        <button
          @click="activeMetric = 'REVENUE'"
          class="px-3 py-1 text-xs font-bold rounded-lg transition-all"
          :class="activeMetric === 'REVENUE' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
        >
          💰 Revenue (ចំណូល $)
        </button>
      </div>
    </div>

    <!-- ECharts Container -->
    <div class="relative w-full h-[400px] sm:h-[480px] rounded-xl overflow-hidden bg-slate-950 border border-slate-800">
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
        <span class="text-slate-400">Displaying: </span>
        <strong :class="activeMetric === 'VOLUME' ? 'text-sky-400' : 'text-amber-400'">
          {{ activeMetric === 'VOLUME' ? '📦 Export Volume' : '💰 Export Revenue ($USD)' }}
        </strong>
      </div>

      <v-chart
        ref="chartRef"
        class="w-full h-full"
        :option="mapChartOption"
        autoresize
      />
    </div>

    <!-- Bottom Destination Market Summary Pills -->
    <div class="mt-4 pt-3 border-t border-slate-100">
      <div class="flex items-center justify-between text-xs text-slate-500 mb-2">
        <span class="font-semibold text-slate-700">Top Destination Markets ({{ marketData.length }} countries):</span>
        <span class="text-[11px] text-slate-400">Hover country on map for trade statistics</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <div
          v-for="mkt in marketData.slice(0, 10)"
          :key="mkt.country"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 border border-slate-200/80 text-xs"
        >
          <span class="font-bold text-slate-800">{{ getCountryFlag(mkt.country) }} {{ getDisplayCountryName(mkt.country) }}</span>
          <span class="text-slate-400">|</span>
          <span class="font-semibold" :class="activeMetric === 'VOLUME' ? 'text-sky-700' : 'text-amber-700'">
            {{ activeMetric === 'VOLUME' ? formatVolumeKg(mkt.weight_kg) : formatRevenueUsd(mkt.val_usd) }}
          </span>
          <span class="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
            {{ mkt.share_pct ? mkt.share_pct.toFixed(1) : ((mkt.val_usd / Math.max(1, totalValUsd)) * 100).toFixed(1) }}%
          </span>
        </div>
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

// Complete Dictionary: Khmer Country Names -> English Standard Name + GPS Coordinates + Flag
interface CountryMeta {
  en: string;
  coords: [number, number];
  flag: string;
}

const COUNTRY_REGISTRY: Record<string, CountryMeta> = {
  // Khmer Names from dataset
  'វៀតណាម': { en: 'Vietnam', coords: [106.6297, 10.8231], flag: '🇻🇳' },
  'ចិន': { en: 'China', coords: [116.4074, 39.9042], flag: '🇨🇳' },
  'ថៃ': { en: 'Thailand', coords: [100.5018, 13.7563], flag: '🇹🇭' },
  'ឥណ្ឌា': { en: 'India', coords: [77.2090, 28.6139], flag: '🇮🇳' },
  'ជប៉ុន': { en: 'Japan', coords: [139.6917, 35.6895], flag: '🇯🇵' },
  'កូរ៉េខាងត្បូង': { en: 'South Korea', coords: [126.9780, 37.5665], flag: '🇰🇷' },
  'កូរ៉េ': { en: 'South Korea', coords: [126.9780, 37.5665], flag: '🇰🇷' },
  'តៃវ៉ាន់': { en: 'Taiwan', coords: [121.5654, 25.0330], flag: '🇹🇼' },
  'អាមេរិក (សហរដ្ឋ)': { en: 'United States', coords: [-95.7129, 37.0902], flag: '🇺🇸' },
  'សហរដ្ឋអាមេរិក': { en: 'United States', coords: [-95.7129, 37.0902], flag: '🇺🇸' },
  'បារាំង': { en: 'France', coords: [2.3522, 48.8566], flag: '🇫🇷' },
  'អាល្លឺម៉ង់': { en: 'Germany', coords: [13.4050, 52.5200], flag: '🇩🇪' },
  'ហូឡង់': { en: 'Netherlands', coords: [4.9041, 52.3676], flag: '🇳🇱' },
  'ហ្វាំងឡង់': { en: 'Finland', coords: [25.7482, 61.9241], flag: '🇫🇮' },
  'អង់គ្លេស (ចក្រភព)': { en: 'United Kingdom', coords: [-0.1278, 51.5074], flag: '🇬🇧' },
  'អង់គ្លេស': { en: 'United Kingdom', coords: [-0.1278, 51.5074], flag: '🇬🇧' },
  'កាណាដា': { en: 'Canada', coords: [-75.6972, 45.4215], flag: '🇨🇦' },
  'អូស្ត្រាលី': { en: 'Australia', coords: [149.1300, -35.2809], flag: '🇦🇺' },
  'ម៉ាឡេស៊ី': { en: 'Malaysia', coords: [101.6869, 3.1390], flag: '🇲🇾' },
  'សិង្ហបុរី': { en: 'Singapore', coords: [103.8198, 1.3521], flag: '🇸🇬' },
  'ហ៊្វីលីពីន': { en: 'Philippines', coords: [120.9842, 14.5995], flag: '🇵🇭' },
  'ហុងកុង': { en: 'Hong Kong', coords: [114.1694, 22.3193], flag: '🇭🇰' },
  'រុស្ស៊ី': { en: 'Russia', coords: [37.6173, 55.7558], flag: '🇷🇺' },
  'ស្វ៊ីស': { en: 'Switzerland', coords: [7.4474, 46.9480], flag: '🇨🇭' },
  'បែលហ្ស៊ិក': { en: 'Belgium', coords: [4.3517, 50.8503], flag: '🇧🇪' },
  'អេស្ប៉ាញ': { en: 'Spain', coords: [-3.7038, 40.4168], flag: '🇪🇸' },
  'អ៊ីតាលី': { en: 'Italy', coords: [12.4964, 41.9028], flag: '🇮🇹' },
  'ប៉ូឡូញ': { en: 'Poland', coords: [21.0122, 52.2297], flag: '🇵🇱' },
  'ដាណឺម៉ាក': { en: 'Denmark', coords: [12.5683, 55.6761], flag: '🇩🇰' },
  'ន័រវែស': { en: 'Norway', coords: [10.7522, 59.9139], flag: '🇳🇴' },
  'ស៊ុយអែត': { en: 'Sweden', coords: [18.0686, 59.3293], flag: '🇸🇪' },
  'ឆែក (សាធារណរដ្ឋ)': { en: 'Czech Republic', coords: [14.4378, 50.0755], flag: '🇨🇿' },
  'ហុងគ្រី': { en: 'Hungary', coords: [19.0402, 47.4979], flag: '🇭🇺' },
  'អូទ្រីស': { en: 'Austria', coords: [16.3738, 48.2082], flag: '🇦🇹' },
  'ក្រូអាស៊ី': { en: 'Croatia', coords: [15.9819, 45.8150], flag: '🇭🇷' },
  'ព័រទុយហ្គាល់': { en: 'Portugal', coords: [-9.1393, 38.7223], flag: '🇵🇹' },
  'លីទុយអានី': { en: 'Lithuania', coords: [25.2797, 54.6872], flag: '🇱🇹' },
  'អៀរឡង់': { en: 'Ireland', coords: [-6.2603, 53.3498], flag: '🇮🇪' },
  'នូវែលសេឡង់': { en: 'New Zealand', coords: [174.7633, -36.8485], flag: '🇳🇿' },
  'កាហ្សាក់ស្ថាន': { en: 'Kazakhstan', coords: [71.4491, 51.1694], flag: '🇰🇿' },
  'បង់ក្លាដែស': { en: 'Bangladesh', coords: [90.4125, 23.8103], flag: '🇧🇩' },
  'អ៊ីស្រាអែល': { en: 'Israel', coords: [35.2137, 31.7683], flag: '🇮🇱' },
  'ហ្កាណា': { en: 'Ghana', coords: [-0.1870, 5.6037], flag: '🇬🇭' },
  'ម៉ាលី': { en: 'Mali', coords: [-8.0029, 12.6392], flag: '🇲🇱' },
  'ស្វាស៊ីឡង់': { en: 'Eswatini', coords: [31.1367, -26.4194], flag: '🇸🇿' },
  'កម្ពុជា': { en: 'Cambodia', coords: [104.9282, 11.5564], flag: '🇰🇭' },

  // English fallback aliases
  'Vietnam': { en: 'Vietnam', coords: [106.6297, 10.8231], flag: '🇻🇳' },
  'China': { en: 'China', coords: [116.4074, 39.9042], flag: '🇨🇳' },
  'Thailand': { en: 'Thailand', coords: [100.5018, 13.7563], flag: '🇹🇭' },
  'India': { en: 'India', coords: [77.2090, 28.6139], flag: '🇮🇳' },
  'Japan': { en: 'Japan', coords: [139.6917, 35.6895], flag: '🇯🇵' },
  'United States': { en: 'United States', coords: [-95.7129, 37.0902], flag: '🇺🇸' },
  'USA': { en: 'United States', coords: [-95.7129, 37.0902], flag: '🇺🇸' },
  'France': { en: 'France', coords: [2.3522, 48.8566], flag: '🇫🇷' },
  'Finland': { en: 'Finland', coords: [25.7482, 61.9241], flag: '🇫🇮' },
  'Germany': { en: 'Germany', coords: [13.4050, 52.5200], flag: '🇩🇪' },
  'Netherlands': { en: 'Netherlands', coords: [4.9041, 52.3676], flag: '🇳🇱' },
  'United Kingdom': { en: 'United Kingdom', coords: [-0.1278, 51.5074], flag: '🇬🇧' },
  'UK': { en: 'United Kingdom', coords: [-0.1278, 51.5074], flag: '🇬🇧' },
  'Cambodia': { en: 'Cambodia', coords: [104.9282, 11.5564], flag: '🇰🇭' },
};

const CAMBODIA_COORDS: [number, number] = [104.9282, 11.5564];

const getCountryMeta = (rawName: string): CountryMeta => {
  const clean = rawName.trim();
  if (COUNTRY_REGISTRY[clean]) return COUNTRY_REGISTRY[clean];
  for (const k in COUNTRY_REGISTRY) {
    if (clean.includes(k) || k.includes(clean)) return COUNTRY_REGISTRY[k];
  }
  return { en: rawName, coords: [100.0, 20.0], flag: '🌐' };
};

const getCountryFlag = (name: string): string => {
  return getCountryMeta(name).flag;
};

const getDisplayCountryName = (name: string): string => {
  const meta = getCountryMeta(name);
  return meta.en !== name ? `${meta.en} (${name})` : name;
};

const totalValUsd = computed(() => {
  return (props.marketData || []).reduce((acc, m) => acc + (m.val_usd || 0), 0);
});

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
      const size = Math.max(12, Math.min(42, Math.sqrt(val / maxVal) * 38));
      return {
        name: `${meta.flag} ${meta.en} (${m.country})`,
        value: [meta.coords[0], meta.coords[1], val],
        symbolSize: size,
        rawMarket: m,
        meta,
        itemStyle: {
          color: activeMetric.value === 'VOLUME' ? '#38bdf8' : '#fbbf24',
          borderColor: '#ffffff',
          borderWidth: 1.5,
          shadowBlur: 12,
          shadowColor: activeMetric.value === 'VOLUME' ? 'rgba(56, 189, 248, 0.7)' : 'rgba(251, 191, 36, 0.7)',
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
        const share = m.share_pct ? m.share_pct.toFixed(1) : ((m.val_usd / Math.max(1, totalValUsd.value)) * 100).toFixed(1);
        const unitPriceUsd = (m.val_usd / Math.max(1, m.weight_kg)).toFixed(2);
        const unitPriceKhr = Math.round(m.val_khr ? (m.val_khr / Math.max(1, m.weight_kg)) : (m.val_usd * (props.exchangeRate || 4000) / Math.max(1, m.weight_kg)));

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
                <span class="text-slate-400">Avg Unit Price:</span>
                <strong class="text-emerald-400 font-mono font-bold">$${unitPriceUsd}/kg <span class="text-[11px] text-slate-400 font-sans">(${unitPriceKhr.toLocaleString()} ៛)</span></strong>
              </div>
            </div>
          </div>
        `;
      }
    },
    geo: {
      map: 'world',
      roam: true,
      zoom: 1.35,
      center: [90, 25],
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
