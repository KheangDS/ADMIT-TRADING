<template>
  <section class="space-y-6 max-w-4xl mx-auto py-6">
    <!-- Header -->
    <div class="space-y-1">
      <h1 class="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">Account Profile</h1>
    </div>

    <!-- Alert 1: Membership Expired (Data Access Locked / Paused) -->
    <div 
      v-if="isExpired" 
      class="bg-rose-50 border-2 border-rose-300/80 rounded-2xl p-5 text-rose-950 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
      role="alert"
    >
      <div class="flex items-start gap-3.5">
        <div class="p-2.5 bg-rose-100 text-rose-700 rounded-xl flex-shrink-0 mt-0.5">
          <AlertOctagonIcon class="w-5 h-5 text-rose-600" />
        </div>
        <div class="space-y-1">
          <h2 class="font-black text-sm sm:text-base text-rose-900 tracking-tight">
            Membership Expired — Data Access Paused
          </h2>
          <p class="text-xs sm:text-sm text-rose-800 leading-relaxed">
            Your subscription expired on <strong class="font-bold font-mono">{{ localDate(auth.membership?.expires_at) }}</strong>. You can no longer access real-time export datasets, comparative charts, AI assistant insights, or private trade documents. Please continue your subscription to restore immediate data access.
          </p>
        </div>
      </div>
      <router-link 
        to="/plans" 
        class="flex-shrink-0 w-full sm:w-auto px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs shadow-sm hover:shadow transition-all inline-flex items-center justify-center gap-1.5 cursor-pointer"
      >
        <LayersIcon class="w-4 h-4" />
        <span>Continue Subscription</span>
      </router-link>
    </div>

    <!-- Alert 2: Membership Expiring Soon (Within 7 Days) -->
    <div 
      v-else-if="isExpiringSoon" 
      class="bg-amber-50 border-2 border-amber-300 rounded-2xl p-5 text-amber-950 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
      role="alert"
    >
      <div class="flex items-start gap-3.5">
        <div class="p-2.5 bg-amber-100 text-amber-700 rounded-xl flex-shrink-0 mt-0.5">
          <AlertTriangleIcon class="w-5 h-5 text-amber-600" />
        </div>
        <div class="space-y-1">
          <h2 class="font-black text-sm sm:text-base text-amber-900 tracking-tight">
            Membership Expiring Soon — {{ daysRemaining }} Day{{ daysRemaining === 1 ? '' : 's' }} Remaining
          </h2>
          <p class="text-xs sm:text-sm text-amber-800 leading-relaxed">
            Your active subscription will expire on <strong class="font-bold font-mono">{{ localDate(auth.membership?.expires_at) }}</strong>. Renew your plan now to prevent any interruption in your analytical dashboard access and export reports.
          </p>
        </div>
      </div>
      <router-link 
        to="/plans" 
        class="flex-shrink-0 w-full sm:w-auto px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-extrabold text-xs shadow-sm hover:shadow transition-all inline-flex items-center justify-center gap-1.5 cursor-pointer"
      >
        <RefreshCwIcon class="w-4 h-4" />
        <span>Renew Membership</span>
      </router-link>
    </div>

    <!-- Alert 3: Pending Plan Submission Awaiting Review (1 Plan Limit) -->
    <div 
      v-if="hasPendingSubmission" 
      class="bg-sky-50 border border-sky-300/80 rounded-2xl p-4 sm:p-5 text-sky-950 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
      role="status"
    >
      <div class="flex items-start gap-3">
        <div class="p-2 bg-sky-100 text-sky-700 rounded-xl flex-shrink-0 mt-0.5">
          <ClockIcon class="w-4 h-4 text-sky-600" />
        </div>
        <div class="space-y-0.5">
          <h3 class="font-extrabold text-xs sm:text-sm text-sky-900">
            Payment Request Under Manual Review
          </h3>
          <p class="text-xs text-sky-800 leading-relaxed">
            You have 1 plan submission awaiting review. Access will be automatically activated upon payment validation.
          </p>
        </div>
      </div>
      <router-link 
        to="/payments" 
        class="flex-shrink-0 text-xs font-bold text-sky-700 hover:text-sky-900 bg-white px-3.5 py-2 rounded-xl border border-sky-200 shadow-2xs hover:shadow-xs transition-all inline-flex items-center gap-1"
      >
        <span>Track Request Status</span>
        <ArrowRightIcon class="w-3.5 h-3.5" />
      </router-link>
    </div>

    <!-- Required Membership Notice from Route Redirect -->
    <div v-if="$route.query.membership && !isExpired" class="notice bg-amber-50 border border-amber-200 rounded-2xl p-4 text-xs sm:text-sm text-amber-900 flex items-center gap-3">
      <AlertCircleIcon class="w-5 h-5 text-amber-600 flex-shrink-0" />
      <span>An active membership subscription is required to access analytics dashboards, dataset AI chat, and proprietary member documents.</span>
    </div>

    <!-- Profile & Access Status Card -->
    <article class="surface space-y-5 sm:space-y-6 rounded-2xl border border-slate-200/90 shadow-xs p-5 sm:p-8">
      <div class="flex items-start sm:items-center justify-between gap-4 border-b border-slate-100 pb-5 sm:pb-6">
        <div class="flex items-center gap-3.5 sm:gap-4 min-w-0">
          <div class="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white flex items-center justify-center font-black text-lg sm:text-xl shadow-md shrink-0">
            {{ (auth.user?.name || auth.user?.email || 'U').charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0">
            <h2 class="text-lg sm:text-xl font-bold text-slate-900 truncate">{{ auth.user?.name || 'User' }}</h2>
            <p class="text-xs sm:text-sm text-slate-500 font-mono truncate mt-0.5">{{ auth.user?.email }}</p>
            <div class="mt-2 sm:hidden">
              <span 
                class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold"
                :class="[
                  auth.user?.role === 'admin' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
                  isExpired ? 'bg-rose-100 text-rose-800 border border-rose-300 font-extrabold' :
                  isExpiringSoon ? 'bg-amber-100 text-amber-800 border border-amber-300 font-extrabold' :
                  auth.membership?.active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                  'bg-slate-100 text-slate-600 border border-slate-200'
                ]"
              >
                <span 
                  class="w-1.5 h-1.5 rounded-full" 
                  :class="[
                    auth.user?.role === 'admin' ? 'bg-indigo-500' :
                    isExpired ? 'bg-rose-500' :
                    isExpiringSoon ? 'bg-amber-500 animate-pulse' :
                    auth.membership?.active ? 'bg-emerald-500' :
                    'bg-slate-400'
                  ]"
                ></span>
                {{ 
                  auth.user?.role === 'admin' ? 'Administrator' : 
                  isExpired ? 'Subscription Expired' : 
                  isExpiringSoon ? `Expiring Soon (${daysRemaining}d)` : 
                  auth.membership?.active ? 'Active Member' : 
                  'Free Account' 
                }}
              </span>
            </div>
          </div>
        </div>

        <div class="hidden sm:block shrink-0">
          <!-- Desktop Access Status Pill Badge -->
          <span 
            class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold"
            :class="[
              auth.user?.role === 'admin' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' :
              isExpired ? 'bg-rose-100 text-rose-800 border border-rose-300 font-extrabold' :
              isExpiringSoon ? 'bg-amber-100 text-amber-800 border border-amber-300 font-extrabold' :
              auth.membership?.active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
              'bg-slate-100 text-slate-600 border border-slate-200'
            ]"
          >
            <span 
              class="w-2 h-2 rounded-full" 
              :class="[
                auth.user?.role === 'admin' ? 'bg-indigo-500' :
                isExpired ? 'bg-rose-500' :
                isExpiringSoon ? 'bg-amber-500 animate-pulse' :
                auth.membership?.active ? 'bg-emerald-500' :
                'bg-slate-400'
              ]"
            ></span>
            {{ 
              auth.user?.role === 'admin' ? 'Administrator' : 
              isExpired ? 'Subscription Expired' : 
              isExpiringSoon ? `Expiring Soon (${daysRemaining}d left)` : 
              auth.membership?.active ? 'Active Member' : 
              'Free Account' 
            }}
          </span>
        </div>
      </div>

      <!-- Access Details Box -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 rounded-2xl bg-slate-50/90 p-4 sm:p-5 border border-slate-200/80">
        <div class="flex items-center justify-between sm:block border-b border-slate-200/60 pb-2.5 sm:border-0 sm:pb-0">
          <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Access Status</span>
          <p 
            class="font-bold text-xs sm:text-sm sm:mt-1 flex items-center gap-1.5" 
            :class="[
              auth.user?.role === 'admin' ? 'text-indigo-700' :
              isExpired ? 'text-rose-700 font-extrabold' :
              isExpiringSoon ? 'text-amber-800 font-extrabold' :
              auth.membership?.active ? 'text-emerald-700' :
              'text-slate-600'
            ]"
          >
            <span 
              class="w-2 h-2 rounded-full" 
              :class="[
                auth.user?.role === 'admin' ? 'bg-indigo-500' :
                isExpired ? 'bg-rose-500' :
                isExpiringSoon ? 'bg-amber-500' :
                auth.membership?.active ? 'bg-emerald-500' :
                'bg-slate-400'
              ]"
            ></span>
            {{ 
              auth.user?.role === 'admin' ? 'Administrator Access' : 
              isExpired ? 'Access Paused (Expired)' : 
              isExpiringSoon ? 'Active (Expiring Soon)' : 
              auth.membership?.active ? 'Membership Active' : 
              'Membership Inactive' 
            }}
          </p>
        </div>
        <div class="flex items-center justify-between sm:block pt-1 sm:pt-0">
          <span class="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            {{ isExpired ? 'Expired On' : 'Expiration Date' }}
          </span>
          <p class="text-xs sm:text-sm font-semibold text-slate-700 sm:mt-1">
            {{ localDate(auth.membership?.expires_at) }}
          </p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="grid grid-cols-1 sm:flex sm:flex-wrap items-center gap-2.5 sm:gap-3 pt-1">
        <router-link 
          v-if="auth.canAccessMembers" 
          class="primary-button text-xs py-2.5 px-5 justify-center sm:justify-start shadow-xs hover:shadow-md transition-all" 
          to="/dashboard"
        >
          <LayoutDashboardIcon class="w-4 h-4 mr-1.5" />
          <span>Open Dashboard</span>
        </router-link>
        <router-link 
          class="text-xs py-2.5 px-4 rounded-xl font-bold transition-all inline-flex items-center justify-center sm:justify-start" 
          :class="isExpired ? 'bg-rose-600 hover:bg-rose-700 text-white shadow-xs' : 'secondary-button shadow-2xs hover:shadow'" 
          to="/plans"
        >
          <LayersIcon class="w-4 h-4 mr-1.5" :class="isExpired ? 'text-white' : 'text-slate-500'" />
          <span>{{ isExpired ? 'Continue Subscription' : auth.membership?.active ? 'Renew Membership' : 'View Plans' }}</span>
        </router-link>
      </div>
    </article>

    <!-- Payments & Receipts Card -->
    <article class="surface space-y-4 rounded-2xl border border-slate-200/90 shadow-xs p-5 sm:p-8">
      <div class="flex items-center justify-between gap-2">
        <h2 class="font-bold text-sm sm:text-base text-slate-900">Payments & Billing History</h2>
        <router-link class="text-xs font-bold text-sky-700 hover:text-sky-800 shrink-0 inline-flex items-center gap-1" to="/payments">
          <span>View All</span>
          <ArrowRightIcon class="w-3.5 h-3.5" />
        </router-link>
      </div>

      <p v-if="loading" class="text-xs text-slate-500" role="status">Loading payment status…</p>
      <div v-else class="rounded-xl bg-slate-50/80 p-3.5 border border-slate-200/70 text-xs text-slate-700">
        {{ member.payments.filter(p => p.status === 'submitted').length }} payment request(s) currently awaiting manual review.
      </div>

      <p v-if="error" class="notice text-xs" role="alert">{{ error }}</p>

      <div class="pt-1">
        <router-link class="inline-flex items-center gap-2 text-xs font-bold text-sky-700 hover:text-sky-900 hover:underline" to="/payments">
          <CreditCardIcon class="w-4 h-4 text-sky-600" />
          <span>Check delayed-approval inquiries & download receipts</span>
        </router-link>
      </div>
      
      <p class="text-[11px] text-slate-400 leading-relaxed border-t border-slate-100 pt-3">
        Payment checks auto-refresh periodically while active. Receipt email delivery issues do not revoke approved memberships.
      </p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { 
  AlertCircle as AlertCircleIcon,
  AlertTriangle as AlertTriangleIcon,
  AlertOctagon as AlertOctagonIcon,
  Clock as ClockIcon,
  ArrowRight as ArrowRightIcon,
  LayoutDashboard as LayoutDashboardIcon,
  Layers as LayersIcon,
  RefreshCw as RefreshCwIcon,
  CreditCard as CreditCardIcon
} from 'lucide-vue-next';
import { useAuthStore } from '../stores/authStore';
import { usePaymentPolling } from '../composables/usePaymentPolling';
import { localDate } from '../utils/membership';

const auth = useAuthStore();
const { member, loading, error } = usePaymentPolling();

// Calculate days remaining before expiration
const daysRemaining = computed<number | null>(() => {
  if (!auth.membership?.expires_at) return null;
  const expiryTime = new Date(auth.membership.expires_at).getTime();
  const diff = expiryTime - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
});

// Rule: Alert when nearing expiration (within 7 days)
const isExpiringSoon = computed(() => {
  if (auth.user?.role === 'admin') return false;
  return Boolean(
    auth.membership?.active && 
    daysRemaining.value !== null && 
    daysRemaining.value <= 7
  );
});

// Rule: Alert when user's subscription has expired and data access is locked
const isExpired = computed(() => {
  if (auth.user?.role === 'admin') return false;
  return Boolean(
    !auth.membership?.active && 
    auth.membership?.expires_at
  );
});

// Rule: Check if user has a pending submitted plan payment
const hasPendingSubmission = computed(() => {
  return member.payments.some(p => p.status === 'submitted');
});
</script>
