<script setup lang="ts">
import { reactive, ref, watch } from 'vue';
import { api } from '../api';
import type { PrivateDocument } from '../types';
import { useTask } from '../composables/useTask';
import TaskNotice from './TaskNotice.vue';
import {
  FileText as FileTextIcon,
  Presentation as PresentationIcon,
  UploadCloud as UploadCloudIcon,
  CheckCircle2 as CheckCircle2Icon,
} from 'lucide-vue-next';

const props = defineProps<{ document?: PrivateDocument | null }>();
const emit = defineEmits<{ saved: []; cancel: [] }>();

const uploadType = ref<'pdf' | 'pptx'>('pdf');

const form = reactive({
  title: '',
  description: '',
  language: 'both' as PrivateDocument['language'],
  publication_id: '',
});

const file = ref<File | null>(null);
const { busy, error, run } = useTask();

watch(
  () => props.document,
  (doc) => {
    if (doc) {
      form.title = doc.title;
      form.description = doc.description;
      form.language = doc.language;
      form.publication_id = doc.publication_id || '';
      uploadType.value = doc.filename.toLowerCase().endsWith('.pptx') ? 'pptx' : 'pdf';
    } else {
      form.title = '';
      form.description = '';
      form.language = 'both';
      form.publication_id = '';
      uploadType.value = 'pdf';
    }
    file.value = null;
  },
  { immediate: true },
);

function onFileSelected(event: Event) {
  const selectedFile = (event.target as HTMLInputElement).files?.[0] || null;
  file.value = selectedFile;
  if (selectedFile && !form.title) {
    // Auto-detect title from file name without extension
    const cleanName = selectedFile.name
      .replace(/\.[^/.]+$/, '')
      .replace(/[_-]+/g, ' ')
      .trim();
    form.title = cleanName;
  }
}

function handleTypeSwitch(type: 'pdf' | 'pptx') {
  uploadType.value = type;
  file.value = null;
}

async function save() {
  await run(async () => {
    if (!form.title.trim()) throw new Error('A title / name is required.');
    if (props.document) {
      await api.patch(`/admin/documents/${encodeURIComponent(props.document.id)}`, {
        title: form.title.trim(),
        description: form.description.trim(),
        language: form.language,
        publication_id: form.publication_id.trim() || null,
      });
    } else {
      if (!file.value) {
        throw new Error(
          uploadType.value === 'pdf'
            ? 'Please choose a PDF document (.pdf).'
            : 'Please choose a presentation slide deck (.pptx, .ppt, or .pdf).'
        );
      }
      if (file.value.size > 25 * 1024 * 1024) {
        throw new Error('Upload exceeds 25 MiB limit.');
      }
      const lowerName = file.value.name.toLowerCase();
      if (uploadType.value === 'pdf' && !lowerName.endsWith('.pdf')) {
        throw new Error('Please select a valid PDF file (.pdf).');
      }
      if (uploadType.value === 'pptx' && !lowerName.endsWith('.pptx') && !lowerName.endsWith('.ppt') && !lowerName.endsWith('.pdf')) {
        throw new Error('Please select a PowerPoint presentation (.pptx, .ppt) or PDF slide export (.pdf).');
      }

      const body = new FormData();
      body.append('file', file.value);
      body.append('title', form.title.trim());
      body.append('description', form.description.trim());
      body.append('language', form.language);
      if (form.publication_id.trim()) body.append('publication_id', form.publication_id.trim());

      const { data } = await api.post<PrivateDocument>('/admin/documents', body, {
        timeout: 120000,
      });
      if (data.status !== 'draft') {
        throw new Error('Uploaded document was not confirmed as draft.');
      }
    }
    emit('saved');
  });
}
</script>

<template>
  <form class="bg-white border border-slate-200/90 rounded-2xl shadow-sm p-6 space-y-5" @submit.prevent="save">
    <div class="flex items-center justify-between border-b border-slate-100 pb-3.5">
      <h2 class="text-base font-bold text-slate-900 m-0">
        {{ document ? 'Edit Document Details' : 'Upload Document or Slide' }}
      </h2>
      <span v-if="document" class="px-2.5 py-1 rounded-full text-xs font-mono font-bold uppercase" :class="document.status === 'published' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'">
        {{ document.status }}
      </span>
    </div>

    <TaskNotice :busy="busy" :error="error" />

    <fieldset :disabled="busy" class="space-y-4">
      <!-- 1. Category Switcher (Document vs Slide) -->
      <div v-if="!document" class="space-y-1.5">
        <label class="block text-xs font-bold text-slate-700 m-0">Upload Type</label>
        <div class="grid grid-cols-2 gap-3 max-w-md">
          <button
            type="button"
            class="p-3 rounded-xl border text-left transition cursor-pointer flex items-center gap-3"
            :class="uploadType === 'pdf' ? 'border-sky-500 bg-sky-50/70 text-sky-900 ring-2 ring-sky-500/20' : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'"
            @click="handleTypeSwitch('pdf')"
          >
            <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-white border border-slate-200/80 text-sky-600 shadow-2xs">
              <FileTextIcon class="w-4 h-4" />
            </div>
            <div>
              <div class="text-xs font-bold">1. Document</div>
              <div class="text-[11px] text-slate-500">PDF file only (.pdf)</div>
            </div>
          </button>

          <button
            type="button"
            class="p-3 rounded-xl border text-left transition cursor-pointer flex items-center gap-3"
            :class="uploadType === 'pptx' ? 'border-purple-500 bg-purple-50/70 text-purple-900 ring-2 ring-purple-500/20' : 'border-slate-200 bg-white hover:bg-slate-50 text-slate-700'"
            @click="handleTypeSwitch('pptx')"
          >
            <div class="w-8 h-8 rounded-lg flex items-center justify-center bg-white border border-slate-200/80 text-purple-600 shadow-2xs">
              <PresentationIcon class="w-4 h-4" />
            </div>
            <div>
              <div class="text-xs font-bold">2. Slide</div>
              <div class="text-[11px] text-slate-500">PowerPoint or PDF (.pptx, .pdf)</div>
            </div>
          </button>
        </div>
      </div>

      <!-- 2. Source File Input (When creating new) -->
      <div v-if="!document" class="space-y-1.5">
        <label class="block text-xs font-bold text-slate-700 m-0">
          Choose {{ uploadType === 'pdf' ? 'PDF Document' : 'Slide Deck (.pptx, .pdf)' }}
          <span class="text-rose-500">*</span>
        </label>
        <div class="p-4 border-2 border-dashed rounded-xl bg-slate-50/60 hover:bg-slate-50 transition border-slate-300 flex flex-col items-center justify-center text-center gap-2">
          <UploadCloudIcon class="w-7 h-7 text-slate-400" />
          <div class="text-xs text-slate-600 font-medium">
            <span v-if="uploadType === 'pdf'">Select a PDF report (up to 25 MiB)</span>
            <span v-else>Select a PowerPoint presentation (.pptx) or PDF slide export (up to 25 MiB)</span>
          </div>
          <input
            type="file"
            :accept="uploadType === 'pdf' ? '.pdf' : '.pptx,.ppt,.pdf'"
            required
            class="text-xs cursor-pointer max-w-xs"
            @change="onFileSelected"
          />
          <div v-if="file" class="text-xs font-bold text-emerald-700 inline-flex items-center gap-1 mt-1">
            <CheckCircle2Icon class="w-3.5 h-3.5" />
            <span>Selected: {{ file.name }} ({{ (file.size / 1024 / 1024).toFixed(2) }} MiB)</span>
          </div>
        </div>
      </div>

      <div v-else class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-600 flex items-center justify-between">
        <span>File: <strong>{{ document.filename }}</strong> ({{ (document.size_bytes / 1024 / 1024).toFixed(2) }} MiB)</span>
        <span class="font-mono text-slate-400 text-[11px]">ID: {{ document.id }}</span>
      </div>

      <!-- 3. Title / Name (Auto-detected from file name) -->
      <div class="space-y-1.5">
        <label class="block text-xs font-bold text-slate-700 m-0">
          Document Title / Name <span class="text-rose-500">*</span>
        </label>
        <input
          v-model="form.title"
          required
          placeholder="e.g. Cambodia Rice Export Market Analysis 2026"
          class="block w-full text-xs border border-slate-200 rounded-xl px-3 py-2 bg-white focus:ring-2 focus:ring-sky-500 focus:outline-none"
        />
        <small class="text-[11px] text-slate-400 block">Auto-filled from file name. You can edit it if needed.</small>
      </div>

      <!-- 4. Description -->
      <div class="space-y-1.5">
        <label class="block text-xs font-bold text-slate-700 m-0">Description (Optional)</label>
        <textarea
          v-model="form.description"
          rows="3"
          placeholder="Summary, key highlights, or takeaways for members..."
          class="block w-full text-xs border border-slate-200 rounded-xl p-3 bg-white focus:ring-2 focus:ring-sky-500 focus:outline-none"
        ></textarea>
      </div>

      <!-- Actions -->
      <div class="pt-3 flex items-center justify-end gap-3 border-t border-slate-100">
        <button type="button" class="btn-secondary text-xs font-semibold py-2 px-4 rounded-xl cursor-pointer" @click="emit('cancel')">
          Cancel
        </button>
        <button type="submit" class="btn-primary text-xs font-bold py-2 px-5 rounded-xl cursor-pointer shadow-sm">
          {{ document ? 'Save Changes' : 'Upload as Private Draft' }}
        </button>
      </div>
    </fieldset>
  </form>
</template>
