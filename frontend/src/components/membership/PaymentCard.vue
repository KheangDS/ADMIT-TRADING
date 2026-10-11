<template>
  <article class="surface space-y-5 rounded-2xl border border-slate-200/90 shadow-sm p-6 sm:p-7">
    <!-- Header: Plan & Status Badge -->
    <div class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-100 pb-4">
      <div>
        <div class="flex items-center gap-2">
          <h2 class="text-xl font-bold text-slate-900">{{ payment.plan_name }}</h2>
          <span 
            class="px-2.5 py-0.5 rounded-full text-xs font-bold"
            :class="payment.currency === 'USD' ? 'bg-sky-50 text-sky-700 border border-sky-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
          >
            {{ payment.currency }}
          </span>
        </div>
        <p class="text-sm font-semibold text-slate-500 mt-1 font-mono">
          {{ money(payment.amount, payment.currency) }} · {{ payment.duration_count }} {{ payment.duration_unit }}{{ payment.duration_count === 1 ? '' : 's' }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <!-- 5-Minute Timer Badge when created -->
        <span 
          v-if="payment.status === 'created' && !isQrExpired"
          class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300 font-mono tracking-wide"
        >
          <ClockIcon class="w-3.5 h-3.5 text-amber-600" />
          <span>{{ formattedTimer }}</span>
        </span>

        <span 
          v-else-if="payment.status === 'created' && isQrExpired"
          class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200 font-mono tracking-wide"
        >
          <AlertCircleIcon class="w-3.5 h-3.5 text-red-600" />
          <span>Expired</span>
        </span>

        <span 
          class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider" 
          :class="{
            'bg-amber-100 text-amber-800 border border-amber-300': payment.status === 'created' && !isQrExpired,
            'bg-slate-100 text-slate-700 border border-slate-300': payment.status === 'created' && isQrExpired,
            'bg-sky-100 text-sky-800 border border-sky-200': payment.status === 'submitted',
            'bg-emerald-100 text-emerald-800 border border-emerald-200': payment.status === 'approved',
            'bg-red-100 text-red-800 border border-red-200': payment.status === 'rejected',
            'bg-slate-100 text-slate-700 border border-slate-200': payment.status === 'cancelled'
          }"
        >
          <span class="w-2 h-2 rounded-full" :class="{
            'bg-amber-500': payment.status === 'created' && !isQrExpired,
            'bg-slate-400': (payment.status === 'created' && isQrExpired) || payment.status === 'cancelled',
            'bg-sky-500 animate-pulse': payment.status === 'submitted',
            'bg-emerald-500': payment.status === 'approved',
            'bg-red-500': payment.status === 'rejected'
          }"></span>
          {{ payment.status === 'created' ? (isQrExpired ? 'QR Expired' : 'Awaiting payment') : payment.status }}
        </span>
      </div>
    </div>

    <!-- Metadata Grid -->
    <dl class="grid sm:grid-cols-2 gap-4 text-xs sm:text-sm bg-slate-50/70 rounded-xl p-4 border border-slate-100">
      <div>
        <dt class="text-slate-400 font-medium uppercase text-[11px] tracking-wider">Payer Account-Holder</dt>
        <dd class="font-bold text-slate-800 break-words mt-0.5 text-sm uppercase">{{ payment.payer_name }}</dd>
      </div>
      <div>
        <dt class="text-slate-400 font-medium uppercase text-[11px] tracking-wider">Request Created</dt>
        <dd class="font-semibold text-slate-700 mt-0.5 font-mono text-xs">{{ localDate(payment.created_at) }}</dd>
      </div>
    </dl>

    <!-- State 1: CREATED - Payment Instructions & QR code -->
    <template v-if="payment.status === 'created'">
      <div v-if="qrUrl || isQrExpired" class="flex flex-col sm:flex-row items-center sm:items-start gap-6 rounded-2xl bg-gradient-to-br from-slate-50 to-sky-50/30 p-5 border border-sky-100">
        <!-- QR Display -->
        <div class="flex-shrink-0 bg-white p-4 rounded-2xl shadow-sm border border-slate-200 text-center w-full sm:w-64 relative">
          <div class="flex items-center justify-between pb-2 mb-1 border-b border-slate-100">
            <span class="text-[11px] font-black tracking-wider text-red-600 uppercase">KHQR</span>
            <span class="text-[11px] font-bold text-slate-700 uppercase">Official Payment</span>
          </div>
          
          <div class="relative mx-auto my-2 w-48 h-48">
            <img 
              :src="qrUrl" 
              :alt="`${payment.currency} payment QR`" 
              @error="qrFailed = true" 
              v-if="qrUrl && !qrFailed && !isQrExpired" 
              class="w-48 h-48 object-contain rounded-xl"
            />
            <div 
              v-if="isQrExpired" 
              class="w-48 h-48 flex flex-col items-center justify-center p-3 text-center bg-slate-900/80 rounded-xl text-white backdrop-blur-[2px]"
            >
              <AlertCircleIcon class="w-6 h-6 text-amber-400 mb-1" />
              <p class="text-xs font-bold uppercase tracking-wider">QR Code Expired</p>
              <p class="text-[10px] text-slate-300 mt-0.5 font-mono">5-minute window ended</p>
            </div>
          </div>

          <span class="inline-block mt-1 text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono">
            {{ payment.currency }} {{ money(payment.amount, payment.currency) }}
          </span>
        </div>

        <!-- Instructions & Countdown -->
        <div class="space-y-3.5 text-xs sm:text-sm text-slate-600 flex-1">
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <h3 class="font-bold text-slate-900 text-base">Payment Instructions</h3>
              <span v-if="!isQrExpired" class="text-xs font-semibold text-amber-800 bg-amber-100/70 px-2 py-0.5 rounded-md font-mono">
                Valid for {{ formattedTimer }}
              </span>
            </div>
            <p>
              Transfer exactly <strong class="text-sky-800 font-mono text-base">{{ money(payment.amount, payment.currency) }}</strong> ({{ payment.currency }}) to the official destination shown.
            </p>
          </div>

          <ul class="space-y-1.5 text-xs text-slate-600 bg-white/80 p-3 rounded-xl border border-slate-200/60">
            <li class="flex items-center gap-1.5 font-medium text-slate-700">
              <CheckCircle2Icon class="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
              <span>Verify recipient details match the official merchant destination.</span>
            </li>
            <li class="flex items-center gap-1.5 font-medium text-slate-700">
              <CheckCircle2Icon class="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
              <span>Ensure payer account matches: <span class="font-bold uppercase text-slate-900">{{ payment.payer_name }}</span>.</span>
            </li>
          </ul>

          <div v-if="!isQrExpired && qrUrl" class="pt-1 flex flex-wrap items-center gap-3">
            <a 
              class="secondary-button text-xs font-bold inline-flex items-center gap-1.5" 
              :href="qrUrl" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              <ExternalLinkIcon class="w-3.5 h-3.5" />
              <span>Open Fullsize QR</span>
            </a>
          </div>

          <p v-if="qrFailed" class="notice text-xs">
            QR image could not load. Try opening the QR link; if unavailable, contact support before transferring.
          </p>
        </div>
      </div>

      <p v-else class="notice" role="alert">
        No valid {{ payment.currency }} payment QR is configured. Please contact support or choose another available currency.
      </p>

      <!-- Action Buttons: Active State vs Expired State -->
      <div v-if="!isQrExpired" class="space-y-2 pt-2">
        <button 
          class="w-full primary-button py-3 text-sm font-bold shadow-md hover:shadow-lg transition-all cursor-pointer" 
          :disabled="busy || !qrUrl" 
          @click="confirm"
        >
          <span v-if="busy" class="inline-flex items-center gap-2">
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Submitting Confirmation…
          </span>
          <span v-else class="inline-flex items-center gap-2">
            <CheckCircle2Icon class="w-4 h-4" />
            I Have Made This Transfer
          </span>
        </button>
        <p class="text-[11px] text-center text-slate-500">
          Click only after completing the mobile transfer. This submits your request for administrator verification.
        </p>
      </div>

      <!-- Expired State Options -->
      <div v-else class="bg-amber-50/90 border border-amber-200 rounded-2xl p-5 space-y-3 mt-3">
        <div class="space-y-1 text-xs sm:text-sm text-amber-950">
          <p class="font-bold text-sm">QR Code Expired (5-minute window completed)</p>
          <p class="text-xs text-amber-900 leading-relaxed">
            If you have not paid yet, please generate a fresh QR code. If you have already completed the transfer in your mobile banking app, click below to submit for review.
          </p>
        </div>
        <div class="flex flex-col sm:flex-row gap-2.5 pt-1">
          <button 
            class="primary-button text-xs font-bold py-2.5 px-4 flex-1 cursor-pointer" 
            :disabled="busy" 
            @click="confirm"
          >
            <span v-if="busy" class="inline-flex items-center gap-2">
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Submitting…
            </span>
            <span v-else class="inline-flex items-center gap-2">
              <CheckCircle2Icon class="w-4 h-4" />
              I Have Already Sent This Transfer
            </span>
          </button>
          <router-link 
            to="/plans" 
            class="secondary-button text-xs font-bold py-2.5 px-4 text-center inline-flex items-center justify-center gap-1.5"
          >
            <RefreshCwIcon class="w-3.5 h-3.5" />
            <span>Generate New QR</span>
          </router-link>
        </div>
      </div>
    </template>

    <!-- State 2: SUBMITTED - Manual Review in Progress -->
    <template v-else-if="payment.status === 'submitted'">
      <div class="bg-amber-50/80 border border-amber-200/80 rounded-2xl p-5 space-y-3">
        <div class="flex items-center gap-2 text-amber-900 font-bold text-sm sm:text-base">
          <ClockIcon class="w-5 h-5 text-amber-600 animate-spin" />
          <span>Awaiting Manual Verification</span>
        </div>
        <p class="text-xs sm:text-sm text-amber-900/90 leading-relaxed">
          You confirmed payment on <strong class="font-mono text-amber-950">{{ localDate(payment.confirmed_at) }}</strong>. An administrator is reviewing incoming bank transactions. Once confirmed, your membership will unlock immediately and an official receipt will be generated.
        </p>
      </div>

      <!-- Delayed Followup Option -->
      <div v-if="payment.delayed_reported_at" class="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs text-slate-600">
        <p class="font-semibold text-slate-800">Delayed approval inquiry submitted</p>
        <p class="mt-0.5">Reported on {{ localDate(payment.delayed_reported_at) }}. Support will prioritize your review.</p>
      </div>

      <div v-else-if="canReportDelay(payment, now) && !reportOpen" class="pt-2">
        <button class="secondary-button text-xs font-semibold" @click="reportOpen = true">
          Report Delayed Approval (Past 24h)
        </button>
      </div>

      <p v-else-if="!reportOpen" class="text-[11px] text-slate-400">
        If approval is still pending 24 hours after your confirmation, an inquiry button will appear here.
      </p>

      <!-- Followup Modal/Form -->
      <form v-if="reportOpen && !payment.delayed_reported_at" @submit.prevent="report" class="border-t border-slate-200 pt-4 space-y-3.5">
        <h3 class="font-bold text-slate-900 text-sm">Submit Delay Followup to Support</h3>
        <div class="grid sm:grid-cols-2 gap-3 text-xs">
          <div>
            <label class="field-label text-xs">Account Name</label>
            <input class="form-input text-xs" :value="auth.user?.name" readonly />
          </div>
          <div>
            <label class="field-label text-xs">Account Email</label>
            <input class="form-input text-xs" :value="auth.user?.email" readonly />
          </div>
        </div>
        <div>
          <label class="field-label text-xs">Additional Context (Optional)</label>
          <textarea 
            class="form-input text-xs" 
            v-model="message" 
            maxlength="2000" 
            rows="3" 
            placeholder="e.g. Transaction reference number or transfer time..."
          ></textarea>
        </div>
        <div class="flex gap-2">
          <button class="primary-button text-xs py-2 px-4" :disabled="busy">Send Inquiry</button>
          <button type="button" class="secondary-button text-xs py-2 px-4" @click="reportOpen = false">Cancel</button>
        </div>
      </form>
    </template>

    <!-- State 3: APPROVED - Access Active & Receipt Download -->
    <template v-else-if="payment.status === 'approved'">
      <div class="bg-emerald-50/80 border border-emerald-200 rounded-2xl p-5 space-y-4">
        <div class="flex items-center gap-2 text-emerald-900 font-bold text-sm sm:text-base">
          <CheckCircle2Icon class="w-5 h-5 text-emerald-600" />
          <span>Payment Verified & Membership Active</span>
        </div>
        <div class="grid sm:grid-cols-2 gap-3 text-xs text-emerald-900">
          <div>
            <span class="text-emerald-700 font-medium">Approved At:</span>
            <p class="font-mono font-bold mt-0.5">{{ localDate(payment.approved_at) }}</p>
          </div>
          <div>
            <span class="text-emerald-700 font-medium">Valid Until:</span>
            <p class="font-mono font-bold mt-0.5">{{ localDate(payment.expires_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Receipt Section -->
      <div v-if="receipt" class="bg-slate-50 rounded-xl p-4 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="text-xs space-y-1">
          <p class="font-bold text-slate-800">Official Receipt #{{ receipt.number }}</p>
          <p class="text-slate-500 font-mono">
            PDF: {{ receipt.pdf_status === 'pending' ? 'Queued for generation' : receipt.pdf_status }} · Email: {{ receipt.email_status === 'pending' ? 'Queued' : receipt.email_status }}
          </p>
        </div>

        <button 
          v-if="receipt.pdf_status === 'ready'" 
          class="secondary-button text-xs font-bold inline-flex items-center gap-1.5 shadow-2xs" 
          :disabled="files.busy.value" 
          @click="files.open(`/receipts/${receipt.id}/download`, `receipt-${receipt.number}.pdf`)"
        >
          <DownloadIcon class="w-3.5 h-3.5 text-slate-500" />
          <span>Download Receipt PDF</span>
        </button>
      </div>

      <div class="flex items-center justify-between pt-1">
        <router-link class="text-xs font-bold text-sky-700 hover:text-sky-800 inline-flex items-center gap-1" to="/dashboard">
          <span>Open Member Dashboard</span>
          <ArrowRightIcon class="w-3 h-3" />
        </router-link>
        <router-link class="text-xs font-semibold text-slate-500 hover:text-slate-700" to="/account">
          Account Profile →
        </router-link>
      </div>
    </template>

    <!-- State 4: REJECTED -->
    <div v-else-if="payment.status === 'rejected'" class="notice bg-red-50 border-red-200 text-red-900 space-y-1">
      <p class="font-bold">Payment Request Rejected</p>
      <p class="text-xs">{{ payment.rejection_reason || 'Transaction could not be verified. Contact support for assistance.' }}</p>
    </div>

    <!-- State 5: CANCELLED -->
    <div v-else class="text-slate-500 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
      This payment request has been cancelled. You can choose a new plan to create another request.
    </div>

    <p v-if="error || files.error.value" class="notice text-xs" role="alert">{{ error || files.error.value }}</p>

    <!-- Submission Feedback Dialog -->
    <dialog ref="pendingDialog" class="max-w-md w-[calc(100%-2rem)] rounded-3xl p-6 sm:p-7 shadow-2xl backdrop:bg-slate-900/60 border border-slate-100" aria-labelledby="pending-title">
      <div class="text-center space-y-4">
        <div class="w-12 h-12 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center mx-auto">
          <ClockIcon class="w-6 h-6" />
        </div>
        <h3 id="pending-title" class="text-xl font-bold text-slate-900">Submitted — Pending Approval</h3>
        <p class="text-xs sm:text-sm text-slate-600 leading-relaxed">
          Thank you. Your payment confirmation has been recorded. Our team will review the transfer. Once approved, your membership unlocks immediately.
        </p>
        <button class="w-full primary-button py-2.5 text-sm font-bold" @click="pendingDialog?.close()" autofocus>
          Understood
        </button>
      </div>
    </dialog>
  </article>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue';
import { 
  CheckCircle2 as CheckCircle2Icon,
  Clock as ClockIcon,
  Download as DownloadIcon,
  ExternalLink as ExternalLinkIcon,
  ArrowRight as ArrowRightIcon,
  AlertCircle as AlertCircleIcon,
  RefreshCw as RefreshCwIcon
} from 'lucide-vue-next';
import type { Payment, Receipt } from '../../types/membership';
import { apiError, confirmPayment, reportPaymentDelay } from '../../services/api';
import { onPrivateReset, privateEpoch } from '../../services/privateState';
import { money, localDate, canReportDelay } from '../../utils/membership';
import { useAuthStore } from '../../stores/authStore';
import { usePrivateFiles } from '../../composables/usePrivateFiles';

const props = defineProps<{ payment: Payment; receipt?: Receipt; now: number }>();
const emit = defineEmits<{ updated: [payment: Payment] }>();
const auth = useAuthStore();
const files = usePrivateFiles();
const busy = ref(false);
const error = ref('');
const reportOpen = ref(false);
const message = ref('');
const qrFailed = ref(false);
const pendingDialog = ref<HTMLDialogElement | null>(null);
let disposed = false;

const off = onPrivateReset(() => { 
  pendingDialog.value?.close(); 
  message.value = ''; 
  reportOpen.value = false; 
  error.value = ''; 
});

onUnmounted(() => { 
  disposed = true; 
  off(); 
});

const qrExpiryMs = computed(() => {
  if (props.payment.qr_expires_at) return Date.parse(props.payment.qr_expires_at);
  if (props.payment.created_at) return Date.parse(props.payment.created_at) + 5 * 60 * 1000;
  return 0;
});

const remainingSeconds = computed(() => {
  if (!qrExpiryMs.value) return 0;
  return Math.max(0, Math.floor((qrExpiryMs.value - props.now) / 1000));
});

const isQrExpired = computed(() => props.payment.status === 'created' && remainingSeconds.value <= 0);

const formattedTimer = computed(() => {
  const m = Math.floor(remainingSeconds.value / 60).toString().padStart(2, '0');
  const s = (remainingSeconds.value % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
});

const qrUrl = computed(() => {
  if (!props.payment.qr_url) return '';
  if (props.payment.qr_url.startsWith('data:image/')) return props.payment.qr_url;
  try { 
    const url = new URL(props.payment.qr_url, window.location.origin); 
    return ['http:', 'https:', 'data:'].includes(url.protocol) ? url.href : ''; 
  } catch { 
    return ''; 
  }
});

async function confirm() {
  if (busy.value) return;
  const epoch = privateEpoch;
  busy.value = true; 
  error.value = '';
  try { 
    const payment = await confirmPayment(props.payment.id); 
    if (epoch !== privateEpoch || disposed) return; 
    emit('updated', payment); 
    if (payment.status === 'submitted') pendingDialog.value?.showModal(); 
  }
  catch (err) { 
    if (epoch === privateEpoch && !disposed) error.value = apiError(err); 
  }
  finally { 
    busy.value = false; 
  }
}

async function report() {
  if (busy.value) return;
  const epoch = privateEpoch;
  busy.value = true; 
  error.value = '';
  try { 
    const payment = await reportPaymentDelay(props.payment.id, message.value.trim()); 
    if (epoch !== privateEpoch || disposed) return; 
    emit('updated', payment); 
    reportOpen.value = false; 
    message.value = ''; 
  }
  catch (err) { 
    if (epoch === privateEpoch && !disposed) error.value = apiError(err); 
  }
  finally { 
    busy.value = false; 
  }
}
</script>
