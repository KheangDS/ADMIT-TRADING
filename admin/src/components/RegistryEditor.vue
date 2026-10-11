<script setup lang="ts">
import { reactive, watch, computed, ref, onMounted } from 'vue';
import { api } from '../api';
import type { RegistryEntry } from '../types';
import { useTask } from '../composables/useTask';
import TaskNotice from './TaskNotice.vue';
import { Search as SearchIcon, Link as LinkIcon, PlusCircle as PlusCircleIcon } from 'lucide-vue-next';

const props = defineProps<{
  entry?: RegistryEntry | null;
  existing?: boolean;
  initialKind?: RegistryEntry['kind'];
  initialParentCode?: string;
}>();
const emit = defineEmits<{ saved: [entry: RegistryEntry]; cancel: [] }>();

const form = reactive({
  kind: 'hs4' as RegistryEntry['kind'],
  code: '',
  name_en: '',
  name_km: '',
  parent_code: '',
  iso3: '',
  aliases: '',
});

const existingCountries = ref<RegistryEntry[]>([]);
const countrySearch = ref('');
const selectedExistingCode = ref('');
const countryMode = ref<'map' | 'create'>('map');

watch(
  () => [props.entry, props.initialKind, props.initialParentCode] as const,
  ([entry, initKind, initParent]) => {
    Object.assign(
      form,
      entry
        ? {
            ...entry,
            parent_code: entry.parent_code || '',
            iso3: entry.iso3 || '',
            aliases: (entry.aliases || []).join('\n'),
          }
        : {
            kind: initKind || 'hs4',
            code: '',
            name_en: '',
            name_km: '',
            parent_code: initParent || '',
            iso3: '',
            aliases: '',
          },
    );
  },
  { immediate: true },
);

const { busy, error, run } = useTask();

const isHS8 = computed(() => form.kind === 'hs8');
const isHS4 = computed(() => form.kind === 'hs4');
const isCountry = computed(() => form.kind === 'country');

const detectedLabel = computed(() => {
  return form.aliases.split('\n')[0] || form.code;
});

const filteredCountries = computed(() => {
  const q = countrySearch.value.trim().toLowerCase();
  if (!q) return existingCountries.value;
  return existingCountries.value.filter(
    (c) =>
      c.name_en.toLowerCase().includes(q) ||
      c.name_km.toLowerCase().includes(q) ||
      (c.iso3 && c.iso3.toLowerCase().includes(q)) ||
      c.code.toLowerCase().includes(q) ||
      (c.aliases && c.aliases.some((a) => a.toLowerCase().includes(q)))
  );
});

const selectedTargetCountry = computed(() => {
  return existingCountries.value.find((c) => c.code === selectedExistingCode.value) || null;
});

const title = computed(() => {
  if (props.existing) {
    if (isHS8.value) return `Edit Commodity (HS8: ${form.code})`;
    if (isHS4.value) return `Edit Chapter (HS4: ${form.code})`;
    if (isCountry.value) return `Edit Country (${form.name_en || form.code})`;
    return 'Edit Dictionary Entry';
  }
  if (props.entry) {
    if (isHS8.value) return `Resolve Product Name (HS8: ${form.code})`;
    if (isHS4.value) return `Resolve Chapter Name (HS4: ${form.code})`;
    if (isCountry.value) {
      return `Resolve Destination Country ("${detectedLabel.value}")`;
    }
  }
  if (isHS8.value) return 'Add New Commodity (HS8)';
  if (isHS4.value) return 'Add New Chapter (HS4)';
  if (isCountry.value) return 'Add New Country';
  return 'Add Dictionary Entry';
});

onMounted(async () => {
  if (isCountry.value) {
    try {
      const { data } = await api.get<RegistryEntry[]>('/admin/registry');
      existingCountries.value = Array.isArray(data) ? data.filter((e) => e.kind === 'country') : [];
      if (existingCountries.value.length > 0 && !props.existing && props.entry) {
        countryMode.value = 'map';
        const raw = detectedLabel.value.toLowerCase();
        const best = existingCountries.value.find(
          (c) =>
            c.name_en.toLowerCase() === raw ||
            c.name_km.toLowerCase() === raw ||
            (c.iso3 && c.iso3.toLowerCase() === raw)
        );
        selectedExistingCode.value = best ? best.code : existingCountries.value[0].code;
      } else {
        countryMode.value = 'create';
      }
    } catch {
      existingCountries.value = [];
      countryMode.value = 'create';
    }
  }
});

async function save() {
  await run(async () => {
    // Mode 1: Linking an unknown country label to an existing registered country
    if (isCountry.value && countryMode.value === 'map' && props.entry && !props.existing) {
      const target = selectedTargetCountry.value;
      if (!target) {
        throw new Error('Please select an existing country to link with, or switch to "Create Brand New Country".');
      }
      const raw = detectedLabel.value.trim();
      const body = {
        kind: 'country',
        code: target.code,
        name_en: target.name_en,
        name_km: target.name_km,
        iso3: target.iso3,
        aliases: raw ? [raw] : [],
      };
      const { data } = await api.post<RegistryEntry>('/admin/registry', body);
      emit('saved', data);
      return;
    }

    // Mode 2: Manual Creation or Direct Edit for Country, HS4, or HS8
    if (!form.name_en.trim() || !form.name_km.trim()) {
      throw new Error('Both English name and Khmer name are required.');
    }
    const aliasesList = props.existing && isCountry.value
      ? form.aliases.split(/[\n,]+/).map((s) => s.trim()).filter(Boolean)
      : (props.entry?.aliases || []).filter(Boolean);

    const body = {
      ...form,
      code: form.code.trim(),
      name_en: form.name_en.trim(),
      name_km: form.name_km.trim(),
      parent_code: form.kind === 'hs8' ? form.parent_code.trim() || null : null,
      iso3: form.kind === 'country' ? form.iso3.trim() || null : null,
      aliases: aliasesList,
    };
    const path = `/admin/registry/${form.kind}/${encodeURIComponent(form.code)}`;
    const { data } = props.existing
      ? await api.put<RegistryEntry>(path, body)
      : await api.post<RegistryEntry>('/admin/registry', body);
    emit('saved', data);
  });
}
</script>

<template>
  <form class="card bg-white border border-slate-200 rounded-2xl shadow-sm p-6 space-y-4" @submit.prevent="save">
    <div class="flex items-center justify-between border-b border-slate-100 pb-3">
      <h2 class="text-base font-bold text-slate-900 m-0">{{ title }}</h2>
      <span class="px-2.5 py-1 rounded-full text-xs font-mono font-bold uppercase bg-sky-50 text-sky-700 border border-sky-200">
        {{ form.kind }}
      </span>
    </div>

    <TaskNotice :busy="busy" :error="error" />

    <fieldset :disabled="busy" class="space-y-4">
      <!-- Readonly / Context info bar when resolving detected unknowns -->
      <div v-if="props.entry" class="p-3 bg-slate-50 rounded-xl border border-slate-200/80 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
        <label class="block space-y-1 text-left">
          <span class="text-slate-500 font-semibold block text-[10px] uppercase">Detected Code</span>
          <input :value="form.code" readonly class="block w-full text-xs font-mono bg-slate-100/80 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 font-bold focus:outline-none" />
        </label>
        <div v-if="isHS8 && form.parent_code" class="flex flex-col justify-center">
          <span class="text-slate-500 font-semibold block text-[10px] uppercase">Parent Chapter (HS4)</span>
          <span class="font-mono font-bold text-sky-700 text-sm mt-1">HS4 {{ form.parent_code }}</span>
        </div>
        <div v-if="isCountry" class="flex flex-col justify-center">
          <span class="text-slate-500 font-semibold block text-[10px] uppercase">Detected Label in File</span>
          <span class="font-bold text-emerald-700 text-sm mt-1">{{ detectedLabel }}</span>
        </div>
      </div>

      <!-- Country Mode Selector Tabs (Shown only when resolving a country with entry prop) -->
      <div v-if="isCountry && props.entry && existingCountries.length > 0" class="pt-1">
        <div class="flex items-center gap-1.5 p-1 bg-slate-100/80 border border-slate-200/70 rounded-xl max-w-fit">
          <button
            type="button"
            class="px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer inline-flex items-center gap-1.5"
            :class="countryMode === 'map' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="countryMode = 'map'"
          >
            <LinkIcon class="w-3.5 h-3.5" />
            <span>Map to Existing Country (Recommended)</span>
          </button>
          <button
            type="button"
            class="px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer inline-flex items-center gap-1.5"
            :class="countryMode === 'create' ? 'bg-white text-sky-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'"
            @click="countryMode = 'create'"
          >
            <PlusCircleIcon class="w-3.5 h-3.5" />
            <span>Create Brand New Country</span>
          </button>
        </div>
      </div>

      <!-- MODE A: MAP TO EXISTING COUNTRY -->
      <div v-if="isCountry && props.entry && countryMode === 'map' && existingCountries.length > 0" class="space-y-3 pt-1">
        <div class="space-y-2">
          <label class="block text-xs font-bold text-slate-700 text-left">
            Search & Select Existing Country:
          </label>
          <div class="search-field w-full">
            <SearchIcon class="search-icon" />
            <input 
              v-model="countrySearch" 
              type="search" 
              placeholder="Type to filter country (e.g. Finland, ហ្វាំងឡង់, FIN, VNM)..."
            />
          </div>
          <select 
            v-model="selectedExistingCode" 
            size="6" 
            required
            class="block w-full text-xs font-medium border border-slate-200 rounded-xl p-2 bg-white focus:ring-2 focus:ring-sky-500 focus:outline-none cursor-pointer divide-y divide-slate-100"
          >
            <option 
              v-for="c in filteredCountries" 
              :key="c.code" 
              :value="c.code"
              class="py-1.5 px-2 rounded-lg hover:bg-sky-50 cursor-pointer"
            >
              {{ c.name_en }} ({{ c.name_km }} · {{ c.iso3 || c.code }})
            </option>
            <option v-if="!filteredCountries.length" disabled class="py-2 px-2 text-slate-400 italic">
              No matching country found. Switch to "Create Brand New Country" tab above.
            </option>
          </select>
        </div>

        <!-- Link Preview Confirmation -->
        <div v-if="selectedTargetCountry" class="p-3 bg-sky-50/80 border border-sky-200 rounded-xl text-xs text-sky-950 flex items-center gap-2.5">
          <LinkIcon class="w-4 h-4 text-sky-600 flex-shrink-0" />
          <span>
            Will permanently link <strong>"{{ detectedLabel }}"</strong> as an alias to <strong>{{ selectedTargetCountry.name_en }} ({{ selectedTargetCountry.name_km }} · {{ selectedTargetCountry.iso3 || selectedTargetCountry.code }})</strong>.
          </span>
        </div>
      </div>

      <!-- MODE B: CREATE NEW / DIRECT FORM FOR HS8, HS4 OR NEW COUNTRY -->
      <div v-else class="space-y-4">
        <!-- General Kind & Code Selector (Shown only when manually adding a new entry from Registry page) -->
        <div v-if="!props.entry" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="block space-y-1 text-left">
            <span class="text-xs font-bold text-slate-700">Kind</span>
            <select v-model="form.kind" class="block w-full text-xs border border-slate-200 rounded-xl px-3 py-2 bg-white focus:ring-2 focus:ring-sky-500 focus:outline-none">
              <option value="hs4">HS4 (4-digit Chapter)</option>
              <option value="hs8">HS8 (8-digit Product)</option>
              <option value="country">Country</option>
            </select>
          </label>
          <label class="block space-y-1 text-left">
            <span class="text-xs font-bold text-slate-700">Code</span>
            <input v-model="form.code" required class="block w-full text-xs font-mono border border-slate-200 rounded-xl px-3 py-2 focus:ring-2 focus:ring-sky-500 focus:outline-none" />
          </label>
        </div>

        <!-- Primary Bilingual Names (Required for ALL kinds) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="block space-y-1 text-left">
            <span class="text-xs font-bold text-slate-700">English name <span class="text-rose-500">*</span></span>
            <input 
              v-model="form.name_en" 
              required 
              class="block w-full text-xs border border-slate-200 rounded-xl px-3 py-2 bg-white focus:ring-2 focus:ring-sky-500 focus:outline-none" 
              :placeholder="isCountry ? 'e.g. Cambodia' : ''"
            />
          </label>
          <label class="block space-y-1 text-left">
            <span class="text-xs font-bold text-slate-700">Khmer name <span class="text-rose-500">*</span></span>
            <input 
              v-model="form.name_km" 
              required 
              lang="km" 
              class="block w-full text-xs border border-slate-200 rounded-xl px-3 py-2 bg-white focus:ring-2 focus:ring-sky-500 focus:outline-none" 
              :placeholder="isCountry ? 'e.g. កម្ពុជា' : ''"
            />
          </label>
        </div>

        <!-- Country-specific fields: ISO3 Code (Strict format examples) -->
        <div v-if="isCountry" class="space-y-4 pt-1">
          <label class="block space-y-1 text-left">
            <span class="text-xs font-bold text-slate-700">ISO3 Country Code (3 letters)</span>
            <input 
              v-model="form.iso3" 
              pattern="[A-Za-z]{3}" 
              maxlength="3" 
              class="block w-full sm:w-48 text-xs font-mono uppercase border border-slate-200 rounded-xl px-3 py-2 bg-white focus:ring-2 focus:ring-sky-500 focus:outline-none" 
              placeholder="e.g. KHM"
            />
            <small class="text-[11px] text-slate-500 block">Strict 3-letter uppercase ISO standard (e.g. KHM, TLS, USA, CHN)</small>
          </label>
        </div>

        <!-- Manual Standalone HS8 Parent (only when manually creating an HS8 from scratch without entry prop) -->
        <div v-if="isHS8 && !props.entry" class="pt-1">
          <label class="block space-y-1 text-left">
            <span class="text-xs font-bold text-slate-700">Parent HS4 Code</span>
            <input 
              v-model="form.parent_code" 
              required
              maxlength="4" 
              class="block w-full sm:w-48 text-xs font-mono border border-slate-200 rounded-xl px-3 py-2 bg-white" 
            />
          </label>
        </div>
      </div>

      <div class="pt-3 flex items-center justify-end gap-3 border-t border-slate-100">
        <button type="button" class="secondary text-xs font-semibold py-2 px-4 rounded-xl cursor-pointer" @click="emit('cancel')">
          Cancel
        </button>
        <button type="submit" class="primary-button text-xs font-bold py-2 px-5 rounded-xl cursor-pointer shadow-sm">
          <span v-if="isCountry && countryMode === 'map' && props.entry && existingCountries.length > 0">Link to Existing Country</span>
          <span v-else-if="isCountry">Save New Country</span>
          <span v-else>Save Bilingual Names</span>
        </button>
      </div>
    </fieldset>
  </form>
</template>

