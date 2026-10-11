<template>
  <section class="space-y-8 py-6 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
      <div class="space-y-1">
        <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-200/80 text-xs font-bold">
          <LayersIcon class="w-3.5 h-3.5 text-sky-600" />
          <span>Proprietary Member Research</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight m-0">
          Strategy & Market Documents
        </h1>
      </div>
    </div>

    <!-- Status States -->
    <div v-if="loading" class="surface text-center py-16 space-y-3" role="status">
      <div class="w-8 h-8 border-3 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="text-xs text-slate-500 font-medium">Loading published documents…</p>
    </div>

    <!-- Page Load Error State (Only when fetching the documents list fails) -->
    <div v-else-if="error" class="notice flex items-center justify-between" role="alert">
      <span>{{ error }}</span>
      <button class="underline font-bold cursor-pointer" @click="load">Retry</button>
    </div>

    <!-- Main Content when loaded -->
    <div v-else class="space-y-6">
      <!-- File Action Error Notice (Dismissible toast/banner that does not hide the documents grid) -->
      <div 
        v-if="files.error.value" 
        class="bg-amber-50 border border-amber-200 text-amber-900 px-4 py-3 rounded-2xl flex items-center justify-between shadow-xs animate-in fade-in"
        role="alert"
      >
        <div class="flex items-center gap-2 text-xs font-semibold">
          <AlertTriangleIcon class="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>{{ files.error.value }}</span>
        </div>
        <button 
          @click="files.clear" 
          class="text-amber-800 hover:text-amber-950 text-xs font-bold px-2.5 py-1 rounded-lg hover:bg-amber-100/80 transition-colors cursor-pointer"
        >
          Dismiss
        </button>
      </div>
      <!-- Segmented Category Tabs & Search Bar -->
      <div class="flex items-center justify-between gap-4 flex-wrap pb-1">
        <!-- 2 Distinct Tabs (Documents vs Slides) -->
        <div class="inline-flex p-1 bg-slate-200/70 border border-slate-200/80 rounded-2xl shadow-inner gap-1">
          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl transition cursor-pointer"
            :class="
              activeTab === 'documents'
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            "
            @click="activeTab = 'documents'"
          >
            <FileTextIcon class="w-4 h-4" :class="activeTab === 'documents' ? 'text-sky-600' : 'text-slate-400'" />
            <span>1. Documents (PDF)</span>
            <span
              class="px-2 py-0.5 text-[11px] font-mono rounded-md"
              :class="activeTab === 'documents' ? 'bg-sky-50 text-sky-800 border border-sky-200/80 font-bold' : 'bg-slate-200 text-slate-600 font-semibold'"
            >
              {{ pdfDocuments.length }}
            </span>
          </button>

          <button
            type="button"
            class="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl transition cursor-pointer"
            :class="
              activeTab === 'slides'
                ? 'bg-white text-slate-900 shadow-sm border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            "
            @click="activeTab = 'slides'"
          >
            <PresentationIcon class="w-4 h-4" :class="activeTab === 'slides' ? 'text-purple-600' : 'text-slate-400'" />
            <span>2. Presentation Slides (PPTX)</span>
            <span
              class="px-2 py-0.5 text-[11px] font-mono rounded-md"
              :class="activeTab === 'slides' ? 'bg-purple-50 text-purple-800 border border-purple-200/80 font-bold' : 'bg-slate-200 text-slate-600 font-semibold'"
            >
              {{ slideDocuments.length }}
            </span>
          </button>
        </div>

        <!-- Search Filter -->
        <div class="relative w-full sm:w-72">
          <SearchIcon class="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
          <input
            v-model="search"
            type="search"
            :placeholder="activeTab === 'documents' ? 'Search PDF documents...' : 'Search presentation slides...'"
            class="block w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-sky-500 focus:outline-none"
          />
        </div>
      </div>

      <!-- ========================================================================= -->
      <!-- TAB 1: PDF DOCUMENTS                                                      -->
      <!-- ========================================================================= -->
      <div v-if="activeTab === 'documents'">
        <div v-if="filteredItems.length === 0" class="surface text-center py-16 text-slate-500 space-y-3 rounded-3xl border border-slate-200/80">
          <FileTextIcon class="w-12 h-12 text-slate-300 mx-auto" />
          <h3 class="font-bold text-slate-800 text-sm m-0">No PDF Documents Available</h3>
          <p class="text-xs text-slate-400 m-0 max-w-sm mx-auto">
            {{ search ? `No PDF documents matched "${search}".` : 'No PDF reports have been published yet. Published reports from the Admin Portal will appear here.' }}
          </p>
        </div>

        <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <article
            v-for="document in filteredItems"
            :key="document.id"
            class="surface relative flex flex-col justify-between hover:border-sky-300 hover:shadow-md transition-all rounded-2xl p-6 group"
          >
            <div class="space-y-3">
              <!-- Badges -->
              <div class="flex items-center justify-between gap-2">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-sky-50 text-sky-700 border border-sky-200">
                  <FileTextIcon class="w-3.5 h-3.5" />
                  <span>PDF REPORT</span>
                </span>
                <span class="text-[11px] font-mono text-slate-400">
                  {{ (document.size_bytes / 1024 / 1024).toFixed(1) }} MiB
                </span>
              </div>

              <!-- Title & Description -->
              <h2 class="text-base font-bold text-slate-900 group-hover:text-sky-800 transition-colors leading-snug m-0">
                {{ document.title }}
              </h2>

              <p v-if="document.description" class="text-xs text-slate-600 leading-relaxed whitespace-pre-line line-clamp-3 m-0">
                {{ document.description }}
              </p>

              <!-- Exact Published Timestamp Meta -->
              <div class="pt-3 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
                <div class="flex items-center gap-1.5 text-slate-600 font-medium">
                  <ClockIcon class="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <span>Published: <strong>{{ localDate(document.created_at) }}</strong></span>
                </div>
                <div class="truncate font-mono text-slate-400 text-[10px]">
                  File: {{ document.filename }}
                </div>
              </div>
            </div>

            <!-- Card Actions -->
            <div class="mt-6 pt-4 border-t border-slate-100 space-y-2.5">
              <div class="flex items-center gap-2">
                <button
                  v-if="document.preview_status === 'ready'"
                  class="secondary-button text-xs py-2 px-3 flex-1 font-bold inline-flex items-center justify-center gap-1.5 whitespace-nowrap cursor-pointer"
                  :disabled="files.busy.value"
                  @click="preview(document.id, document.title)"
                >
                  <EyeIcon class="w-3.5 h-3.5 text-slate-500" />
                  <span>Preview</span>
                </button>
                <button
                  class="primary-button text-xs py-2 px-3 flex-1 font-bold shadow-2xs inline-flex items-center justify-center gap-1.5 whitespace-nowrap cursor-pointer"
                  :disabled="files.busy.value"
                  @click="files.open(`/documents/${document.id}/download`, document.filename)"
                >
                  <DownloadIcon class="w-3.5 h-3.5" />
                  <span>Download</span>
                </button>
              </div>

              <p v-if="document.preview_status === 'pending'" class="text-[11px] text-amber-600 font-medium m-0">
                Preview is preparing. Direct download is ready above.
              </p>
            </div>
          </article>
        </div>
      </div>

      <!-- ========================================================================= -->
      <!-- TAB 2: PRESENTATION SLIDES (PPTX)                                         -->
      <!-- ========================================================================= -->
      <div v-else>
        <div v-if="filteredItems.length === 0" class="surface text-center py-16 text-slate-500 space-y-3 rounded-3xl border border-slate-200/80">
          <PresentationIcon class="w-12 h-12 text-slate-300 mx-auto" />
          <h3 class="font-bold text-slate-800 text-sm m-0">No Presentation Slides Available</h3>
          <p class="text-xs text-slate-400 m-0 max-w-sm mx-auto">
            {{ search ? `No presentation slides matched "${search}".` : 'No slide presentations have been published yet. Published decks from the Admin Portal will appear here.' }}
          </p>
        </div>

        <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <article
            v-for="document in filteredItems"
            :key="document.id"
            class="surface relative flex flex-col justify-between hover:border-purple-300 hover:shadow-md transition-all rounded-2xl p-6 group"
          >
            <div class="space-y-3">
              <!-- Badges -->
              <div class="flex items-center justify-between gap-2">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg text-[11px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                  <PresentationIcon class="w-3.5 h-3.5" />
                  <span>POWERPOINT SLIDE</span>
                </span>
                <span class="text-[11px] font-mono text-slate-400">
                  {{ (document.size_bytes / 1024 / 1024).toFixed(1) }} MiB
                </span>
              </div>

              <!-- Title & Description -->
              <h2 class="text-base font-bold text-slate-900 group-hover:text-purple-800 transition-colors leading-snug m-0">
                {{ document.title }}
              </h2>

              <p v-if="document.description" class="text-xs text-slate-600 leading-relaxed whitespace-pre-line line-clamp-3 m-0">
                {{ document.description }}
              </p>

              <!-- Exact Published Timestamp Meta -->
              <div class="pt-3 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
                <div class="flex items-center gap-1.5 text-slate-600 font-medium">
                  <ClockIcon class="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  <span>Published: <strong>{{ localDate(document.created_at) }}</strong></span>
                </div>
                <div class="truncate font-mono text-slate-400 text-[10px]">
                  File: {{ document.filename }}
                </div>
              </div>
            </div>

            <!-- Card Actions -->
            <div class="mt-6 pt-4 border-t border-slate-100 space-y-2.5">
              <div class="flex items-center gap-2">
                <button
                  v-if="document.preview_status === 'ready' || isPptx(document)"
                  class="secondary-button text-xs py-2 px-3 flex-1 font-bold inline-flex items-center justify-center gap-1.5 whitespace-nowrap cursor-pointer"
                  :disabled="files.busy.value"
                  @click="preview(document.id, document.title)"
                >
                  <EyeIcon class="w-3.5 h-3.5 text-slate-500" />
                  <span>Preview</span>
                </button>
                <button
                  class="primary-button text-xs py-2 px-3 flex-1 font-bold shadow-2xs inline-flex items-center justify-center gap-1.5 whitespace-nowrap cursor-pointer !bg-purple-600 hover:!bg-purple-700"
                  :disabled="files.busy.value"
                  @click="files.open(`/documents/${document.id}/download`, document.filename)"
                >
                  <DownloadIcon class="w-3.5 h-3.5" />
                  <span>Download</span>
                </button>
              </div>

              <p v-if="document.preview_status === 'pending'" class="text-[11px] text-amber-600 font-medium m-0">
                Slide preview is converting. Direct download is ready above.
              </p>
            </div>
          </article>
        </div>
      </div>
    </div>

    <!-- Active Loading File Indicator -->
    <p v-if="files.busy.value" class="text-xs font-semibold text-sky-700 animate-pulse text-center" role="status">
      Downloading/opening protected document…
    </p>

    <!-- Embedded In-Browser PDF Preview Viewer Modal -->
    <section ref="previewSectionRef" v-if="files.previewUrl.value" class="surface space-y-4 rounded-3xl border-2 border-sky-200 shadow-xl p-4 sm:p-6 animate-in fade-in">
      <div class="flex items-center justify-between gap-3 border-b border-slate-100 pb-3 flex-wrap">
        <div class="flex items-center gap-2">
          <FileTextIcon class="w-5 h-5 text-sky-600 flex-shrink-0" />
          <h2 class="font-bold text-slate-900 text-sm sm:text-base m-0">{{ previewTitle }}</h2>
        </div>
        <div class="flex items-center gap-2">
          <a
            :href="files.previewUrl.value"
            target="_blank"
            rel="noopener noreferrer"
            class="secondary-button text-xs font-bold py-1.5 px-3 inline-flex items-center gap-1.5 cursor-pointer text-sky-700 hover:text-sky-800"
            title="Open in separate tab"
          >
            <ExternalLinkIcon class="w-3.5 h-3.5" />
            <span>Open in New Tab</span>
          </a>
          <button class="secondary-button text-xs font-bold py-1.5 px-3 cursor-pointer inline-flex items-center gap-1" @click="files.clear">
            <XIcon class="w-3.5 h-3.5 text-slate-500" />
            <span>Close Preview</span>
          </button>
        </div>
      </div>

      <div class="bg-slate-900 rounded-2xl overflow-hidden shadow-inner">
        <iframe 
          :src="files.previewUrl.value" 
          :title="previewTitle" 
          class="w-full h-[65vh] sm:h-[75vh] min-h-[400px] border-0"
        ></iframe>
      </div>

      <p class="text-[11px] text-slate-400 text-center m-0">
        If your mobile browser does not display the embedded PDF above, tap <a :href="files.previewUrl.value" target="_blank" rel="noopener noreferrer" class="text-sky-600 font-bold underline">Open in New Tab</a> to view directly.
      </p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, nextTick } from 'vue';
import { 
  FileText as FileTextIcon,
  Presentation as PresentationIcon,
  Download as DownloadIcon,
  Eye as EyeIcon,
  X as XIcon,
  Clock as ClockIcon,
  Search as SearchIcon,
  Layers as LayersIcon,
  AlertTriangle as AlertTriangleIcon,
  ExternalLink as ExternalLinkIcon
} from 'lucide-vue-next';
import { useMemberStore } from '../stores/memberStore';
import { usePrivateFiles } from '../composables/usePrivateFiles';
import { apiError } from '../services/api';
import { onPrivateReset, privateEpoch } from '../services/privateState';
import { localDate } from '../utils/membership';

function isPptx(doc: { filename: string }) {
  return doc.filename.toLowerCase().endsWith('.pptx') || doc.filename.toLowerCase().endsWith('.ppt');
}

const member = useMemberStore();
const files = usePrivateFiles();
const loading = ref(true);
const error = ref('');
const previewTitle = ref('');
const activeTab = ref<'documents' | 'slides'>('documents');
const search = ref('');
let disposed = false;

const off = onPrivateReset(() => { 
  previewTitle.value = ''; 
  error.value = ''; 
});

onUnmounted(() => { 
  disposed = true; 
  off(); 
});

async function load() {
  const epoch = privateEpoch;
  loading.value = true; 
  error.value = '';
  try { 
    await member.loadDocuments(); 
  } catch (err) { 
    if (!disposed && epoch === privateEpoch) error.value = apiError(err); 
  }
  finally { 
    if (!disposed) loading.value = false; 
  }
}

const previewSectionRef = ref<HTMLElement | null>(null);

async function preview(id: string, title: string) { 
  previewTitle.value = title; 
  await files.open(`/documents/${id}/preview`); 
  if (files.previewUrl.value) {
    await nextTick();
    previewSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

const pdfDocuments = computed(() =>
  member.documents.filter((d) => d.filename.toLowerCase().endsWith('.pdf')),
);

const slideDocuments = computed(() =>
  member.documents.filter(
    (d) => d.filename.toLowerCase().endsWith('.pptx') || d.filename.toLowerCase().endsWith('.ppt'),
  ),
);

const filteredItems = computed(() => {
  const source = activeTab.value === 'documents' ? pdfDocuments.value : slideDocuments.value;
  const q = search.value.trim().toLowerCase();
  if (!q) return source;
  return source.filter(
    (d) =>
      d.title.toLowerCase().includes(q) ||
      d.description.toLowerCase().includes(q) ||
      d.filename.toLowerCase().includes(q),
  );
});

onMounted(load);
</script>
