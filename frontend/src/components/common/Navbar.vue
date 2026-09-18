<template>
  <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      
      <!-- Full Size Brand Logo -->
      <router-link to="/" class="flex items-center gap-3 hover:opacity-90 transition-opacity">
        <img 
          src="/admit-trading.png" 
          alt="ADMIT TRADING" 
          class="h-8 sm:h-9 md:h-10 w-auto object-contain max-w-[200px] sm:max-w-[240px]" 
        />
        <div class="hidden lg:block pl-3 border-l border-slate-200">
          <span class="text-xs px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 font-semibold">Intelligence</span>
          <p class="text-[11px] text-slate-500 mt-0.5">Agricultural Export Analytics</p>
        </div>
      </router-link>

      <!-- Center Nav Links -->
      <nav class="hidden md:flex items-center gap-2">
        <router-link
          to="/"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors"
          :class="$route.path === '/' ? 'bg-sky-50 text-sky-700 font-bold border border-sky-200' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'"
        >
          Macro Overview
        </router-link>
        <router-link
          to="/compare"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5"
          :class="$route.path === '/compare' ? 'bg-sky-50 text-sky-700 font-bold border border-sky-200' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'"
        >
          <span>⚖️ Compare HS8</span>
        </router-link>
      </nav>

      <!-- Center / Right Controls -->
      <div class="flex items-center gap-4">
        
        <!-- Live Reporting Period Indicator if loaded -->
        <div v-if="store.dashboardData && store.dashboardData.begin_date" class="hidden md:flex items-center gap-2 px-3 py-1 bg-sky-50 border border-sky-200 rounded-xl text-xs text-sky-900">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Period: <strong>{{ store.dashboardData.begin_date }} – {{ store.dashboardData.end_date }}</strong></span>
        </div>

        <!-- Exchange Rate Read-Only Display Badge -->
        <div class="flex items-center gap-2.5 bg-slate-50 px-3.5 py-1.5 rounded-xl border border-slate-200 shadow-xs">
          <span class="text-xs font-bold text-slate-500 uppercase">Rate:</span>
          <div class="flex items-center gap-1.5 text-xs font-bold text-slate-800">
            <span>$1 USD =</span>
            <span class="text-sky-600 font-extrabold">{{ (store.dashboardData?.exchange_rate || store.exchangeRate).toLocaleString() }}</span>
            <span class="text-slate-500 text-[11px]">៛ KHR</span>
          </div>

          <!-- Realtime status badge -->
          <span 
            v-if="store.dashboardData?.exchange_rate_info?.is_realtime" 
            class="hidden sm:inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800"
            :title="`Official exchange rate from MEF API for date ${store.dashboardData.exchange_rate_info.valid_date || 'Today'}`"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Live MEF{{ store.dashboardData.exchange_rate_info.valid_date ? ` (${store.dashboardData.exchange_rate_info.valid_date})` : '' }}
          </span>
        </div>

      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useDatasetStore } from '../../stores/datasetStore';

const store = useDatasetStore();
</script>
