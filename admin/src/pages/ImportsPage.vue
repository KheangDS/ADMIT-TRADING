<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { api } from '../api';
import { dateTime, monthRange } from '../format';
import type { Schema, TradeImport, RegistryEntry, Publication, Revision } from '../types';
import { useTask } from '../composables/useTask';
import TaskNotice from '../components/TaskNotice.vue';
import RegistryEditor from '../components/RegistryEditor.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';
import { 
  UploadCloud as UploadCloudIcon,
  FileSpreadsheet as FileSpreadsheetIcon,
  RefreshCw as RefreshCwIcon,
  CheckCircle2 as CheckCircle2Icon,
  AlertTriangle as AlertTriangleIcon,
  AlertCircle as AlertCircleIcon,
  Layers as LayersIcon,
  Calendar as CalendarIcon,
  Globe as GlobeIcon,
  FileCheck as FileCheckIcon,
  Trash2 as Trash2Icon,
  ChevronDown as ChevronDownIcon,
  X as XIcon
} from 'lucide-vue-next';

type ReviewedImport = TradeImport & { review_token?: string };

const schema = ref<Schema | null>(null);
const imports = ref<TradeImport[]>([]);
const selected = ref<ReviewedImport | null>(null);
const file = ref<File | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const isDragging = ref(false);
const resolving = ref<RegistryEntry | null>(null);
const confirmCommit = ref(false);
const confirmPub = ref(false);
const confirmDeleteRev = ref(false);
const deleteRevTargetId = ref<string | null>(null);

const publication = ref<Publication | null>(null);
const revisions = ref<Revision[]>([]);
const pubRevisionId = ref('');
const pubStart = ref('');
const pubEnd = ref('');

const { busy, error, notice, run } = useTask();

const targetDeleteRevision = computed(() => {
  const targetId = deleteRevTargetId.value || pubRevisionId.value;
  return revisions.value.find(r => r.id === targetId) || null;
});

const targetDeleteRevNumber = computed(() => {
  if (!targetDeleteRevision.value) return null;
  return getRevisionNumber(targetDeleteRevision.value.id);
});

const deleteRevMessage = computed(() => {
  if (!targetDeleteRevision.value) return 'Are you sure you want to delete this revision?';
  const revNum = targetDeleteRevNumber.value ? `Revision ${targetDeleteRevNumber.value}` : 'this revision';
  const rowCount = targetDeleteRevision.value.row_count.toLocaleString();
  const period = targetDeleteRevision.value.start_month && targetDeleteRevision.value.end_month 
    ? ` (${targetDeleteRevision.value.start_month} → ${targetDeleteRevision.value.end_month})`
    : '';
  
  if (revisions.value.length <= 1) {
    return `Warning: You are about to delete ${revNum}${period} with ${rowCount} rows. This is the only revision in the system. Deleting it will clear the trade dataset until a new file is committed.`;
  }
  return `Are you sure you want to delete ${revNum}${period} with ${rowCount} rows? The system will automatically rollback the active dataset head and live publication scope to the previous revision.`;
});

const activeRecordCount = computed(() => {
  if (publication.value && publication.value.row_count !== undefined) {
    return publication.value.row_count;
  }
  if (publication.value?.revision_id) {
    const rev = revisions.value.find(r => r.id === publication.value?.revision_id);
    if (rev) return rev.row_count;
  }
  return previousRecordCount.value;
});

const previousRecordCount = computed(() => {
  if (revisions.value.length > 0) return revisions.value[0].row_count;
  const lastCommitted = imports.value.find(i => i.status === 'committed');
  return lastCommitted ? lastCommitted.row_count : 0;
});

const previousPeriod = computed(() => {
  if (publication.value?.start_month && publication.value?.end_month) {
    return `${publication.value.start_month} → ${publication.value.end_month}`;
  }
  const lastCommitted = imports.value.find(i => i.status === 'committed');
  return lastCommitted ? `${lastCommitted.start_month} → ${lastCommitted.end_month}` : 'None active';
});

const hasCommittedDuplicate = computed(() => {
  if (!selected.value || selected.value.status !== 'staged') return false;
  const stagedNameLower = selected.value.filename.trim().toLowerCase();
  return imports.value.some(
    (i) => i.status === 'committed' && i.filename.trim().toLowerCase() === stagedNameLower && i.id !== selected.value?.id,
  );
});

const canCommit = computed(
  () =>
    !!selected.value &&
    selected.value.status === 'staged' &&
    !!selected.value.review_token &&
    !selected.value.errors.length &&
    !selected.value.unknowns.length &&
    !hasCommittedDuplicate.value,
);

const chosenRevision = computed(() => revisions.value.find(r => r.id === pubRevisionId.value));

const availableMonths = computed(() => {
  if (!chosenRevision.value) return [];
  if (chosenRevision.value.available_months && chosenRevision.value.available_months.length > 0) {
    return chosenRevision.value.available_months;
  }
  const start = chosenRevision.value.start_month;
  const end = chosenRevision.value.end_month;
  if (start && end) {
    const list: string[] = [];
    let [curY, curM] = start.split('-').map(Number);
    const [endY, endM] = end.split('-').map(Number);
    while (curY < endY || (curY === endY && curM <= endM)) {
      list.push(`${curY}-${String(curM).padStart(2, '0')}`);
      curM++;
      if (curM > 12) {
        curM = 1;
        curY++;
      }
    }
    return list;
  }
  return [];
});

const availableStartMonths = computed(() => availableMonths.value);

const availableEndMonths = computed(() => {
  if (!pubStart.value) return availableMonths.value;
  return availableMonths.value.filter(m => m >= pubStart.value);
});

interface YearMonthOption {
  value: string;
  label: string;
}

interface YearGroup {
  year: string;
  months: YearMonthOption[];
}

const groupedStartMonths = computed<YearGroup[]>(() => {
  const groups: Record<string, YearMonthOption[]> = {};
  for (const m of availableStartMonths.value) {
    const [year] = m.split('-');
    if (!groups[year]) groups[year] = [];
    groups[year].push({
      value: m,
      label: formatMonthLabel(m),
    });
  }
  return Object.keys(groups).sort().map(year => ({
    year: `Year ${year}`,
    months: groups[year],
  }));
});

const groupedEndMonths = computed<YearGroup[]>(() => {
  const groups: Record<string, YearMonthOption[]> = {};
  for (const m of availableEndMonths.value) {
    const [year] = m.split('-');
    if (!groups[year]) groups[year] = [];
    groups[year].push({
      value: m,
      label: formatMonthLabel(m),
    });
  }
  return Object.keys(groups).sort().map(year => ({
    year: `Year ${year}`,
    months: groups[year],
  }));
});

function formatMonthLabel(m: string): string {
  if (!m) return '';
  const parts = m.split('-');
  if (parts.length !== 2) return m;
  const year = parts[0];
  const monthIdx = parseInt(parts[1], 10) - 1;
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const monthName = monthNames[monthIdx] || '';
  return `${monthName} ${year}`;
}

function handleRevisionChange() {
  const months = availableMonths.value;
  if (months.length > 0) {
    if (!pubStart.value || !months.includes(pubStart.value)) {
      pubStart.value = months[0];
    }
    if (!pubEnd.value || !months.includes(pubEnd.value) || pubEnd.value < pubStart.value) {
      pubEnd.value = months[months.length - 1];
    }
  }
}

function handleStartMonthChange() {
  if (pubEnd.value && pubEnd.value < pubStart.value) {
    pubEnd.value = pubStart.value;
  }
}

async function list() {
  const res = await api.get<TradeImport[]>('/admin/imports');
  imports.value = Array.isArray(res.data) ? res.data : [];
}

async function loadPublicationAndRevisions() {
  try {
    const pubRes = await api.get<Publication | null>('/admin/publication');
    if (pubRes.data && typeof pubRes.data === 'object' && 'start_month' in pubRes.data) {
      publication.value = pubRes.data;
      pubStart.value = pubRes.data.start_month;
      pubEnd.value = pubRes.data.end_month;
      pubRevisionId.value = pubRes.data.revision_id;
    }
  } catch {
    publication.value = null;
  }

  try {
    const revRes = await api.get<Revision[]>('/admin/revisions');
    if (Array.isArray(revRes.data)) {
      revisions.value = revRes.data;
      if (!pubRevisionId.value && revisions.value.length > 0) {
        pubRevisionId.value = revisions.value[0].id;
      }
      if (chosenRevision.value) {
        const months = chosenRevision.value.available_months || [];
        if (!pubStart.value && months.length > 0) pubStart.value = months[0];
        if (!pubEnd.value && months.length > 0) pubEnd.value = months[months.length - 1];
      }
    }
  } catch {
    revisions.value = [];
  }
}

async function load() {
  await run(async () => {
    const schemaRes = await api.get<Schema>('/admin/schema');
    schema.value = schemaRes.data;
    await list();
    await loadPublicationAndRevisions();
  });
}

async function select(id: string) {
  resolving.value = null;
  await run(async () => {
    selected.value = (await api.get<ReviewedImport>(`/admin/imports/${encodeURIComponent(id)}`)).data;
  });
}

function choose(event: Event) {
  file.value = (event.target as HTMLInputElement).files?.[0] || null;
}

function handleDrop(event: DragEvent) {
  isDragging.value = false;
  if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
    const droppedFile = event.dataTransfer.files[0];
    file.value = droppedFile;
    if (fileInput.value) {
      const dt = new DataTransfer();
      dt.items.add(droppedFile);
      fileInput.value.files = dt.files;
    }
  }
}

function triggerFileInput() {
  fileInput.value?.click();
}

function clearFile() {
  file.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

async function stage() {
  await run(async () => {
    if (!file.value) throw new Error('Select an XLSX or CSV file.');
    if (file.value.size > 25 * 1024 * 1024) throw new Error('Default upload limit is 25 MiB.');
    
    const body = new FormData();
    body.append('file', file.value);
    body.append('mode', 'partial');
    
    selected.value = (
      await api.post<ReviewedImport>('/admin/imports', body, { timeout: 120000 })
    ).data;
    resolving.value = null;
    await list();
    
    if (selected.value.status === 'invalid' || selected.value.errors.length) {
      error.value =
        'Import rejected or blocked by validation. Please double-check your Excel column names and data rows against the required specification below.';
    } else {
      notice.value =
        'Dataset validated successfully! Source rows and date coverage detected automatically. Confirm below to push to the ETL pipeline.';
      if (selected.value.start_month && selected.value.end_month) {
        pubStart.value = selected.value.start_month;
        pubEnd.value = selected.value.end_month;
      }
    }
  });
}

async function commit() {
  await run(async () => {
    if (!canCommit.value || !selected.value) {
      throw new Error('Refresh and resolve all errors and bilingual unknowns first.');
    }
    
    selected.value = (
      await api.post<TradeImport>(
        `/admin/imports/${encodeURIComponent(selected.value.id)}/commit`,
        { review_token: selected.value.review_token },
      )
    ).data;
    confirmCommit.value = false;
    await list();
    await loadPublicationAndRevisions();
    
    if (selected.value.status !== 'committed') {
      throw new Error('Backend did not confirm a committed import. Review diagnostics.');
    }
    
    notice.value =
      'Data successfully committed and processed by the ETL pipeline! You can now adjust the active frontend display period below.';
  });
}

async function publishScope() {
  await run(async () => {
    monthRange(pubStart.value, pubEnd.value);
    const targetRevId = pubRevisionId.value || (revisions.value[0]?.id) || (selected.value?.revision_id);
    if (!targetRevId) {
      throw new Error('No ready trade revision available to publish. Commit a valid import first.');
    }

    publication.value = (
      await api.post<Publication>('/admin/publication', {
        revision_id: targetRevId,
        start_month: pubStart.value,
        end_month: pubEnd.value,
      })
    ).data;
    
    confirmPub.value = false;
    notice.value = `Frontend display period updated successfully! Members can now explore data for ${publication.value.start_month} → ${publication.value.end_month}.`;
  });
}

async function resolved() {
  const currentId = selected.value?.id;
  resolving.value = null;
  if (currentId) {
    await select(currentId);
  }
  notice.value = 'Registry name saved and staged dataset revalidated successfully.';
}

function getRevisionNumber(revId: string | null | undefined): number | null {
  if (!revId) return null;
  const idx = revisions.value.findIndex(r => r.id === revId);
  return idx !== -1 ? revisions.value.length - idx : null;
}

function promptDeleteRevision(revId?: string) {
  deleteRevTargetId.value = revId || pubRevisionId.value || null;
  confirmDeleteRev.value = true;
}

async function handleDeleteRevision() {
  const targetId = deleteRevTargetId.value || pubRevisionId.value;
  if (!targetId) return;

  await run(async () => {
    await api.delete(`/admin/revisions/${encodeURIComponent(targetId)}`);
    confirmDeleteRev.value = false;
    deleteRevTargetId.value = null;
    pubRevisionId.value = '';
    
    await list();
    await loadPublicationAndRevisions();

    notice.value = 'Revision successfully deleted and rolled back!';
  });
}

onMounted(load);
</script>

<template>
  <!-- Page Header -->
  <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 sm:pb-4 mb-5">
    <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">Trade Data Management</h1>
  </div>

  <TaskNotice :busy="busy" :error="error" :notice="notice" />

  <div class="space-y-6">

    <!-- SECTION 1: LIVE FRONTEND DISPLAY SCOPE (Top Executive Control) -->
    <section class="card rounded-2xl border border-slate-200/90 shadow-sm p-4 sm:p-6 space-y-5">
      <!-- Section Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-3">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-sky-100 text-sky-800 flex items-center justify-center font-bold flex-shrink-0">
            <GlobeIcon class="w-4 h-4" />
          </div>
          <h2 class="font-bold text-base text-slate-900 m-0">Live Frontend Scope & Status</h2>
        </div>
        <span v-if="publication" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 self-start sm:self-auto shadow-2xs">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Live Scope Configured</span>
        </span>
      </div>

      <!-- Current Live Status Banner (Centered Metrics) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <!-- Current Live Period (Centered) -->
        <div class="p-4 sm:p-5 rounded-xl bg-gradient-to-br from-sky-50/70 via-sky-50/30 to-white border border-sky-200/80 space-y-3 shadow-xs">
          <div class="flex items-center justify-between border-b border-sky-100 pb-2">
            <span class="text-[11px] font-bold text-sky-900 uppercase tracking-wider">
              Public Display Period
            </span>
            <span class="text-[10px] font-bold text-sky-700 bg-sky-100/90 px-2.5 py-0.5 rounded-md">
              Live Range
            </span>
          </div>
          <div class="flex items-center justify-center gap-3 py-1.5">
            <div class="w-9 h-9 rounded-xl bg-sky-500/10 flex items-center justify-center text-sky-600 flex-shrink-0">
              <CalendarIcon class="w-5 h-5" />
            </div>
            <span class="text-xl sm:text-2xl font-black text-slate-900 font-mono tracking-tight">
              {{ publication?.start_month && publication?.end_month ? `${publication.start_month} → ${publication.end_month}` : 'Not yet configured' }}
            </span>
          </div>
        </div>

        <!-- Live Dataset Records (Centered - Value Only) -->
        <div class="p-4 sm:p-5 rounded-xl bg-gradient-to-br from-slate-50/80 via-slate-50/30 to-white border border-slate-200/90 space-y-3 shadow-xs">
          <div class="flex items-center justify-between border-b border-slate-100 pb-2">
            <span class="text-[11px] font-bold text-slate-600 uppercase tracking-wider">
              Live Dataset Records
            </span>
            <span v-if="publication" class="px-2.5 py-0.5 rounded-md text-[10px] font-extrabold bg-emerald-100 text-emerald-800">
              Revision {{ getRevisionNumber(publication.revision_id) || 1 }}
            </span>
          </div>
          <div class="flex items-center justify-center gap-3 py-1.5">
            <div class="w-9 h-9 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-600 flex-shrink-0">
              <FileSpreadsheetIcon class="w-5 h-5" />
            </div>
            <div class="flex items-baseline gap-1.5">
              <span class="text-xl sm:text-2xl font-black text-slate-900 font-mono tracking-tight">
                {{ publication ? activeRecordCount.toLocaleString() : '0' }}
              </span>
              <span class="text-xs font-semibold text-slate-500">records</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Update Controls with Grounded Date Dropdowns -->
      <div class="space-y-4 pt-2 border-t border-slate-100">
        <h3 class="text-xs font-bold text-slate-700 uppercase tracking-wider m-0">
          Update Reporting Scope
        </h3>
        
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
          <!-- Dataset Version Selector -->
          <div class="space-y-1.5 text-left">
            <label class="block text-xs font-bold text-slate-700">Target Revision</label>
            <select 
              v-model="pubRevisionId" 
              required
              class="block w-full text-xs font-medium text-slate-800 bg-white border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer shadow-xs"
              @change="handleRevisionChange"
            >
              <option disabled value="">Select revision</option>
              <option 
                v-for="(rev, idx) in revisions" 
                :key="rev.id" 
                :value="rev.id"
                :disabled="rev.status !== 'ready'"
              >
                Revision {{ revisions.length - idx }} · {{ rev.row_count.toLocaleString() }} rows ({{ rev.start_month && rev.end_month ? `${rev.start_month} → ${rev.end_month}` : dateTime(rev.created_at) }})
              </option>
            </select>
          </div>

          <!-- Grounded Display Start Month Dropdown (Categorized by Year) -->
          <div class="space-y-1.5 text-left">
            <label class="block text-xs font-bold text-slate-700">Display Start Month</label>
            <select 
              v-model="pubStart" 
              required 
              :disabled="!pubRevisionId || availableStartMonths.length === 0"
              class="block w-full text-xs font-mono font-medium text-slate-800 bg-white border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer shadow-xs disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed"
              @change="handleStartMonthChange"
            >
              <option disabled value="">Select start month</option>
              <optgroup 
                v-for="group in groupedStartMonths" 
                :key="group.year" 
                :label="group.year"
                class="font-bold text-slate-900 bg-slate-50"
              >
                <option 
                  v-for="item in group.months" 
                  :key="item.value" 
                  :value="item.value"
                  class="font-normal font-mono text-slate-800 bg-white"
                >
                  {{ item.label }}
                </option>
              </optgroup>
            </select>
          </div>

          <!-- Grounded Display End Month Dropdown (Categorized by Year) -->
          <div class="space-y-1.5 text-left">
            <label class="block text-xs font-bold text-slate-700">Display End Month</label>
            <select 
              v-model="pubEnd" 
              required 
              :disabled="!pubRevisionId || availableEndMonths.length === 0"
              class="block w-full text-xs font-mono font-medium text-slate-800 bg-white border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer shadow-xs disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed"
            >
              <option disabled value="">Select end month</option>
              <optgroup 
                v-for="group in groupedEndMonths" 
                :key="group.year" 
                :label="group.year"
                class="font-bold text-slate-900 bg-slate-50"
              >
                <option 
                  v-for="item in group.months" 
                  :key="item.value" 
                  :value="item.value"
                  class="font-normal font-mono text-slate-800 bg-white"
                >
                  {{ item.label }}
                </option>
              </optgroup>
            </select>
          </div>
        </div>

        <div class="pt-1">
          <button 
            type="button" 
            class="primary-button text-xs font-bold py-2.5 px-6 shadow-sm hover:shadow transition-all inline-flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto"
            :disabled="busy || !pubRevisionId || !pubStart || !pubEnd"
            @click="confirmPub = true"
          >
            <GlobeIcon class="w-4 h-4" />
            <span>Update Live Scope</span>
          </button>
        </div>
      </div>
    </section>

    <!-- SECTION 2: UPLOAD & AUTOMATIC VALIDATION (Modern Dropzone) -->
    <section class="card rounded-2xl border border-slate-200/90 shadow-sm p-4 sm:p-6 space-y-5">
      <div class="flex items-center justify-between border-b border-slate-100 pb-3">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-sky-100 text-sky-800 flex items-center justify-center font-bold flex-shrink-0">
            <UploadCloudIcon class="w-4 h-4" />
          </div>
          <h2 class="font-bold text-base text-slate-900 m-0">Upload Dataset & Auto-Validate</h2>
        </div>
        <span class="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 border border-slate-200">
          .xlsx, .csv · Max 25 MB
        </span>
      </div>

      <form @submit.prevent="stage" class="space-y-4">
        <fieldset :disabled="busy" class="space-y-4 border-0 p-0 m-0">
          <!-- Hidden Native File Input -->
          <input
            ref="fileInput"
            type="file"
            accept=".xlsx,.csv"
            required
            class="sr-only"
            @change="choose"
          />

          <!-- Interactive Drag & Drop Area -->
          <div 
            class="border-2 border-dashed rounded-2xl p-6 sm:p-8 text-center cursor-pointer transition-all group"
            :class="isDragging ? 'border-sky-500 bg-sky-50/80 scale-[0.99]' : 'border-sky-300/80 hover:border-sky-500 bg-sky-50/20 hover:bg-sky-50/50'"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
          >
            <div class="w-12 h-12 rounded-2xl bg-sky-100 text-sky-700 flex items-center justify-center mx-auto mb-3 group-hover:scale-105 transition-transform shadow-xs">
              <UploadCloudIcon class="w-6 h-6" />
            </div>
            <p class="text-sm font-bold text-slate-800 mb-1">
              Drag and drop your spreadsheet here, or <span class="text-sky-600 underline">Browse Files</span>
            </p>
            <p class="text-xs text-slate-500 m-0">Supports Excel (<code class="font-semibold text-slate-700">.xlsx</code>) and CSV (<code class="font-semibold text-slate-700">.csv</code>)</p>
          </div>

          <!-- Selected File Preview Card -->
          <div v-if="file" class="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                <FileSpreadsheetIcon class="w-4 h-4" />
              </div>
              <div>
                <div class="text-xs font-bold text-slate-900">{{ file.name }}</div>
                <div class="text-[11px] text-slate-500 font-mono">{{ (file.size / 1024).toFixed(1) }} KB · Ready for automated validation</div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button 
                type="submit" 
                class="primary-button text-xs font-bold py-1.5 px-4 rounded-xl shadow-xs inline-flex items-center gap-1.5 cursor-pointer"
                :disabled="busy"
              >
                <UploadCloudIcon class="w-3.5 h-3.5" />
                <span>Upload & Auto-Validate</span>
              </button>
              <button 
                type="button" 
                class="text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-200 cursor-pointer"
                title="Remove file"
                @click.stop="clearFile"
              >
                <XIcon class="w-4 h-4" />
              </button>
            </div>
          </div>

          <div v-if="!file" class="pt-1 flex flex-col sm:flex-row sm:items-center gap-3">
            <button 
              type="button" 
              class="primary-button text-xs font-bold py-2.5 px-6 shadow-sm hover:shadow transition-all inline-flex items-center justify-center gap-2 cursor-pointer w-full sm:w-auto"
              :disabled="busy"
              @click="triggerFileInput"
            >
              <UploadCloudIcon class="w-4 h-4" />
              <span>Select Spreadsheet</span>
            </button>
            <button 
              v-if="selected" 
              type="button" 
              class="secondary text-xs font-semibold py-2.5 px-4 rounded-xl cursor-pointer w-full sm:w-auto justify-center"
              @click="selected = null"
            >
              Clear Result
            </button>
          </div>
        </fieldset>
      </form>

      <!-- VALIDATION RESULT PANEL -->
      <div 
        v-if="selected" 
        class="rounded-2xl border-2 shadow-sm p-4 sm:p-6 space-y-5 mt-4" 
        :class="selected.status === 'invalid' || selected.errors.length ? 'border-rose-300 bg-rose-50/20' : 'border-emerald-300 bg-emerald-50/30'"
      >
        <!-- Review Header & Refresh Button -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-3" :class="selected.status === 'invalid' || selected.errors.length ? 'border-rose-200' : 'border-emerald-200/70'">
          <div class="flex items-center gap-2">
            <AlertCircleIcon v-if="selected.status === 'invalid' || selected.errors.length" class="w-5 h-5 text-rose-600 flex-shrink-0" />
            <CheckCircle2Icon v-else class="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <div>
              <h3 class="text-sm font-black m-0" :class="selected.status === 'invalid' || selected.errors.length ? 'text-rose-950' : 'text-emerald-950'">
                {{ selected.filename }}
              </h3>
              <p class="text-[11px] m-0" :class="selected.status === 'invalid' || selected.errors.length ? 'text-rose-700' : 'text-emerald-800'">
                Validation Status: <strong class="uppercase font-bold">{{ selected.status }}</strong>
              </p>
            </div>
          </div>
          <button class="secondary text-xs font-semibold py-1.5 px-3 inline-flex items-center gap-1.5" :disabled="busy" @click="select(selected.id)">
            <RefreshCwIcon class="w-3.5 h-3.5" :class="{ 'animate-spin': busy }" />
            <span>Refresh staged review</span>
          </button>
        </div>

        <!-- DUPLICATE FILENAME WARNING BANNER -->
        <div 
          v-if="hasCommittedDuplicate" 
          class="notice error bg-amber-50 border border-amber-300 rounded-xl p-3.5 text-xs text-amber-950 flex items-center gap-2.5"
          role="alert"
        >
          <AlertTriangleIcon class="w-4 h-4 text-amber-600 flex-shrink-0" />
          <div class="flex items-center gap-1.5 flex-wrap">
            <strong class="font-bold text-amber-950">Unique Filename Required Before Commit:</strong>
            <span class="text-amber-800 text-[11px]">This file name already exists.</span>
          </div>
        </div>

        <!-- VALIDATION ERROR NOTICE -->
        <div 
          v-if="selected.status === 'invalid' || selected.errors.length" 
          class="notice error bg-rose-50 border border-rose-300 rounded-xl p-4 text-xs text-rose-900 space-y-2"
          role="alert"
        >
          <div class="flex items-center gap-2">
            <AlertCircleIcon class="w-4 h-4 text-rose-600 flex-shrink-0" />
            <h4 class="font-bold text-sm text-rose-900 m-0">Validation errors — not committed</h4>
          </div>
          <p class="text-xs text-rose-800 m-0 text-justify">
            Import rejected or blocked by validation. Nothing was committed. Please double check that your Excel column headers match the required specification.
          </p>
          <ul class="space-y-1 pl-5 list-disc mt-2 text-rose-900 font-mono text-[11px]">
            <li v-for="(issue, idx) in selected.errors" :key="idx">
              Row {{ issue.row }}: {{ issue.message }}
            </li>
          </ul>
        </div>

        <!-- VALIDATION SUCCESS & COMPARISON METRICS -->
        <div v-else class="space-y-4">
          <div class="grid sm:grid-cols-2 gap-4">
            <!-- Metric 1: Record Count Comparison -->
            <div class="bg-white rounded-xl p-4 border border-emerald-200/80 shadow-xs space-y-3">
              <div class="flex items-center justify-between text-slate-500">
                <span class="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-slate-700">
                  <LayersIcon class="w-4 h-4 text-sky-600" />
                  <span>Dataset Record Count</span>
                </span>
                <span class="text-[11px] font-medium text-slate-400">Total processed</span>
              </div>
              
              <div class="grid grid-cols-2 gap-3">
                <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-left">
                  <span class="text-[10px] font-bold text-slate-400 uppercase block">Previous Records</span>
                  <span class="text-lg font-black text-slate-700 font-mono mt-0.5 block">
                    {{ previousRecordCount.toLocaleString() }} rows
                  </span>
                </div>
                <div class="p-2.5 rounded-lg bg-emerald-50/70 border border-emerald-100 text-left">
                  <span class="text-[10px] font-extrabold text-emerald-800 uppercase block">Staged New Records</span>
                  <span class="text-lg font-black text-emerald-700 font-mono mt-0.5 block">
                    {{ selected.row_count.toLocaleString() }} rows
                  </span>
                </div>
              </div>

              <div class="flex items-center flex-wrap gap-2 text-[11px] font-mono pt-0.5">
                <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200/70 font-bold">
                  +{{ selected.preview.inserted }} new
                </span>
                <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 border border-sky-200/70 font-bold">
                  {{ selected.preview.updated }} updated
                </span>
                <span class="inline-flex items-center px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200/70 font-medium">
                  = {{ selected.preview.unchanged }} unchanged
                </span>
              </div>

              <div v-if="selected.duplicate_count > 0" class="p-2.5 rounded-lg bg-amber-50/80 border border-amber-200 text-xs text-amber-900 space-y-1">
                <div class="flex items-center justify-between font-medium">
                  <span class="flex items-center gap-1.5 font-bold text-amber-950">
                    <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                    {{ selected.duplicate_count.toLocaleString() }} Duplicate Rows Deduplicated
                  </span>
                  <span class="font-mono text-[11px] text-amber-800 font-semibold">
                    {{ (selected.row_count + selected.duplicate_count).toLocaleString() }} total source rows
                  </span>
                </div>
                <p class="text-[11px] text-amber-800 m-0 leading-relaxed">
                  The uploaded file contains multiple identical declarations for the same monthly commodity and destination country. The system safely deduplicated identical entries to prevent double-counting trade volume and value.
                </p>
              </div>
            </div>

            <!-- Metric 2: Date Period Scope Comparison -->
            <div class="bg-white rounded-xl p-4 border border-emerald-200/80 shadow-xs space-y-3">
              <div class="flex items-center justify-between text-slate-500">
                <span class="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 text-slate-700">
                  <CalendarIcon class="w-4 h-4 text-emerald-600" />
                  <span>Data Period Coverage</span>
                </span>
                <span class="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-bold">
                  Auto-Detected
                </span>
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-left">
                  <span class="text-[10px] font-bold text-slate-400 uppercase block">Previous Active Period</span>
                  <span class="text-xs sm:text-sm font-bold text-slate-700 font-mono mt-0.5 block">
                    {{ previousPeriod }}
                  </span>
                </div>
                <div class="p-2.5 rounded-lg bg-emerald-50/70 border border-emerald-100 text-left">
                  <span class="text-[10px] font-extrabold text-emerald-800 uppercase block">Detected Staged Period</span>
                  <span class="text-xs sm:text-sm font-bold text-emerald-700 font-mono mt-0.5 block">
                    {{ selected.start_month }} → {{ selected.end_month }}
                  </span>
                </div>
              </div>

              <p class="text-[11px] text-slate-500 m-0 text-justify">
                Derived automatically from the minimum and maximum year/month values in declared rows.
              </p>
            </div>
          </div>
        </div>

        <!-- Unknowns Resolver -->
        <div v-if="selected.unknowns && selected.unknowns.length" class="space-y-3 pt-2">
          <div class="flex items-center justify-between">
            <h4 class="font-bold text-xs text-amber-900 m-0 flex items-center gap-2">
              <AlertTriangleIcon class="w-4 h-4 text-amber-600" />
              <span>Unknown Registry Names Detected (Must resolve before ETL commit): {{ selected.unknowns.length }}</span>
            </h4>
          </div>

          <div class="table-scroll overflow-x-auto border border-amber-200 rounded-xl bg-white">
            <table class="w-full text-xs">
              <thead>
                <tr class="bg-amber-50/80 text-amber-900 border-b border-amber-200">
                  <th class="py-2 px-3 text-left font-bold">Kind / Code</th>
                  <th class="py-2 px-3 text-left font-bold">English / Khmer Name</th>
                  <th class="py-2 px-3 text-right font-bold">Action</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-amber-100">
                <tr v-for="entry in selected.unknowns" :key="`${entry.kind}:${entry.code}`">
                  <td class="py-2 px-3 mono font-semibold text-slate-800">
                    <span class="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] uppercase mr-1">{{ entry.kind }}</span>
                    <span>{{ entry.code }}</span>
                  </td>
                  <td class="py-2 px-3 text-slate-700">
                    <span class="font-medium">{{ entry.name_en || 'Missing English' }}</span>
                    <span class="text-slate-400 mx-1">/</span>
                    <span lang="km">{{ entry.name_km || 'Missing Khmer' }}</span>
                  </td>
                  <td class="py-2 px-3 text-right">
                    <button class="secondary text-xs py-1 px-3 rounded-lg font-bold" :disabled="busy" @click="resolving = entry">
                      Resolve bilingual names
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Registry Editor Inline Modal -->
        <RegistryEditor
          v-if="resolving"
          :entry="resolving"
          @saved="resolved"
          @cancel="resolving = null"
        />

        <!-- CONFIRM & PUSH TO ETL ACTION BUTTON -->
        <div class="pt-3 border-t flex items-center justify-between flex-wrap gap-4" :class="selected.status === 'invalid' || selected.errors.length ? 'border-rose-200' : 'border-emerald-200/70'">
          <p v-if="selected.status === 'committed'" class="text-xs text-emerald-800 font-bold inline-flex items-center gap-1.5 m-0">
            <CheckCircle2Icon class="w-4 h-4 text-emerald-600" />
            <span>Dataset committed to ETL pipeline successfully!</span>
          </p>
          <div v-else class="flex items-center gap-3">
            <button 
              class="primary-button text-xs font-bold py-2.5 px-6 shadow-sm hover:shadow transition-all inline-flex items-center gap-2 cursor-pointer bg-emerald-700 hover:bg-emerald-800"
              :disabled="busy || !canCommit || !!resolving" 
              @click="confirmCommit = true"
            >
              <FileCheckIcon class="w-4 h-4" />
              <span>Review explicit commit</span>
            </button>
            <span v-if="hasCommittedDuplicate" class="text-xs text-amber-700 font-semibold">
              (Filename already committed on server — rename file to commit)
            </span>
            <span v-else-if="!canCommit" class="text-xs text-slate-500 font-medium">
              (Resolve all diagnostics and unknowns to enable commit)
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION 3: EXPANDABLE DATASET SPECIFICATION GUIDE -->
    <details class="card rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden group p-0">
      <summary class="flex items-center justify-between p-4 sm:p-5 cursor-pointer select-none hover:bg-slate-50/70 transition-colors">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center font-bold flex-shrink-0">
            <FileSpreadsheetIcon class="w-4 h-4" />
          </div>
          <h2 class="font-bold text-sm sm:text-base text-slate-900 m-0">Dataset Specification & Required Columns</h2>
        </div>
        <span class="text-xs font-semibold text-sky-600 group-open:rotate-180 transition-transform flex items-center gap-1">
          <ChevronDownIcon class="w-4 h-4" />
        </span>
      </summary>

      <div class="p-5 pt-0 border-t border-slate-100 space-y-3">
        <!-- Format & Matching Rule Notice -->
        <div class="rounded-xl p-3.5 sm:p-4 bg-amber-50/80 border border-amber-200/90 text-amber-950 text-xs leading-relaxed space-y-1">
          <div class="flex items-start gap-2">
            <AlertTriangleIcon class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div class="flex-1 min-w-0">
              <strong class="font-bold text-amber-900 block mb-0.5">Strict Column Matching Rule:</strong>
              <p class="m-0 text-amber-800 text-justify">
                The dataset file must be in Excel (<code class="font-bold text-amber-900">.xlsx</code>) or CSV (<code class="font-bold text-amber-900">.csv</code>) format. 
                Column headers in the uploaded file <strong>must exactly match</strong> either the English or Khmer column names listed below. 
                If the column names do not match, the automated ingestion will reject the file.
              </p>
            </div>
          </div>
        </div>

        <!-- Bilingual Column Table -->
        <div class="table-scroll overflow-x-auto border border-slate-200/80 rounded-xl">
          <table class="w-full text-xs min-w-[620px]">
            <thead>
              <tr class="bg-slate-50 border-b border-slate-200 text-slate-700">
                <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">Field Key</th>
                <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">English Column Header</th>
                <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">Khmer Header (ក្បាលជួរជាភាសាខ្មែរ)</th>
                <th class="py-2.5 px-3 text-center font-bold whitespace-nowrap">Status</th>
                <th class="py-2.5 px-3.5 text-left font-bold min-w-[200px]">Description</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 bg-white">
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">year</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">Year</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">ឆ្នាំ</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Required</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">4-digit declaration year (e.g. 2023, 2024)</td>
              </tr>
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">month</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">Month</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">ខែ</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Required</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">Month number (1 – 12)</td>
              </tr>
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">hs8</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">HS8</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">កូដទំនិញ ៨ខ្ទង់</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Required</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">8-digit Harmonized System commodity code</td>
              </tr>
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">hs4</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">HS4</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">កូដទំនិញ ៤ខ្ទង់</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Required</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">4-digit HS heading (must match first 4 digits of HS8)</td>
              </tr>
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">country</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">Country</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">ប្រទេសគម្យដ្ឋាន</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Required</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">Destination trading partner name or ISO3 code</td>
              </tr>
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">weight</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">Weight (kg)</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">ទម្ងន់ (គក្រ)</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Required</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">Net trade export quantity strictly in kilograms (kg)</td>
              </tr>
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">value</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">Value (KHR)</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">តម្លៃ (រៀល)</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Required</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">Declared export customs value in Khmer Riel (KHR)</td>
              </tr>
              <tr class="hover:bg-slate-50/50">
                <td class="py-2.5 px-3.5 mono font-bold text-sky-800 whitespace-nowrap">desc</td>
                <td class="py-2.5 px-3.5 font-semibold text-slate-900 whitespace-nowrap">Description</td>
                <td class="py-2.5 px-3.5 text-slate-800 font-medium whitespace-nowrap" lang="km">បរិយាយកូដ ៤ខ្ទង់</td>
                <td class="py-2.5 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500">Optional</span>
                </td>
                <td class="py-2.5 px-3.5 text-slate-500">Supplementary chapter text / notes</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </details>

    <!-- SECTION 4: IMPORT HISTORY -->
    <section class="card rounded-2xl border border-slate-200/90 shadow-sm p-4 sm:p-6 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
        <h2 class="font-bold text-base text-slate-900 m-0">Committed Datasets & Revision History</h2>
        <span class="text-xs font-mono text-slate-500">{{ imports.length }} {{ imports.length === 1 ? 'committed file' : 'committed files' }}</span>
      </div>

      <div class="table-scroll overflow-x-auto">
        <table class="w-full text-xs min-w-[680px]">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200 text-slate-700">
              <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">Source File</th>
              <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">Scope Period</th>
              <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">Records</th>
              <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">Status & Version</th>
              <th class="py-2.5 px-3.5 text-left font-bold whitespace-nowrap">Committed At</th>
              <th class="py-2.5 px-3.5 text-right font-bold whitespace-nowrap">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="item in imports" :key="item.id" class="hover:bg-slate-50/70 transition-colors">
              <td class="py-2.5 px-3.5 font-semibold text-slate-900 flex items-center gap-2 whitespace-nowrap">
                <FileSpreadsheetIcon class="w-4 h-4 text-sky-600 flex-shrink-0" />
                <span class="truncate max-w-[220px]" :title="item.filename">{{ item.filename }}</span>
              </td>
              <td class="py-2.5 px-3.5 font-mono font-medium text-slate-700 whitespace-nowrap">
                {{ item.start_month }} → {{ item.end_month }}
              </td>
              <td class="py-2.5 px-3.5 font-mono text-slate-700 whitespace-nowrap">
                <span>{{ item.row_count.toLocaleString() }}</span>
                <span v-if="item.duplicate_count" class="text-[10px] text-amber-600 font-medium block">
                  ({{ item.duplicate_count.toLocaleString() }} dups deduplicated)
                </span>
              </td>
              <td class="py-2.5 px-3.5 whitespace-nowrap">
                <div class="inline-flex items-center gap-1.5 flex-wrap">
                  <span class="px-2 py-0.5 rounded-full text-[11px] font-bold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
                    COMMITTED
                  </span>
                  <span 
                    v-if="getRevisionNumber(item.revision_id)" 
                    class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-50 text-indigo-700 border border-indigo-200"
                  >
                    Revision {{ getRevisionNumber(item.revision_id) }}
                  </span>
                </div>
              </td>
              <td class="py-2.5 px-3.5 text-slate-500 font-mono text-[11px] whitespace-nowrap">
                {{ dateTime(item.created_at) }}
              </td>
              <td class="py-2.5 px-3.5 text-right whitespace-nowrap">
                <button 
                  v-if="item.revision_id" 
                  type="button" 
                  class="text-rose-600 hover:text-rose-800 hover:bg-rose-50 border border-rose-200 text-xs font-semibold py-1 px-2.5 rounded-lg inline-flex items-center gap-1 transition-colors cursor-pointer" 
                  @click="promptDeleteRevision(item.revision_id)"
                  title="Delete this revision and rollback dataset"
                >
                  <Trash2Icon class="w-3.5 h-3.5" />
                  <span>Delete / Rollback</span>
                </button>
              </td>
            </tr>
            <tr v-if="!imports.length">
              <td colspan="6" class="text-center py-6 text-slate-400">No committed datasets found on the server.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <!-- Confirm ETL Revision Commit Dialog -->
  <ConfirmDialog
    :open="confirmCommit"
    :busy="busy"
    :error="error"
    title="Commit & Push to ETL Pipeline?"
    :message="
      selected
        ? `Confirm committing ${selected.filename} (${selected.start_month} → ${selected.end_month}) to the ETL pipeline. Preview: insert +${selected.preview.inserted}, update ${selected.preview.updated}. This creates an immutable revision for analytics.`
        : ''
    "
    @cancel="confirmCommit = false"
    @confirm="commit"
  />

  <!-- Confirm Publication Update Dialog -->
  <ConfirmDialog
    :open="confirmPub"
    :busy="busy"
    :error="error"
    title="Update Live Display Period?"
    :message="`Are you sure you want to update the live frontend display period to ${pubStart} → ${pubEnd}? Members on the dashboard will immediately see trade data within this date range.`"
    @cancel="confirmPub = false"
    @confirm="publishScope"
  />

  <!-- Confirm Revision Deletion & Rollback Dialog -->
  <ConfirmDialog
    :open="confirmDeleteRev"
    :busy="busy"
    :error="error"
    title="Delete Revision & Rollback?"
    :message="deleteRevMessage"
    @cancel="confirmDeleteRev = false; deleteRevTargetId = null"
    @confirm="handleDeleteRevision"
  />
</template>
