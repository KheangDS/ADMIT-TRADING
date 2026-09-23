<template>
  <header class="bg-white/95 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-40 shadow-xs transition-all">
    <div class="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
      
      <!-- Brand Logo & Identity -->
      <router-link to="/" class="flex items-center gap-3 group hover:opacity-95 transition-opacity flex-shrink-0">
        <img 
          src="/admit-trading.png" 
          alt="ADMIT TRADING" 
          class="h-8 sm:h-9 md:h-10 w-auto object-contain max-w-[180px] sm:max-w-[220px] flex-shrink-0" 
        />
        <div class="hidden xl:flex items-center h-8 pl-3 border-l border-slate-200 gap-2">
          <span class="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200/80 whitespace-nowrap">
            <SparklesIcon class="w-3 h-3 text-sky-600" />
            Intelligence
          </span>
          <span class="text-[11px] text-slate-500 font-medium whitespace-nowrap">Agricultural Analytics</span>
        </div>
      </router-link>

      <!-- Center Segmented Nav Tabs -->
      <nav class="hidden md:inline-flex items-center p-1 bg-slate-100/90 rounded-xl border border-slate-200/80 gap-1 flex-shrink-0">
        <router-link
          to="/"
          class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all"
          :class="$route.path === '/' 
            ? 'bg-white text-sky-700 shadow-xs border border-slate-200/80' 
            : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'"
        >
          <LayoutDashboardIcon class="w-3.5 h-3.5 flex-shrink-0" :class="$route.path === '/' ? 'text-sky-600' : 'text-slate-400'" />
          <span>Overview</span>
        </router-link>
        
        <router-link
          to="/compare"
          class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all"
          :class="$route.path === '/compare' 
            ? 'bg-white text-sky-700 shadow-xs border border-slate-200/80' 
            : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'"
        >
          <ArrowLeftRightIcon class="w-3.5 h-3.5 flex-shrink-0" :class="$route.path === '/compare' ? 'text-sky-600' : 'text-slate-400'" />
          <span>Compare Commodities</span>
        </router-link>
      </nav>

      <!-- Right Controls: Period & Live Currency -->
      <div class="flex items-center gap-2.5 flex-shrink-0">
        
        <!-- Live Reporting Period Indicator -->
        <div 
          v-if="store.dashboardData && store.dashboardData.begin_date" 
          class="hidden lg:inline-flex items-center gap-2 px-3 py-1.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-700 shadow-2xs whitespace-nowrap"
        >
          <CalendarIcon class="w-3.5 h-3.5 text-sky-600 flex-shrink-0" />
          <span class="text-[11px] font-medium text-slate-500">Period:</span>
          <span class="font-bold text-slate-800 text-xs font-mono">{{ store.dashboardData.begin_date }} – {{ store.dashboardData.end_date }}</span>
        </div>

        <!-- Exchange Rate Capsule Badge with Live Date & Status Feedback -->
        <div 
          class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl border shadow-2xs whitespace-nowrap transition-all"
          :class="isLiveRateOnline 
            ? 'bg-slate-50/95 border-slate-200 hover:border-emerald-300' 
            : 'bg-amber-50/80 border-amber-200 hover:border-amber-300'"
        >
          <!-- Currency Rate Display -->
          <div class="inline-flex items-center gap-1.5 text-xs font-bold text-slate-800 whitespace-nowrap">
            <CoinsIcon class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
            <span class="text-slate-500 text-[11px] font-medium">$1 =</span>
            <span class="text-sky-700 font-extrabold font-mono text-xs">
              {{ (store.dashboardData?.exchange_rate || store.exchangeRate).toLocaleString() }}
            </span>
            <span class="text-slate-400 text-[11px] font-medium">៛ KHR</span>
          </div>

          <!-- Vertical Divider -->
          <div class="h-3.5 w-px bg-slate-200 flex-shrink-0"></div>

          <!-- Real-Time Online Status with Date -->
          <span 
            v-if="isLiveRateOnline" 
            class="inline-flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 whitespace-nowrap cursor-help"
            :title="`Official exchange rate from Ministry of Economy and Finance (MEF)\nDate: ${formattedRateDate}\nRate: $1 USD = ${(store.dashboardData?.exchange_rate || store.exchangeRate).toLocaleString()} KHR`"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0"></span>
            <span>Live MEF • {{ formattedRateDate }}</span>
          </span>

          <!-- Fallback / API Failed Status -->
          <span 
            v-else 
            class="inline-flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-amber-100/90 text-amber-800 border border-amber-300 whitespace-nowrap cursor-help"
            :title="rateErrorMessage"
          >
            <AlertCircleIcon class="w-3 h-3 text-amber-600 flex-shrink-0" />
            <span>MEF Offline • Fallback (4,000 ៛)</span>
          </span>
        </div>

      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { 
  LayoutDashboard as LayoutDashboardIcon,
  ArrowLeftRight as ArrowLeftRightIcon,
  Calendar as CalendarIcon,
  Coins as CoinsIcon,
  Sparkles as SparklesIcon,
  AlertCircle as AlertCircleIcon
} from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';

const store = useDatasetStore();

const isLiveRateOnline = computed(() => {
  return !!store.dashboardData?.exchange_rate_info?.is_realtime;
});

const formattedRateDate = computed(() => {
  const info = store.dashboardData?.exchange_rate_info;
  if (info?.valid_date) {
    try {
      const d = new Date(info.valid_date);
      if (!isNaN(d.getTime())) {
        return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
      }
      return info.valid_date;
    } catch {
      return info.valid_date;
    }
  }
  return new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
});

const rateErrorMessage = computed(() => {
  const msg = store.dashboardData?.exchange_rate_info?.error_message;
  return msg 
    ? `MEF Live API Notice: ${msg}\nUsing default standard rate: $1 USD = 4,000 KHR.`
    : 'Could not reach MEF Live Exchange Rate API. Using standard fallback rate: $1 USD = 4,000 KHR.';
});
</script>
