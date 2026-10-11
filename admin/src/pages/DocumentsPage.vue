<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { api, download } from '../api';
import { dateTime } from '../format';
import type { PrivateDocument, Publication } from '../types';
import { useTask } from '../composables/useTask';
import TaskNotice from '../components/TaskNotice.vue';
import DocumentEditor from '../components/DocumentEditor.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';
import {
  FileText as FileTextIcon,
  Presentation as PresentationIcon,
  RefreshCw as RefreshCwIcon,
  Plus as PlusIcon,
  Download as DownloadIcon,
  Eye as EyeIcon,
  Globe as GlobeIcon,
  EyeOff as EyeOffIcon,
  Trash2 as TrashIcon,
  Edit3 as EditIcon,
  Search as SearchIcon,
  X as XIcon,
  Layers as LayersIcon,
} from 'lucide-vue-next';

const documents = ref<PrivateDocument[]>([]);
const publication = ref<Publication | null>(null);
const showForm = ref(false);
const editing = ref<PrivateDocument | null>(null);
const target = ref<PrivateDocument | null>(null);
const action = ref<'publish' | 'draft' | 'delete'>('publish');
const previewUrl = ref('');
const previewTitle = ref('');
const activeFilter = ref<'all' | 'pdf' | 'pptx' | 'published' | 'draft'>('all');
const search = ref('');
let disposed = false;

const { busy, error, notice, run } = useTask();

async function fetchDocs() {
  const res = await api.get<PrivateDocument[]>('/admin/documents');
  documents.value = Array.isArray(res.data) ? res.data : [];
}

async function load() {
  await run(async () => {
    await fetchDocs();
    try {
      publication.value = (await api.get<Publication | null>('/admin/publication')).data;
    } catch {
      publication.value = null;
    }
  });
}

const pdfCount = computed(() =>
  documents.value.filter((d) => d.filename.toLowerCase().endsWith('.pdf')).length,
);
const pptxCount = computed(() =>
  documents.value.filter((d) => d.filename.toLowerCase().endsWith('.pptx') || d.filename.toLowerCase().endsWith('.ppt')).length,
);
const publishedCount = computed(() =>
  documents.value.filter((d) => d.status === 'published').length,
);
const draftCount = computed(() =>
  documents.value.filter((d) => d.status === 'draft').length,
);

const filteredDocuments = computed(() => {
  let list = documents.value;

  if (activeFilter.value === 'pdf') {
    list = list.filter((d) => d.filename.toLowerCase().endsWith('.pdf'));
  } else if (activeFilter.value === 'pptx') {
    list = list.filter((d) => d.filename.toLowerCase().endsWith('.pptx') || d.filename.toLowerCase().endsWith('.ppt'));
  } else if (activeFilter.value === 'published') {
    list = list.filter((d) => d.status === 'published');
  } else if (activeFilter.value === 'draft') {
    list = list.filter((d) => d.status === 'draft');
  }

  const q = search.value.trim().toLowerCase();
  if (!q) return list;

  return list.filter(
    (d) =>
      d.title.toLowerCase().includes(q) ||
      d.description.toLowerCase().includes(q) ||
      d.filename.toLowerCase().includes(q),
  );
});

function isPptx(doc: PrivateDocument): boolean {
  const f = doc.filename.toLowerCase();
  return f.endsWith('.pptx') || f.endsWith('.ppt');
}

function edit(doc: PrivateDocument | null) {
  editing.value = doc;
  showForm.value = true;
}

function closePreview() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value);
  previewUrl.value = '';
  previewTitle.value = '';
}

async function preview(doc: PrivateDocument) {
  await run(async () => {
    closePreview();
    const { data } = await api.get<Blob>(`/documents/${encodeURIComponent(doc.id)}/preview`, {
      responseType: 'blob',
    });
    if (disposed) return;
    if (!data.type.includes('application/pdf')) {
      throw new Error('Backend preview was not a PDF; no preview is shown.');
    }
    previewUrl.value = URL.createObjectURL(data);
    previewTitle.value = doc.title;
  });
}

async function saved() {
  showForm.value = false;
  await run(async () => {
    await fetchDocs();
    notice.value = 'Document saved successfully as a private draft. Click "Publish" when you are ready to make it live on the portal.';
  });
}

function requestAction(doc: PrivateDocument, next: typeof action.value) {
  target.value = doc;
  action.value = next;
  if (next !== 'delete') {
    // Quick confirm for publish/unpublish
    void executeAction();
  }
}

async function executeAction() {
  await run(async () => {
    if (!target.value) return;
    const id = target.value.id;
    const docTitle = target.value.title;

    if (action.value === 'delete') {
      await api.delete(`/admin/documents/${encodeURIComponent(id)}`);
      notice.value = `"${docTitle}" was permanently deleted.`;
    } else {
      const newStatus = action.value === 'publish' ? 'published' : 'draft';
      const { data } = await api.patch<PrivateDocument>(
        `/admin/documents/${encodeURIComponent(id)}`,
        { status: newStatus },
      );
      if (data.status !== newStatus) {
        throw new Error('Backend did not confirm the requested document status.');
      }
      notice.value =
        newStatus === 'published'
          ? `"${docTitle}" is now published and live on the member portal!`
          : `"${docTitle}" was unpublished and reverted to private draft.`;
    }

    target.value = null;
    closePreview();
    await fetchDocs();
  });
}

onMounted(load);
onUnmounted(() => {
  disposed = true;
  closePreview();
});
</script>

<template>
  <div class="space-y-6 w-full max-w-[1560px] mx-auto pb-12">
    <!-- Page Header -->
    <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 sm:pb-4 mb-5">
      <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">Reports & Presentations</h1>
      <button
        type="button"
        class="btn-primary inline-flex items-center gap-1.5 px-3 py-1.5 sm:px-4 sm:py-2 text-xs font-bold rounded-xl bg-sky-600 hover:bg-sky-700 text-white transition cursor-pointer shadow-xs flex-shrink-0"
        @click="edit(null)"
      >
        <PlusIcon class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        <span>Upload File</span>
      </button>
    </div>

    <TaskNotice :busy="busy" :error="error" :notice="notice" />

    <!-- Upload / Edit Modal Overlay -->
    <div
      v-if="showForm"
      class="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto"
      @click.self="showForm = false"
    >
      <div class="w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <DocumentEditor
          :document="editing"
          @saved="saved"
          @cancel="showForm = false"
        />
      </div>
    </div>

    <!-- PDF Preview Modal Overlay -->
    <div
      v-if="previewUrl"
      class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto"
      @click.self="closePreview"
    >
      <div class="w-full max-w-4xl bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">
        <div class="flex items-center justify-between p-4 bg-slate-900 text-white border-b border-slate-800">
          <div class="flex items-center gap-2.5 min-w-0">
            <FileTextIcon class="w-5 h-5 text-sky-400 flex-shrink-0" />
            <h2 class="text-sm font-bold truncate">{{ previewTitle }}</h2>
          </div>
          <button
            type="button"
            class="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
            @click="closePreview"
          >
            <XIcon class="w-5 h-5" />
          </button>
        </div>
        <div class="flex-1 bg-slate-950 min-h-[60vh]">
          <iframe :src="previewUrl" :title="previewTitle" class="w-full h-full min-h-[70vh] border-0"></iframe>
        </div>
      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <ConfirmDialog
      :open="!!target && action === 'delete'"
      title="Delete Document"
      :message="target ? `Are you sure you want to permanently delete '${target.title}'? This action cannot be undone.` : ''"
      :busy="busy"
      :error="error"
      @confirm="executeAction"
      @cancel="target = null"
    />

    <!-- Filter Pills & Search Bar Toolbar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-1">
      <div class="flex flex-wrap p-1 bg-slate-200/70 border border-slate-200/80 rounded-2xl shadow-inner gap-1 w-full sm:w-auto">
        <button
          type="button"
          class="tab-btn inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 text-xs font-bold rounded-xl transition cursor-pointer"
          :class="activeFilter === 'all' ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
          @click="activeFilter = 'all'"
        >
          <span>All</span>
          <span class="px-1.5 py-0.2 text-[10px] font-mono rounded-md" :class="activeFilter === 'all' ? 'bg-slate-900 text-white font-bold' : 'bg-slate-200 text-slate-600'">
            {{ documents.length }}
          </span>
        </button>

        <button
          type="button"
          class="tab-btn inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 text-xs font-bold rounded-xl transition cursor-pointer"
          :class="activeFilter === 'pdf' ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
          @click="activeFilter = 'pdf'"
        >
          <FileTextIcon class="w-3.5 h-3.5 text-sky-600" />
          <span>PDF</span>
          <span class="px-1.5 py-0.2 text-[10px] font-mono rounded-md" :class="activeFilter === 'pdf' ? 'bg-sky-50 text-sky-800 border border-sky-200 font-bold' : 'bg-slate-200 text-slate-600'">
            {{ pdfCount }}
          </span>
        </button>

        <button
          type="button"
          class="tab-btn inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 text-xs font-bold rounded-xl transition cursor-pointer"
          :class="activeFilter === 'pptx' ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
          @click="activeFilter = 'pptx'"
        >
          <PresentationIcon class="w-3.5 h-3.5 text-purple-600" />
          <span>PPTX</span>
          <span class="px-1.5 py-0.2 text-[10px] font-mono rounded-md" :class="activeFilter === 'pptx' ? 'bg-purple-50 text-purple-800 border border-purple-200 font-bold' : 'bg-slate-200 text-slate-600'">
            {{ pptxCount }}
          </span>
        </button>

        <button
          type="button"
          class="tab-btn inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 text-xs font-bold rounded-xl transition cursor-pointer"
          :class="activeFilter === 'published' ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
          @click="activeFilter = 'published'"
        >
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Live</span>
          <span class="px-1.5 py-0.2 text-[10px] font-mono rounded-md" :class="activeFilter === 'published' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold' : 'bg-slate-200 text-slate-600'">
            {{ publishedCount }}
          </span>
        </button>

        <button
          type="button"
          class="tab-btn inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 text-xs font-bold rounded-xl transition cursor-pointer"
          :class="activeFilter === 'draft' ? 'bg-white text-slate-900 shadow-xs border border-slate-200/60' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'"
          @click="activeFilter = 'draft'"
        >
          <span>Drafts</span>
          <span class="px-1.5 py-0.2 text-[10px] font-mono rounded-md" :class="activeFilter === 'draft' ? 'bg-slate-100 text-slate-700 font-bold' : 'bg-slate-200 text-slate-600'">
            {{ draftCount }}
          </span>
        </button>
      </div>

      <!-- Search Bar -->
      <div class="search-field w-full sm:w-64 lg:w-72 flex-shrink-0">
        <SearchIcon class="search-icon" />
        <input
          v-model="search"
          type="search"
          placeholder="Filter documents..."
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
    </div>

    <!-- Document Catalogue Cards Grid -->
    <div v-if="filteredDocuments.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5">
      <div
        v-for="doc in filteredDocuments"
        :key="doc.id"
        class="bg-white rounded-2xl border border-slate-200/90 shadow-xs hover:border-slate-300 transition-all p-5 flex flex-col justify-between"
      >
        <div class="space-y-3">
          <!-- Top Badges -->
          <div class="flex items-center justify-between gap-2">
            <!-- Format Badge -->
            <span
              v-if="!isPptx(doc)"
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-sky-50 text-sky-700 border border-sky-200"
            >
              <FileTextIcon class="w-3.5 h-3.5" />
              <span>Document (PDF)</span>
            </span>
            <span
              v-else
              class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-bold bg-purple-50 text-purple-700 border border-purple-200"
            >
              <PresentationIcon class="w-3.5 h-3.5" />
              <span>Slide (PPTX)</span>
            </span>

            <!-- Status Badge -->
            <span
              class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider"
              :class="
                doc.status === 'published'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              "
            >
              <span v-if="doc.status === 'published'" class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>{{ doc.status === 'published' ? 'Live' : 'Draft' }}</span>
            </span>
          </div>

          <!-- Document Title & Description -->
          <div>
            <h2 class="text-sm font-bold text-slate-900 leading-snug m-0">
              {{ doc.title }}
            </h2>
            <p v-if="doc.description" class="text-xs text-slate-500 m-0 mt-1 line-clamp-2 text-justify">
              {{ doc.description }}
            </p>
          </div>

          <!-- File Info -->
          <div class="pt-2 border-t border-slate-100 text-[11px] text-slate-400 space-y-0.5">
            <div class="truncate font-mono text-slate-600 font-medium">{{ doc.filename }}</div>
            <div class="flex items-center justify-between text-slate-400">
              <span>{{ (doc.size_bytes / 1024 / 1024).toFixed(2) }} MiB</span>
              <span>{{ dateTime(doc.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="mt-5 pt-3.5 border-t border-slate-100 space-y-2">
          <!-- Main Publishing Toggle Button -->
          <div>
            <button
              v-if="doc.status === 'draft'"
              type="button"
              class="w-full inline-flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition cursor-pointer shadow-xs"
              @click="requestAction(doc, 'publish')"
            >
              <GlobeIcon class="w-3.5 h-3.5" />
              <span>Publish to Portal</span>
            </button>
            <button
              v-else
              type="button"
              class="w-full btn-secondary inline-flex items-center justify-center gap-1.5 py-2 px-3 text-xs font-semibold rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition cursor-pointer shadow-2xs"
              @click="requestAction(doc, 'draft')"
            >
              <EyeOffIcon class="w-3.5 h-3.5 text-slate-500" />
              <span>Unpublish (Move to Draft)</span>
            </button>
          </div>

          <!-- Auxiliary Tools: Preview, Download, Edit, Delete -->
          <div class="flex items-center justify-between gap-1.5 pt-1">
            <button
              v-if="doc.preview_status === 'ready' || isPptx(doc)"
              type="button"
              class="btn-secondary text-xs px-2.5 py-1.5 rounded-lg inline-flex items-center gap-1 border border-slate-200 bg-white hover:bg-sky-50 hover:text-sky-700 hover:border-sky-200 text-slate-700 font-semibold shadow-2xs transition cursor-pointer"
              @click="preview(doc)"
            >
              <EyeIcon class="w-3.5 h-3.5" />
              <span>Preview</span>
            </button>

            <button
              type="button"
              class="btn-secondary text-xs px-2.5 py-1.5 rounded-lg inline-flex items-center gap-1 border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold shadow-2xs transition"
              @click="download(`/documents/${doc.id}/download`, doc.filename)"
            >
              <DownloadIcon class="w-3.5 h-3.5 text-slate-500" />
              <span>Download</span>
            </button>

            <div class="flex items-center gap-1 ml-auto">
              <button
                type="button"
                class="btn-ghost p-1.5 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition cursor-pointer"
                title="Edit metadata"
                @click="edit(doc)"
              >
                <EditIcon class="w-4 h-4" />
              </button>
              <button
                type="button"
                class="btn-ghost p-1.5 rounded-lg text-rose-400 hover:text-rose-600 hover:bg-rose-50 transition cursor-pointer"
                title="Delete file"
                @click="requestAction(doc, 'delete')"
              >
                <TrashIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="p-16 text-center bg-white rounded-3xl border border-slate-200 shadow-xs space-y-3"
    >
      <FileTextIcon class="w-12 h-12 text-slate-300 mx-auto" />
      <h3 class="text-sm font-bold text-slate-700 m-0">No documents or presentation slides found</h3>
      <p class="text-xs text-slate-400 m-0">
        {{ search ? `No items matched your search "${search}".` : 'Click "Upload Document / Slide" above to add reports for members.' }}
      </p>
      <div v-if="!search" class="pt-2">
        <button
          type="button"
          class="btn-primary text-xs font-bold py-2 px-4 rounded-xl inline-flex items-center gap-1.5"
          @click="edit(null)"
        >
          <PlusIcon class="w-4 h-4" />
          <span>Upload First File</span>
        </button>
      </div>
    </div>
  </div>
</template>
