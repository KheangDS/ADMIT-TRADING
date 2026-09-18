<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    
    <!-- Top Navigation Header matching Main App UI -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        <!-- Full Size Brand Logo -->
        <div class="flex items-center gap-3">
          <img 
            src="/admit-trading.png" 
            alt="ADMIT TRADING" 
            class="h-8 sm:h-9 md:h-10 w-auto object-contain max-w-[200px] sm:max-w-[240px]" 
          />
          <div class="hidden lg:block pl-3 border-l border-slate-200">
            <span class="text-xs px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 font-semibold">Admin Ingestion</span>
            <p class="text-[11px] text-slate-500 mt-0.5">Customs Dataset Management</p>
          </div>
        </div>

        <!-- Right Rate Display & Public Link Widget -->
        <div class="flex items-center gap-4">
          <!-- Real-Time Exchange Rate Badge (Automated from MEF API) -->
          <div class="flex items-center gap-2.5 bg-slate-50 px-3.5 py-1.5 rounded-xl border border-slate-200 shadow-inner">
            <span class="text-xs font-bold text-slate-500 uppercase">Rate:</span>
            <div class="flex items-center gap-1.5 text-xs font-bold text-slate-800">
              <span>$1 USD =</span>
              <span class="text-sky-600 font-extrabold text-sm">{{ rateInfo.rate.toLocaleString() }}</span>
              <span class="text-slate-500 text-[11px]">KHR</span>
            </div>
            
            <!-- Real-time Live Status Pill -->
            <span 
              v-if="rateInfo.is_realtime" 
              class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800"
              :title="`Fetched live from MEF API for official trade date ${rateInfo.valid_date || 'Today'}`"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Live MEF{{ rateInfo.valid_date ? ` (${rateInfo.valid_date})` : '' }}
            </span>
            <span 
              v-else 
              class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800"
              title="API unreachable. Defaulting to 4000 KHR."
            >
              <span class="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
              Default
            </span>
          </div>

          <a
            href="http://localhost:5173"
            target="_blank"
            class="hidden sm:flex items-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-all"
          >
            <span>Public Dashboard</span>
            <ExternalLinkIcon class="w-3.5 h-3.5" />
          </a>
        </div>

      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      <!-- Exchange Rate Failed Notice Banner (Shown ONLY if MEF API fetch failed) -->
      <div 
        v-if="!rateInfo.is_realtime && rateInfo.error_message" 
        class="w-full bg-amber-50 border-l-4 border-amber-500 p-3.5 rounded-xl shadow-sm flex items-center justify-between text-xs text-amber-900 animate-in fade-in"
      >
        <div class="flex items-center gap-2.5">
          <AlertTriangleIcon class="w-5 h-5 text-amber-600 flex-shrink-0" />
          <div>
            <p class="font-bold">Real-Time Exchange Rate Fetch Failed</p>
            <p class="text-amber-700 text-[11px] mt-0.5">Could not reach MEF API. Defaulting to <strong>4,000 KHR / 1 USD</strong>.</p>
          </div>
        </div>
        <button 
          @click="fetchAdminStatus" 
          :disabled="isFetchingRate"
          class="cursor-pointer ml-3 px-2.5 py-1 bg-amber-200 hover:bg-amber-300 disabled:opacity-50 text-amber-900 font-semibold rounded-lg text-[11px] transition-colors whitespace-nowrap"
        >
          {{ isFetchingRate ? 'Retrying...' : 'Retry' }}
        </button>
      </div>

      <!-- Ingestion Success Alert Banner -->
      <div v-if="uploadResult" class="w-full bg-emerald-50 border-l-4 border-emerald-500 p-4 rounded-xl shadow-sm flex items-start gap-3 animate-in fade-in">
        <CheckCircle2Icon class="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div class="text-xs">
          <h4 class="text-sm font-bold text-emerald-900">Dataset Ingested Successfully</h4>
          <p class="text-emerald-700 mt-0.5 leading-relaxed">{{ uploadResult.message }}</p>
          <div class="mt-2 pt-2 border-t border-emerald-200 flex flex-wrap gap-4 text-emerald-800 font-semibold">
            <span>Added: +{{ uploadResult.rows_inserted }}</span>
            <span>Updated: {{ uploadResult.rows_updated }}</span>
            <span>Total: {{ uploadResult.total_records.toLocaleString() }} records</span>
            <span>Merged Period: {{ uploadResult.reporting_period }}</span>
            <span>Rate Applied: {{ (uploadResult.exchange_rate_info?.rate || rateInfo.rate).toLocaleString() }} KHR</span>
          </div>
        </div>
      </div>

      <!-- Dataset Validation Error Alert Banner -->
      <div v-if="errorMessage" class="w-full bg-amber-50 border-l-4 border-amber-500 p-4 rounded-xl shadow-sm flex items-start gap-3 animate-in fade-in">
        <AlertTriangleIcon class="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
        <div class="text-xs">
          <h4 class="text-sm font-bold text-amber-900">Dataset Format Notice</h4>
          <p class="text-amber-700 mt-0.5 leading-relaxed">{{ errorMessage }}</p>
        </div>
      </div>

      <!-- SECTION 1: Consolidated Merged Dataset Status Overview -->
      <div v-if="adminStatus" class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
          <div>
            <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <DatabaseIcon class="w-4 h-4 text-sky-600" />
              Consolidated Trade Database
            </h3>
            <p class="text-xs text-slate-500 mt-0.5">Summary of all incremental trade datasets merged into persistent storage</p>
          </div>
          
          <!-- Consolidated Merged Date Period Badge -->
          <div class="flex items-center gap-2 px-3.5 py-1.5 bg-gradient-to-r from-sky-50 to-indigo-50 border border-sky-200 rounded-xl text-xs text-sky-950 shadow-xs">
            <CalendarIcon class="w-4 h-4 text-sky-600 flex-shrink-0" />
            <span>Merged Date Period: <strong class="text-sky-900 font-bold">{{ adminStatus.reporting_period }}</strong></span>
          </div>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
          <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
            <span class="text-[11px] font-bold text-slate-500 uppercase block">Total Records</span>
            <span class="text-lg font-black text-slate-900 mt-0.5 block">{{ adminStatus.total_records.toLocaleString() }}</span>
            <span class="text-[10px] text-slate-400">Rows in DuckDB</span>
          </div>

          <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
            <span class="text-[11px] font-bold text-slate-500 uppercase block">Export Value</span>
            <span class="text-lg font-black text-sky-600 mt-0.5 block">${{ (adminStatus.total_export_val_usd / 1e6).toFixed(2) }}M</span>
            <span class="text-[10px] text-slate-400">USD Equivalent</span>
          </div>

          <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
            <span class="text-[11px] font-bold text-slate-500 uppercase block">Export Volume</span>
            <span class="text-lg font-black text-slate-900 mt-0.5 block">{{ (adminStatus.total_weight_tonnes / 1e3).toFixed(1) }}k</span>
            <span class="text-[10px] text-slate-400">Tonnes Weight</span>
          </div>

          <div class="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
            <span class="text-[11px] font-bold text-slate-500 uppercase block">HS Chapters</span>
            <span class="text-lg font-black text-emerald-600 mt-0.5 block">{{ adminStatus.hs4_chapters_count }}</span>
            <span class="text-[10px] text-slate-400">4-Digit Categories</span>
          </div>
        </div>
      </div>

      <!-- SECTION 2: Ingest New Dataset Card -->
      <div class="bg-white p-8 rounded-3xl border-2 border-dashed border-slate-300 shadow-sm flex flex-col items-center space-y-4 hover:border-sky-500 transition-colors text-center">
        
        <!-- Icon -->
        <div class="w-14 h-14 rounded-2xl bg-sky-50 text-sky-600 flex items-center justify-center">
          <UploadCloudIcon class="w-7 h-7" />
        </div>

        <div>
          <h2 class="text-lg font-bold text-slate-900">Upload New Trade Dataset Batch</h2>
          <p class="text-xs text-slate-500 mt-1 max-w-md mx-auto leading-relaxed">
            Upload an Excel (.xlsx / .csv) file to merge records into the persistent trade dataset.
          </p>
        </div>

        <!-- Selected File Name Pill -->
        <div v-if="selectedFile" class="max-w-md w-full flex items-center gap-2.5 px-4 py-2 bg-sky-50 border border-sky-200 rounded-xl text-xs text-sky-900 font-semibold justify-between">
          <div class="flex items-center gap-2 truncate">
            <FileSpreadsheetIcon class="w-4 h-4 text-sky-600 flex-shrink-0" />
            <span class="truncate">{{ selectedFile.name }}</span>
            <span class="text-slate-400 text-[11px]">({{ (selectedFile.size / 1024).toFixed(1) }} KB)</span>
          </div>
          <button @click="selectedFile = null" class="cursor-pointer text-slate-400 hover:text-red-500">
            <XIcon class="w-4 h-4" />
          </button>
        </div>

        <!-- Action Button -->
        <div class="pt-1 max-w-xs w-full flex flex-col items-center gap-3">
          <label
            v-if="!selectedFile"
            class="cursor-pointer px-6 py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-2"
          >
            <FileSpreadsheetIcon class="w-4 h-4" />
            <span>Browse Excel File</span>
            <input type="file" accept=".xlsx, .xls, .csv" class="hidden" @change="onFileSelected" />
          </label>

          <button
            v-else
            @click="submitUpload"
            :disabled="isProcessing"
            class="cursor-pointer w-full py-2.5 bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
          >
            <Loader2Icon v-if="isProcessing" class="w-4 h-4 animate-spin" />
            <UploadCloudIcon v-else class="w-4 h-4" />
            <span>{{ isProcessing ? 'Processing & Ingesting Dataset...' : 'Upload & Merge Dataset' }}</span>
          </button>
        </div>

        <p class="text-[11px] text-slate-400">Supported formats: .xlsx, .xls, .csv (Customs & Trade Schema)</p>

      </div>

      <!-- SECTION 3: Uploaded Files & Ingestion History Table -->
      <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div class="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
              <HistoryIcon class="w-4 h-4 text-sky-600" />
              Uploaded Datasets History
            </h3>
            <p class="text-xs text-slate-500 mt-0.5">List of all dataset files uploaded and merged into the platform</p>
          </div>
          <span class="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg">
            {{ (adminStatus?.upload_history?.length || 0) }} Ingested Files
          </span>
        </div>

        <div class="overflow-x-auto mt-4">
          <table class="w-full text-left text-xs">
            <thead class="bg-slate-50 text-slate-600 font-bold uppercase border-b border-slate-200">
              <tr>
                <th class="p-3">File Name</th>
                <th class="p-3">Date Period</th>
                <th class="p-3 text-right">Rows Added</th>
                <th class="p-3 text-right">Rows Updated</th>
                <th class="p-3 text-right">Total Database Records</th>
                <th class="p-3 text-right">Upload Time</th>
                <th class="p-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr 
                v-if="!adminStatus?.upload_history || adminStatus.upload_history.length === 0"
              >
                <td colspan="7" class="p-6 text-center text-slate-400">
                  No dataset file uploads recorded yet. Upload an Excel file above to begin.
                </td>
              </tr>
              <tr 
                v-for="(hist, idx) in adminStatus?.upload_history" 
                :key="idx"
                class="hover:bg-slate-50/80 transition-colors"
              >
                <td class="p-3 font-semibold text-slate-900 flex items-center gap-2">
                  <FileSpreadsheetIcon class="w-4 h-4 text-sky-600 flex-shrink-0" />
                  <span>{{ hist.filename }}</span>
                </td>
                <td class="p-3 font-medium text-slate-700">
                  <span class="px-2 py-0.5 bg-sky-50 text-sky-800 rounded font-semibold text-[11px]">
                    {{ hist.period_range || adminStatus?.reporting_period || 'All Available' }}
                  </span>
                </td>
                <td class="p-3 text-right font-mono text-emerald-600 font-bold">
                  +{{ hist.rows_inserted }}
                </td>
                <td class="p-3 text-right font-mono text-slate-600">
                  {{ hist.rows_updated }}
                </td>
                <td class="p-3 text-right font-mono font-bold text-slate-900">
                  {{ hist.total_records.toLocaleString() }}
                </td>
                <td class="p-3 text-right text-slate-500 font-mono text-[11px]">
                  {{ hist.uploaded_at ? hist.uploaded_at.split('.')[0] : 'Just now' }}
                </td>
                <td class="p-3 text-center">
                  <span class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    Merged
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </main>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { 
  FileSpreadsheet as FileSpreadsheetIcon,
  UploadCloud as UploadCloudIcon,
  AlertTriangle as AlertTriangleIcon,
  CheckCircle2 as CheckCircle2Icon,
  ExternalLink as ExternalLinkIcon,
  Loader2 as Loader2Icon,
  Database as DatabaseIcon,
  Calendar as CalendarIcon,
  History as HistoryIcon,
  X as XIcon
} from 'lucide-vue-next';

interface ExchangeRateInfo {
  rate: number;
  is_realtime: boolean;
  currency: string;
  valid_date?: string | null;
  source: string;
  error_message?: string | null;
}

interface UploadHistoryItem {
  filename: string;
  rows_inserted: number;
  rows_updated: number;
  total_records: number;
  period_range?: string | null;
  uploaded_at: string;
}

interface AdminStatus {
  total_records: number;
  total_export_val_usd: number;
  total_weight_tonnes: number;
  reporting_period: string;
  hs4_chapters_count: number;
  last_updated: string;
  exchange_rate_info?: ExchangeRateInfo;
  upload_history: UploadHistoryItem[];
}

interface UploadResponse {
  success: boolean;
  message: string;
  rows_inserted: number;
  rows_updated: number;
  total_records: number;
  reporting_period: string;
  exchange_rate_info?: ExchangeRateInfo;
  upload_history: UploadHistoryItem[];
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

const adminStatus = ref<AdminStatus | null>(null);

const rateInfo = ref<ExchangeRateInfo>({
  rate: 4000,
  is_realtime: false,
  currency: 'USD',
  source: 'Default Fallback',
  error_message: null
});

const isFetchingRate = ref<boolean>(false);
const selectedFile = ref<File | null>(null);
const isProcessing = ref<boolean>(false);
const uploadResult = ref<UploadResponse | null>(null);
const errorMessage = ref<string | null>(null);

async function fetchAdminStatus() {
  isFetchingRate.value = true;
  try {
    const res = await axios.get<AdminStatus>(`${API_BASE_URL}/admin/status`);
    if (res.data) {
      adminStatus.value = res.data;
      if (res.data.exchange_rate_info) {
        rateInfo.value = res.data.exchange_rate_info;
      }
    }
  } catch (err: any) {
    console.warn('Could not fetch admin status:', err);
  } finally {
    isFetchingRate.value = false;
  }
}

function onFileSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    selectedFile.value = target.files[0];
    errorMessage.value = null;
    uploadResult.value = null;
  }
}

async function submitUpload() {
  if (!selectedFile.value || isProcessing.value) return;

  isProcessing.value = true;
  errorMessage.value = null;
  uploadResult.value = null;

  const formData = new FormData();
  formData.append('file', selectedFile.value);

  try {
    const res = await axios.post<UploadResponse>(`${API_BASE_URL}/admin/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    uploadResult.value = res.data;
    if (res.data.exchange_rate_info) {
      rateInfo.value = res.data.exchange_rate_info;
    }
    selectedFile.value = null;
    await fetchAdminStatus();
  } catch (err: any) {
    errorMessage.value = err.response?.data?.detail || err.message || 'Failed to upload and ingest dataset.';
  } finally {
    isProcessing.value = false;
  }
}

onMounted(() => {
  fetchAdminStatus();
});
</script>
