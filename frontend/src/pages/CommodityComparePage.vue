<template>
  <div 
    ref="containerRef" 
    class="relative w-full h-[calc(100vh-80px)] sm:h-[calc(100vh-100px)] min-h-[580px] sm:min-h-[720px] rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl flex flex-col justify-between select-none transition-colors duration-300"
    :class="isDarkTheme ? 'bg-slate-950 border border-slate-800 text-white' : 'bg-slate-100/80 border border-slate-200/90 text-slate-900'"
  >
    
    <!-- ==================== TOP FLOATING CONTROLS BAR ==================== -->
    <div class="absolute top-2 sm:top-4 left-2 sm:left-4 right-2 sm:right-4 z-30 flex items-center justify-between pointer-events-none gap-1 sm:gap-2">
      
      <!-- Back Button & Title -->
      <div 
        class="flex items-center gap-1 sm:gap-2 pointer-events-auto backdrop-blur-md px-2 sm:px-3 py-1.5 sm:py-2 rounded-xl sm:rounded-2xl shadow-xl transition-all"
        :class="isDarkTheme ? 'bg-slate-900/95 border border-slate-700 text-white' : 'bg-white/95 border border-slate-200 text-slate-800'"
      >
        <button
          @click="goBack"
          class="cursor-pointer flex items-center gap-1 font-semibold text-xs transition-colors"
          :class="isDarkTheme ? 'text-slate-300 hover:text-white' : 'text-slate-600 hover:text-slate-900'"
          title="Return to Main Dashboard"
        >
          <ArrowLeftIcon class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          <span class="hidden sm:inline text-xs">Back</span>
        </button>
        <span class="hidden sm:inline" :class="isDarkTheme ? 'text-slate-600' : 'text-slate-300'">|</span>
        <div class="hidden sm:flex items-center gap-1.5">
          <GlobeIcon class="w-3.5 h-3.5 sm:w-4 sm:h-4" :class="isDarkTheme ? 'text-sky-400' : 'text-sky-600'" />
          <h2 class="text-xs font-bold tracking-wide uppercase truncate" :class="isDarkTheme ? 'text-white' : 'text-slate-800'">
            Compare Commodities
          </h2>
        </div>
      </div>

      <!-- Center Year Slicer -->
      <div 
        class="pointer-events-auto flex items-center gap-1 sm:gap-1.5 backdrop-blur-md px-1.5 sm:px-3 py-1 sm:py-1.5 rounded-xl sm:rounded-2xl shadow-xl transition-all"
        :class="isDarkTheme ? 'bg-slate-900/95 border border-slate-700 text-white' : 'bg-white/95 border border-slate-200 text-slate-800'"
      >
        <CalendarIcon class="w-3.5 h-3.5 text-sky-600 hidden md:inline" />
        <span class="text-xs font-bold hidden md:inline" :class="isDarkTheme ? 'text-slate-300' : 'text-slate-600'">Year:</span>
        <div 
          class="flex items-center gap-0.5 p-0.5 rounded-lg sm:rounded-xl text-xs border"
          :class="isDarkTheme ? 'bg-slate-950 border-slate-800' : 'bg-slate-100 border-slate-200'"
        >
          <button
            @click="selectedYear = 'ALL'"
            class="cursor-pointer px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg text-[10px] sm:text-xs font-bold transition-all"
            :class="selectedYear === 'ALL' 
              ? 'bg-sky-600 text-white shadow-xs' 
              : (isDarkTheme ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900')"
            title="Show aggregate trade data across all recorded years"
          >
            All
          </button>
          <button
            v-for="yr in availableYears"
            :key="yr"
            @click="selectedYear = yr.toString()"
            class="cursor-pointer px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg text-[10px] sm:text-xs font-bold transition-all"
            :class="selectedYear === yr.toString() 
              ? 'bg-sky-600 text-white shadow-xs' 
              : (isDarkTheme ? 'text-slate-400 hover:text-white' : 'text-slate-600 hover:text-slate-900')"
            :title="`Filter comparison data for Year ${yr}`"
          >
            {{ yr }}
          </button>
        </div>
      </div>

      <!-- Right Controls: Theme Switcher & Fullscreen -->
      <div class="pointer-events-auto flex items-center gap-1 sm:gap-2">
        <!-- Theme Toggle Button -->
        <button
          @click="isDarkTheme = !isDarkTheme"
          class="cursor-pointer flex items-center gap-1 backdrop-blur-md px-2 sm:px-3 py-1.5 sm:py-2 rounded-xl sm:rounded-2xl shadow-xl text-xs font-bold transition-all border"
          :class="isDarkTheme 
            ? 'bg-slate-900/95 border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800' 
            : 'bg-white/95 border-slate-200 text-slate-700 hover:text-slate-900 hover:bg-slate-50'"
          :title="isDarkTheme ? 'Switch to Light Theme' : 'Switch to Dark Theme'"
        >
          <SunIcon v-if="!isDarkTheme" class="w-3.5 h-3.5 text-amber-500" />
          <MoonIcon v-else class="w-3.5 h-3.5 text-sky-400" />
          <span class="hidden md:inline">{{ isDarkTheme ? 'Dark' : 'Light' }}</span>
        </button>

        <!-- Fullscreen Toggle -->
        <button
          @click="toggleFullscreen"
          class="cursor-pointer flex items-center gap-1 backdrop-blur-md px-2 sm:px-3 py-1.5 sm:py-2 rounded-xl sm:rounded-2xl shadow-xl text-xs font-semibold transition-all border"
          :class="isDarkTheme 
            ? 'bg-slate-900/95 border-slate-700 text-slate-300 hover:text-white' 
            : 'bg-white/95 border-slate-200 text-slate-700 hover:text-slate-900'"
          :title="isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'"
        >
          <component :is="isFullscreen ? Minimize2Icon : Maximize2Icon" class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-sky-500" />
          <span class="hidden md:inline text-xs">{{ isFullscreen ? 'Exit' : 'Fullscreen' }}</span>
        </button>
      </div>

    </div>

    <!-- ==================== MOBILE VIEWPORT SWITCHER (< md screens) ==================== -->
    <div class="md:hidden absolute top-13 xs:top-14 left-2 right-2 z-30 flex items-center justify-center pointer-events-auto">
      <div 
        class="flex items-center p-1 rounded-2xl shadow-lg border backdrop-blur-md gap-1"
        :class="isDarkTheme ? 'bg-slate-900/95 border-slate-700 text-white' : 'bg-white/95 border-slate-200 text-slate-900'"
      >
        <button
          @click="mobileView = 'MAP'"
          class="cursor-pointer flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold transition-all"
          :class="mobileView === 'MAP' ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
        >
          <GlobeIcon class="w-3.5 h-3.5" />
          <span>Map</span>
        </button>

        <button
          @click="mobileView = 'A'"
          class="cursor-pointer flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold transition-all"
          :class="mobileView === 'A' ? 'bg-sky-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
        >
          <span class="w-2 h-2 rounded-full bg-sky-400"></span>
          <span>Comm A</span>
          <span class="text-[10px] font-mono opacity-80">({{ selectedCodesA.length }})</span>
        </button>

        <button
          @click="mobileView = 'B'"
          class="cursor-pointer flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold transition-all"
          :class="mobileView === 'B' ? 'bg-amber-600 text-white shadow-xs' : 'text-slate-500 hover:text-slate-800'"
        >
          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
          <span>Comm B</span>
          <span class="text-[10px] font-mono opacity-80">({{ selectedCodesB.length }})</span>
        </button>
      </div>
    </div>

    <!-- ==================== LEFT FLOATING OVERLAY: COMMODITY A & KPIS ==================== -->
    <div
      class="absolute top-26 md:top-16 left-2 sm:left-4 z-20 w-[calc(100%-1rem)] sm:w-84 sm:max-w-[calc(50vw-1.5rem)] max-h-[calc(100%-7.5rem)] md:max-h-[calc(100%-8.5rem)] overflow-y-auto space-y-3 pr-1 pb-2 custom-scrollbar pointer-events-auto"
      :class="{
        'hidden md:block': mobileView !== 'A',
        'block': mobileView === 'A'
      }"
      @click.stop
    >
      
      <!-- Custom Multi-Commodity Checkbox Picker: Commodity A -->
      <div 
        class="backdrop-blur-md p-4 rounded-2xl border-2 shadow-xl space-y-2.5 transition-all"
        :class="isDarkTheme ? 'bg-slate-900/95 border-sky-500/60 text-white' : 'bg-white/95 border-sky-400 text-slate-900'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5" :class="isDarkTheme ? 'text-sky-400' : 'text-sky-700'">
            <span class="w-2.5 h-2.5 rounded-full bg-sky-500 animate-pulse"></span>
            Commodity A (ទំនិញ ទី១)
          </span>
          <span 
            class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border"
            :class="isDarkTheme ? 'text-sky-300 bg-sky-950 border-sky-800' : 'text-sky-800 bg-sky-50 border-sky-200'"
          >
            {{ selectedCodesA.length }} Selected
          </span>
        </div>

        <!-- Custom Dropdown Trigger Button -->
        <button
          type="button"
          @click="openDropdownA = !openDropdownA; openDropdownB = false"
          class="cursor-pointer w-full border-2 rounded-xl px-3.5 py-2.5 text-left flex items-center justify-between transition-all shadow-xs"
          :class="[
            isDarkTheme 
              ? (openDropdownA ? 'bg-slate-950 border-sky-400 ring-2 ring-sky-500/30' : 'bg-slate-950/90 border-slate-700 hover:border-sky-500/50')
              : (openDropdownA ? 'bg-white border-sky-500 ring-2 ring-sky-500/20' : 'bg-slate-50 hover:bg-white border-slate-200 hover:border-sky-400')
          ]"
          :title="selectedCodesA.length === 1 && summaryA ? `[HS ${selectedCodesA[0]}] ${summaryA.name_en}${summaryA.name_km ? ' (' + summaryA.name_km + ')' : ''}` : (selectedCodesA.length > 1 ? selectedCommoditiesTooltipA : 'Choose commodities...')"
        >
          <div class="truncate flex-1 pr-2">
            <span v-if="selectedCodesA.length === 0" class="text-xs text-slate-400 italic">
              Choose Commodity A...
            </span>
            <span v-else-if="selectedCodesA.length === 1 && summaryA" class="font-bold text-xs block truncate" :class="isDarkTheme ? 'text-white' : 'text-slate-900'" :title="`[HS ${selectedCodesA[0]}] ${summaryA.name_en}`">
              [HS {{ selectedCodesA[0] }}] {{ summaryA.name_en }}
            </span>
            <span v-else class="font-bold text-xs block truncate" :class="isDarkTheme ? 'text-sky-300' : 'text-sky-700'" :title="selectedCommoditiesTooltipA">
              {{ selectedCodesA.length }} Commodities Selected (Multi-Crop)
            </span>

          </div>
          <ChevronDownIcon
            class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
            :class="[
              isDarkTheme ? 'text-sky-400' : 'text-sky-600',
              { 'rotate-180': openDropdownA }
            ]"
          />
        </button>

        <!-- Inline Expandable Checkbox Options List A -->
        <div
          v-if="openDropdownA"
          class="border rounded-xl p-2.5 space-y-2 animate-in fade-in duration-150 shadow-2xl"
          :class="isDarkTheme ? 'bg-slate-950/95 border-sky-500/40 text-white' : 'bg-white border-sky-300 text-slate-900'"
        >
          <!-- Search & Select Controls -->
          <div class="relative">
            <SearchIcon class="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" />
            <input
              v-model="searchA"
              type="text"
              placeholder="Search commodity name or HS code..."
              class="w-full pl-8 pr-3 py-1.5 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-sky-500 border"
              :class="isDarkTheme ? 'bg-slate-900 border-slate-700 text-white' : 'bg-slate-50 border-slate-200 text-slate-900'"
              @click.stop
            />
          </div>

          <div class="flex items-center justify-between text-[11px] pb-1 border-b" :class="isDarkTheme ? 'border-slate-800' : 'border-slate-100'">
            <button
              type="button"
              @click="selectAllA"
              class="font-bold hover:underline"
              :class="isDarkTheme ? 'text-sky-400' : 'text-sky-600'"
            >
              Select All ({{ commodityOptions.length }})
            </button>
            <button
              type="button"
              @click="clearA"
              class="font-semibold hover:underline"
              :class="isDarkTheme ? 'text-slate-400 hover:text-white' : 'text-slate-500 hover:text-slate-800'"
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
              :class="selectedCodesA.includes(item.hs8_code) 
                ? (isDarkTheme ? 'bg-sky-950 border-sky-400 text-white shadow-xs' : 'bg-sky-50 border-sky-400 text-sky-950 shadow-xs') 
                : (isDarkTheme ? 'bg-slate-900/60 border-slate-800 hover:bg-slate-800 text-slate-300' : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700')"
              :title="`[HS ${item.hs8_code}] ${item.name_en}${item.name_km ? ' (' + item.name_km + ')' : ''}`"
            >
              <!-- Styled Checkbox Box -->
              <div
                class="w-4 h-4 rounded-md border flex items-center justify-center flex-shrink-0 transition-colors"
                :class="selectedCodesA.includes(item.hs8_code) 
                  ? 'bg-sky-500 border-sky-400 text-white' 
                  : (isDarkTheme ? 'border-slate-600 bg-slate-800' : 'border-slate-300 bg-white')"
              >
                <CheckIcon v-if="selectedCodesA.includes(item.hs8_code)" class="w-3 h-3 stroke-[3]" />
              </div>

              <!-- Label & HS Code -->
              <div class="flex-1 truncate">
                <div class="flex items-center gap-1.5">
                  <span 
                    class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded"
                    :class="isDarkTheme ? 'bg-slate-800 text-sky-400' : 'bg-sky-100 text-sky-800'"
                  >
                    HS {{ item.hs8_code }}
                  </span>
                  <span class="font-bold text-xs truncate" :class="isDarkTheme ? 'text-white' : 'text-slate-900'" :title="item.name_en">{{ item.name_en }}</span>
                </div>
                <span v-if="item.name_km" class="text-[10px] block font-sans truncate mt-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" :title="item.name_km">
                  {{ item.name_km }}
                </span>
              </div>
            </div>

            <div v-if="filteredOptionsA.length === 0" class="text-center py-4 text-xs text-slate-400">
              No matching commodities
            </div>
          </div>

          <!-- Done Button -->
          <div class="pt-1.5 border-t flex justify-end" :class="isDarkTheme ? 'border-slate-800' : 'border-slate-100'">
            <button
              type="button"
              @click="openDropdownA = false"
              class="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-bold transition-colors"
            >
              Done ({{ selectedCodesA.length }})
            </button>
          </div>
        </div>

        <div v-if="summaryA && selectedCodesA.length === 1 && !openDropdownA" class="text-xs flex items-center justify-between pt-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" :title="`${summaryA.name_en} (${summaryA.name_km})`">
          <span class="truncate font-sans font-medium text-[11px]" :class="isDarkTheme ? 'text-slate-300' : 'text-slate-700'" :title="summaryA.name_km">{{ summaryA.name_km }}</span>
          <router-link :to="`/commodity/${selectedCodesA[0]}`" class="font-bold hover:underline ml-2 text-[11px] whitespace-nowrap" :class="isDarkTheme ? 'text-sky-400' : 'text-sky-600'" :title="`View deep-dive analytics for ${summaryA.name_en}`">
            Detail →
          </router-link>
        </div>

      </div>

      <!-- 5-Metric Dedicated KPI Panel A -->
      <div 
        class="backdrop-blur-md p-3.5 rounded-2xl border shadow-xl space-y-2 transition-all"
        :class="isDarkTheme ? 'bg-slate-900/90 border-sky-500/30 text-white' : 'bg-white/95 border-sky-200 text-slate-900'"
      >
        
        <!-- 1. Revenue $ -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-sky-200' : 'text-sky-800'">
              Revenue ($USD)
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Scale: $k / $M</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            {{ formatRevenue(summaryA?.total_val_usd || 0) }}
          </div>
        </div>

        <!-- 2. Volume -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-sky-200' : 'text-sky-800'">
              Export Volume
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Scale: kg / Tonnes</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            {{ formatVolumeKg(summaryA?.total_weight_kg || 0) }}
          </div>
        </div>

        <!-- 3. Transaction -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-sky-200' : 'text-sky-800'">
              Transactions
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Declarations</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            Not available
          </div>
        </div>

        <!-- 4. Destination Markets -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-sky-200' : 'text-sky-800'">
              Destination Markets
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Active Partners</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            {{ marketsA.length }} Countries
          </div>
        </div>

        <!-- 5. Avg Price (Suppressed if multi-crop or null) -->
        <div 
          class="p-3 rounded-xl border"
          :class="isDarkTheme ? 'bg-sky-950/70 border-sky-600/60 text-sky-300' : 'bg-sky-50 border-sky-300 text-sky-900'"
        >
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-sky-300' : 'text-sky-800'">
            <span class="font-bold flex items-center gap-1.5">
              Benchmark Avg Price
            </span>
            <span class="text-[10px] font-sans" :class="isDarkTheme ? 'text-sky-400' : 'text-sky-600'">Unit Rate</span>
          </div>

          
          <div v-if="selectedCodesA.length === 1 && summaryA?.avg_price_usd_per_kg">
            <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-sky-300' : 'text-sky-700'">
              ${{ summaryA.avg_price_usd_per_kg.toFixed(2) }} <span class="text-xs font-normal text-slate-500">/ kg</span>
            </div>
            <div class="text-[11px] mt-0.5 font-sans" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-600'">
              ≈ {{ Math.round(summaryA.avg_price_khr_per_kg || summaryA.avg_price_usd_per_kg * 4000).toLocaleString() }} ៛/kg
            </div>
          </div>
          <div v-else-if="selectedCodesA.length > 1" class="text-xs font-semibold font-mono pt-0.5" :class="isDarkTheme ? 'text-amber-300/90' : 'text-amber-700'">
            N/A (Multi-Crop Aggregate)
          </div>
          <div v-else class="text-xs text-slate-400 italic pt-0.5">
            — (No crop selected)
          </div>
        </div>

      </div>
    </div>

    <!-- ==================== RIGHT FLOATING OVERLAY: COMMODITY B & KPIS ==================== -->
    <div
      class="absolute top-26 md:top-16 right-2 sm:right-4 z-20 w-[calc(100%-1rem)] sm:w-84 sm:max-w-[calc(50vw-1.5rem)] max-h-[calc(100%-7.5rem)] md:max-h-[calc(100%-8.5rem)] overflow-y-auto space-y-3 pr-1 pb-2 custom-scrollbar pointer-events-auto"
      :class="{
        'hidden md:block': mobileView !== 'B',
        'block': mobileView === 'B'
      }"
      @click.stop
    >
      
      <!-- Custom Multi-Commodity Checkbox Picker: Commodity B -->
      <div 
        class="backdrop-blur-md p-4 rounded-2xl border-2 shadow-xl space-y-2.5 transition-all"
        :class="isDarkTheme ? 'bg-slate-900/95 border-amber-500/60 text-white' : 'bg-white/95 border-amber-400 text-slate-900'"
      >
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5" :class="isDarkTheme ? 'text-amber-400' : 'text-amber-700'">
            <span class="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse"></span>
            Commodity B (ទំនិញ ទី២)
          </span>
          <span 
            class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border"
            :class="isDarkTheme ? 'text-amber-300 bg-amber-950 border-amber-800' : 'text-amber-800 bg-amber-50 border-amber-200'"
          >
            {{ selectedCodesB.length }} Selected
          </span>
        </div>

        <!-- Custom Dropdown Trigger Button -->
        <button
          type="button"
          @click="openDropdownB = !openDropdownB; openDropdownA = false"
          class="cursor-pointer w-full border-2 rounded-xl px-3.5 py-2.5 text-left flex items-center justify-between transition-all shadow-xs"
          :class="[
            isDarkTheme 
              ? (openDropdownB ? 'bg-slate-950 border-amber-400 ring-2 ring-amber-500/30' : 'bg-slate-950/90 border-slate-700 hover:border-amber-500/50')
              : (openDropdownB ? 'bg-white border-amber-500 ring-2 ring-amber-500/20' : 'bg-slate-50 hover:bg-white border-slate-200 hover:border-amber-400')
          ]"
          :title="selectedCodesB.length === 1 && summaryB ? `[HS ${selectedCodesB[0]}] ${summaryB.name_en}${summaryB.name_km ? ' (' + summaryB.name_km + ')' : ''}` : (selectedCodesB.length > 1 ? selectedCommoditiesTooltipB : 'Choose commodities...')"
        >
          <div class="truncate flex-1 pr-2">
            <span v-if="selectedCodesB.length === 0" class="text-xs text-slate-400 italic">
              Choose Commodity B...
            </span>
            <span v-else-if="selectedCodesB.length === 1 && summaryB" class="font-bold text-xs block truncate" :class="isDarkTheme ? 'text-white' : 'text-slate-900'" :title="`[HS ${selectedCodesB[0]}] ${summaryB.name_en}`">
              [HS {{ selectedCodesB[0] }}] {{ summaryB.name_en }}
            </span>
            <span v-else class="font-bold text-xs block truncate" :class="isDarkTheme ? 'text-amber-300' : 'text-amber-700'" :title="selectedCommoditiesTooltipB">
              {{ selectedCodesB.length }} Commodities Selected (Multi-Crop)
            </span>

          </div>
          <ChevronDownIcon
            class="w-4 h-4 flex-shrink-0 transition-transform duration-200"
            :class="[
              isDarkTheme ? 'text-amber-400' : 'text-amber-600',
              { 'rotate-180': openDropdownB }
            ]"
          />
        </button>

        <!-- Inline Expandable Checkbox Options List B -->
        <div
          v-if="openDropdownB"
          class="border rounded-xl p-2.5 space-y-2 animate-in fade-in duration-150 shadow-2xl"
          :class="isDarkTheme ? 'bg-slate-950/95 border-amber-500/40 text-white' : 'bg-white border-amber-300 text-slate-900'"
        >
          <!-- Search & Select Controls -->
          <div class="relative">
            <SearchIcon class="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" />
            <input
              v-model="searchB"
              type="text"
              placeholder="Search commodity name or HS code..."
              class="w-full pl-8 pr-3 py-1.5 rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-amber-500 border"
              :class="isDarkTheme ? 'bg-slate-900 border-slate-700 text-white' : 'bg-slate-50 border-slate-200 text-slate-900'"
              @click.stop
            />
          </div>

          <div class="flex items-center justify-between text-[11px] pb-1 border-b" :class="isDarkTheme ? 'border-slate-800' : 'border-slate-100'">
            <button
              type="button"
              @click="selectAllB"
              class="font-bold hover:underline"
              :class="isDarkTheme ? 'text-amber-400' : 'text-amber-600'"
            >
              Select All ({{ commodityOptions.length }})
            </button>
            <button
              type="button"
              @click="clearB"
              class="font-semibold hover:underline"
              :class="isDarkTheme ? 'text-slate-400 hover:text-white' : 'text-slate-500 hover:text-slate-800'"
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
              :class="selectedCodesB.includes(item.hs8_code) 
                ? (isDarkTheme ? 'bg-amber-950 border-amber-400 text-white shadow-xs' : 'bg-amber-50 border-amber-400 text-amber-950 shadow-xs') 
                : (isDarkTheme ? 'bg-slate-900/60 border-slate-800 hover:bg-slate-800 text-slate-300' : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700')"
              :title="`[HS ${item.hs8_code}] ${item.name_en}${item.name_km ? ' (' + item.name_km + ')' : ''}`"
            >
              <!-- Styled Checkbox Box -->
              <div
                class="w-4 h-4 rounded-md border flex items-center justify-center flex-shrink-0 transition-colors"
                :class="selectedCodesB.includes(item.hs8_code) 
                  ? 'bg-amber-500 border-amber-400 text-white' 
                  : (isDarkTheme ? 'border-slate-600 bg-slate-800' : 'border-slate-300 bg-white')"
              >
                <CheckIcon v-if="selectedCodesB.includes(item.hs8_code)" class="w-3 h-3 stroke-[3]" />
              </div>

              <!-- Label & HS Code -->
              <div class="flex-1 truncate">
                <div class="flex items-center gap-1.5">
                  <span 
                    class="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded"
                    :class="isDarkTheme ? 'bg-slate-800 text-amber-400' : 'bg-amber-100 text-amber-800'"
                  >
                    HS {{ item.hs8_code }}
                  </span>
                  <span class="font-bold text-xs truncate" :class="isDarkTheme ? 'text-white' : 'text-slate-900'" :title="item.name_en">{{ item.name_en }}</span>
                </div>
                <span v-if="item.name_km" class="text-[10px] block font-sans truncate mt-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" :title="item.name_km">
                  {{ item.name_km }}
                </span>
              </div>
            </div>

            <div v-if="filteredOptionsB.length === 0" class="text-center py-4 text-xs text-slate-400">
              No matching commodities
            </div>
          </div>

          <!-- Done Button -->
          <div class="pt-1.5 border-t flex justify-end" :class="isDarkTheme ? 'border-slate-800' : 'border-slate-100'">
            <button
              type="button"
              @click="openDropdownB = false"
              class="px-3 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition-colors"
            >
              Done ({{ selectedCodesB.length }})
            </button>
          </div>
        </div>

        <div v-if="summaryB && selectedCodesB.length === 1 && !openDropdownB" class="text-xs flex items-center justify-between pt-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'" :title="`${summaryB.name_en} (${summaryB.name_km})`">
          <span class="truncate font-sans font-medium text-[11px]" :class="isDarkTheme ? 'text-slate-300' : 'text-slate-700'" :title="summaryB.name_km">{{ summaryB.name_km }}</span>
          <router-link :to="`/commodity/${selectedCodesB[0]}`" class="font-bold hover:underline ml-2 text-[11px] whitespace-nowrap" :class="isDarkTheme ? 'text-amber-400' : 'text-amber-600'" :title="`View deep-dive analytics for ${summaryB.name_en}`">
            Detail →
          </router-link>
        </div>

      </div>

      <!-- 5-Metric Dedicated KPI Panel B -->
      <div 
        class="backdrop-blur-md p-3.5 rounded-2xl border shadow-xl space-y-2 transition-all"
        :class="isDarkTheme ? 'bg-slate-900/90 border-amber-500/30 text-white' : 'bg-white/95 border-amber-200 text-slate-900'"
      >
        
        <!-- 1. Revenue $ -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-amber-200' : 'text-amber-800'">
              Revenue ($USD)
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Scale: $k / $M</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            {{ formatRevenue(summaryB?.total_val_usd || 0) }}
          </div>
        </div>

        <!-- 2. Volume -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-amber-200' : 'text-amber-800'">
              Export Volume
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Scale: kg / Tonnes</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            {{ formatVolumeKg(summaryB?.total_weight_kg || 0) }}
          </div>
        </div>

        <!-- 3. Transaction -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-amber-200' : 'text-amber-800'">
              Transactions
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Declarations</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            Not available
          </div>
        </div>

        <!-- 4. Destination Markets -->
        <div class="p-2.5 rounded-xl border" :class="isDarkTheme ? 'bg-slate-950/70 border-slate-800' : 'bg-slate-50 border-slate-200/80'">
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">
            <span class="font-semibold flex items-center gap-1.5" :class="isDarkTheme ? 'text-amber-200' : 'text-amber-800'">
              Destination Markets
            </span>
            <span class="text-[10px] text-slate-400 font-sans">Active Partners</span>
          </div>
          <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
            {{ marketsB.length }} Countries
          </div>
        </div>

        <!-- 5. Avg Price (Suppressed if multi-crop or null) -->
        <div 
          class="p-3 rounded-xl border"
          :class="isDarkTheme ? 'bg-amber-950/70 border-amber-600/60 text-amber-300' : 'bg-amber-50 border-amber-300 text-amber-900'"
        >
          <div class="flex items-center justify-between text-xs mb-0.5" :class="isDarkTheme ? 'text-amber-300' : 'text-amber-800'">
            <span class="font-bold flex items-center gap-1.5">
              Benchmark Avg Price
            </span>
            <span class="text-[10px] font-sans" :class="isDarkTheme ? 'text-amber-400' : 'text-amber-600'">Unit Rate</span>
          </div>

          
          <div v-if="selectedCodesB.length === 1 && summaryB?.avg_price_usd_per_kg">
            <div class="text-base font-black font-mono" :class="isDarkTheme ? 'text-amber-300' : 'text-amber-700'">
              ${{ summaryB.avg_price_usd_per_kg.toFixed(2) }} <span class="text-xs font-normal text-slate-500">/ kg</span>
            </div>
            <div class="text-[11px] mt-0.5 font-sans" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-600'">
              ≈ {{ Math.round(summaryB.avg_price_khr_per_kg || summaryB.avg_price_usd_per_kg * 4000).toLocaleString() }} ៛/kg
            </div>
          </div>
          <div v-else-if="selectedCodesB.length > 1" class="text-xs font-semibold font-mono pt-0.5" :class="isDarkTheme ? 'text-amber-300/90' : 'text-amber-700'">
            N/A (Multi-Crop Aggregate)
          </div>
          <div v-else class="text-xs text-slate-400 italic pt-0.5">
            — (No crop selected)
          </div>
        </div>

      </div>
    </div>

    <!-- ==================== FULLSCREEN ECHARTS MAP CANVAS ==================== -->
    <div 
      class="absolute inset-0 w-full h-full overflow-hidden select-none cursor-grab active:cursor-grabbing z-0" 
      style="touch-action: none; -webkit-user-select: none; user-select: none;"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @mouseleave="handleMouseUp"
      @wheel.prevent="handleWheel"
      @touchstart="handleTouchStart"
      @touchmove.prevent="handleTouchMove"
      @touchend="handleTouchEnd"
      @click="closeDropdowns"
    >
      
      <!-- Cambodia Hub Badge & Destination Color Legend (Always visible & never obscured) -->
      <div 
        class="absolute top-24 sm:top-auto sm:bottom-16 left-2 sm:left-4 z-20 flex flex-wrap items-center gap-1.5 sm:gap-2.5 pointer-events-auto transition-all"
        :class="{ 'hidden md:flex': mobileView !== 'MAP' }"
      >
        <!-- Origin Badge -->
        <div 
          class="backdrop-blur-md px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl border text-[10px] sm:text-[11px] flex items-center gap-1.5 sm:gap-2 shadow-lg transition-all font-bold"
          :class="isDarkTheme ? 'bg-slate-900/95 border-slate-700 text-slate-200' : 'bg-white/95 border-slate-200 text-slate-800'"
        >
          <span class="relative flex h-2 sm:h-2.5 w-2 sm:w-2.5">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 sm:h-2.5 w-2 sm:w-2.5 bg-emerald-500"></span>
          </span>
          <span>Origin: Cambodia</span>
        </div>

        <!-- Destination Color Legend Badge -->
        <div 
          class="backdrop-blur-md px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl border text-[10px] sm:text-[11px] flex items-center gap-2 shadow-lg transition-all font-semibold"
          :class="isDarkTheme ? 'bg-slate-900/95 border-slate-700 text-slate-300' : 'bg-white/95 border-slate-200 text-slate-700'"
        >
          <span class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-sky-500"></span>
            <span class="font-bold text-sky-600">A Only</span>
          </span>
          <span :class="isDarkTheme ? 'text-slate-600' : 'text-slate-300'">|</span>
          <span class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-amber-500"></span>
            <span class="font-bold text-amber-600">B Only</span>
          </span>
          <span :class="isDarkTheme ? 'text-slate-600' : 'text-slate-300'">|</span>
          <span class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span class="font-bold text-emerald-600">Shared</span>
          </span>
        </div>
      </div>

      <!-- In-Map Floating Country Intelligence Comparison Card -->
      <div
        v-if="selectedMapCountry"
        class="absolute bottom-14 sm:bottom-16 left-2 right-2 sm:left-1/2 sm:-translate-x-1/2 z-30 backdrop-blur-md border p-3.5 sm:p-4 rounded-2xl shadow-2xl max-w-sm sm:w-full mx-auto animate-in fade-in transition-all"
        :class="isDarkTheme ? 'bg-slate-900/95 border-slate-700 text-white' : 'bg-white/98 border-slate-200 text-slate-900'"
        @click.stop
      >
        <div class="flex items-center justify-between pb-2 border-b mb-2.5" :class="isDarkTheme ? 'border-slate-800' : 'border-slate-100'">
          <div class="flex items-center gap-2">
            <span class="text-xl">{{ getCountryFlag(selectedMapCountry.country) }}</span>
            <div>
              <h4 class="font-bold text-xs leading-tight" :class="isDarkTheme ? 'text-white' : 'text-slate-900'">
                {{ getDisplayCountryName(selectedMapCountry.country) }}
              </h4>
              <span class="text-[10px]" :class="isDarkTheme ? 'text-slate-400' : 'text-slate-500'">Destination Comparison</span>
            </div>
          </div>
          <button
            @click="closeSelectedCountry"
            class="cursor-pointer w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold transition-colors"
            :class="isDarkTheme ? 'bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white' : 'bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900'"
          >
            ✕
          </button>
        </div>

        <div class="space-y-2 text-xs">
          <!-- Comm A in this Country -->
          <div
            class="p-2.5 rounded-xl border space-y-1"
            :class="isDarkTheme ? 'bg-sky-950/50 border-sky-800/50 text-white' : 'bg-sky-50 border-sky-200 text-slate-900'"
            :title="selectedCodesA.length === 1 ? `[HS ${selectedCodesA[0]}] ${summaryA?.name_en || ''}` : selectedCommoditiesTooltipA"
          >
            <div class="flex justify-between items-center text-xs">
              <strong class="font-bold truncate max-w-[190px]" :class="isDarkTheme ? 'text-sky-300' : 'text-sky-800'">
                A: {{ selectedCodesA.length === 1 ? (summaryA?.name_en || 'Comm A') : `Group A (${selectedCodesA.length} crops)` }}
              </strong>

              <span class="text-[11px] font-mono font-bold" :class="isDarkTheme ? 'text-sky-400' : 'text-sky-700'">
                {{ selectedMapCountry.valA ? (selectedCodesA.length === 1 && selectedMapCountry.valA.weight_kg > 0 ? `$${(selectedMapCountry.valA.val_usd / selectedMapCountry.valA.weight_kg).toFixed(2)}/kg` : '') : 'No Export' }}
              </span>
            </div>
            <div v-if="selectedMapCountry.valA" class="flex justify-between text-[11px]" :class="isDarkTheme ? 'text-slate-300' : 'text-slate-600'">
              <span>{{ formatVolumeKg(selectedMapCountry.valA.weight_kg) }}</span>
              <strong :class="isDarkTheme ? 'text-white' : 'text-slate-900'">{{ formatRevenue(selectedMapCountry.valA.val_usd) }}</strong>
            </div>
          </div>

          <!-- Comm B in this Country -->
          <div
            class="p-2.5 rounded-xl border space-y-1"
            :class="isDarkTheme ? 'bg-amber-950/50 border-amber-800/50 text-white' : 'bg-amber-50 border-amber-200 text-slate-900'"
            :title="selectedCodesB.length === 1 ? `[HS ${selectedCodesB[0]}] ${summaryB?.name_en || ''}` : selectedCommoditiesTooltipB"
          >
            <div class="flex justify-between items-center text-xs">
              <strong class="font-bold truncate max-w-[190px]" :class="isDarkTheme ? 'text-amber-300' : 'text-amber-800'">
                🟠 B: {{ selectedCodesB.length === 1 ? (summaryB?.name_en || 'Comm B') : `Group B (${selectedCodesB.length} crops)` }}
              </strong>
              <span class="text-[11px] font-mono font-bold" :class="isDarkTheme ? 'text-amber-400' : 'text-amber-700'">
                {{ selectedMapCountry.valB ? (selectedCodesB.length === 1 && selectedMapCountry.valB.weight_kg > 0 ? `$${(selectedMapCountry.valB.val_usd / selectedMapCountry.valB.weight_kg).toFixed(2)}/kg` : '') : 'No Export' }}
              </span>
            </div>
            <div v-if="selectedMapCountry.valB" class="flex justify-between text-[11px]" :class="isDarkTheme ? 'text-slate-300' : 'text-slate-600'">
              <span>{{ formatVolumeKg(selectedMapCountry.valB.weight_kg) }}</span>
              <strong :class="isDarkTheme ? 'text-white' : 'text-slate-900'">{{ formatRevenue(selectedMapCountry.valB.val_usd) }}</strong>
            </div>
          </div>
        </div>
      </div>

      <!-- Main ECharts Map Canvas -->
      <v-chart
        ref="chartRef"
        class="w-full h-full cursor-pointer"
        style="width: 100%; height: 100%; min-height: 100%; display: block;"
        :option="comparativeMapChartOption"
        @click="onMapPointClick"
        autoresize
      />
    </div>

    <!-- ==================== SEPARATE DUAL DESTINATIONS DOCKS (A & B) ==================== -->
    <div class="absolute bottom-1.5 sm:bottom-3 left-2 sm:left-4 right-2 sm:right-4 z-20 pointer-events-none flex flex-col md:flex-row items-stretch md:items-center justify-between gap-1.5 md:gap-4">
      
      <!-- Left Dock: Commodity A Destinations Only -->
      <div
        v-if="marketsA.length > 0"
        class="pointer-events-auto backdrop-blur-md px-2.5 py-1 sm:px-3.5 sm:py-1.5 rounded-xl sm:rounded-2xl shadow-xl w-full md:max-w-[48%] items-center gap-2 text-xs transition-all border"
        :class="[
          isDarkTheme ? 'bg-slate-900/95 border-sky-500/50 text-white' : 'bg-white/95 border-sky-300 text-slate-900',
          mobileView === 'B' ? 'hidden md:flex' : 'flex'
        ]"
      >
        <div class="flex items-center gap-1.5 flex-shrink-0">
          <span class="w-2 h-2 rounded-full bg-sky-500"></span>
          <span class="font-bold text-[10px] sm:text-[11px]" :class="isDarkTheme ? 'text-sky-300' : 'text-sky-800'">A Markets ({{ marketsA.length }}):</span>
        </div>
        <div class="flex items-center gap-1.5 overflow-x-auto py-0.5 custom-scrollbar flex-1">
          <button
            v-for="m in marketsA"
            :key="`bottom-a-${m.country}`"
            @click="selectMarketA(m)"
            class="cursor-pointer flex items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-lg border text-[10px] transition-all flex-shrink-0 font-medium"
            :class="selectedMapCountry?.country === m.country 
              ? 'ring-2 ring-sky-500 bg-sky-600 text-white border-sky-600' 
              : (isDarkTheme ? 'bg-sky-950/80 hover:bg-sky-900 border-sky-800/60 text-sky-200' : 'bg-sky-50 hover:bg-sky-100 border-sky-200 text-sky-900')"
            :title="`${m.country}: ${formatVolumeKg(m.weight_kg)} | ${formatRevenue(m.val_usd)}`"
          >
            <span>{{ getCountryFlag(m.country) }}</span>
            <span class="font-semibold truncate max-w-[70px] sm:max-w-[80px]">{{ m.country }}</span>
            <span class="text-[9px] font-mono" :class="selectedMapCountry?.country === m.country ? 'text-sky-100' : (isDarkTheme ? 'text-sky-300' : 'text-sky-700')">
              {{ formatRevenue(m.val_usd) }}
            </span>
          </button>
        </div>
      </div>
      <div v-else class="pointer-events-none"></div>

      <!-- Right Dock: Commodity B Destinations Only -->
      <div
        v-if="marketsB.length > 0"
        class="pointer-events-auto backdrop-blur-md px-2.5 py-1 sm:px-3.5 sm:py-1.5 rounded-xl sm:rounded-2xl shadow-xl w-full md:max-w-[48%] items-center gap-2 text-xs justify-end transition-all border"
        :class="[
          isDarkTheme ? 'bg-slate-900/95 border-amber-500/50 text-white' : 'bg-white/95 border-amber-300 text-slate-900',
          mobileView === 'A' ? 'hidden md:flex' : 'flex'
        ]"
      >
        <div class="flex items-center gap-1.5 flex-shrink-0">
          <span class="w-2 h-2 rounded-full bg-amber-500"></span>
          <span class="font-bold text-[10px] sm:text-[11px]" :class="isDarkTheme ? 'text-amber-300' : 'text-amber-800'">B Markets ({{ marketsB.length }}):</span>
        </div>
        <div class="flex items-center gap-1.5 overflow-x-auto py-0.5 custom-scrollbar flex-1 justify-start md:justify-end">
          <button
            v-for="m in marketsB"
            :key="`bottom-b-${m.country}`"
            @click="selectMarketB(m)"
            class="cursor-pointer flex items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-lg border text-[10px] transition-all flex-shrink-0 font-medium"
            :class="selectedMapCountry?.country === m.country 
              ? 'ring-2 ring-amber-500 bg-amber-600 text-white border-amber-600' 
              : (isDarkTheme ? 'bg-amber-950/80 hover:bg-amber-900 border-amber-800/60 text-amber-200' : 'bg-amber-50 hover:bg-amber-100 border-amber-200 text-amber-900')"
            :title="`${m.country}: ${formatVolumeKg(m.weight_kg)} | ${formatRevenue(m.val_usd)}`"
          >
            <span>{{ getCountryFlag(m.country) }}</span>
            <span class="font-semibold truncate max-w-[70px] sm:max-w-[80px]">{{ m.country }}</span>
            <span class="text-[9px] font-mono" :class="selectedMapCountry?.country === m.country ? 'text-amber-100' : (isDarkTheme ? 'text-amber-300' : 'text-amber-700')">
              {{ formatRevenue(m.val_usd) }}
            </span>
          </button>
        </div>
      </div>
      <div v-else class="pointer-events-none"></div>

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
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
import {
  ArrowLeft as ArrowLeftIcon,
  Globe as GlobeIcon,
  Maximize2 as Maximize2Icon,
  Minimize2 as Minimize2Icon,
  ChevronDown as ChevronDownIcon,
  Search as SearchIcon,
  Check as CheckIcon,
  Calendar as CalendarIcon,
  Sun as SunIcon,
  Moon as MoonIcon,
} from 'lucide-vue-next';
import VChart from 'vue-echarts';
import worldGeoJson from '../assets/world.json';
import { useDatasetStore } from '../stores/datasetStore';
import { allowedYears } from '../utils/analyticsFilters';
import type { CommodityListItem, MarketBreakdownItem } from '../types/dataset';
import {
  getCountryMeta,
  getCountryFlag,
  getDisplayCountryName,
  isSameCountry,
  CAMBODIA_COORDS
} from '../utils/countryRegistry';

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

const route = useRoute();
const router = useRouter();
const store = useDatasetStore();

const containerRef = ref<HTMLElement | null>(null);
const chartRef = ref<any>(null);
const isFullscreen = ref<boolean>(false);
const isDarkTheme = ref<boolean>(false); // Default to Light Theme matching the application
const mobileView = ref<'MAP' | 'A' | 'B'>('MAP'); // Responsive mobile active tab

// Year Slicer State ('ALL' | '2023' | '2024' | ...)
const selectedYear = ref<string>('ALL');

// Support Multi-Select arrays (can be empty/null, single, or multiple)
const selectedCodesA = ref<string[]>([]);
const selectedCodesB = ref<string[]>([]);

const openDropdownA = ref<boolean>(false);
const openDropdownB = ref<boolean>(false);
const searchA = ref<string>('');
const searchB = ref<string>('');

const mapMetric = ref<'VOLUME' | 'REVENUE'>('VOLUME');
const selectedCountryName = ref<string | null>(null);

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

function initCommoditySelection() {
  const list = store.dashboardData?.commodity_list || [];
  if (!list.length) return;

  const queryA = route.query.a as string;
  const queryB = route.query.b as string;

  if (selectedCodesA.value.length === 0 && queryA && list.some(c => c.hs8_code === queryA)) {
    selectedCodesA.value = [queryA];
  }

  if (selectedCodesB.value.length === 0 && queryB && list.some(c => c.hs8_code === queryB)) {
    selectedCodesB.value = [queryB];
  }
}

onMounted(() => {
  initCommoditySelection();

  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement;
    setTimeout(resizeChart, 100);
  });

  window.addEventListener('resize', resizeChart);
  nextTick(resizeChart);
  setTimeout(resizeChart, 50);
  setTimeout(resizeChart, 200);
  setTimeout(resizeChart, 500);
});

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart);
});

// Watch when commodity options / dashboardData finishes loading from API
watch(
  () => store.dashboardData?.commodity_list,
  () => {
    initCommoditySelection();
    nextTick(resizeChart);
  },
  { deep: true, immediate: true }
);


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

const closeDropdowns = () => {
  openDropdownA.value = false;
  openDropdownB.value = false;
};

// Available Years dynamically from dataset
const availableYears = computed<number[]>(() => allowedYears(store.dashboardData));
watch(availableYears, years => {
  if (selectedYear.value !== 'ALL' && !years.includes(Number(selectedYear.value))) selectedYear.value = 'ALL';
}, { immediate: true });

// All Commodity Items for selection list
const commodityOptions = computed<CommodityListItem[]>(() => {
  return store.dashboardData?.commodity_list || [];
});

const filteredOptionsA = computed(() => {
  const q = searchA.value.toLowerCase().trim();
  if (!q) return commodityOptions.value;
  return commodityOptions.value.filter(c => 
    c.hs8_code.toLowerCase().includes(q) || 
    c.name_en.toLowerCase().includes(q) ||
    (c.name_km && c.name_km.toLowerCase().includes(q))
  );
});

const filteredOptionsB = computed(() => {
  const q = searchB.value.toLowerCase().trim();
  if (!q) return commodityOptions.value;
  return commodityOptions.value.filter(c => 
    c.hs8_code.toLowerCase().includes(q) || 
    c.name_en.toLowerCase().includes(q) ||
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

const toggleCommodityB = (code: string) => {
  const idx = selectedCodesB.value.indexOf(code);
  if (idx > -1) {
    selectedCodesB.value.splice(idx, 1);
  } else {
    selectedCodesB.value.push(code);
  }
};

const selectAllA = () => {
  selectedCodesA.value = commodityOptions.value.map(c => c.hs8_code);
};

const clearA = () => {
  selectedCodesA.value = [];
};

const selectAllB = () => {
  selectedCodesB.value = commodityOptions.value.map(c => c.hs8_code);
};

const clearB = () => {
  selectedCodesB.value = [];
};

// Tooltip helpers
const selectedCommoditiesTooltipA = computed(() => {
  if (selectedCodesA.value.length === 0) return 'No commodities selected';
  const list = store.dashboardData?.commodity_list || [];
  return selectedCodesA.value.map(code => {
    const item = list.find(c => c.hs8_code === code);
    return item ? `[HS ${code}] ${item.name_en}` : `HS ${code}`;
  }).join('\n');
});

const selectedCommoditiesTooltipB = computed(() => {
  if (selectedCodesB.value.length === 0) return 'No commodities selected';
  const list = store.dashboardData?.commodity_list || [];
  return selectedCodesB.value.map(code => {
    const item = list.find(c => c.hs8_code === code);
    return item ? `[HS ${code}] ${item.name_en}` : `HS ${code}`;
  }).join('\n');
});

// Aggregated Summary for Group A (Dynamically filtered by year)
function summarizeGroup(codes: string[]) {
  const detailsMap = store.dashboardData?.commodity_details || {};
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
      total_transactions: undefined,
      market_breakdown: yearMarkets,
      monthly_trend: yearMonths,
    };
  }

  // Multi-Commodity Aggregation
  let totValUsd = 0;
  let totValKhr = 0;
  let totWeightKg = 0;
  const marketMap = new Map<string, MarketBreakdownItem>();

  for (const code of codes) {
    const det = detailsMap[code];
    if (det) {
      if (selectedYear.value === 'ALL') {
        totValUsd += det.total_val_usd || 0;
        totValKhr += det.total_val_khr || 0;
        totWeightKg += det.total_weight_kg || 0;
        
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
    total_transactions: undefined,
    num_markets: finalMarkets.length,
    avg_price_usd_per_kg: null, // Suppress blended average price for multi-crop
    avg_price_khr_per_kg: null,
    market_breakdown: finalMarkets,
  };
}

const summaryA = computed(() => summarizeGroup(selectedCodesA.value));
const summaryB = computed(() => summarizeGroup(selectedCodesB.value));

const goBack = () => {
  router.push('/dashboard');
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
  const found = combinedMarkets.value.find(m => isSameCountry(m.country, target));
  if (found) return found;
  return {
    country: target,
    valA: null,
    valB: null
  };
});

const closeSelectedCountry = () => {
  selectedCountryName.value = null;
  const inst = getChartInstance();
  if (inst && typeof inst.dispatchAction === 'function') {
    inst.dispatchAction({ type: 'hideTip' });
  }
};

const selectMarketA = (m: MarketBreakdownItem) => {
  selectedCountryName.value = m.country;
  const inst = getChartInstance();
  if (inst && typeof inst.dispatchAction === 'function') {
    inst.dispatchAction({ type: 'hideTip' });
  }
};

const selectMarketB = (m: MarketBreakdownItem) => {
  selectedCountryName.value = m.country;
  const inst = getChartInstance();
  if (inst && typeof inst.dispatchAction === 'function') {
    inst.dispatchAction({ type: 'hideTip' });
  }
};

const onMapPointClick = (params: any) => {
  if (hasMoved.value) return;

  const inst = getChartInstance();
  if (inst && typeof inst.dispatchAction === 'function') {
    inst.dispatchAction({ type: 'hideTip' });
  }

  if (params.data?.marketItem) {
    selectedCountryName.value = params.data.marketItem.country;
  } else if (params.name) {
    const found = combinedMarkets.value.find(m => isSameCountry(m.country, params.name));
    if (found) {
      selectedCountryName.value = found.country;
    } else {
      selectedCountryName.value = params.name;
    }
  }
};

// Comparative Global Map Option (Dynamic Light vs Dark Theme)
const comparativeMapChartOption = computed(() => {
  const isDark = isDarkTheme.value;
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
    if (m.valA && !m.valB) pointColor = isDark ? '#38bdf8' : '#0284c7'; // A only
    else if (!m.valA && m.valB) pointColor = isDark ? '#fbbf24' : '#d97706'; // B only

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
        color: isDark ? '#f8fafc' : '#0f172a',
        fontSize: 10,
        fontWeight: 'bold',
        textBorderColor: isDark ? '#090d16' : '#ffffff',
        textBorderWidth: 3,
        distance: 6,
      },
      itemStyle: {
        color: pointColor,
        borderColor: '#ffffff',
        borderWidth: 1.5,
        shadowBlur: isDark ? 12 : 6,
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
        color: m.valB 
          ? (isDark ? 'rgba(16, 185, 129, 0.75)' : 'rgba(16, 185, 129, 0.85)')
          : (isDark ? 'rgba(56, 189, 248, 0.75)' : 'rgba(2, 132, 199, 0.85)'),
        width: 2.2,
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
        color: isDark ? 'rgba(251, 191, 36, 0.75)' : 'rgba(217, 119, 6, 0.85)',
        width: 2.2,
        curveness: -0.2,
      }
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
      label: { show: false },
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
      {
        name: 'Export Routes Comm A',
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
        },
        data: flowLinesA,
      },
      {
        name: 'Export Routes Comm B',
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
        },
        data: flowLinesB,
      },
      {
        name: 'Destination Markets',
        type: 'scatter',
        coordinateSystem: 'geo',
        z: 3,
        data: scatterPoints,
      },
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
    ]
  };
});
</script>
