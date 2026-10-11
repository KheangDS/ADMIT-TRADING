<script setup lang="ts">
import { computed, onMounted, ref, reactive } from 'vue';
import { api } from '../api';
import type { RegistryEntry } from '../types';
import RegistryEditor from '../components/RegistryEditor.vue';
import TaskNotice from '../components/TaskNotice.vue';
import { useTask } from '../composables/useTask';
import {
  Package as PackageIcon,
  Globe as GlobeIcon,
  Search as SearchIcon,
  Plus as PlusIcon,
  Edit3 as EditIcon,
  ChevronDown as ChevronDownIcon,
  ChevronRight as ChevronRightIcon,
  Layers as LayersIcon,
  Maximize2 as Maximize2Icon,
  Minimize2 as Minimize2Icon,
  RefreshCw as RefreshCwIcon,
  X as XIcon,
} from 'lucide-vue-next';

const entries = ref<RegistryEntry[]>([]);
const activeTab = ref<'commodities' | 'countries'>('commodities');
const search = ref('');
const editorOpen = ref(false);
const editingEntry = ref<RegistryEntry | null>(null);
const initialKind = ref<RegistryEntry['kind']>('hs4');
const initialParentCode = ref<string>('');

// Collapsed state tracking for HS4 chapters (key: hs4 code, value: boolean isExpanded)
const expandedChapters = reactive<Record<string, boolean>>({});

const { busy, error, notice, run } = useTask();

async function load() {
  await run(async () => {
    const res = await api.get<RegistryEntry[]>('/admin/registry');
    entries.value = Array.isArray(res.data) ? res.data : [];
    // Expand top 10 chapters by default
    const hs4s = entries.value.filter((e) => e.kind === 'hs4');
    for (const h of hs4s) {
      if (expandedChapters[h.code] === undefined) {
        expandedChapters[h.code] = true;
      }
    }
  });
}

const hs4Entries = computed(() => entries.value.filter((e) => e.kind === 'hs4'));
const hs8Entries = computed(() => entries.value.filter((e) => e.kind === 'hs8'));
const countryEntries = computed(() => entries.value.filter((e) => e.kind === 'country'));

// Group HS8 commodities by their HS4 parent code
const hs8ByParent = computed(() => {
  const map: Record<string, RegistryEntry[]> = {};
  for (const item of hs8Entries.value) {
    const parent = item.parent_code || item.code.slice(0, 4);
    if (!map[parent]) map[parent] = [];
    map[parent].push(item);
  }
  for (const p in map) {
    map[p].sort((a, b) => a.code.localeCompare(b.code));
  }
  return map;
});

// Filtered and grouped commodities
interface ChapterGroup {
  chapter: RegistryEntry;
  items: RegistryEntry[];
  matchesFilter: boolean;
}

const filteredCommodityGroups = computed<ChapterGroup[]>(() => {
  const q = search.value.trim().toLowerCase();
  const sortedChapters = [...hs4Entries.value].sort((a, b) => a.code.localeCompare(b.code));

  return sortedChapters
    .map((chapter) => {
      const allItems = hs8ByParent.value[chapter.code] || [];
      if (!q) {
        return {
          chapter,
          items: allItems,
          matchesFilter: true,
        };
      }

      const chapterMatches =
        chapter.code.toLowerCase().includes(q) ||
        chapter.name_en.toLowerCase().includes(q) ||
        chapter.name_km.toLowerCase().includes(q);

      const matchingItems = allItems.filter(
        (item) =>
          item.code.toLowerCase().includes(q) ||
          item.name_en.toLowerCase().includes(q) ||
          item.name_km.toLowerCase().includes(q),
      );

      if (chapterMatches) {
        return {
          chapter,
          items: allItems,
          matchesFilter: true,
        };
      }

      if (matchingItems.length > 0) {
        return {
          chapter,
          items: matchingItems,
          matchesFilter: true,
        };
      }

      return null;
    })
    .filter((g): g is ChapterGroup => g !== null);
});

// Standalone HS8 commodities whose parent HS4 is not registered in the system
const orphanHs8 = computed(() => {
  const q = search.value.trim().toLowerCase();
  const knownHs4Codes = new Set(hs4Entries.value.map((h) => h.code));
  const orphans = hs8Entries.value.filter((item) => {
    const parent = item.parent_code || item.code.slice(0, 4);
    return !knownHs4Codes.has(parent);
  });

  if (!q) return orphans;
  return orphans.filter(
    (item) =>
      item.code.toLowerCase().includes(q) ||
      item.name_en.toLowerCase().includes(q) ||
      item.name_km.toLowerCase().includes(q),
  );
});

// Filtered countries
const filteredCountries = computed(() => {
  const q = search.value.trim().toLowerCase();
  const sorted = [...countryEntries.value].sort((a, b) => a.name_en.localeCompare(b.name_en));
  if (!q) return sorted;
  return sorted.filter(
    (c) =>
      c.code.toLowerCase().includes(q) ||
      c.name_en.toLowerCase().includes(q) ||
      c.name_km.toLowerCase().includes(q) ||
      (c.iso3 && c.iso3.toLowerCase().includes(q)) ||
      c.aliases.some((a) => a.toLowerCase().includes(q)),
  );
});

function toggleChapter(code: string) {
  expandedChapters[code] = !expandedChapters[code];
}

function expandAllChapters(expand: boolean) {
  for (const h of hs4Entries.value) {
    expandedChapters[h.code] = expand;
  }
}

function openAdd(kind?: RegistryEntry['kind'], parentCode?: string) {
  editingEntry.value = null;
  initialKind.value = kind || (activeTab.value === 'commodities' ? 'hs4' : 'country');
  initialParentCode.value = parentCode || '';
  editorOpen.value = true;
}

function openEdit(entry: RegistryEntry) {
  editingEntry.value = entry;
  initialKind.value = entry.kind;
  initialParentCode.value = entry.parent_code || '';
  editorOpen.value = true;
}

async function onSaved() {
  editorOpen.value = false;
  editingEntry.value = null;
  await load();
  if (!error.value) {
    notice.value = 'Dictionary entry saved successfully. All future imports will use this definition.';
  }
}

function formatHsCode(code: string): string {
  if (code.length === 8) {
    return `${code.slice(0, 4)}.${code.slice(4, 6)}.${code.slice(6, 8)}`;
  }
  return code;
}

onMounted(load);
</script>

<template>
  <div class="space-y-6 w-full max-w-[1560px] mx-auto pb-12">
    <!-- Page Header -->
    <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 sm:pb-4">
      <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">Dictionary</h1>
      <button
        type="button"
        class="btn-primary inline-flex items-center gap-1.5 !px-2.5 !py-1 sm:!px-3.5 sm:!py-1.5 text-xs font-bold rounded-lg bg-sky-600 hover:bg-sky-700 text-white transition cursor-pointer shadow-xs flex-shrink-0"
        @click="openAdd()"
      >
        <PlusIcon class="w-3.5 h-3.5" />
        <span>Add Entry</span>
      </button>
    </div>

    <TaskNotice :busy="busy" :error="error" :notice="notice" />

    <!-- Overlay / Modal for Editor -->
    <div
      v-if="editorOpen"
      class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto"
      @click.self="editorOpen = false"
    >
      <div class="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <RegistryEditor
          :entry="editingEntry"
          :existing="!!editingEntry"
          :initial-kind="initialKind"
          :initial-parent-code="initialParentCode"
          @saved="onSaved"
          @cancel="editorOpen = false"
        />
      </div>
    </div>

    <!-- Section Navigation Tabs & Search Toolbar -->
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 pb-1">
      <!-- Modern 2-Column Segmented Pill Tabs (Horizontal on all screen sizes) -->
      <div class="grid grid-cols-2 p-1 bg-slate-200/70 border border-slate-200/80 rounded-2xl shadow-inner gap-1 w-full lg:w-auto flex-shrink-0">
        <button
          type="button"
          class="tab-btn inline-flex items-center justify-center sm:justify-between gap-2 !px-2.5 !py-1.5 sm:!px-3 sm:!py-1.5 text-xs font-bold rounded-xl transition cursor-pointer"
          :class="
            activeTab === 'commodities'
              ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
          "
          @click="activeTab = 'commodities'"
        >
          <span class="inline-flex items-center gap-1.5">
            <PackageIcon class="w-3.5 h-3.5" :class="activeTab === 'commodities' ? 'text-sky-600' : 'text-slate-400'" />
            <span>Commodities</span>
          </span>
          <span
            class="px-1.5 py-0.5 text-[10px] font-mono rounded-md"
            :class="activeTab === 'commodities' ? 'bg-sky-50 text-sky-800 border border-sky-200/80 font-bold' : 'bg-slate-200 text-slate-600 font-semibold'"
          >
            <span class="sm:hidden">{{ hs8Entries.length }}</span>
            <span class="hidden sm:inline">{{ hs4Entries.length }} Ch · {{ hs8Entries.length }} Items</span>
          </span>
        </button>

        <button
          type="button"
          class="tab-btn inline-flex items-center justify-center sm:justify-between gap-2 !px-2.5 !py-1.5 sm:!px-3 sm:!py-1.5 text-xs font-bold rounded-xl transition cursor-pointer"
          :class="
            activeTab === 'countries'
              ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
          "
          @click="activeTab = 'countries'"
        >
          <span class="inline-flex items-center gap-1.5">
            <GlobeIcon class="w-3.5 h-3.5" :class="activeTab === 'countries' ? 'text-emerald-600' : 'text-slate-400'" />
            <span>Countries</span>
          </span>
          <span
            class="px-1.5 py-0.5 text-[10px] font-mono rounded-md"
            :class="activeTab === 'countries' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200/80 font-bold' : 'bg-slate-200 text-slate-600 font-semibold'"
          >
            <span class="sm:hidden">{{ countryEntries.length }}</span>
            <span class="hidden sm:inline">{{ countryEntries.length }} Countries</span>
          </span>
        </button>
      </div>

      <!-- Right: Action Controls (Expand, Collapse, Chapter) & Search Bar -->
      <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between sm:justify-end gap-2 w-full lg:w-auto">
        <!-- Search Bar (Full width on mobile, compact on tablet/desktop) -->
        <div class="search-field w-full sm:w-56 lg:w-64 flex-shrink-0 order-1 sm:order-2">
          <SearchIcon class="search-icon" />
          <input
            v-model="search"
            type="search"
            :placeholder="
              activeTab === 'commodities'
                ? 'Search chapters...'
                : 'Search countries...'
            "
          />
          <button
            v-if="search"
            type="button"
            class="search-clear-btn"
            aria-label="Clear search"
            @click="search = ''"
          >
            <XIcon class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Action Buttons Row -->
        <div class="flex items-center justify-between sm:justify-end gap-2 w-full sm:w-auto order-2 sm:order-1">
          <!-- Action Buttons for Commodities -->
          <template v-if="activeTab === 'commodities'">
            <div class="flex items-center gap-1.5">
              <button
                type="button"
                class="btn-secondary inline-flex items-center gap-1 !px-2.5 !py-1 text-[11px] sm:text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition cursor-pointer shadow-2xs"
                @click="expandAllChapters(true)"
              >
                <Maximize2Icon class="w-3.5 h-3.5 text-slate-500" />
                <span>Expand</span>
              </button>
              <button
                type="button"
                class="btn-secondary inline-flex items-center gap-1 !px-2.5 !py-1 text-[11px] sm:text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl transition cursor-pointer shadow-2xs"
                @click="expandAllChapters(false)"
              >
                <Minimize2Icon class="w-3.5 h-3.5 text-slate-500" />
                <span>Collapse</span>
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- SECTION 1: COMMODITIES (Grouped by HS4 Chapter Class)                     -->
    <!-- ========================================================================= -->
    <div v-if="activeTab === 'commodities'" class="space-y-2.5 sm:space-y-3">
      <!-- List of HS4 Chapter Classes -->
      <div class="space-y-2.5 sm:space-y-3">
        <div
          v-for="group in filteredCommodityGroups"
          :key="group.chapter.code"
          class="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden transition-all hover:border-slate-300"
        >
          <!-- HS4 Chapter Card Header -->
          <div
            class="p-2.5 sm:p-3.5 bg-slate-50/60 hover:bg-slate-100/70 flex items-center justify-between gap-2 sm:gap-3 cursor-pointer select-none transition border-b border-transparent"
            :class="{ '!border-slate-200 !bg-slate-100/80': expandedChapters[group.chapter.code] }"
            @click="toggleChapter(group.chapter.code)"
          >
            <div class="flex items-center gap-2 sm:gap-2.5 min-w-0 flex-1">
              <div
                class="w-6 h-6 sm:w-6.5 sm:h-6.5 rounded-lg bg-white border border-slate-200/90 flex items-center justify-center text-slate-500 shadow-2xs flex-shrink-0"
              >
                <ChevronDownIcon
                  v-if="expandedChapters[group.chapter.code]"
                  class="w-3.5 h-3.5 text-slate-700"
                />
                <ChevronRightIcon v-else class="w-3.5 h-3.5 text-slate-400" />
              </div>

              <span class="px-1.5 py-0.5 rounded-md text-[10px] sm:text-xs font-mono font-bold bg-sky-50 text-sky-800 border border-sky-200 flex-shrink-0">
                HS4 {{ group.chapter.code }}
              </span>

              <div class="min-w-0">
                <span class="text-xs sm:text-sm font-bold text-slate-900 block truncate">
                  {{ group.chapter.name_en }}
                </span>
                <span v-if="group.chapter.name_km" class="text-[11px] text-slate-500 block truncate" lang="km">
                  {{ group.chapter.name_km }}
                </span>
              </div>
            </div>

            <div class="flex items-center gap-1 sm:gap-1.5 flex-shrink-0" @click.stop>
              <span class="hidden xs:inline-block px-1.5 py-0.5 rounded-full text-[10px] sm:text-[11px] font-semibold bg-slate-200/70 text-slate-700 border border-slate-200/60">
                {{ group.items.length }} {{ group.items.length === 1 ? 'item' : 'items' }}
              </span>
              <button
                type="button"
                title="Add commodity under this chapter"
                class="inline-flex items-center justify-center gap-1 !p-0 w-6.5 h-6.5 sm:w-auto sm:!px-2 sm:!py-1 text-[11px] font-semibold text-sky-700 bg-sky-50 hover:bg-sky-100 hover:text-sky-800 rounded-lg border border-sky-200 transition cursor-pointer shadow-2xs"
                @click="openAdd('hs8', group.chapter.code)"
              >
                <PlusIcon class="w-3.5 h-3.5 text-sky-600" />
                <span class="hidden sm:inline">Add</span>
              </button>
              <button
                type="button"
                title="Edit chapter names"
                class="btn-ghost inline-flex items-center gap-1 !px-2 !py-1 text-[11px] font-medium text-slate-500 hover:text-slate-900 hover:bg-slate-200/60 rounded-lg transition cursor-pointer h-6.5 sm:h-auto"
                @click="openEdit(group.chapter)"
              >
                <EditIcon class="w-3 h-3" />
                <span>Edit</span>
              </button>
            </div>
          </div>

          <!-- Expanded HS8 Commodities Sub-Table -->
          <div v-show="expandedChapters[group.chapter.code]" class="divide-y divide-slate-100">
            <div v-if="group.items.length === 0" class="p-6 text-center text-xs text-slate-400 italic">
              No 8-digit commodity tariff lines registered under Chapter {{ group.chapter.code }} yet.
              <button
                type="button"
                class="text-sky-600 font-bold hover:underline ml-1 cursor-pointer bg-transparent border-0 shadow-none p-0 inline"
                @click="openAdd('hs8', group.chapter.code)"
              >
                + Add first commodity
              </button>
            </div>

            <div v-else class="overflow-x-auto">
              <table class="w-full text-left border-collapse min-w-[560px]">
                <thead>
                  <tr class="bg-slate-50/50 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-100">
                    <th class="py-2.5 px-4 w-36">HS8 Code</th>
                    <th class="py-2.5 px-4">Commodity Name (English)</th>
                    <th class="py-2.5 px-4">Commodity Name (Khmer)</th>
                    <th class="py-2.5 px-4 text-right w-24">Action</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 text-xs">
                  <tr
                    v-for="item in group.items"
                    :key="item.code"
                    class="hover:bg-slate-50/70 transition"
                  >
                    <td class="py-2.5 px-4 font-mono font-bold text-slate-700">
                      <span class="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200/60">
                        {{ formatHsCode(item.code) }}
                      </span>
                    </td>
                    <td class="py-2.5 px-4 font-semibold text-slate-900">
                      {{ item.name_en }}
                    </td>
                    <td class="py-2.5 px-4 font-medium text-slate-600" lang="km">
                      {{ item.name_km }}
                    </td>
                    <td class="py-2.5 px-4 text-right">
                      <button
                        type="button"
                        class="btn-ghost inline-flex items-center gap-1 !px-2 !py-0.5 text-xs font-semibold text-slate-500 hover:text-sky-700 hover:bg-sky-50 rounded-lg transition cursor-pointer"
                        @click="openEdit(item)"
                      >
                        <EditIcon class="w-3.5 h-3.5" />
                        <span>Edit</span>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Standalone / Orphan HS8 Items (if any exist without registered HS4) -->
        <div
          v-if="orphanHs8.length > 0"
          class="bg-amber-50/40 rounded-2xl border border-amber-200 shadow-xs overflow-hidden"
        >
          <div class="p-3.5 sm:p-4 bg-amber-100/50 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-amber-200 text-amber-900">
                Unassigned Chapters
              </span>
              <span class="text-xs font-bold text-amber-900">
                These HS8 commodities have parent codes that are not yet in the HS4 dictionary.
              </span>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
              <tbody class="divide-y divide-amber-100">
                <tr v-for="item in orphanHs8" :key="item.code" class="hover:bg-amber-50">
                  <td class="py-2.5 px-4 font-mono font-bold text-slate-800 w-36">
                    <span class="inline-block px-2 py-0.5 rounded bg-amber-100/80 text-amber-900 border border-amber-200">
                      {{ formatHsCode(item.code) }}
                    </span>
                  </td>
                  <td class="py-2.5 px-4 font-medium text-slate-900">
                    {{ item.name_en }}
                  </td>
                  <td class="py-2.5 px-4 font-medium text-slate-700" lang="km">
                    {{ item.name_km }}
                  </td>
                  <td class="py-2.5 px-4 text-right w-24">
                    <button
                      type="button"
                      class="btn-ghost inline-flex items-center gap-1 !px-2 !py-0.5 text-xs font-semibold text-amber-800 hover:bg-amber-100 rounded-md transition cursor-pointer"
                      @click="openEdit(item)"
                    >
                      <EditIcon class="w-3.5 h-3.5" />
                      <span>Edit</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Empty state when no commodities match search -->
        <div
          v-if="filteredCommodityGroups.length === 0 && orphanHs8.length === 0"
          class="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500 text-xs"
        >
          No chapters or commodities found matching "{{ search }}".
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- SECTION 2: DESTINATION COUNTRIES                                         -->
    <!-- ========================================================================= -->
    <div v-else class="space-y-3 sm:space-y-4">
      <!-- Countries Table -->
      <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse min-w-[580px]">
            <thead>
              <tr class="bg-slate-50/70 text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-200">
                <th class="py-3 px-4 w-28">ISO3 Code</th>
                <th class="py-3 px-4">English Name</th>
                <th class="py-3 px-4">Khmer Name</th>
                <th class="py-3 px-4">Recognized File Aliases</th>
                <th class="py-3 px-4 text-right w-24">Action</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 text-xs">
              <tr
                v-for="country in filteredCountries"
                :key="country.code"
                class="hover:bg-slate-50/70 transition"
              >
                <td class="py-3 px-4">
                  <span class="inline-block px-2.5 py-1 rounded-lg text-xs font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200/80">
                    {{ country.iso3 || country.code }}
                  </span>
                </td>
                <td class="py-3 px-4 font-bold text-slate-900">
                  {{ country.name_en }}
                </td>
                <td class="py-3 px-4 font-medium text-slate-700" lang="km">
                  {{ country.name_km }}
                </td>
                <td class="py-3 px-4">
                  <div v-if="country.aliases && country.aliases.length > 0" class="flex flex-wrap gap-1">
                    <span
                      v-for="alias in country.aliases"
                      :key="alias"
                      class="inline-block px-2 py-0.5 rounded-md text-[11px] bg-slate-100 text-slate-600 border border-slate-200/60"
                    >
                      {{ alias }}
                    </span>
                  </div>
                  <span v-else class="text-slate-300 italic">—</span>
                </td>
                <td class="py-3 px-4 text-right">
                  <button
                    type="button"
                    class="btn-ghost inline-flex items-center gap-1 !px-2 !py-0.5 text-xs font-semibold text-slate-500 hover:text-sky-700 hover:bg-sky-50 rounded-md transition cursor-pointer"
                    @click="openEdit(country)"
                  >
                    <EditIcon class="w-3.5 h-3.5" />
                    <span>Edit</span>
                  </button>
                </td>
              </tr>
              <tr v-if="filteredCountries.length === 0">
                <td colspan="5" class="p-12 text-center text-slate-400 italic">
                  No destination countries found matching "{{ search }}".
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
