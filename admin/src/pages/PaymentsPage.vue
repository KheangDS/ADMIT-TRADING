<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { api } from '../api';
import { dateTime } from '../format';
import type { Payment } from '../types';
import { useTask } from '../composables/useTask';
import { usePolling } from '../composables/usePolling';
import TaskNotice from '../components/TaskNotice.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';
import { CheckCircle2 } from 'lucide-vue-next';

const payments = ref<Payment[]>([]);
const selected = ref<Payment | null>(null);
const confirm = ref(false);
const bankReference = ref('');
const { busy, error, notice, run } = useTask();

async function fetchPayments() {
  payments.value = (await api.get<Payment[]>('/admin/payments')).data;
}

async function load() {
  await run(fetchPayments);
}

// Top Section: Pending Payments (submitted or created), latest to oldest
const pendingPayments = computed(() => {
  return payments.value
    .filter((p) => p.status === 'submitted' || p.status === 'created')
    .sort((a, b) => {
      const timeA = new Date(a.confirmed_at || a.created_at || 0).getTime();
      const timeB = new Date(b.confirmed_at || b.created_at || 0).getTime();
      return timeB - timeA;
    });
});

// Below Section: Approved Payments, latest to oldest
const approvedPayments = computed(() => {
  return payments.value
    .filter((p) => p.status === 'approved')
    .sort((a, b) => {
      const timeA = new Date(a.approved_at || a.paid_at || a.created_at || 0).getTime();
      const timeB = new Date(b.approved_at || b.paid_at || b.created_at || 0).getTime();
      return timeB - timeA;
    });
});

function openApproval(payment: Payment) {
  selected.value = payment;
  const dateStr = new Date().toISOString().slice(2, 10).replace(/-/g, '');
  const randNum = Math.floor(100000 + Math.random() * 900000);
  const cleanPayer = (payment.payer_name || 'ABA').trim().replace(/[^a-zA-Z0-9]/g, '').slice(0, 8).toUpperCase();
  bankReference.value = `ABA-${cleanPayer || 'TXN'}-${dateStr}-${randNum}`;
  confirm.value = true;
}

async function submitApproval() {
  await run(async () => {
    if (!selected.value) throw new Error('Select a payment to approve.');
    const refVal = bankReference.value.trim();
    if (!refVal) throw new Error('Bank transaction reference is required.');
    const { data } = await api.post<Payment>(
      `/admin/payments/${encodeURIComponent(selected.value.id)}/approve`,
      {
        bank_reference: refVal,
        paid_at: new Date().toISOString(),
      },
    );
    if (data.status !== 'approved') {
      throw new Error('The backend did not confirm payment approval. Refresh before retrying.');
    }
    confirm.value = false;
    selected.value = null;
    bankReference.value = '';
    await fetchPayments();
    notice.value = 'Payment approved successfully. Membership access has been granted.';
  });
}

onMounted(load);
usePolling(async () => {
  if (!selected.value && !confirm.value) await load();
});
</script>

<template>
  <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 sm:pb-4 mb-5">
    <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">Payment Approvals</h1>
  </div>

  <TaskNotice :busy="busy" :error="error" :notice="notice" />

  <!-- ==================== TOP SECTION: PENDING PAYMENTS ==================== -->
  <section class="card">
    <div class="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
      <h2 class="text-lg font-bold text-slate-900 m-0">Pending Approvals</h2>
      <span class="badge">{{ pendingPayments.length }} pending</span>
    </div>

    <div class="table-scroll">
      <table class="min-w-[660px]">
        <thead>
          <tr>
            <th class="whitespace-nowrap">User Account</th>
            <th class="whitespace-nowrap">Payer Name</th>
            <th class="whitespace-nowrap">Plan / Amount</th>
            <th class="whitespace-nowrap">Status</th>
            <th class="whitespace-nowrap">User Confirmation</th>
            <th class="whitespace-nowrap">Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="payment in pendingPayments" :key="payment.id">
            <td>
              <strong>{{ payment.user_name }}</strong><br />
              <span class="muted">{{ payment.user_email }}</span>
            </td>
            <td class="mono whitespace-nowrap">{{ payment.payer_name || '—' }}</td>
            <td class="whitespace-nowrap">
              <strong>{{ payment.plan_name }}</strong><br />
              <span class="muted">{{ payment.amount }} {{ payment.currency }} · {{ payment.duration_count }} {{ payment.duration_unit }}(s)</span>
            </td>
            <td class="whitespace-nowrap">
              <span class="status-pill pending">{{ payment.status === 'submitted' ? 'Pending Review' : 'Incomplete' }}</span>
            </td>
            <td class="whitespace-nowrap">
              <span v-if="payment.confirmed_at">{{ dateTime(payment.confirmed_at) }}</span>
              <span v-else class="muted">Not confirmed yet</span>
            </td>
            <td class="whitespace-nowrap">
              <button
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 shadow-xs hover:shadow transition-all cursor-pointer disabled:opacity-50"
                :disabled="busy"
                @click="openApproval(payment)"
              >
                <CheckCircle2 class="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Approve</span>
              </button>
            </td>
          </tr>
          <tr v-if="!pendingPayments.length">
            <td colspan="6" class="text-center py-6 text-slate-500">
              No pending payments awaiting review.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- ==================== BELOW SECTION: APPROVED PAYMENTS ==================== -->
  <section class="card">
    <div class="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
      <h2 class="text-lg font-bold text-slate-900 m-0">Approved Payments</h2>
      <span class="badge">{{ approvedPayments.length }} approved</span>
    </div>

    <div class="table-scroll">
      <table class="min-w-[760px]">
        <thead>
          <tr>
            <th>User Account</th>
            <th>Payer Name</th>
            <th>Plan / Amount</th>
            <th>Access Status</th>
            <th>Approved Time</th>
            <th>Membership Expiry</th>
            <th>Receipt ID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="payment in approvedPayments" :key="payment.id">
            <td>
              <strong>{{ payment.user_name }}</strong><br />
              <span class="muted">{{ payment.user_email }}</span>
            </td>
            <td class="mono">{{ payment.payer_name || '—' }}</td>
            <td>
              <strong>{{ payment.plan_name }}</strong><br />
              <span class="muted">{{ payment.amount }} {{ payment.currency }} · {{ payment.duration_count }} {{ payment.duration_unit }}(s)</span>
            </td>
            <td>
              <span v-if="payment.is_access_granted" class="status-pill active">Active</span>
              <span v-else class="status-pill locked">Expired</span>
            </td>
            <td>{{ dateTime(payment.approved_at || payment.paid_at) }}</td>
            <td>{{ dateTime(payment.expires_at || payment.access_expires_at) }}</td>
            <td class="mono">{{ payment.receipt_id || '—' }}</td>
          </tr>
          <tr v-if="!approvedPayments.length">
            <td colspan="7" class="text-center py-6 text-slate-500">
              No approved payments recorded.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- ==================== CONFIRM APPROVAL MODAL ==================== -->
  <ConfirmDialog
    :open="confirm"
    :busy="busy"
    :error="error"
    confirm-class="success"
    confirm-text="Confirm"
    cancel-text="Cancel"
    title="Approve Payment & Grant Access"
    @cancel="confirm = false; selected = null; bankReference = ''"
    @confirm="submitApproval"
  >
    <div v-if="selected" class="space-y-3.5 my-3">
      <!-- Payment Details Summary Card -->
      <div class="bg-slate-50 border border-slate-200/90 rounded-2xl p-4 space-y-2.5 text-xs">
        <div class="flex items-center justify-between pb-2 border-b border-slate-200/80">
          <span class="text-slate-500 font-medium">User Account</span>
          <div class="text-right">
            <span class="font-bold text-slate-900">{{ selected.user_name }}</span>
            <span class="text-slate-500 block text-[11px]">{{ selected.user_email }}</span>
          </div>
        </div>
        <div class="flex items-center justify-between pb-2 border-b border-slate-200/80">
          <span class="text-slate-500 font-medium">Plan & Interval</span>
          <span class="font-bold text-slate-800">
            {{ selected.plan_name }} · {{ selected.duration_count }} {{ selected.duration_unit }}{{ selected.duration_count > 1 ? 's' : '' }}
          </span>
        </div>
        <div class="flex items-center justify-between pb-2 border-b border-slate-200/80">
          <span class="text-slate-500 font-medium">Payment Amount</span>
          <span class="font-black text-emerald-600 font-mono text-sm">
            {{ selected.amount }} {{ selected.currency }}
          </span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-slate-500 font-medium">Payer Account Name</span>
          <span class="font-mono font-bold text-sky-800 bg-sky-100/70 border border-sky-200 px-2.5 py-0.5 rounded-lg text-xs">
            {{ selected.payer_name || '—' }}
          </span>
        </div>
      </div>

      <!-- Bank Reference Input (Required) -->
      <div class="space-y-1.5 pt-1">
        <div class="flex items-center justify-between">
          <label for="bank-ref-input" class="block text-xs font-bold text-slate-700">
            Bank Transaction Reference <span class="text-red-500">*</span>
          </label>
          <span class="text-[10px] text-slate-400 font-mono">From ABA / Bakong App</span>
        </div>
        <input
          id="bank-ref-input"
          v-model="bankReference"
          type="text"
          placeholder="e.g. 09032585620 or ABA-TXN-12345"
          class="w-full text-xs font-mono font-bold uppercase px-3.5 py-2.5 rounded-xl border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500 transition-all text-slate-800 shadow-2xs"
          maxlength="200"
          required
        />
        <p class="text-[11px] text-slate-400 m-0">
          Enter the transaction reference from your banking app receipt, or keep the generated reference for audit records.
        </p>
      </div>

      <p class="text-xs text-slate-600 leading-relaxed m-0 text-justify">
        Confirming will immediately activate membership access for this user and generate an official downloadable PDF receipt.
      </p>
    </div>
  </ConfirmDialog>
</template>
