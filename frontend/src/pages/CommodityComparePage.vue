<template>
  <div ref="containerRef" class="relative w-full h-[calc(100vh-100px)] min-h-[720px] rounded-3xl overflow-hidden bg-slate-950 border border-slate-800 shadow-2xl flex flex-col justify-between select-none">
    
    <!-- ==================== TOP FLOATING CONTROLS BAR ==================== -->
    <div class="absolute top-4 left-4 right-4 z-30 flex items-center justify-between pointer-events-none">
      
      <!-- Back Button & Title -->
      <div class="flex items-center gap-2.5 pointer-events-auto bg-slate-900/95 backdrop-blur-md border border-slate-700 px-3.5 py-2 rounded-2xl shadow-xl">
        <button
          @click="goBack"
          class="cursor-pointer flex items-center gap-1.5 text-slate-300 hover:text-white font-semibold text-xs transition-colors"
          title="Return to Main Dashboard"
        >
          <ArrowLeftIcon class="w-3.5 h-3.5" />
          <span>Back</span>
        </button>
        <span class="text-slate-600">|</span>
        <div class="flex items-center gap-1.5">
          <GlobeIcon class="w-4 h-4 text-sky-400" />
          <h2 class="text-xs font-bold text-white tracking-wide uppercase">
            Commodity Comparison Map
          </h2>
        </div>
      </div>

      <!-- Center Year Slicer -->
      <div class="pointer-events-auto flex items-center gap-2 bg-slate-900/95 backdrop-blur-md border border-slate-700 px-3 py-1.5 rounded-2xl shadow-xl text-white">
        <CalendarIcon class="w-3.5 h-3.5 text-sky-400" />
        <span class="text-xs font-bold text-slate-300">Year:</span>
        <div class="flex items-center gap-1 bg-slate-950 p-0.5 rounded-xl border border-slate-800 text-xs">
          <button
            @click="selectedYear = 'ALL'"
            class="cursor-pointer px-2.5 py-1 rounded-lg text-xs font-bold transition-all"
            :class="selectedYear === 'ALL' ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-400 hover:text-white'"
            title="Show aggregate trade data across all recorded years"
          >
            All Years
          </button>
          <button
            v-for="yr in availableYears"
            :key="yr"
            @click="selectedYear = yr.toString()"
            class="cursor-pointer px-2.5 py-1 rounded-lg text-xs font-bold transition-all"
            :class="selectedYear === yr.toString() ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-400 hover:text-white'"
            :title="`Filter comparison data for Year ${yr}`"
          >
            {{ yr }}
          </button>
        </div>
      </div>

      <!-- Right Fullscreen Toggle -->
      <div class="pointer-events-auto flex items-center gap-2 bg-slate-900/95 backdrop-blur-md border border-slate-700 px-3 py-2 rounded-2xl shadow-xl text-white">
        <button
          @click="toggleFullscreen"
          class="cursor-pointer flex items-center gap-1.5 text-slate-300 hover:text-white text-xs font-semibold transition-colors"
          :title="isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'"
        >
          <component :is="isFullscreen ? Minimize2Icon : Maximize2Icon" class="w-4 h-4 text-sky-400" />
          <span class="hidden sm:inline text-xs">{{ isFullscreen ? 'Exit Fullscreen' : 'Fullscreen' }}</span>
        </button>
      </div>

    </div>

    <!-- ==================== LEFT FLOATING OVERLAY: COMMODITY A & KPIS ==================== -->
    <div
      class="absolute top-16 left-4 z-20 w-84 max-w-[calc(50vw-1.5rem)] max-h-[calc(100%-8.5rem)] overflow-y-auto space-y-3 pr-1 pb-2 custom-scrollbar pointer-events-auto"
      @click.stop
    >
      
      <!-- Custom Multi-Commodity Checkbox Picker: Commodity A -->
      <div class="bg-slate-900/95 backdrop-blur-md p-4 rounded-2xl border-2 border-sky-500/60 shadow-2xl text-white space-y-2.5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-sky-400 animate-pulse"></span>
            Commodity A (ទំនិញ ទី១)
          </span>
          <span class="text-[10px] font-mono font-bold text-sky-300 bg-sky-950 border border-sky-800/80 px-2 py-0.5 rounded-md">
            {{ selectedCodesA.length }} Selected
          </span>
        </div>

        <!-- Custom Dropdown Trigger Button -->
        <button
          type="button"
          @click="openDropdownA = !openDropdownA; openDropdownB = false"
          class="cursor-pointer w-full bg-slate-950/90 hover:bg-slate-950 border-2 rounded-xl px-3.5 py-2.5 text-left flex items-center justify-between transition-all shadow-inner"
          :class="openDropdownA ? 'border-sky-400 ring-2 ring-sky-500/30' : 'border-slate-700 hover:border-sky-500/50'"
          :title="selectedCodesA.length === 1 && summaryA ? `[HS ${selectedCodesA[0]}] ${summaryA.name_en}${summaryA.name_km ? ' (' + summaryA.name_km + ')' : ''}` : (selectedCodesA.length > 1 ? selectedCommoditiesTooltipA : 'Choose commodities...')"
        >
          <div class="truncate flex-1 pr-2">
            <span v-if="selectedCodesA.length === 0" class="text-xs text-slate-400 italic">
              None Selected (Choose commodities...)
            </span>
            <span v-else-if="selectedCodesA.length === 1 && summaryA" class="font-bold text-xs text-white block truncate" :title="`[HS ${selectedCodesA[0]}] ${summaryA.name_en}`">
              [HS {{ selectedCodesA[0] }}] {{ summaryA.name_en }}
            </span>
            <span v-else class="font-bold text-xs text-sky-300 block truncate" :title="selectedCommoditiesTooltipA">
              🗂️ {{ selectedCodesA.length }} Commodities Selected (Multi-Crop)
            </span>
          </div>
          <ChevronDownIcon
            class="w-4 h-4 text-sky-400 flex-shrink-0 transition-transform duration-200"
            :class="{ 'rotate-180': openDropdownA }"
          />
        </button>

        <!-- Inline Expandable Checkbox Options List A -->
        <div
          v-if="openDropdownA"
          class="bg-slate-950/90 border border-sky-500/40 rounded-xl p-2.5 space-y-2 animate-in fade-in duration-150"
        >
          <!-- Search & Select Controls -->
          <div class="relative">
            <SearchIcon class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              v-model="searchA"
              type="text"
              placeholder="Search commodity name or HS code..."
              class="w-full pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              @click.stop
            />
          </div>

          <div class="flex items-center justify-between text-[11px] pb-1 border-b border-slate-800">
            <button
              type="button"
              @click="selectAllA"
              class="text-sky-400 font-bold hover:underline"
            >
              Select All ({{ commodityOptions.length }})
            </button>
            <button
              type="button"
              @click="clearA"
              class="text-slate-400 font-semibold hover:text-white"
            >
              Clear (None)
            </button>
          </div>

          <!-- Options Checklist -->
          <div class="max-h-56 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
            <div
              v-for="item in filteredOptionsA"
              :key="`opt-a-${item.hs8_code}`"
              @click="toggleCommodityA(item.hs8_code)"
              class="cursor-pointer flex items-center gap-2.5 p-2 rounded-xl border transition-all text-left group"
              :class="selectedCodesA.includes(item.hs8_code) ? 'bg-sky-950 border-sky-400 text-white shadow-xs' : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800 text-slate-300'"
              :title="`[HS ${item.hs8_code}] ${item.name_en}${item.name_km ? ' (' + item.name_km + ')' : ''}`"
            >
              <!-- Styled Checkbox Box -->
              <div
                class="w-4 h-4 rounded-md border flex items-center justify-center flex-shrink-0 transition-colors"
                :class="selectedCodesA.includes(item.hs8_code) ? 'bg-sky-500 border-sky-400 text-white' : 'border-slate-600 bg-slate-800'"
              >
                <CheckIcon v-if="selectedCodesA.includes(item.hs8_code)" class="w-3 h-3 stroke-[3]" />
              </div>

              <!-- Label & HS Code -->
              <div class="flex-1 truncate">
                <div class="flex items-center gap-1.5">
                  <span class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-800 text-sky-400">
                    HS {{ item.hs8_code }}
                  </span>
                  <span class="font-bold text-xs truncate text-white" :title="item.name_en">{{ item.name_en }}</span>
                </div>
                <span v-if="item.name_km" class="text-[10px] text-slate-400 block font-sans truncate mt-0.5" :title="item.name_km">
                  {{ item.name_km }}
                </span>
              </div>
            </div>

            <div v-if="filteredOptionsA.length === 0" class="text-center py-4 text-xs text-slate-500">
              No matching commodities
            </div>
          </div>

          <!-- Done Button -->
          <div class="pt-1.5 border-t border-slate-800 flex justify-end">
            <button
              type="button"
              @click="openDropdownA = false"
              class="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-bold transition-colors"
            >
              Done ({{ selectedCodesA.length }})
            </button>
          </div>
        </div>

        <div v-if="summaryA && selectedCodesA.length === 1 && !openDropdownA" class="text-xs text-slate-400 flex items-center justify-between pt-0.5" :title="`${summaryA.name_en} (${summaryA.name_km})`">
          <span class="truncate font-sans font-medium text-slate-300 text-[11px]" :title="summaryA.name_km">{{ summaryA.name_km }}</span>
          <router-link :to="`/commodity/${selectedCodesA[0]}`" class="text-sky-400 font-bold hover:underline ml-2 text-[11px] whitespace-nowrap" :title="`View deep-dive analytics for ${summaryA.name_en}`">
            Detail →
          </router-link>
        </div>

      </div>

      <!-- 5-Metric Dedicated KPI Panel A -->
      <div class="bg-slate-900/90 backdrop-blur-md p-3.5 rounded-2xl border border-sky-500/30 shadow-2xl text-white space-y-2">
        
        <!-- 1. Revenue $ -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-sky-200">
              <span>💵</span> Revenue ($USD)
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Scale: $k / $M</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ formatRevenue(summaryA?.total_val_usd || 0) }}
          </div>
        </div>

        <!-- 2. Volume -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-sky-200">
              <span>📦</span> Export Volume
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Scale: kg / Tonnes</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ formatVolumeKg(summaryA?.total_weight_kg || 0) }}
          </div>
        </div>

        <!-- 3. Transaction -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-sky-200">
              <span>📑</span> Transactions
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Declarations</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ summaryA?.total_transactions || 0 }} Shipments
          </div>
        </div>

        <!-- 4. Destination Markets -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-sky-200">
              <span>🌐</span> Destination Markets
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Active Partners</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ marketsA.length }} Countries
          </div>
        </div>

        <!-- 5. Avg Price (Suppressed if multi-crop or null) -->
        <div class="bg-sky-950/70 p-3 rounded-xl border border-sky-600/60">
          <div class="flex items-center justify-between text-xs text-sky-300 mb-0.5">
            <span class="font-bold flex items-center gap-1.5">
              <span>🏷️</span> Benchmark Avg Price
            </span>
            <span class="text-[10px] text-sky-400 font-sans">Unit Rate</span>
          </div>
          
          <div v-if="selectedCodesA.length === 1 && summaryA?.avg_price_usd_per_kg">
            <div class="text-base font-black text-sky-300 font-mono">
              ${{ summaryA.avg_price_usd_per_kg.toFixed(2) }} <span class="text-xs font-normal text-slate-400">/ kg</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-0.5 font-sans">
              ≈ {{ Math.round(summaryA.avg_price_khr_per_kg || summaryA.avg_price_usd_per_kg * 4000).toLocaleString() }} ៛/kg
            </div>
          </div>
          <div v-else-if="selectedCodesA.length > 1" class="text-xs font-semibold text-amber-300/90 font-mono pt-0.5">
            N/A (Multi-Crop Aggregate)
          </div>
          <div v-else class="text-xs text-slate-500 italic pt-0.5">
            — (No crop selected)
          </div>
        </div>

      </div>
    </div>

    <!-- ==================== RIGHT FLOATING OVERLAY: COMMODITY B & KPIS ==================== -->
    <div
      class="absolute top-16 right-4 z-20 w-84 max-w-[calc(50vw-1.5rem)] max-h-[calc(100%-8.5rem)] overflow-y-auto space-y-3 pr-1 pb-2 custom-scrollbar pointer-events-auto"
      @click.stop
    >
      
      <!-- Custom Multi-Commodity Checkbox Picker: Commodity B -->
      <div class="bg-slate-900/95 backdrop-blur-md p-4 rounded-2xl border-2 border-amber-500/60 shadow-2xl text-white space-y-2.5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse"></span>
            Commodity B (ទំនិញ ទី២)
          </span>
          <span class="text-[10px] font-mono font-bold text-amber-300 bg-amber-950 border border-amber-800/80 px-2 py-0.5 rounded-md">
            {{ selectedCodesB.length }} Selected
          </span>
        </div>

        <!-- Custom Dropdown Trigger Button -->
        <button
          type="button"
          @click="openDropdownB = !openDropdownB; openDropdownA = false"
          class="cursor-pointer w-full bg-slate-950/90 hover:bg-slate-950 border-2 rounded-xl px-3.5 py-2.5 text-left flex items-center justify-between transition-all shadow-inner"
          :class="openDropdownB ? 'border-amber-400 ring-2 ring-amber-500/30' : 'border-slate-700 hover:border-amber-500/50'"
          :title="selectedCodesB.length === 1 && summaryB ? `[HS ${selectedCodesB[0]}] ${summaryB.name_en}${summaryB.name_km ? ' (' + summaryB.name_km + ')' : ''}` : (selectedCodesB.length > 1 ? selectedCommoditiesTooltipB : 'Choose commodities...')"
        >
          <div class="truncate flex-1 pr-2">
            <span v-if="selectedCodesB.length === 0" class="text-xs text-slate-400 italic">
              None Selected (Choose commodities...)
            </span>
            <span v-else-if="selectedCodesB.length === 1 && summaryB" class="font-bold text-xs text-white block truncate" :title="`[HS ${selectedCodesB[0]}] ${summaryB.name_en}`">
              [HS {{ selectedCodesB[0] }}] {{ summaryB.name_en }}
            </span>
            <span v-else class="font-bold text-xs text-amber-300 block truncate" :title="selectedCommoditiesTooltipB">
              🗂️ {{ selectedCodesB.length }} Commodities Selected (Multi-Crop)
            </span>
          </div>
          <ChevronDownIcon
            class="w-4 h-4 text-amber-400 flex-shrink-0 transition-transform duration-200"
            :class="{ 'rotate-180': openDropdownB }"
          />
        </button>

        <!-- Inline Expandable Checkbox Options List B -->
        <div
          v-if="openDropdownB"
          class="bg-slate-950/90 border border-amber-500/40 rounded-xl p-2.5 space-y-2 animate-in fade-in duration-150"
        >
          <!-- Search & Select Controls -->
          <div class="relative">
            <SearchIcon class="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              v-model="searchB"
              type="text"
              placeholder="Search commodity name or HS code..."
              class="w-full pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              @click.stop
            />
          </div>

          <div class="flex items-center justify-between text-[11px] pb-1 border-b border-slate-800">
            <button
              type="button"
              @click="selectAllB"
              class="text-amber-400 font-bold hover:underline"
            >
              Select All ({{ commodityOptions.length }})
            </button>
            <button
              type="button"
              @click="clearB"
              class="text-slate-400 font-semibold hover:text-white"
            >
              Clear (None)
            </button>
          </div>

          <!-- Options Checklist -->
          <div class="max-h-56 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
            <div
              v-for="item in filteredOptionsB"
              :key="`opt-b-${item.hs8_code}`"
              @click="toggleCommodityB(item.hs8_code)"
              class="cursor-pointer flex items-center gap-2.5 p-2 rounded-xl border transition-all text-left group"
              :class="selectedCodesB.includes(item.hs8_code) ? 'bg-amber-950 border-amber-400 text-white shadow-xs' : 'bg-slate-900/60 border-slate-800 hover:bg-slate-800 text-slate-300'"
              :title="`[HS ${item.hs8_code}] ${item.name_en}${item.name_km ? ' (' + item.name_km + ')' : ''}`"
            >
              <!-- Styled Checkbox Box -->
              <div
                class="w-4 h-4 rounded-md border flex items-center justify-center flex-shrink-0 transition-colors"
                :class="selectedCodesB.includes(item.hs8_code) ? 'bg-amber-500 border-amber-400 text-white' : 'border-slate-600 bg-slate-800'"
              >
                <CheckIcon v-if="selectedCodesB.includes(item.hs8_code)" class="w-3 h-3 stroke-[3]" />
              </div>

              <!-- Label & HS Code -->
              <div class="flex-1 truncate">
                <div class="flex items-center gap-1.5">
                  <span class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-slate-800 text-amber-400">
                    HS {{ item.hs8_code }}
                  </span>
                  <span class="font-bold text-xs truncate text-white" :title="item.name_en">{{ item.name_en }}</span>
                </div>
                <span v-if="item.name_km" class="text-[10px] text-slate-400 block font-sans truncate mt-0.5" :title="item.name_km">
                  {{ item.name_km }}
                </span>
              </div>
            </div>

            <div v-if="filteredOptionsB.length === 0" class="text-center py-4 text-xs text-slate-500">
              No matching commodities
            </div>
          </div>

          <!-- Done Button -->
          <div class="pt-1.5 border-t border-slate-800 flex justify-end">
            <button
              type="button"
              @click="openDropdownB = false"
              class="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition-colors"
            >
              Done ({{ selectedCodesB.length }})
            </button>
          </div>
        </div>

        <div v-if="summaryB && selectedCodesB.length === 1 && !openDropdownB" class="text-xs text-slate-400 flex items-center justify-between pt-0.5" :title="`${summaryB.name_en} (${summaryB.name_km})`">
          <span class="truncate font-sans font-medium text-slate-300 text-[11px]" :title="summaryB.name_km">{{ summaryB.name_km }}</span>
          <router-link :to="`/commodity/${selectedCodesB[0]}`" class="text-amber-400 font-bold hover:underline ml-2 text-[11px] whitespace-nowrap" :title="`View deep-dive analytics for ${summaryB.name_en}`">
            Detail →
          </router-link>
        </div>

      </div>

      <!-- 5-Metric Dedicated KPI Panel B -->
      <div class="bg-slate-900/90 backdrop-blur-md p-3.5 rounded-2xl border border-amber-500/30 shadow-2xl text-white space-y-2">
        
        <!-- 1. Revenue $ -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-amber-200">
              <span>💵</span> Revenue ($USD)
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Scale: $k / $M</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ formatRevenue(summaryB?.total_val_usd || 0) }}
          </div>
        </div>

        <!-- 2. Volume -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-amber-200">
              <span>📦</span> Export Volume
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Scale: kg / Tonnes</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ formatVolumeKg(summaryB?.total_weight_kg || 0) }}
          </div>
        </div>

        <!-- 3. Transaction -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-amber-200">
              <span>📑</span> Transactions
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Declarations</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ summaryB?.total_transactions || 0 }} Shipments
          </div>
        </div>

        <!-- 4. Destination Markets -->
        <div class="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-0.5">
            <span class="font-semibold flex items-center gap-1.5 text-amber-200">
              <span>🌐</span> Destination Markets
            </span>
            <span class="text-[10px] text-slate-500 font-sans">Active Partners</span>
          </div>
          <div class="text-base font-black text-white font-mono">
            {{ marketsB.length }} Countries
          </div>
        </div>

        <!-- 5. Avg Price (Suppressed if multi-crop or null) -->
        <div class="bg-amber-950/70 p-3 rounded-xl border border-amber-600/60">
          <div class="flex items-center justify-between text-xs text-amber-300 mb-0.5">
            <span class="font-bold flex items-center gap-1.5">
              <span>🏷️</span> Benchmark Avg Price
            </span>
            <span class="text-[10px] text-amber-400 font-sans">Unit Rate</span>
          </div>
          
          <div v-if="selectedCodesB.length === 1 && summaryB?.avg_price_usd_per_kg">
            <div class="text-base font-black text-amber-300 font-mono">
              ${{ summaryB.avg_price_usd_per_kg.toFixed(2) }} <span class="text-xs font-normal text-slate-400">/ kg</span>
            </div>
            <div class="text-[11px] text-slate-400 mt-0.5 font-sans">
              ≈ {{ Math.round(summaryB.avg_price_khr_per_kg || summaryB.avg_price_usd_per_kg * 4000).toLocaleString() }} ៛/kg
            </div>
          </div>
          <div v-else-if="selectedCodesB.length > 1" class="text-xs font-semibold text-amber-300/90 font-mono pt-0.5">
            N/A (Multi-Crop Aggregate)
          </div>
          <div v-else class="text-xs text-slate-500 italic pt-0.5">
            — (No crop selected)
          </div>
        </div>

      </div>
    </div>

    <!-- ==================== FULLSCREEN ECHARTS MAP CANVAS ==================== -->
    <div class="relative w-full h-full flex-1" @click="closeDropdowns">
      
      <!-- Cambodia Hub Badge (Center Map) -->
      <div class="absolute bottom-16 left-4 z-10 bg-slate-900/90 backdrop-blur-xs px-2.5 py-1 rounded-xl border border-slate-700 text-[11px] text-slate-200 flex items-center gap-1.5 shadow-md">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        <span class="font-bold text-white">Origin: Cambodia 🇰🇭</span>
      </div>

      <!-- In-Map Floating Country Intelligence Comparison Card -->
      <div
        v-if="selectedMapCountry"
        class="absolute bottom-16 left-1/2 -translate-x-1/2 z-30 bg-slate-900/95 backdrop-blur-md border border-slate-700 p-4 rounded-2xl shadow-2xl text-white max-w-sm w-full animate-in fade-in"
        @click.stop
      >
        <div class="flex items-center justify-between pb-2 border-b border-slate-800 mb-2.5">
          <div class="flex items-center gap-2">
            <span class="text-xl">{{ getCountryFlag(selectedMapCountry.country) }}</span>
            <div>
              <h4 class="font-bold text-xs text-white leading-tight">
                {{ getDisplayCountryName(selectedMapCountry.country) }}
              </h4>
              <span class="text-[10px] text-slate-400">Destination Comparison</span>
            </div>
          </div>
          <button
            @click="selectedCountryName = null"
            class="cursor-pointer w-6 h-6 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center text-xs font-bold"
          >
            ✕
          </button>
        </div>

        <div class="space-y-2 text-xs">
          <!-- Comm A in this Country -->
          <div
            class="bg-sky-950/50 p-2 rounded-xl border border-sky-800/50 space-y-1"
            :title="selectedCodesA.length === 1 ? `[HS ${selectedCodesA[0]}] ${summaryA?.name_en || ''}` : selectedCommoditiesTooltipA"
          >
            <div class="flex justify-between items-center text-xs">
              <strong class="text-sky-300 font-bold truncate max-w-[190px]">
                🔵 A: {{ selectedCodesA.length === 1 ? (summaryA?.name_en || 'Comm A') : `Group A (${selectedCodesA.length} crops)` }}
              </strong>
              <span class="text-[11px] font-mono text-sky-400 font-bold">
                {{ selectedMapCountry.valA ? (selectedCodesA.length === 1 && selectedMapCountry.valA.weight_kg > 0 ? `$${(selectedMapCountry.valA.val_usd / selectedMapCountry.valA.weight_kg).toFixed(2)}/kg` : '') : 'No Export' }}
              </span>
            </div>
            <div v-if="selectedMapCountry.valA" class="flex justify-between text-[11px] text-slate-300">
              <span>{{ formatVolumeKg(selectedMapCountry.valA.weight_kg) }}</span>
              <strong class="text-white">{{ formatRevenue(selectedMapCountry.valA.val_usd) }}</strong>
            </div>
          </div>

          <!-- Comm B in this Country -->
          <div
            class="bg-amber-950/50 p-2 rounded-xl border border-amber-800/50 space-y-1"
            :title="selectedCodesB.length === 1 ? `[HS ${selectedCodesB[0]}] ${summaryB?.name_en || ''}` : selectedCommoditiesTooltipB"
          >
            <div class="flex justify-between items-center text-xs">
              <strong class="text-amber-300 font-bold truncate max-w-[190px]">
                🟠 B: {{ selectedCodesB.length === 1 ? (summaryB?.name_en || 'Comm B') : `Group B (${selectedCodesB.length} crops)` }}
              </strong>
              <span class="text-[11px] font-mono text-amber-400 font-bold">
                {{ selectedMapCountry.valB ? (selectedCodesB.length === 1 && selectedMapCountry.valB.weight_kg > 0 ? `$${(selectedMapCountry.valB.val_usd / selectedMapCountry.valB.weight_kg).toFixed(2)}/kg` : '') : 'No Export' }}
              </span>
            </div>
            <div v-if="selectedMapCountry.valB" class="flex justify-between text-[11px] text-slate-300">
              <span>{{ formatVolumeKg(selectedMapCountry.valB.weight_kg) }}</span>
              <strong class="text-white">{{ formatRevenue(selectedMapCountry.valB.val_usd) }}</strong>
            </div>
          </div>
        </div>
      </div>

      <!-- Main ECharts Component -->
      <v-chart
        ref="chartRef"
        class="w-full h-full cursor-pointer"
        :option="comparativeMapChartOption"
        @click="onMapPointClick"
        autoresize
      />
    </div>

    <!-- ==================== SEPARATE DUAL DESTINATIONS DOCKS (A & B) ==================== -->
    <div class="absolute bottom-3 left-4 right-4 z-20 pointer-events-none flex items-center justify-between gap-4">
      
      <!-- Left Dock: Commodity A Destinations Only -->
      <div
        v-if="marketsA.length > 0"
        class="pointer-events-auto bg-slate-900/95 backdrop-blur-md border border-sky-500/50 px-3.5 py-1.5 rounded-2xl shadow-xl max-w-[48%] flex items-center gap-2 text-xs text-white"
      >
        <div class="flex items-center gap-1.5 flex-shrink-0">
          <span class="w-2 h-2 rounded-full bg-sky-400"></span>
          <span class="font-bold text-sky-300 text-[11px]">A Destinations ({{ marketsA.length }}):</span>
        </div>
        <div class="flex items-center gap-1.5 overflow-x-auto py-0.5 custom-scrollbar flex-1">
          <button
            v-for="m in marketsA"
            :key="`bottom-a-${m.country}`"
            @click="selectMarketA(m)"
            class="cursor-pointer flex items-center gap-1 px-2 py-0.5 rounded-lg border text-[10px] transition-all flex-shrink-0"
            :class="selectedMapCountry?.country === m.country ? 'ring-2 ring-sky-400 bg-sky-500 text-white border-sky-400' : 'bg-sky-950/80 hover:bg-sky-900 border-sky-800/60 text-sky-200'"
            :title="`${m.country}: ${formatVolumeKg(m.weight_kg)} | ${formatRevenue(m.val_usd)}`"
          >
            <span>{{ getCountryFlag(m.country) }}</span>
            <span class="font-semibold truncate max-w-[80px]">{{ m.country }}</span>
            <span class="text-[9px] font-mono text-sky-300">{{ formatRevenue(m.val_usd) }}</span>
          </button>
        </div>
      </div>
      <div v-else class="pointer-events-none"></div>

      <!-- Right Dock: Commodity B Destinations Only -->
      <div
        v-if="marketsB.length > 0"
        class="pointer-events-auto bg-slate-900/95 backdrop-blur-md border border-amber-500/50 px-3.5 py-1.5 rounded-2xl shadow-xl max-w-[48%] flex items-center gap-2 text-xs text-white justify-end"
      >
        <div class="flex items-center gap-1.5 flex-shrink-0">
          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
          <span class="font-bold text-amber-300 text-[11px]">B Destinations ({{ marketsB.length }}):</span>
        </div>
        <div class="flex items-center gap-1.5 overflow-x-auto py-0.5 custom-scrollbar flex-1 justify-end">
          <button
            v-for="m in marketsB"
            :key="`bottom-b-${m.country}`"
            @click="selectMarketB(m)"
            class="cursor-pointer flex items-center gap-1 px-2 py-0.5 rounded-lg border text-[10px] transition-all flex-shrink-0"
            :class="selectedMapCountry?.country === m.country ? 'ring-2 ring-amber-400 bg-amber-500 text-white border-amber-400' : 'bg-amber-950/80 hover:bg-amber-900 border-amber-800/60 text-amber-200'"
            :title="`${m.country}: ${formatVolumeKg(m.weight_kg)} | ${formatRevenue(m.val_usd)}`"
          >
            <span>{{ getCountryFlag(m.country) }}</span>
            <span class="font-semibold truncate max-w-[80px]">{{ m.country }}</span>
            <span class="text-[9px] font-mono text-amber-300">{{ formatRevenue(m.val_usd) }}</span>
          </button>
        </div>
      </div>
      <div v-else class="pointer-events-none"></div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
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
  ArrowLeft as ArrowLeftIcon,
  Globe as GlobeIcon,
  Maximize2 as Maximize2Icon,
  Minimize2 as Minimize2Icon,
  ChevronDown as ChevronDownIcon,
  Search as SearchIcon,
  Check as CheckIcon,
  Calendar as CalendarIcon,
} from 'lucide-vue-next';
import worldGeoJson from '../assets/world.json';
import { useDatasetStore } from '../stores/datasetStore';
import type { CommodityListItem, MarketBreakdownItem } from '../types/dataset';
import {
  getCountryMeta,
  getCountryFlag,
  getDisplayCountryName,
  CAMBODIA_COORDS
} from '../utils/countryRegistry';

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

const route = useRoute();
const router = useRouter();
const store = useDatasetStore();

const containerRef = ref<HTMLElement | null>(null);
const isFullscreen = ref<boolean>(false);

// Year Slicer State ('ALL' | '2023' | '2024' | ...)
const selectedYear = ref<string>('ALL');

// Support Multi-Select arrays (can be empty/null, single, or multiple)
const selectedCodesA = ref<string[]>(['08013100']);
const selectedCodesB = ref<string[]>(['08013200']);

const openDropdownA = ref<boolean>(false);
const openDropdownB = ref<boolean>(false);
const searchA = ref<string>('');
const searchB = ref<string>('');

const mapMetric = ref<'VOLUME' | 'REVENUE'>('VOLUME');
const selectedCountryName = ref<string | null>(null);

onMounted(() => {
  const queryA = route.query.a as string;
  const queryB = route.query.b as string;
  const list = store.dashboardData?.commodity_list || [];

  if (queryA && list.some(c => c.hs8_code === queryA)) {
    selectedCodesA.value = [queryA];
  } else if (list.length > 0) {
    selectedCodesA.value = [list[0].hs8_code];
  }

  if (queryB && list.some(c => c.hs8_code === queryB)) {
    selectedCodesB.value = [queryB];
  } else if (list.length > 1) {
    selectedCodesB.value = [list[1].hs8_code];
  }

  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement;
  });
});

const toggleFullscreen = () => {
  if (!containerRef.value) return;
  if (!document.fullscreenElement) {
    containerRef.value.requestFullscreen().catch(err => {
      console.warn('Error attempting to enable fullscreen:', err);
    });
  } else {
    document.exitFullscreen().catch(err => {
      console.warn('Error attempting to exit fullscreen:', err);
    });
  }
};

const availableYears = computed<number[]>(() => {
  if (store.dashboardData?.available_years && store.dashboardData.available_years.length > 0) {
    return store.dashboardData.available_years;
  }
  const yearSet = new Set<number>();
  const details = store.dashboardData?.commodity_details || {};
  for (const code in details) {
    for (const m of details[code]?.monthly_trend || []) {
      if (m.yyyy_mm) {
        const yr = parseInt(m.yyyy_mm.split('-')[0], 10);
        if (!isNaN(yr)) yearSet.add(yr);
      }
    }
  }
  if (yearSet.size > 0) {
    return Array.from(yearSet).sort();
  }
  return [2023, 2024];
});

const commodityOptions = computed<CommodityListItem[]>(() => {
  return store.dashboardData?.commodity_list || [];
});

const selectedCommoditiesTooltipA = computed<string>(() => {
  const detailsMap = store.dashboardData?.commodity_details || {};
  const opts = commodityOptions.value;
  const names = selectedCodesA.value.map(code => {
    const item = opts.find(c => c.hs8_code === code) || detailsMap[code];
    if (item) {
      return `[HS ${code}] ${item.name_en}${item.name_km ? ' (' + item.name_km + ')' : ''}`;
    }
    return `[HS ${code}]`;
  });
  return names.join('\n');
});

const selectedCommoditiesTooltipB = computed<string>(() => {
  const detailsMap = store.dashboardData?.commodity_details || {};
  const opts = commodityOptions.value;
  const names = selectedCodesB.value.map(code => {
    const item = opts.find(c => c.hs8_code === code) || detailsMap[code];
    if (item) {
      return `[HS ${code}] ${item.name_en}${item.name_km ? ' (' + item.name_km + ')' : ''}`;
    }
    return `[HS ${code}]`;
  });
  return names.join('\n');
});

const filteredOptionsA = computed(() => {
  const q = searchA.value.trim().toLowerCase();
  if (!q) return commodityOptions.value;
  return commodityOptions.value.filter(c => 
    c.hs8_code.includes(q) || 
    (c.name_en && c.name_en.toLowerCase().includes(q)) ||
    (c.name_km && c.name_km.toLowerCase().includes(q))
  );
});

const filteredOptionsB = computed(() => {
  const q = searchB.value.trim().toLowerCase();
  if (!q) return commodityOptions.value;
  return commodityOptions.value.filter(c => 
    c.hs8_code.includes(q) || 
    (c.name_en && c.name_en.toLowerCase().includes(q)) ||
    (c.name_km && c.name_km.toLowerCase().includes(q))
  );
});

const toggleCommodityA = (code: string) => {
  const idx = selectedCodesA.value.indexOf(code);
  if (idx > -1) {
    selectedCodesA.value.splice(idx, 1);
  } else {
    selectedCodesA.value.push(code);
  }
};

const selectAllA = () => {
  selectedCodesA.value = commodityOptions.value.map(c => c.hs8_code);
};

const clearA = () => {
  selectedCodesA.value = [];
};

const toggleCommodityB = (code: string) => {
  const idx = selectedCodesB.value.indexOf(code);
  if (idx > -1) {
    selectedCodesB.value.splice(idx, 1);
  } else {
    selectedCodesB.value.push(code);
  }
};

const selectAllB = () => {
  selectedCodesB.value = commodityOptions.value.map(c => c.hs8_code);
};

const clearB = () => {
  selectedCodesB.value = [];
};

const closeDropdowns = () => {
  openDropdownA.value = false;
  openDropdownB.value = false;
};

// Aggregated Summary for Group A (Handles null/empty, single, or multiple items, dynamically filtered by year)
const summaryA = computed(() => {
  const detailsMap = store.dashboardData?.commodity_details || {};
  const codes = selectedCodesA.value;
  if (!codes || codes.length === 0) return null;

  if (codes.length === 1) {
    const det = detailsMap[codes[0]];
    if (!det) return null;
    if (selectedYear.value === 'ALL') {
      return det;
    }
    const selYr = parseInt(selectedYear.value, 10);
    const yearMonths = (det.monthly_trend || []).filter(m => m.yyyy_mm && m.yyyy_mm.startsWith(selectedYear.value));
    const totValUsd = yearMonths.reduce((s, m) => s + (m.val_usd || 0), 0);
    const totValKhr = yearMonths.reduce((s, m) => s + (m.val_khr || 0), 0);
    const totWeightKg = yearMonths.reduce((s, m) => s + (m.weight_kg || 0), 0);
    const ratio = det.total_val_usd > 0 ? (totValUsd / det.total_val_usd) : (det.total_weight_kg > 0 ? totWeightKg / det.total_weight_kg : 1);

    const yearMarkets: MarketBreakdownItem[] = (det.yearly_markets && det.yearly_markets.length > 0)
      ? det.yearly_markets
          .filter(m => m.year === selYr)
          .map(m => ({
            country: m.country,
            val_usd: m.val_usd,
            val_khr: m.val_khr,
            weight_kg: m.weight_kg,
            share_pct: totValUsd > 0 ? (m.val_usd / totValUsd) * 100 : 0
          }))
          .sort((a, b) => b.val_usd - a.val_usd)
      : (det.market_breakdown || []).map(m => ({
          ...m,
          val_usd: m.val_usd * ratio,
          val_khr: m.val_khr * ratio,
          weight_kg: m.weight_kg * ratio,
          share_pct: totValUsd > 0 ? ((m.val_usd * ratio) / totValUsd) * 100 : 0
        })).filter(m => m.val_usd > 0 || m.weight_kg > 0);

    return {
      ...det,
      total_val_usd: totValUsd,
      total_val_khr: totValKhr,
      total_weight_kg: totWeightKg,
      total_weight_ton: totWeightKg / 1000,
      avg_price_usd_per_kg: totWeightKg > 0 ? (totValUsd / totWeightKg) : (totValUsd > 0 ? det.avg_price_usd_per_kg : 0),
      avg_price_khr_per_kg: totWeightKg > 0 ? (totValKhr / totWeightKg) : (totValKhr > 0 ? det.avg_price_khr_per_kg : 0),
      num_markets: yearMarkets.length,
      total_transactions: Math.max(1, Math.round((det.total_transactions || 1) * (ratio || 1))),
      market_breakdown: yearMarkets,
      monthly_trend: yearMonths,
    };
  }

  // Multi-Commodity Aggregation
  let totValUsd = 0;
  let totValKhr = 0;
  let totWeightKg = 0;
  let totTrans = 0;
  const marketMap = new Map<string, MarketBreakdownItem>();

  for (const code of codes) {
    const det = detailsMap[code];
    if (det) {
      if (selectedYear.value === 'ALL') {
        totValUsd += det.total_val_usd || 0;
        totValKhr += det.total_val_khr || 0;
        totWeightKg += det.total_weight_kg || 0;
        totTrans += det.total_transactions || det.market_breakdown?.length || 0;
        
        for (const m of det.market_breakdown || []) {
          if (!marketMap.has(m.country)) {
            marketMap.set(m.country, { ...m });
          } else {
            const cur = marketMap.get(m.country)!;
            cur.val_usd += m.val_usd;
            cur.val_khr += m.val_khr;
            cur.weight_kg += m.weight_kg;
          }
        }
      } else {
        const selYr = parseInt(selectedYear.value, 10);
        const yearMonths = (det.monthly_trend || []).filter(m => m.yyyy_mm && m.yyyy_mm.startsWith(selectedYear.value));
        const yValUsd = yearMonths.reduce((s, m) => s + (m.val_usd || 0), 0);
        const yValKhr = yearMonths.reduce((s, m) => s + (m.val_khr || 0), 0);
        const yWeightKg = yearMonths.reduce((s, m) => s + (m.weight_kg || 0), 0);
        const ratio = det.total_val_usd > 0 ? (yValUsd / det.total_val_usd) : (det.total_weight_kg > 0 ? yWeightKg / det.total_weight_kg : 1);

        totValUsd += yValUsd;
        totValKhr += yValKhr;
        totWeightKg += yWeightKg;
        totTrans += Math.max(1, Math.round((det.total_transactions || det.market_breakdown?.length || 1) * (ratio || 1)));

        const yearMarketItems = (det.yearly_markets && det.yearly_markets.length > 0)
          ? det.yearly_markets.filter(m => m.year === selYr)
          : (det.market_breakdown || []).map(m => ({
              country: m.country,
              year: selYr,
              val_usd: m.val_usd * ratio,
              val_khr: m.val_khr * ratio,
              weight_kg: m.weight_kg * ratio,
            }));

        for (const m of yearMarketItems) {
          if (m.val_usd > 0 || m.weight_kg > 0) {
            if (!marketMap.has(m.country)) {
              marketMap.set(m.country, {
                country: m.country,
                val_usd: m.val_usd,
                val_khr: m.val_khr,
                weight_kg: m.weight_kg,
                share_pct: 0,
              });
            } else {
              const cur = marketMap.get(m.country)!;
              cur.val_usd += m.val_usd;
              cur.val_khr += m.val_khr;
              cur.weight_kg += m.weight_kg;
            }
          }
        }
      }
    }
  }

  // Update share percentages
  const finalMarkets = Array.from(marketMap.values()).map(m => ({
    ...m,
    share_pct: totValUsd > 0 ? (m.val_usd / totValUsd) * 100 : 0
  })).sort((a, b) => b.val_usd - a.val_usd);

  return {
    hs8_code: 'MULTI',
    name_en: `${codes.length} Commodities`,
    name_km: `${codes.length} មុខទំនិញ`,
    total_val_usd: totValUsd,
    total_val_khr: totValKhr,
    total_weight_kg: totWeightKg,
    total_transactions: totTrans,
    num_markets: finalMarkets.length,
    avg_price_usd_per_kg: null, // Suppress blended average price for multi-crop
    avg_price_khr_per_kg: null,
    market_breakdown: finalMarkets,
  };
});

// Aggregated Summary for Group B (Dynamically filtered by year)
const summaryB = computed(() => {
  const detailsMap = store.dashboardData?.commodity_details || {};
  const codes = selectedCodesB.value;
  if (!codes || codes.length === 0) return null;

  if (codes.length === 1) {
    const det = detailsMap[codes[0]];
    if (!det) return null;
    if (selectedYear.value === 'ALL') {
      return det;
    }
    const selYr = parseInt(selectedYear.value, 10);
    const yearMonths = (det.monthly_trend || []).filter(m => m.yyyy_mm && m.yyyy_mm.startsWith(selectedYear.value));
    const totValUsd = yearMonths.reduce((s, m) => s + (m.val_usd || 0), 0);
    const totValKhr = yearMonths.reduce((s, m) => s + (m.val_khr || 0), 0);
    const totWeightKg = yearMonths.reduce((s, m) => s + (m.weight_kg || 0), 0);
    const ratio = det.total_val_usd > 0 ? (totValUsd / det.total_val_usd) : (det.total_weight_kg > 0 ? totWeightKg / det.total_weight_kg : 1);

    const yearMarkets: MarketBreakdownItem[] = (det.yearly_markets && det.yearly_markets.length > 0)
      ? det.yearly_markets
          .filter(m => m.year === selYr)
          .map(m => ({
            country: m.country,
            val_usd: m.val_usd,
            val_khr: m.val_khr,
            weight_kg: m.weight_kg,
            share_pct: totValUsd > 0 ? (m.val_usd / totValUsd) * 100 : 0
          }))
          .sort((a, b) => b.val_usd - a.val_usd)
      : (det.market_breakdown || []).map(m => ({
          ...m,
          val_usd: m.val_usd * ratio,
          val_khr: m.val_khr * ratio,
          weight_kg: m.weight_kg * ratio,
          share_pct: totValUsd > 0 ? ((m.val_usd * ratio) / totValUsd) * 100 : 0
        })).filter(m => m.val_usd > 0 || m.weight_kg > 0);

    return {
      ...det,
      total_val_usd: totValUsd,
      total_val_khr: totValKhr,
      total_weight_kg: totWeightKg,
      total_weight_ton: totWeightKg / 1000,
      avg_price_usd_per_kg: totWeightKg > 0 ? (totValUsd / totWeightKg) : (totValUsd > 0 ? det.avg_price_usd_per_kg : 0),
      avg_price_khr_per_kg: totWeightKg > 0 ? (totValKhr / totWeightKg) : (totValKhr > 0 ? det.avg_price_khr_per_kg : 0),
      num_markets: yearMarkets.length,
      total_transactions: Math.max(1, Math.round((det.total_transactions || 1) * (ratio || 1))),
      market_breakdown: yearMarkets,
      monthly_trend: yearMonths,
    };
  }

  let totValUsd = 0;
  let totValKhr = 0;
  let totWeightKg = 0;
  let totTrans = 0;
  const marketMap = new Map<string, MarketBreakdownItem>();

  for (const code of codes) {
    const det = detailsMap[code];
    if (det) {
      if (selectedYear.value === 'ALL') {
        totValUsd += det.total_val_usd || 0;
        totValKhr += det.total_val_khr || 0;
        totWeightKg += det.total_weight_kg || 0;
        totTrans += det.total_transactions || det.market_breakdown?.length || 0;
        
        for (const m of det.market_breakdown || []) {
          if (!marketMap.has(m.country)) {
            marketMap.set(m.country, { ...m });
          } else {
            const cur = marketMap.get(m.country)!;
            cur.val_usd += m.val_usd;
            cur.val_khr += m.val_khr;
            cur.weight_kg += m.weight_kg;
          }
        }
      } else {
        const selYr = parseInt(selectedYear.value, 10);
        const yearMonths = (det.monthly_trend || []).filter(m => m.yyyy_mm && m.yyyy_mm.startsWith(selectedYear.value));
        const yValUsd = yearMonths.reduce((s, m) => s + (m.val_usd || 0), 0);
        const yValKhr = yearMonths.reduce((s, m) => s + (m.val_khr || 0), 0);
        const yWeightKg = yearMonths.reduce((s, m) => s + (m.weight_kg || 0), 0);
        const ratio = det.total_val_usd > 0 ? (yValUsd / det.total_val_usd) : (det.total_weight_kg > 0 ? yWeightKg / det.total_weight_kg : 1);

        totValUsd += yValUsd;
        totValKhr += yValKhr;
        totWeightKg += yWeightKg;
        totTrans += Math.max(1, Math.round((det.total_transactions || det.market_breakdown?.length || 1) * (ratio || 1)));

        const yearMarketItems = (det.yearly_markets && det.yearly_markets.length > 0)
          ? det.yearly_markets.filter(m => m.year === selYr)
          : (det.market_breakdown || []).map(m => ({
              country: m.country,
              year: selYr,
              val_usd: m.val_usd * ratio,
              val_khr: m.val_khr * ratio,
              weight_kg: m.weight_kg * ratio,
            }));

        for (const m of yearMarketItems) {
          if (m.val_usd > 0 || m.weight_kg > 0) {
            if (!marketMap.has(m.country)) {
              marketMap.set(m.country, {
                country: m.country,
                val_usd: m.val_usd,
                val_khr: m.val_khr,
                weight_kg: m.weight_kg,
                share_pct: 0,
              });
            } else {
              const cur = marketMap.get(m.country)!;
              cur.val_usd += m.val_usd;
              cur.val_khr += m.val_khr;
              cur.weight_kg += m.weight_kg;
            }
          }
        }
      }
    }
  }

  const finalMarkets = Array.from(marketMap.values()).map(m => ({
    ...m,
    share_pct: totValUsd > 0 ? (m.val_usd / totValUsd) * 100 : 0
  })).sort((a, b) => b.val_usd - a.val_usd);

  return {
    hs8_code: 'MULTI',
    name_en: `${codes.length} Commodities`,
    name_km: `${codes.length} មុខទំនិញ`,
    total_val_usd: totValUsd,
    total_val_khr: totValKhr,
    total_weight_kg: totWeightKg,
    total_transactions: totTrans,
    num_markets: finalMarkets.length,
    avg_price_usd_per_kg: null,
    avg_price_khr_per_kg: null,
    market_breakdown: finalMarkets,
  };
});

const goBack = () => {
  router.push('/');
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
  const listA = summaryA.value?.market_breakdown || [];
  const listB = summaryB.value?.market_breakdown || [];
  if (listA.length === 0 && listB.length === 0) return [];

  const mapA = new Map(listA.map(m => [m.country, m]));
  const mapB = new Map(listB.map(m => [m.country, m]));
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

// Separated Markets for A and B
const marketsA = computed<MarketBreakdownItem[]>(() => {
  return summaryA.value?.market_breakdown || [];
});

const marketsB = computed<MarketBreakdownItem[]>(() => {
  return summaryB.value?.market_breakdown || [];
});

// Reactively resolve active country comparison data across year changes
const selectedMapCountry = computed(() => {
  if (!selectedCountryName.value) return null;
  const target = selectedCountryName.value;
  const found = combinedMarkets.value.find(m => {
    const meta = getCountryMeta(m.country);
    return m.country === target || 
           meta.en.toLowerCase() === target.toLowerCase() ||
           target.toLowerCase() === meta.km.toLowerCase() ||
           target.toLowerCase().includes(meta.en.toLowerCase()) ||
           target.toLowerCase().includes(m.country.toLowerCase());
  });
  if (found) return found;
  return {
    country: target,
    valA: null,
    valB: null
  };
});

const selectMarketA = (m: MarketBreakdownItem) => {
  selectedCountryName.value = m.country;
};

const selectMarketB = (m: MarketBreakdownItem) => {
  selectedCountryName.value = m.country;
};

const onMapPointClick = (params: any) => {
  if (params.data?.marketItem) {
    selectedCountryName.value = params.data.marketItem.country;
  } else if (params.name) {
    const found = combinedMarkets.value.find(m => {
      const meta = getCountryMeta(m.country);
      return m.country === params.name || 
             meta.en.toLowerCase() === params.name.toLowerCase() ||
             params.name.includes(meta.en) ||
             params.name.includes(m.country);
    });
    if (found) {
      selectedCountryName.value = found.country;
    } else {
      selectedCountryName.value = params.name;
    }
  }
};

// Comparative Global Map Option
const comparativeMapChartOption = computed(() => {
  const mList = combinedMarkets.value;
  const cambodiaHub = {
    name: 'Cambodia (Origin / ប្រទេសដើមកំណើត)',
    value: [...CAMBODIA_COORDS, 100],
    itemStyle: { color: '#10b981' }
  };

  const maxVal = Math.max(
    1,
    ...mList.map(m => {
      const aVal = mapMetric.value === 'VOLUME' ? (m.valA?.weight_kg || 0) : (m.valA?.val_usd || 0);
      const bVal = mapMetric.value === 'VOLUME' ? (m.valB?.weight_kg || 0) : (m.valB?.val_usd || 0);
      return Math.max(aVal, bVal);
    })
  );

  // Scatter points
  const scatterPoints = mList.map(m => {
    const meta = getCountryMeta(m.country);
    const aVal = mapMetric.value === 'VOLUME' ? (m.valA?.weight_kg || 0) : (m.valA?.val_usd || 0);
    const bVal = mapMetric.value === 'VOLUME' ? (m.valB?.weight_kg || 0) : (m.valB?.val_usd || 0);
    const highestVal = Math.max(aVal, bVal);
    const size = Math.max(14, Math.min(38, Math.sqrt(highestVal / maxVal) * 34));

    let pointColor = '#10b981'; // Shared
    if (m.valA && !m.valB) pointColor = '#38bdf8'; // A only
    else if (!m.valA && m.valB) pointColor = '#fbbf24'; // B only

    return {
      name: `${meta.flag} ${meta.en}`,
      value: [meta.coords[0], meta.coords[1], highestVal],
      symbolSize: size,
      marketItem: m,
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
        color: pointColor,
        borderColor: '#ffffff',
        borderWidth: 1.5,
        shadowBlur: 12,
        shadowColor: pointColor,
      }
    };
  });

  // Flow Lines
  const flowLinesA = mList.filter(m => m.valA).map(m => {
    const meta = getCountryMeta(m.country);
    return {
      fromName: 'Cambodia',
      toName: meta.en,
      coords: [CAMBODIA_COORDS, meta.coords],
      lineStyle: {
        color: m.valB ? 'rgba(16, 185, 129, 0.75)' : 'rgba(56, 189, 248, 0.75)',
        width: 2,
        curveness: 0.2,
      }
    };
  });

  const flowLinesB = mList.filter(m => m.valB && !m.valA).map(m => {
    const meta = getCountryMeta(m.country);
    return {
      fromName: 'Cambodia',
      toName: meta.en,
      coords: [CAMBODIA_COORDS, meta.coords],
      lineStyle: {
        color: 'rgba(251, 191, 36, 0.75)',
        width: 2,
        curveness: -0.2,
      }
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
          return `<div class="font-bold text-sky-400">✈️ Export Flow: Cambodia 🇰🇭 → ${params.data.toName}</div>`;
        }
        if (params.data?.name && params.data.name.includes('Cambodia (Origin')) {
          return `<div class="p-1">
            <div class="font-bold text-emerald-400 text-sm">🇰🇭 Cambodia (Origin Country)</div>
            <div class="text-xs text-slate-300 mt-0.5">Agricultural Trade Hub (ភ្នំពេញ)</div>
          </div>`;
        }
        const m = params.data?.marketItem;
        const meta = params.data?.meta;
        if (!m) return params.name;
        const flag = meta?.flag || '🌐';
        const enName = meta?.en || m.country;

        return `
          <div class="p-1 space-y-2 min-w-[240px]">
            <div class="flex items-center justify-between border-b border-slate-700 pb-1.5">
              <span class="font-black text-sm text-white">${flag} ${enName}</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded ${m.valA && m.valB ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : (m.valA ? 'bg-sky-950 text-sky-300 border border-sky-800' : 'bg-amber-950 text-amber-300 border border-amber-800')}">
                ${m.valA && m.valB ? 'Shared Market' : (m.valA ? 'A Only' : 'B Only')}
              </span>
            </div>
            <div class="text-xs space-y-1.5">
              <div class="bg-sky-950/40 p-1.5 rounded border border-sky-900/40">
                <div class="text-sky-300 font-bold text-[11px]">🔵 Group A (${selectedCodesA.value.length} crops)</div>
                <div class="flex justify-between text-slate-300 text-[10px] mt-0.5">
                  <span>${m.valA ? formatVolumeKg(m.valA.weight_kg) : '—'}</span>
                  <strong class="text-white">${m.valA ? formatRevenue(m.valA.val_usd) : '—'}</strong>
                </div>
              </div>
              <div class="bg-amber-950/40 p-1.5 rounded border border-amber-900/40">
                <div class="text-amber-300 font-bold text-[11px]">🟠 Group B (${selectedCodesB.value.length} crops)</div>
                <div class="flex justify-between text-slate-300 text-[10px] mt-0.5">
                  <span>${m.valB ? formatVolumeKg(m.valB.weight_kg) : '—'}</span>
                  <strong class="text-white">${m.valB ? formatRevenue(m.valB.val_usd) : '—'}</strong>
                </div>
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
      label: { show: false },
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
      {
        name: 'Export Routes Comm A',
        type: 'lines',
        coordinateSystem: 'geo',
        zlevel: 1,
        effect: {
          show: true,
          period: 4,
          trailLength: 0.25,
          symbol: 'arrow',
          symbolSize: 6,
        },
        data: flowLinesA,
      },
      {
        name: 'Export Routes Comm B',
        type: 'lines',
        coordinateSystem: 'geo',
        zlevel: 1,
        effect: {
          show: true,
          period: 4,
          trailLength: 0.25,
          symbol: 'arrow',
          symbolSize: 6,
        },
        data: flowLinesB,
      },
      {
        name: 'Destination Markets',
        type: 'scatter',
        coordinateSystem: 'geo',
        zlevel: 2,
        data: scatterPoints,
      },
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

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.6);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(56, 189, 248, 0.4);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(56, 189, 248, 0.7);
}
</style>
