<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { api } from '../api';
import type { Plan } from '../types';
import { useTask } from '../composables/useTask';
import TaskNotice from '../components/TaskNotice.vue';
import { Check, Plus } from 'lucide-vue-next';

const plans = ref<Plan[]>([]);
const editing = ref<string | null>(null);
const showForm = ref(false);
const defaults = () => ({
  name: '',
  description: '',
  amount: '',
  currency: 'USD' as Plan['currency'],
  duration_unit: 'month' as Plan['duration_unit'],
  duration_count: 1,
  display_order: 0,
  active: true,
});
const form = reactive(defaults());
const { busy, error, notice, run } = useTask();

async function fetchPlans() {
  plans.value = (await api.get<Plan[]>('/admin/plans')).data;
}

async function load() {
  await run(fetchPlans);
}

function edit(plan?: Plan) {
  editing.value = plan?.id || null;
  Object.assign(form, plan || defaults());
  showForm.value = true;
}

async function save() {
  await run(async () => {
    if (!form.name.trim()) throw new Error('Plan name is required.');
    const pattern = form.currency === 'USD' ? /^\d+(\.\d{1,2})?$/ : /^\d+$/;
    if (!pattern.test(form.amount) || Number(form.amount) <= 0)
      throw new Error('Enter a positive amount: USD up to two decimal places; KHR integer only.');
    if (!Number.isInteger(form.duration_count) || form.duration_count < 1)
      throw new Error('Calendar duration count must be a positive integer.');
    const body = {
      name: form.name.trim(),
      description: form.description,
      amount: form.amount,
      currency: form.currency,
      duration_unit: form.duration_unit,
      duration_count: form.duration_count,
      display_order: Number(form.display_order) || 0,
      active: form.active,
    };
    if (editing.value) await api.patch(`/admin/plans/${encodeURIComponent(editing.value)}`, body);
    else await api.post('/admin/plans', body);
    showForm.value = false;
    await fetchPlans();
    notice.value = 'Plan saved. Existing payment requests retain their frozen price and duration.';
  });
}

function parseFeatures(desc: string | null | undefined): string[] {
  if (!desc || !desc.trim()) return [];
  return desc
    .split('\n')
    .map(line => line.replace(/^[-*•\d.)\s]+/, '').trim())
    .filter(Boolean);
}

onMounted(load);
</script>

<template>
  <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 sm:pb-4 mb-5">
    <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">Membership Plans</h1>
    <button class="primary-button text-xs font-bold py-1.5 px-3 sm:px-4 sm:py-2 rounded-xl inline-flex items-center gap-1.5 justify-center flex-shrink-0 cursor-pointer" @click="edit()">
      <Plus class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
      <span>Create plan</span>
    </button>
  </div>

  <TaskNotice :busy="busy" :error="error" :notice="notice" />

  <form v-if="showForm" class="card" @submit.prevent="save">
    <h2>{{ editing ? 'Edit plan' : 'New plan' }}</h2>
    <fieldset :disabled="busy">
      <div class="grid two">
        <label>Plan name<input v-model="form.name" required /></label>
        <label>Currency<select v-model="form.currency">
            <option value="USD">USD</option>
            <option value="KHR">KHR</option>
          </select></label>
        <label>Amount ({{ form.currency }})<input
            v-model="form.amount"
            required
            inputmode="decimal"
            :pattern="form.currency === 'USD' ? '[0-9]+(\\.[0-9]{1,2})?' : '[0-9]+'"
          /><small>Positive; USD maximum 2 decimals, KHR whole riel.</small></label>
        <label>Duration count<input
            v-model.number="form.duration_count"
            type="number"
            min="1"
            step="1"
            required /></label>
        <label>Calendar duration unit<select v-model="form.duration_unit">
            <option value="month">Month</option>
            <option value="year">Year</option>
          </select></label>
        <label>Display order<input
            v-model.number="form.display_order"
            type="number"
            min="0"
            step="1"
            placeholder="0"
          /><small>Lower numbers display first (e.g. 1, 2, 3).</small></label>
        <label class="check">
          <input v-model="form.active" type="checkbox" />Active / offered to users
        </label>
      </div>
      <label>
        <span class="font-bold">Plan Features & Benefits (1 per line for bullet points)</span>
        <textarea 
          v-model="form.description" 
          rows="4"
          placeholder="Full access to Overview & Compare charts&#10;Dataset-grounded AI assistant query tool&#10;Download proprietary PDF strategy decks&#10;Official downloadable payment receipt"
        ></textarea>
        <small>Each line entered here will appear as a checkmark bullet point on the member pricing page.</small>
      </label>
      <div class="actions flex flex-col sm:flex-row sm:items-center gap-2 pt-2">
        <button type="submit" class="w-full sm:w-auto">Save plan</button>
        <button class="secondary w-full sm:w-auto" type="button" @click="showForm = false">Cancel</button>
      </div>
    </fieldset>
  </form>

  <section class="card">
    <div class="table-scroll">
      <table class="min-w-[620px]">
        <caption>
          All plans
        </caption>
        <thead>
          <tr>
            <th class="w-16 text-center">Order</th>
            <th>Name / Features</th>
            <th>Amount</th>
            <th>Calendar duration</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="plan in plans" :key="plan.id">
            <td class="text-center font-mono">
              <span class="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-slate-100 font-bold text-slate-700 text-xs">
                {{ plan.display_order ?? 0 }}
              </span>
            </td>
            <td>
              <strong class="text-sm text-slate-900 block">{{ plan.name }}</strong>
              <ul v-if="parseFeatures(plan.description).length" class="mt-1 space-y-0.5 text-xs text-slate-600">
                <li v-for="(feat, idx) in parseFeatures(plan.description)" :key="idx" class="flex items-center gap-1.5">
                  <Check class="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  <span>{{ feat }}</span>
                </li>
              </ul>
              <span v-else class="text-xs text-slate-400 italic mt-0.5 block">Standard default benefits</span>
            </td>
            <td class="font-mono font-semibold">{{ plan.amount }} {{ plan.currency }}</td>
            <td>{{ plan.duration_count }} {{ plan.duration_unit }}(s)</td>
            <td>
              <span class="px-2 py-0.5 rounded-md text-xs font-bold" :class="plan.active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'">
                {{ plan.active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td><button class="secondary" @click="edit(plan)">Edit</button></td>
          </tr>
          <tr v-if="!plans.length">
            <td colspan="6">No plans returned. Create a reviewed plan when ready.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
