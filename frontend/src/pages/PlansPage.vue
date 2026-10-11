<template>
  <section class="space-y-8 sm:space-y-12 py-4 sm:py-6 max-w-6xl mx-auto px-4 sm:px-6">
    <!-- Header -->
    <div class="text-center max-w-2xl mx-auto space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-200/80 text-xs font-bold">
        <SparklesIcon class="w-3.5 h-3.5 text-sky-600" />
        <span>Flexible Subscription Tiers</span>
      </div>
      <h1 class="text-2xl sm:text-4xl lg:text-5xl font-black text-slate-900 tracking-tight">
        Membership Plans & Pricing
      </h1>
    </div>

    <!-- Status Messages -->
    <!-- Active Pending Submission Banner (1 Plan Limit) -->
    <div v-if="existingSubmittedPayment" class="bg-sky-50 border border-sky-300/90 rounded-2xl p-4 sm:p-5 text-sky-950 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="flex items-start gap-3">
        <div class="p-2 bg-sky-100 text-sky-700 rounded-xl flex-shrink-0 mt-0.5">
          <ClockIcon class="w-4 h-4 text-sky-600" />
        </div>
        <div>
          <h2 class="font-extrabold text-xs sm:text-sm text-sky-900">
            Plan Request Currently Under Review
          </h2>
          <p class="text-xs text-sky-800 leading-relaxed mt-0.5">
            You currently have a submitted payment for <strong>{{ existingSubmittedPayment.plan_name }}</strong> awaiting review. Only 1 plan submission is allowed at a time.
          </p>
        </div>
      </div>
      <router-link to="/payments" class="flex-shrink-0 px-4 py-2 rounded-xl bg-sky-700 hover:bg-sky-800 text-white font-bold text-xs transition-all flex items-center gap-1.5">
        <span>Track Status</span>
        <ArrowRightIcon class="w-3.5 h-3.5" />
      </router-link>
    </div>

    <div v-if="loading" class="surface text-center py-12 space-y-3" role="status">
      <div class="w-8 h-8 border-3 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="text-sm font-semibold text-slate-600">Loading available plans…</p>
    </div>

    <div v-else-if="error" class="notice flex items-center justify-between" role="alert">
      <span>{{ error }}</span>
      <button class="font-bold underline cursor-pointer ml-4" @click="load">Retry</button>
    </div>

    <div v-else-if="!plans.length" class="surface text-center py-12 text-slate-600">
      <AlertCircleIcon class="w-10 h-10 text-slate-400 mx-auto mb-2" />
      <p class="font-semibold">No active membership plans are available right now.</p>
      <p class="text-xs text-slate-500 mt-1">Please check back soon or contact administrator support.</p>
    </div>

    <template v-else>
      <!-- Plan Cards: Horizontal Snap Carousel on Mobile, Responsive Grid on Desktop -->
      <div
        class="flex sm:grid overflow-x-auto sm:overflow-x-visible pb-4 sm:pb-0 pt-1 -mx-4 px-4 sm:mx-0 sm:px-0 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 items-stretch snap-x snap-mandatory scroll-smooth no-scrollbar"
      >
        <article 
          v-for="plan in plans" 
          :key="plan.id" 
          class="w-[78vw] sm:w-auto max-w-[290px] sm:max-w-none shrink-0 snap-center bg-white rounded-2xl border border-slate-200/90 hover:border-sky-300 p-5 sm:p-7 shadow-xs hover:shadow-xl hover:-translate-y-1 transition-all duration-200 flex flex-col justify-between group"
        >
          <div class="flex-1 flex flex-col">
            <!-- Card Header: Plan Name + Duration Pill -->
            <div class="flex items-start justify-between gap-2.5">
              <h2 class="text-lg sm:text-xl font-bold text-slate-900 group-hover:text-sky-700 transition-colors leading-snug">
                {{ plan.name }}
              </h2>
              <span class="inline-flex items-center px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[11px] sm:text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200/70 font-mono whitespace-nowrap shrink-0">
                {{ plan.duration_count }} {{ plan.duration_unit }}{{ plan.duration_count === 1 ? '' : 's' }}
              </span>
            </div>

            <!-- Price Display -->
            <div class="mt-3.5 sm:mt-4 flex items-baseline gap-1.5">
              <span class="text-3xl sm:text-4xl font-black text-slate-900 font-mono tracking-tight">
                {{ money(plan.amount, plan.currency) }}
              </span>
              <span class="text-xs sm:text-sm font-medium text-slate-500">
                / {{ plan.duration_count > 1 ? `${plan.duration_count} ` : '' }}{{ plan.duration_unit }}
              </span>
            </div>

            <!-- Included Features List -->
            <div class="mt-5 sm:mt-6 pt-4 sm:pt-5 border-t border-slate-100 flex-1 flex flex-col">
              <p class="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2.5 sm:mb-3.5">
                Included Features
              </p>
              <ul class="space-y-2.5 sm:space-y-3 text-xs sm:text-[13px] text-slate-600 flex-1">
                <li 
                  v-for="(feature, idx) in parseFeatures(plan.description)" 
                  :key="idx" 
                  class="flex items-start gap-2 sm:gap-2.5"
                >
                  <div class="w-4 h-4 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 mt-0.5 border border-emerald-200/60">
                    <CheckIcon class="w-2.5 h-2.5 stroke-[3]" />
                  </div>
                  <span class="leading-relaxed">{{ feature }}</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- Action Button -->
          <div class="mt-6 sm:mt-8 pt-3.5 sm:pt-4 border-t border-slate-100">
            <router-link 
              v-if="existingSubmittedPayment"
              to="/payments"
              class="w-full secondary-button py-2.5 sm:py-3 text-center text-xs font-bold shadow-2xs hover:shadow text-sky-800 border-sky-200 bg-sky-50/50 justify-center"
            >
              <span>Request Under Review →</span>
            </router-link>
            <router-link 
              v-else
              class="w-full primary-button py-2.5 sm:py-3 text-center text-xs sm:text-sm font-bold shadow-xs hover:shadow-md justify-center flex items-center gap-2"
              :to="auth.user ? `/checkout/${plan.id}` : { path: '/login', query: { return_to: `/checkout/${plan.id}` } }"
            >
              <span>{{ !auth.user ? 'Sign In to Select Plan' : (auth.membership?.active ? 'Renew with this Plan' : 'Choose Plan & Pay') }}</span>
              <ArrowRightIcon class="w-3.5 h-3.5 sm:w-4 sm:h-4 opacity-80 group-hover:translate-x-0.5 transition-transform" />
            </router-link>
          </div>
        </article>
      </div>
    </template>

    <!-- How Membership Works Explainer -->
    <div class="surface space-y-4 bg-slate-50/80 border border-slate-200/90 rounded-2xl p-6 sm:p-8">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-sky-100 text-sky-800 flex items-center justify-center">
          <CreditCardIcon class="w-4 h-4" />
        </div>
        <h2 class="font-bold text-slate-900 text-base sm:text-lg">How Payment & Activation Works</h2>
      </div>

      <div class="grid sm:grid-cols-2 gap-4 text-xs sm:text-sm text-slate-600 leading-relaxed pt-2">
        <div class="space-y-1.5">
          <h3 class="font-bold text-slate-800">1. Transfer via Official QR</h3>
          <p>
            When you select a plan, an official KHQR code will be displayed with the exact frozen amount. Transfer the funds using your mobile banking app (e.g. ABA Bank) matching the payer account-holder name.
          </p>
        </div>
        <div class="space-y-1.5">
          <h3 class="font-bold text-slate-800">2. Confirmation & Review</h3>
          <p>
            Click <span class="font-semibold text-slate-800">“I have paid”</span> after transferring. An administrator reviews incoming payments and validates access. You will immediately receive access upon approval alongside an official downloadable PDF receipt.
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { 
  Sparkles as SparklesIcon,
  Check as CheckIcon,
  AlertCircle as AlertCircleIcon,
  CreditCard as CreditCardIcon,
  Clock as ClockIcon,
  ArrowRight as ArrowRightIcon
} from 'lucide-vue-next';
import { getPlans, apiError } from '../services/api';
import type { Plan } from '../types/membership';
import { money } from '../utils/membership';
import { useAuthStore } from '../stores/authStore';
import { usePaymentPolling } from '../composables/usePaymentPolling';

const auth = useAuthStore();
const { member } = usePaymentPolling();
const plans = ref<Plan[]>([]);
const loading = ref(true);
const error = ref('');

const existingSubmittedPayment = computed(() => {
  return member.payments.find(p => p.status === 'submitted');
});

function parseFeatures(desc: string | null | undefined): string[] {
  if (!desc || !desc.trim()) {
    return [
      'Full access to Overview & Compare charts',
      'Dataset-grounded AI assistant query tool',
      'Download proprietary PDF strategy decks',
      'Official downloadable payment receipt',
    ];
  }
  const lines = desc
    .split('\n')
    .map(line => line.replace(/^[-*•\d.)\s]+/, '').trim())
    .filter(Boolean);

  return lines.length > 0 ? lines : [
    'Full access to Overview & Compare charts',
    'Dataset-grounded AI assistant query tool',
    'Download proprietary PDF strategy decks',
    'Official downloadable payment receipt',
  ];
}

async function load() { 
  loading.value = true; 
  error.value = ''; 
  try { 
    plans.value = await getPlans(); 
  } catch (err) { 
    error.value = apiError(err); 
  } finally { 
    loading.value = false; 
  } 
}

onMounted(load);
</script>
