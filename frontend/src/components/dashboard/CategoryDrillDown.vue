<template>
  <div v-if="detail" class="space-y-8">
    
    <!-- Navigation Back & Executive Chapter Header -->
    <div class="bg-white p-5 sm:p-6 rounded-2xl border border-slate-100 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
      <div class="space-y-2">
        <button
          @click="goBack"
          class="cursor-pointer inline-flex items-center gap-2 px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 hover:text-slate-900 font-bold text-xs rounded-xl transition-all shadow-xs"
        >
          <ArrowLeftIcon class="w-4 h-4 text-slate-500" />
          <span>Back to Macro Overview</span>
        </button>

        <div class="flex items-center gap-2.5 flex-wrap pt-1">
          <span class="text-xs font-mono font-black px-2.5 py-1 rounded-lg bg-sky-100 text-sky-800 border border-sky-200">
            HS {{ detail.hs4_code }}
          </span>
          <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Commodity Chapter Drill-Down
          </span>
          <span 
            v-if="detail.revenue_share_pct" 
            class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60"
          >
            {{ detail.revenue_share_pct.toFixed(1) }}% of National Exports
          </span>
        </div>

        <div>
          <h1 class="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight leading-tight">
            {{ detail.title_en || hs4Category?.title_en || hs4Category?.official_title || detail.hs4_desc }}
          </h1>
          <p v-if="detail.title_km || hs4Category?.title_km" class="text-sm font-semibold text-slate-500 mt-0.5 font-sans">
            {{ detail.title_km || hs4Category?.title_km }}
          </p>
        </div>
      </div>

      <!-- Quick Action / Shortcut to Comparison -->
      <div class="flex items-center gap-2.5 self-stretch md:self-auto justify-end">
        <button
          @click="goToCompare"
          class="cursor-pointer flex items-center gap-2 px-4 py-2.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-bold text-xs rounded-xl border border-indigo-200/80 transition-all shadow-xs"
        >
          <ScaleIcon class="w-4 h-4 text-indigo-600" />
          <span>Compare Commodities</span>
        </button>
      </div>
    </div>

    <!-- Official Tariff Description Accordion / Note -->
    <div 
      v-if="detail.full_desc_en || detail.full_desc_km || detail.hs4_desc" 
      class="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 text-xs text-slate-600 space-y-1"
    >
      <div class="flex items-center gap-1.5 font-bold text-slate-700 uppercase tracking-wider text-[11px]">
        <InfoIcon class="w-3.5 h-3.5 text-sky-600" />
        <span>Official Harmonized System (HS) Chapter Definition</span>
      </div>
      <p class="text-slate-700 font-medium leading-relaxed">
        {{ detail.full_desc_en || detail.hs4_desc }}
      </p>
      <p v-if="detail.full_desc_km" class="text-slate-500 font-sans leading-relaxed pt-0.5">
        {{ detail.full_desc_km }}
      </p>
    </div>

    <!-- Chapter Executive 4 KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- KPI 1: Total Chapter Revenue -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-xs flex flex-col justify-between min-h-[116px]">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Chapter Revenue</span>
          <div class="w-8 h-8 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <DollarSignIcon class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-3 text-center">
          <div class="text-2xl font-black text-slate-900 tracking-tight leading-none">
            {{ formatRevenueDisplay(chapterTotalValUsd) }}
          </div>
          <div class="text-[11px] font-semibold text-slate-400 mt-1.5">
            ≈ {{ formatKhrBillions(chapterTotalValKhr) }}
          </div>
        </div>
      </div>

      <!-- KPI 2: Total Chapter Volume -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-xs flex flex-col justify-between min-h-[116px]">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Total Chapter Volume</span>
          <div class="w-8 h-8 rounded-xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
            <ScaleIcon class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-3 text-center">
          <div class="text-2xl font-black text-slate-900 tracking-tight leading-none">
            {{ formatVolumeDisplay(chapterTotalWeightTon) }}
          </div>
          <div class="text-[11px] font-semibold text-slate-400 mt-1.5">
            {{ (chapterTotalWeightTon * 1000).toLocaleString() }} kg export weight
          </div>
        </div>
      </div>

      <!-- KPI 3: Chapter Avg Unit Price -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-xs flex flex-col justify-between min-h-[116px]">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Average Unit Price</span>
          <div class="w-8 h-8 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <TrendingUpIcon class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-3 text-center">
          <div class="text-2xl font-black text-slate-900 tracking-tight leading-none">
            ${{ chapterAvgPriceUsd.toFixed(2) }} <span class="text-xs font-bold text-slate-500">/ kg</span>
          </div>
          <div class="text-[11px] font-semibold text-slate-400 mt-1.5">
            ≈ {{ Math.round(chapterAvgPriceKhr).toLocaleString() }} ៛ / kg
          </div>
        </div>
      </div>

      <!-- KPI 4: Destination Markets & HS8 Products Count -->
      <div class="bg-white p-5 rounded-2xl border border-slate-100 shadow-xs flex flex-col justify-between min-h-[116px]">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Markets & Products</span>
          <div class="w-8 h-8 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <GlobeIcon class="w-4 h-4" />
          </div>
        </div>
        <div class="mt-3 text-center">
          <div class="flex items-center justify-center gap-2">
            <span class="text-2xl font-black text-slate-900 tracking-tight leading-none">
              {{ detail.top_destinations?.length || detail.num_markets || 0 }}
            </span>
            <span class="text-[11px] font-bold px-1.5 py-0.5 rounded-md text-indigo-700 bg-indigo-50 border border-indigo-100">
              Markets
            </span>
            <span class="text-slate-300 font-bold">·</span>
            <span class="text-2xl font-black text-purple-900 tracking-tight leading-none">
              {{ detail.sub_products?.length || 0 }}
            </span>
            <span class="text-[11px] font-bold px-1.5 py-0.5 rounded-md text-purple-700 bg-purple-50 border border-purple-100">
              HS8
            </span>
          </div>
          <div class="text-[11px] font-semibold text-slate-400 mt-1.5">
            {{ detail.hhi_score ? `Market HHI = ${Math.round(detail.hhi_score)}` : 'Active trading destinations' }}
          </div>
        </div>
      </div>

    </div>

    <!-- Chapter Global Destination Map (World Map) -->
    <div v-if="mapMarketList.length > 0" class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 class="text-base font-bold text-slate-900">
            Global Destination Map for HS {{ detail.hs4_code }}
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">
            Interactive international trade distribution for this commodity chapter
          </p>
        </div>
        <span class="text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-100 px-3 py-1 rounded-lg self-start">
          {{ mapMarketList.length }} Buyer Countries
        </span>
      </div>

      <WorldExportMap
        :market-data="mapMarketList"
        :exchange-rate="store.exchangeRate"
      />
    </div>

    <!-- Sub-Products Breakdown Table (8-Digit HS Codes) -->
    <div class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 class="text-base font-bold text-slate-900">Sub-Products Breakdown (8-Digit HS Codes)</h3>
          <p class="text-xs text-slate-500 mt-0.5">
            Click any commodity row or the "View HS8 →" button to open dedicated micro-level analytics.
          </p>
        </div>
        <span class="text-xs font-semibold text-sky-700 bg-sky-50 border border-sky-100 px-3 py-1 rounded-lg self-start">
          {{ detail.sub_products.length }} HS8 Commodities in Chapter
        </span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
            <tr>
              <th class="p-3">HS 8-Digit Code</th>
              <th class="p-3">Product Name (English / ភាសាខ្មែរ)</th>
              <th class="p-3 text-right">Volume</th>
              <th class="p-3 text-right">Revenue ($ USD)</th>
              <th class="p-3 text-right">Chapter Share</th>
              <th class="p-3 text-right">Unit Price ($/kg)</th>
              <th class="p-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr 
              v-for="sp in detail.sub_products" 
              :key="sp.hs8_code" 
              @click="goToCommodity(sp.hs8_code)"
              class="hover:bg-sky-50/60 transition-colors cursor-pointer group"
            >
              <td class="p-3 font-mono font-bold text-sky-700 group-hover:underline">
                {{ sp.hs8_code }}
              </td>
              <td class="p-3">
                <span class="font-bold text-slate-900 block group-hover:text-sky-700 transition-colors">
                  {{ sp.name_en || sp.product_name || sp.hs8_desc }}
                </span>
                <span v-if="sp.name_km" class="text-[11px] text-slate-500 block font-sans mt-0.5">
                  {{ sp.name_km }}
                </span>
                <span v-else-if="sp.product_name && sp.product_name !== sp.hs8_desc" class="text-[11px] text-slate-400 block truncate max-w-md mt-0.5">
                  {{ sp.hs8_desc }}
                </span>
              </td>
              <td class="p-3 text-right text-slate-700 font-medium">
                {{ formatVolume(sp.weight_tonnes) }}
              </td>
              <td class="p-3 text-right font-bold text-slate-900">
                {{ formatRevenue(sp.val_usd) }}
              </td>
              <td class="p-3 text-right font-bold text-sky-600">
                {{ sp.revenue_share_pct ? `${sp.revenue_share_pct.toFixed(1)}%` : calculateSpShare(sp.val_usd) }}
              </td>
              <td class="p-3 text-right font-bold text-emerald-600">
                ${{ sp.unit_price_usd_per_kg.toFixed(2) }} / kg
              </td>
              <td class="p-3 text-center">
                <span class="inline-flex items-center gap-1 text-[11px] font-bold text-sky-600 group-hover:text-sky-800 bg-sky-50 group-hover:bg-sky-100 px-2.5 py-1 rounded-lg transition-colors">
                  <span>View HS8</span>
                  <ArrowRightIcon class="w-3.5 h-3.5" />
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Chapter Charts Grid (Powered by Interactive ChartCustomizer) -->
    <div v-if="detail.charts && detail.charts.length > 0" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <ChartCustomizer
        v-for="chart in detail.charts"
        :key="chart.chart_id"
        :chart-id="chart.chart_id"
        :title="chart.title"
        :chart-type="chart.chart_type"
        :data="chart.data"
        :ai-meaning="chart.ai_meaning"
      />
    </div>

    <!-- Destination Markets Ranked Table -->
    <div v-if="detail.top_destinations && detail.top_destinations.length > 0" class="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm">
      <div class="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
        <div>
          <h3 class="text-base font-bold text-slate-900">Top Export Destination Markets</h3>
          <p class="text-xs text-slate-500">Destination countries importing chapter HS {{ detail.hs4_code }} commodities</p>
        </div>
        <span class="text-xs font-semibold text-slate-600 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
          {{ detail.top_destinations.length }} Active Buyers
        </span>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
            <tr>
              <th class="p-3">Rank</th>
              <th class="p-3">Destination Country</th>
              <th class="p-3 text-right">Volume</th>
              <th class="p-3 text-right">Revenue ($ USD)</th>
              <th class="p-3 text-right">Revenue (KHR)</th>
              <th class="p-3 text-right">Market Share</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="(m, idx) in detail.top_destinations" :key="m.country" class="hover:bg-slate-50/80 transition-colors">
              <td class="p-3 font-mono font-bold text-slate-400">#{{ idx + 1 }}</td>
              <td class="p-3 font-bold text-slate-900 flex items-center gap-2">
                <span>{{ m.country }}</span>
              </td>
              <td class="p-3 text-right text-slate-700 font-medium">
                {{ formatVolume((m.weight_kg || 0) / 1000.0) }}
              </td>
              <td class="p-3 text-right font-bold text-slate-900">
                {{ formatRevenue(m.val_usd) }}
              </td>
              <td class="p-3 text-right font-mono text-slate-500">
                {{ formatKhrBillions(m.val_khr || m.val_usd * store.exchangeRate) }}
              </td>
              <td class="p-3 text-right font-bold text-sky-600">
                {{ (m.share_pct || 0).toFixed(1) }}%
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Chapter Strategic AI Action Plan -->
    <div v-if="detail.ai_strategy" class="p-6 bg-gradient-to-r from-sky-900 to-indigo-950 rounded-2xl text-white shadow-lg flex items-start gap-4">
      <div class="w-10 h-10 rounded-xl bg-sky-500/20 text-sky-300 flex items-center justify-center flex-shrink-0 border border-sky-400/30">
        <TargetIcon class="w-5 h-5 text-sky-300" />
      </div>
      <div>
        <h4 class="font-bold text-sky-300 uppercase text-xs tracking-wider">
          Chapter Strategic Recommendations & Policy Roadmap
        </h4>
        <p class="mt-1.5 text-sm text-slate-200 leading-relaxed font-normal">
          {{ detail.ai_strategy }}
        </p>
      </div>
    </div>

  </div>
  <div v-else class="text-center py-20 bg-white rounded-2xl border border-slate-100 p-8 space-y-3">
    <p class="text-base font-bold text-slate-700">Category not found or dataset is not loaded yet.</p>
    <p class="text-xs text-slate-400">Please ingest a trade dataset or return to the overview page.</p>
    <button
      @click="goBack"
      class="mt-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl transition-colors shadow-xs"
    >
      Return to Overview
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  ArrowLeft as ArrowLeftIcon, 
  ArrowRight as ArrowRightIcon, 
  Target as TargetIcon,
  DollarSign as DollarSignIcon,
  Scale as ScaleIcon,
  TrendingUp as TrendingUpIcon,
  Globe as GlobeIcon,
  Info as InfoIcon
} from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';
import ChartCustomizer from './ChartCustomizer.vue';
import WorldExportMap from './WorldExportMap.vue';
import type { MarketBreakdownItem } from '../../types/dataset';

const route = useRoute();
const router = useRouter();
const store = useDatasetStore();

const currentHs4Code = computed(() => {
  return (route.params.hs4code as string) || store.activeCategory || '0801';
});

onMounted(() => {
  if (route.params.hs4code) {
    store.selectCategory(route.params.hs4code as string);
  }
});

const detail = computed(() => {
  if (!store.dashboardData || !store.dashboardData.category_details) return null;
  return store.dashboardData.category_details[currentHs4Code.value] || null;
});

const hs4Category = computed(() => {
  if (!store.dashboardData || !store.dashboardData.hs4_categories) return null;
  return store.dashboardData.hs4_categories.find(c => c.hs4_code === currentHs4Code.value) || null;
});

const chapterTotalValUsd = computed(() => {
  if (detail.value?.total_val_usd) return detail.value.total_val_usd;
  if (hs4Category.value?.val_usd) return hs4Category.value.val_usd;
  return detail.value?.sub_products?.reduce((sum, sp) => sum + sp.val_usd, 0) || 0;
});

const chapterTotalValKhr = computed(() => {
  if (detail.value?.total_val_khr) return detail.value.total_val_khr;
  if (hs4Category.value?.val_khr) return hs4Category.value.val_khr;
  return chapterTotalValUsd.value * (store.exchangeRate || 4000);
});

const chapterTotalWeightTon = computed(() => {
  if (detail.value?.total_weight_ton) return detail.value.total_weight_ton;
  if (hs4Category.value?.weight_tonnes) return hs4Category.value.weight_tonnes;
  return detail.value?.sub_products?.reduce((sum, sp) => sum + sp.weight_tonnes, 0) || 0;
});

const chapterAvgPriceUsd = computed(() => {
  if (detail.value?.avg_price_usd_per_kg) return detail.value.avg_price_usd_per_kg;
  if (hs4Category.value?.unit_price_usd_per_kg) return hs4Category.value.unit_price_usd_per_kg;
  const wKg = chapterTotalWeightTon.value * 1000.0;
  return wKg > 0 ? (chapterTotalValUsd.value / wKg) : 0;
});

const chapterAvgPriceKhr = computed(() => {
  if (detail.value?.avg_price_khr_per_kg) return detail.value.avg_price_khr_per_kg;
  return chapterAvgPriceUsd.value * (store.exchangeRate || 4000);
});

const mapMarketList = computed<MarketBreakdownItem[]>(() => {
  if (detail.value?.top_destinations && detail.value.top_destinations.length > 0) {
    return detail.value.top_destinations.map(d => ({
      country: d.country,
      val_usd: d.val_usd,
      val_khr: d.val_khr || d.val_usd * (store.exchangeRate || 4000),
      weight_kg: d.weight_kg || 0,
      share_pct: d.share_pct || 0
    }));
  }
  return [];
});

const goBack = () => {
  store.selectCategory(null);
  router.push('/');
};

const goToCompare = () => {
  router.push('/compare');
};

const goToCommodity = (hs8Code: string) => {
  router.push(`/commodity/${hs8Code}`);
};

const calculateSpShare = (spVal: number): string => {
  const tot = chapterTotalValUsd.value;
  if (!tot || tot === 0) return '0.0%';
  return `${((spVal / tot) * 100).toFixed(1)}%`;
};

const formatRevenue = (valUsd: number): string => {
  if (!valUsd || valUsd === 0) return '$0 USD';
  if (valUsd < 1_000_000) {
    const kUsd = Math.round((valUsd / 1000) * 10) / 10;
    return `$${kUsd.toLocaleString()}k USD`;
  }
  return `$${(valUsd / 1e6).toFixed(2)}M USD`;
};

const formatRevenueDisplay = (valUsd: number): string => {
  if (!valUsd || valUsd === 0) return '$0';
  if (valUsd < 1_000_000) {
    const kUsd = Math.round((valUsd / 1000) * 10) / 10;
    return `$${kUsd.toLocaleString()}k`;
  }
  return `$${(valUsd / 1e6).toFixed(2)}M`;
};

const formatVolume = (tonnes: number): string => {
  if (!tonnes || tonnes === 0) return '0 Tonnes';
  if (tonnes < 1) {
    const kg = Math.round(tonnes * 1000 * 10) / 10;
    return `${kg.toLocaleString()} kg`;
  }
  return `${(Math.round(tonnes * 10) / 10).toLocaleString()} Tonnes`;
};

const formatVolumeDisplay = (tonnes: number): string => {
  if (!tonnes || tonnes === 0) return '0 t';
  if (tonnes < 1) {
    const kg = Math.round(tonnes * 1000 * 10) / 10;
    return `${kg.toLocaleString()} kg`;
  }
  if (tonnes >= 1_000_000) {
    return `${(tonnes / 1e6).toFixed(2)}M t`;
  }
  return `${(Math.round(tonnes * 10) / 10).toLocaleString()} t`;
};

const formatKhrBillions = (khr: number): string => {
  if (!khr || khr === 0) return '៛0 KHR';
  if (khr >= 1e12) {
    return `៛${(khr / 1e12).toFixed(2)}T KHR`;
  }
  if (khr >= 1e9) {
    return `៛${(khr / 1e9).toFixed(2)}B KHR`;
  }
  if (khr >= 1e6) {
    return `៛${(khr / 1e6).toFixed(2)}M KHR`;
  }
  return `៛${Math.round(khr).toLocaleString()} KHR`;
};
</script>
