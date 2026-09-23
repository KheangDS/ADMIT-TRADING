<template>
  <header class="bg-white/95 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-40 shadow-xs transition-all">
    <div class="max-w-[1600px] mx-auto px-3 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2 sm:gap-4">
      
      <!-- Brand Logo & Identity -->
      <router-link to="/" class="flex items-center gap-2 sm:gap-3 group hover:opacity-95 transition-opacity flex-shrink-0">
        <img 
          src="/admit-trading.png" 
          alt="ADMIT TRADING" 
          class="h-7 sm:h-9 md:h-10 w-auto object-contain max-w-[140px] sm:max-w-[200px] flex-shrink-0" 
        />
        <div class="hidden xl:flex items-center h-8 pl-3 border-l border-slate-200 gap-2">
          <span class="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200/80 whitespace-nowrap">
            <SparklesIcon class="w-3 h-3 text-sky-600" />
            Intelligence
          </span>
          <span class="text-[11px] text-slate-500 font-medium whitespace-nowrap">Agricultural Analytics</span>
        </div>
      </router-link>

      <!-- Center Segmented Nav Tabs (Desktop) -->
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

      <!-- Right Controls: Period & Live Currency & Mobile Menu Toggle -->
      <div class="flex items-center gap-1.5 sm:gap-2.5 flex-shrink-0">
        
        <!-- Live Reporting Period Indicator (Desktop) -->
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
          class="inline-flex items-center gap-1.5 sm:gap-2.5 px-2.5 sm:px-3.5 py-1.5 rounded-xl border shadow-2xs whitespace-nowrap transition-all"
          :class="isLiveRateOnline 
            ? 'bg-slate-50/95 border-slate-200 hover:border-emerald-300' 
            : 'bg-amber-50/80 border-amber-200 hover:border-amber-300'"
        >
          <!-- Currency Rate Display -->
          <div class="inline-flex items-center gap-1 text-[11px] sm:text-xs font-bold text-slate-800 whitespace-nowrap">
            <CoinsIcon class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
            <span class="text-slate-500 text-[10px] sm:text-[11px] font-medium hidden xs:inline">$1 =</span>
            <span class="text-sky-700 font-extrabold font-mono text-[11px] sm:text-xs">
              {{ (store.dashboardData?.exchange_rate || store.exchangeRate).toLocaleString() }}
            </span>
            <span class="text-slate-400 text-[10px] sm:text-[11px] font-medium">៛</span>
          </div>

          <!-- Vertical Divider (Hidden on very small screens) -->
          <div class="hidden sm:block h-3.5 w-px bg-slate-200 flex-shrink-0"></div>

          <!-- Real-Time Online Status with Date (Hidden on mobile phones) -->
          <span 
            v-if="isLiveRateOnline" 
            class="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 whitespace-nowrap cursor-help"
            :title="`Official exchange rate from Ministry of Economy and Finance (MEF)\nDate: ${formattedRateDate}\nRate: $1 USD = ${(store.dashboardData?.exchange_rate || store.exchangeRate).toLocaleString()} KHR`"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0"></span>
            <span>Live MEF • {{ formattedRateDate }}</span>
          </span>

          <!-- Fallback / API Failed Status (Hidden on mobile phones) -->
          <span 
            v-else 
            class="hidden sm:inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100/90 text-amber-800 border border-amber-300 whitespace-nowrap cursor-help"
            :title="rateErrorMessage"
          >
            <AlertCircleIcon class="w-3 h-3 text-amber-600 flex-shrink-0" />
            <span>Fallback (4,000 ៛)</span>
          </span>
        </div>

        <!-- Mobile Navigation Menu Toggle Button (Visible on < md) -->
        <button
          @click="isMobileMenuOpen = !isMobileMenuOpen"
          type="button"
          class="md:hidden cursor-pointer p-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 transition-colors shadow-2xs"
          :aria-expanded="isMobileMenuOpen"
          aria-label="Toggle Navigation Menu"
        >
          <MenuIcon v-if="!isMobileMenuOpen" class="w-5 h-5 text-slate-700" />
          <XIcon v-else class="w-5 h-5 text-slate-700" />
        </button>

      </div>
    </div>

    <!-- Mobile Dropdown Navigation Menu (Animated Dropdown on < md) -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform -translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-2 opacity-0"
    >
      <div 
        v-if="isMobileMenuOpen" 
        class="md:hidden border-t border-slate-100 bg-white/98 backdrop-blur-xl px-4 py-3 shadow-lg space-y-2 animate-in fade-in"
      >
        <!-- Nav Links -->
        <div class="grid grid-cols-2 gap-2">
          <router-link
            to="/"
            @click="isMobileMenuOpen = false"
            class="flex items-center justify-center gap-2 p-2.5 rounded-xl text-xs font-bold transition-all border"
            :class="$route.path === '/' 
              ? 'bg-sky-50 text-sky-700 border-sky-200 shadow-2xs' 
              : 'bg-slate-50 text-slate-700 border-slate-200/80 hover:bg-slate-100'"
          >
            <LayoutDashboardIcon class="w-4 h-4 text-sky-600" />
            <span>Overview</span>
          </router-link>

          <router-link
            to="/compare"
            @click="isMobileMenuOpen = false"
            class="flex items-center justify-center gap-2 p-2.5 rounded-xl text-xs font-bold transition-all border"
            :class="$route.path === '/compare' 
              ? 'bg-sky-50 text-sky-700 border-sky-200 shadow-2xs' 
              : 'bg-slate-50 text-slate-700 border-slate-200/80 hover:bg-slate-100'"
          >
            <ArrowLeftRightIcon class="w-4 h-4 text-sky-600" />
            <span>Compare</span>
          </router-link>
        </div>

        <!-- Period & Exchange Rate Details for Mobile -->
        <div class="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
          <div class="flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full" :class="isLiveRateOnline ? 'bg-emerald-500' : 'bg-amber-500'"></span>
            <span>MEF {{ isLiveRateOnline ? `Live (${formattedRateDate})` : 'Offline' }}</span>
          </div>
          <div v-if="store.dashboardData && store.dashboardData.begin_date" class="font-mono text-slate-600 font-semibold">
            {{ store.dashboardData.begin_date }} – {{ store.dashboardData.end_date }}
          </div>
        </div>
      </div>
    </transition>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  LayoutDashboard as LayoutDashboardIcon,
  ArrowLeftRight as ArrowLeftRightIcon,
  Calendar as CalendarIcon,
  Coins as CoinsIcon,
  Sparkles as SparklesIcon,
  AlertCircle as AlertCircleIcon,
  Menu as MenuIcon,
  X as XIcon
} from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';

const store = useDatasetStore();
const isMobileMenuOpen = ref(false);

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
