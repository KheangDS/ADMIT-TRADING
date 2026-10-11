<template>
  <section class="max-w-2xl mx-auto space-y-6 py-6">
    <!-- Header -->
    <div class="space-y-2 text-left">
      <router-link to="/plans" class="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-700 hover:text-sky-800 transition-colors">
        <ArrowLeftIcon class="w-3.5 h-3.5" />
        <span>Back to Plans</span>
      </router-link>
      <h1 class="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
        Membership Checkout
      </h1>
    </div>

    <!-- Loading / Error States -->
    <div v-if="loadingPlan" class="surface text-center py-10 space-y-3" role="status">
      <div class="w-7 h-7 border-3 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="text-xs text-slate-500 font-medium">Loading plan details…</p>
    </div>

    <div v-if="error" class="notice flex items-center justify-between" role="alert">
      <span>{{ error }}</span>
      <router-link to="/plans" class="font-bold underline ml-3">Choose another plan</router-link>
    </div>

    <!-- Rule: 1 Plan Submission Limit Alert -->
    <div 
      v-if="existingSubmittedPayment && !payment" 
      class="bg-sky-50 border border-sky-300 rounded-2xl p-6 text-sky-950 shadow-xs space-y-4"
    >
      <div class="flex items-start gap-3.5">
        <div class="p-2.5 bg-sky-100 text-sky-700 rounded-xl flex-shrink-0 mt-0.5">
          <ClockIcon class="w-5 h-5 text-sky-600" />
        </div>
        <div class="space-y-1">
          <h2 class="font-black text-sm sm:text-base text-sky-900">
            Payment Request Already Under Review
          </h2>
          <p class="text-xs sm:text-sm text-sky-800 leading-relaxed">
            You currently have a submitted payment for <strong class="font-bold">{{ existingSubmittedPayment.plan_name }}</strong> awaiting administrative validation. Only 1 plan submission is permitted at a time.
          </p>
        </div>
      </div>
      <div class="pt-2 flex flex-wrap gap-3">
        <router-link 
          to="/payments" 
          class="primary-button text-xs py-2.5 px-4 inline-flex items-center gap-1.5"
        >
          <span>Track Pending Payment</span>
          <ArrowRightIcon class="w-3.5 h-3.5" />
        </router-link>
        <router-link 
          to="/plans" 
          class="secondary-button text-xs py-2.5 px-4"
        >
          <span>View All Plans</span>
        </router-link>
      </div>
    </div>

    <!-- Step 1 Form: Plan Summary & Payer Name -->
    <form v-else-if="plan && !payment" @submit.prevent="create" class="surface space-y-6">
      <!-- Plan Summary Card -->
      <div class="bg-gradient-to-br from-slate-50 to-sky-50/50 rounded-2xl p-5 border border-sky-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span class="text-[11px] font-bold px-2 py-0.5 rounded-full bg-sky-100 text-sky-800">
            Selected Tier
          </span>
          <h2 class="text-lg font-bold text-slate-900 mt-1">{{ plan.name }}</h2>
          <p class="text-xs text-slate-600 mt-0.5">
            {{ plan.duration_count }} {{ plan.duration_unit }}{{ plan.duration_count === 1 ? '' : 's' }} term
          </p>
        </div>
        <div class="sm:text-right">
          <p class="text-2xl sm:text-3xl font-black text-sky-800 font-mono">
            {{ money(plan.amount, plan.currency) }}
          </p>
          <span class="text-xs font-bold text-slate-500 uppercase">{{ plan.currency }}</span>
        </div>
      </div>

      <!-- Payer Input Field -->
      <div class="space-y-2">
        <label class="field-label flex items-center justify-between" for="payer-name">
          <span>Payer Account-Holder Name</span>
          <span class="text-xs font-normal text-slate-400">Required for transfer match</span>
        </label>
        <input 
          id="payer-name" 
          class="form-input text-sm font-medium uppercase tracking-wide" 
          :value="payerName" 
          @input="uppercaseInput" 
          autocomplete="name" 
          required 
          maxlength="200" 
          placeholder="e.g. SOK DARA" 
        />
        <p class="text-xs text-slate-500 leading-relaxed">
          Must match the name on your paying bank account. Latin characters are automatically uppercased; Khmer text is preserved.
        </p>
      </div>

      <!-- Submit Button -->
      <div class="pt-2">
        <button 
          class="w-full primary-button py-3 text-sm font-bold shadow-md hover:shadow-lg transition-all" 
          :disabled="creating || !payerName.trim()"
        >
          <span v-if="creating" class="inline-flex items-center gap-2">
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Creating Request…
          </span>
          <span v-else class="inline-flex items-center gap-2">
            <QrCodeIcon class="w-4 h-4" />
            Generate {{ plan.currency }} Payment QR
          </span>
        </button>
      </div>

      <!-- Security / Process Footnote -->
      <div class="rounded-xl bg-slate-50 p-3.5 border border-slate-200/70 text-xs text-slate-600 space-y-1">
        <p class="font-semibold text-slate-700">Payment verification procedure:</p>
        <p>
          After generating the request, scan the QR code to make the transfer, then click <span class="font-bold text-slate-800">“I have paid”</span>. Our team reviews incoming transfers to unlock your member access.
        </p>
      </div>
    </form>

    <!-- Payment Generated View -->
    <PaymentCard v-if="payment" :payment="payment" :receipt="receipt" :now="now" @updated="member.putPayment" />

    <div class="text-center pt-2">
      <router-link class="text-xs font-bold text-sky-700 hover:text-sky-800 inline-flex items-center gap-1" to="/payments">
        <span>View all your payment requests & receipts</span>
        <ArrowRightIcon class="w-3.5 h-3.5" />
      </router-link>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { 
  ArrowLeft as ArrowLeftIcon,
  ArrowRight as ArrowRightIcon,
  QrCode as QrCodeIcon,
  Clock as ClockIcon
} from 'lucide-vue-next';
import type { Plan } from '../types/membership';
import { apiError, getPlans, createPayment } from '../services/api';
import { privateEpoch, onPrivateReset } from '../services/privateState';
import { money, uppercasePayerName } from '../utils/membership';
import PaymentCard from '../components/membership/PaymentCard.vue';
import { usePaymentPolling } from '../composables/usePaymentPolling';

const route = useRoute();
const { member, now } = usePaymentPolling();
const plan = ref<Plan | null>(null);
const payerName = ref('');
const paymentId = ref('');
const payment = computed(() => member.payments.find(p => p.id === paymentId.value));
const receipt = computed(() => member.receipts.find(r => r.payment_id === paymentId.value));
const existingSubmittedPayment = computed(() => {
  return member.payments.find(p => p.status === 'submitted');
});
const loadingPlan = ref(true);
const creating = ref(false);
const error = ref('');
let disposed = false;

const off = onPrivateReset(() => { 
  payerName.value = ''; 
  paymentId.value = ''; 
  error.value = ''; 
});

onUnmounted(() => { 
  disposed = true; 
  off(); 
});

onMounted(async () => {
  try { 
    const plans = await getPlans(); 
    if (disposed) return; 
    plan.value = plans.find(p => p.id === route.params.planId) || null; 
    if (!plan.value) error.value = 'This plan is no longer available. Choose an active plan from Plans & pricing.'; 
  }
  catch (err) { 
    if (!disposed) error.value = apiError(err); 
  }
  finally { 
    loadingPlan.value = false; 
  }
});

function uppercaseInput(event: Event) {
  const input = event.target as HTMLInputElement;
  const start = input.selectionStart;
  const end = input.selectionEnd;
  const original = input.value;
  payerName.value = uppercasePayerName(original);
  input.value = payerName.value;
  if (start !== null && end !== null) {
    input.setSelectionRange(
      uppercasePayerName(original.slice(0, start)).length, 
      uppercasePayerName(original.slice(0, end)).length
    );
  }
}

async function create() {
  if (!plan.value || creating.value || !payerName.value.trim()) return;
  const epoch = privateEpoch;
  creating.value = true; 
  error.value = '';
  try { 
    const created = await createPayment(plan.value.id, payerName.value.trim().replace(/\s+/g, ' ')); 
    if (epoch !== privateEpoch || disposed) return; 
    member.putPayment(created); 
    paymentId.value = created.id; 
  }
  catch (err) { 
    if (epoch === privateEpoch && !disposed) {
      error.value = apiError(err, 'Payment destination unavailable. Contact support to configure the QR for this currency before paying.'); 
    }
  }
  finally { 
    creating.value = false; 
  }
}
</script>
