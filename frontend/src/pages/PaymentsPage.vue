<template>
  <section class="space-y-6 max-w-4xl mx-auto py-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">Payment Requests & Receipts</h1>
      </div>
    </div>

    <!-- Status Messages -->
    <div v-if="loading" class="surface text-center py-10 space-y-3" role="status">
      <div class="w-7 h-7 border-3 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
      <p class="text-xs text-slate-500 font-medium">Loading your payment records…</p>
    </div>

    <div v-if="error" class="notice flex items-center justify-between" role="alert">
      <span>{{ error }}</span>
      <button class="underline font-bold" @click="refresh">Retry</button>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && !member.payments.length" class="surface text-center py-12 space-y-4">
      <CreditCardIcon class="w-12 h-12 text-slate-300 mx-auto" />
      <div>
        <p class="font-bold text-slate-700">No payment requests created yet.</p>
        <p class="text-xs text-slate-500 mt-1">Select an active membership plan to get started.</p>
      </div>
      <router-link class="primary-button text-xs font-bold" to="/plans">
        Explore Membership Plans
      </router-link>
    </div>

    <!-- Payment List -->
    <div v-else class="space-y-5">
      <PaymentCard 
        v-for="payment in member.payments" 
        :key="payment.id" 
        :payment="payment" 
        :receipt="member.receipts.find(r => r.payment_id === payment.id)" 
        :now="now" 
        @updated="member.putPayment" 
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { 
  CreditCard as CreditCardIcon 
} from 'lucide-vue-next';
import PaymentCard from '../components/membership/PaymentCard.vue';
import { usePaymentPolling } from '../composables/usePaymentPolling';

const { member, loading, error, now, refresh } = usePaymentPolling();
</script>
