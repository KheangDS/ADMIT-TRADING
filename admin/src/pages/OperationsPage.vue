<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import {
  RefreshCw,
  Search,
  X,
} from 'lucide-vue-next';
import { api } from '../api';
import { dateTime } from '../format';
import type { AuditEvent } from '../types';
import { useTask } from '../composables/useTask';
import TaskNotice from '../components/TaskNotice.vue';

const events = ref<AuditEvent[]>([]);
const auditCategory = ref<'all' | 'accounts' | 'payments' | 'trade' | 'documents'>('all');
const searchQuery = ref('');

const { busy, error, notice, run } = useTask();

async function fetchAudit() {
  events.value = (await api.get<AuditEvent[]>('/admin/audit')).data;
}

async function load() {
  await run(fetchAudit);
}

// Category Count Badges
const categoryCounts = computed(() => {
  const counts = {
    all: events.value.length,
    accounts: 0,
    payments: 0,
    trade: 0,
    documents: 0,
  };
  for (const e of events.value) {
    if (e.action.startsWith('account.') || e.action.startsWith('auth.')) counts.accounts++;
    if (e.action.startsWith('payment.') || e.action.startsWith('membership.') || e.action.startsWith('plan.')) counts.payments++;
    if (e.action.startsWith('trade.')) counts.trade++;
    if (e.action.startsWith('document.')) counts.documents++;
  }
  return counts;
});

// Friendly Action Label
function formatAction(action: string): string {
  const map: Record<string, string> = {
    'payment.approve': 'Payment Approved',
    'payment.reject': 'Payment Rejected',
    'payment.create': 'Payment Created',
    'payment.confirm': 'Payment Submitted',
    'payment.delayed_report': 'Delayed Report Submitted',
    'membership.grant': 'Membership Granted',
    'membership.revoke': 'Membership Revoked',
    'account.create_admin': 'Administrator Created',
    'account.update_admin': 'Administrator Updated',
    'account.delete_admin': 'Administrator Deleted',
    'account.change_role': 'User Role Changed',
    'account.promote': 'Account Promoted',
    'account.seed_admin': 'Superadmin Seeded',
    'auth.login': 'User Login',
    'auth.login_password': 'Password Login',
    'auth.register': 'User Registration',
    'auth.logout': 'User Logout',
    'auth.refresh_reuse': 'Refresh Reuse Alert',
    'document.create': 'Document Created',
    'document.update': 'Document Updated',
    'document.delete': 'Document Deleted',
    'plan.create': 'Membership Plan Created',
    'plan.update': 'Membership Plan Updated',
    'trade.import.stage': 'Trade Dataset Staged',
    'trade.import.commit': 'Trade Import Committed',
    'trade.import.discard': 'Trade Import Discarded',
    'trade.publish': 'Trade Publication Updated',
    'trade.revision.delete': 'Trade Revision Deleted',
    'trade.registry.seed': 'Trade Registry Initialized',
    'trade.registry.update': 'Trade Registry Updated',
    'trade.registry.create': 'Trade Registry Entry Created',
    'trade.registry.alias': 'Trade Registry Alias Added',
    'job.retry': 'Background Job Retried',
  };
  return map[action] || action.replace(/\./g, ' ').toUpperCase();
}

// Action Category Badge Style
function getActionBadgeClass(action: string): string {
  if (action.includes('delete') || action.includes('revoke') || action.includes('reject') || action.includes('reuse')) {
    return 'locked';
  }
  if (action.includes('approve') || action.includes('create') || action.includes('commit') || action.includes('grant')) {
    return 'active';
  }
  if (action.includes('update') || action.includes('promote') || action.includes('stage')) {
    return 'admin';
  }
  return 'info';
}

// Short ID Formatter (avoids line breaking of raw 36-character UUIDs)
function formatShortId(id: string | null | undefined): string {
  if (!id) return '—';
  if (id.length <= 16) return id;
  return `${id.slice(0, 8)}...${id.slice(-6)}`;
}

// Extract Entity Name from Details if available
function getEntityName(event: AuditEvent): string | null {
  if (!event.details || typeof event.details !== 'object') return null;
  const d = event.details as Record<string, unknown>;
  return (
    (d.filename as string) ||
    (d.email as string) ||
    (d.name as string) ||
    (d.user_email as string) ||
    (d.deleted_email as string) ||
    (d.title as string) ||
    (d.plan_name as string) ||
    null
  );
}

// Formatted Object Descriptor
interface FormattedObject {
  kind: string;
  label: string;
  badgeClass: string;
}

function formatAuditObject(event: AuditEvent): FormattedObject {
  const d = (event.details || {}) as Record<string, unknown>;
  const action = event.action || '';
  const type = event.entity_type || '';

  // 1. Authentication & Session actions
  if (action === 'auth.login' || action === 'auth.login_password' || action === 'auth.register') {
    const userEmail = (d.email as string) || event.actor_email || 'User Account';
    return {
      kind: 'User Account',
      label: userEmail,
      badgeClass: 'admin',
    };
  }
  if (action === 'auth.logout') {
    const userEmail = (d.email as string) || event.actor_email || 'Portal Session';
    return {
      kind: 'Web Session',
      label: `${userEmail} (Active Sign-out)`,
      badgeClass: 'info',
    };
  }
  if (action === 'auth.refresh_reuse') {
    return {
      kind: 'Security Alert',
      label: 'Compromised Web Session (Terminated)',
      badgeClass: 'locked',
    };
  }

  // 2. Account & User Management
  if (action === 'account.seed_admin') {
    const targetEmail = (d.email as string) || event.actor_email || 'superadmin@agritrade.gov.kh';
    return {
      kind: 'Superadmin Account',
      label: targetEmail,
      badgeClass: 'superadmin',
    };
  }
  if (action.startsWith('account.')) {
    const targetEmail = (d.email as string) || (d.deleted_email as string) || event.actor_email || 'Admin User';
    const roleHint = (d.new_role as string) || (d.role as string) || (action.includes('admin') ? 'Administrator' : '');
    return {
      kind: roleHint ? `${roleHint} Account` : 'User Account',
      label: targetEmail,
      badgeClass: action.includes('delete') ? 'locked' : action.includes('superadmin') ? 'superadmin' : 'admin',
    };
  }

  // 3. Payment & Memberships
  if (action.startsWith('payment.')) {
    const payer = (d.payer_name as string) || (d.user_email as string) || 'Payment Request';
    const amount = d.amount ? ` • ${d.amount}` : '';
    const plan = d.plan_name ? ` • ${d.plan_name}` : '';
    return {
      kind: 'Payment Request',
      label: `${payer}${amount}${plan}`,
      badgeClass: 'active',
    };
  }
  if (action.startsWith('membership.')) {
    const reason = d.reason ? ` (${d.reason})` : '';
    return {
      kind: 'Member Subscription',
      label: `Membership Access${reason}`,
      badgeClass: 'active',
    };
  }
  if (action.startsWith('plan.')) {
    const planName = (d.plan_name as string) || (d.name as string) || 'Membership Plan';
    const amount = d.amount ? ` (${d.amount} ${d.currency || 'USD'})` : '';
    return {
      kind: 'Membership Plan',
      label: `${planName}${amount}`,
      badgeClass: 'admin',
    };
  }

  // 4. Documents
  if (action.startsWith('document.')) {
    const docName = (d.title as string) || (d.filename as string) || 'Document File';
    return {
      kind: 'Document',
      label: docName,
      badgeClass: 'info',
    };
  }

  // 5. Trade & Datasets
  if (action.startsWith('trade.')) {
    const filename = (d.filename as string) || (d.import_id as string) || 'Trade Dataset';
    return {
      kind: 'Trade Dataset',
      label: filename,
      badgeClass: 'admin',
    };
  }

  // 6. Generic Fallback
  return {
    kind: type ? type.replace(/_/g, ' ') : 'Record',
    label: getEntityName(event) || `${(type || 'Record').replace(/_/g, ' ')}`,
    badgeClass: 'info',
  };
}

// Human-friendly Recorded Details Formatter
interface EventDetailItem {
  label?: string;
  value: string;
  badgeClass?: string;
}

function formatEventDetails(event: AuditEvent): EventDetailItem[] {
  if (!event.details || typeof event.details !== 'object' || Array.isArray(event.details)) {
    return [];
  }
  const d = event.details as Record<string, unknown>;
  const action = event.action || '';
  const items: EventDetailItem[] = [];

  // Keys to filter out (raw UUIDs, internal identifiers, redundant strings already in actor/object)
  const blacklist = new Set([
    'id',
    'revision_id',
    'import_id',
    'user_id',
    'session_id',
    'token_id',
    'actor_id',
    'plan_id',
    'auth_session_id',
    'entity_id',
    'email',
    'deleted_email',
    'user_email',
    'name',
    'filename',
    'by',
    'by_superadmin',
  ]);

  // 1. Trade Publication
  if (action === 'trade.publish' && (d.start_month || d.end_month)) {
    items.push({
      label: 'Coverage',
      value: `${d.start_month || ''} → ${d.end_month || ''}`,
    });
    return items;
  }

  // 2. Trade Commit Preview
  if (action === 'trade.import.commit') {
    const ins = Number(d.inserted) || 0;
    const upd = Number(d.updated) || 0;
    const rem = Number(d.removed) || 0;
    const unc = Number(d.unchanged) || 0;
    if (ins > 0) items.push({ value: `+${ins.toLocaleString()} inserted`, badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200' });
    if (upd > 0) items.push({ value: `${upd.toLocaleString()} updated`, badgeClass: 'bg-sky-50 text-sky-700 border-sky-200' });
    if (rem > 0) items.push({ value: `-${rem.toLocaleString()} removed`, badgeClass: 'bg-rose-50 text-rose-700 border-rose-200' });
    if (unc > 0 && ins === 0 && upd === 0 && rem === 0) items.push({ value: `${unc.toLocaleString()} unchanged` });
    if (items.length) return items;
  }

  // 3. Trade Stage
  if (action === 'trade.import.stage') {
    if (d.row_count !== undefined && d.row_count !== null) {
      items.push({ value: `${Number(d.row_count).toLocaleString()} rows` });
    }
    if (d.mode) {
      items.push({ label: 'Mode', value: d.mode === 'partial' ? 'Partial Update' : 'Full Dataset' });
    }
    if (items.length) return items;
  }

  // 4. Trade Revision Delete
  if (action === 'trade.revision.delete' && Array.isArray(d.periods) && d.periods.length) {
    items.push({ label: 'Periods', value: (d.periods as string[]).join(', ') });
    return items;
  }

  // 5. Trade Registry
  if (action === 'trade.registry.seed' && d.count) {
    items.push({ value: `${d.count} registry items initialized` });
    return items;
  }
  if (action.startsWith('trade.registry.')) {
    if (d.code) items.push({ label: 'Code', value: String(d.code) });
    if (d.kind) items.push({ label: 'Level', value: String(d.kind).toUpperCase() });
    if (d.name_km) items.push({ label: 'Khmer', value: String(d.name_km) });
    if (d.name_en) items.push({ label: 'English', value: String(d.name_en) });
    if (d.alias) items.push({ label: 'Alias', value: String(d.alias) });
    if (d.parent_code) items.push({ label: 'Parent', value: String(d.parent_code) });
    if (items.length) return items;
  }

  // 6. Plan / Document / Account updates (Field changes list)
  const fields = (d.fields || d.changes) as unknown;
  if (Array.isArray(fields) && fields.length > 0) {
    const fieldNames = fields
      .map((f) => String(f).replace(/_/g, ' '))
      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
      .join(', ');
    items.push({
      label: 'Updated Properties',
      value: fieldNames,
    });
    return items;
  }

  // 7. Role changes
  if (d.new_role || (action.startsWith('account.') && d.role)) {
    const role = String(d.new_role || d.role);
    const roleLabel = role === 'superadmin' ? 'Superadmin' : role === 'admin' ? 'Administrator' : 'User';
    if (!action.includes('seed_admin')) {
      items.push({ label: 'Role', value: roleLabel });
    }
  }

  // 8. Reason / Note
  if (d.reason && typeof d.reason === 'string' && d.reason.trim()) {
    items.push({ label: 'Reason', value: d.reason.trim() });
  }

  // 9. Expiration Date
  if (d.expires_at && typeof d.expires_at === 'string') {
    try {
      const expDate = new Date(d.expires_at);
      if (!isNaN(expDate.getTime())) {
        items.push({
          label: 'Expires',
          value: expDate.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }),
        });
      }
    } catch {
      // ignore
    }
  }

  // 10. Provisioned by CLI
  if (d.provisioned_by && typeof d.provisioned_by === 'string') {
    items.push({ label: 'Provisioned By', value: String(d.provisioned_by).replace(/_/g, ' ') });
  }

  // 11. Generic fallback for any other meaningful non-blacklisted keys
  for (const [key, val] of Object.entries(d)) {
    if (blacklist.has(key)) continue;
    if (['fields', 'changes', 'new_role', 'role', 'reason', 'expires_at', 'provisioned_by', 'start_month', 'end_month', 'row_count', 'mode', 'inserted', 'updated', 'removed', 'unchanged', 'count', 'code', 'kind', 'name_km', 'name_en', 'alias', 'parent_code', 'payer_name', 'plan_name'].includes(key)) continue;
    if (val === null || val === undefined || val === '') continue;

    const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    let value = String(val);
    if (Array.isArray(val)) {
      value = val.join(', ');
    } else if (typeof val === 'object') {
      value = JSON.stringify(val);
    }
    items.push({ label, value });
  }

  return items;
}

// Filtered Audit Events
const filteredEvents = computed(() => {
  let list = events.value;
  if (auditCategory.value === 'accounts') {
    list = list.filter((e) => e.action.startsWith('account.') || e.action.startsWith('auth.'));
  } else if (auditCategory.value === 'payments') {
    list = list.filter(
      (e) => e.action.startsWith('payment.') || e.action.startsWith('membership.') || e.action.startsWith('plan.'),
    );
  } else if (auditCategory.value === 'trade') {
    list = list.filter((e) => e.action.startsWith('trade.'));
  } else if (auditCategory.value === 'documents') {
    list = list.filter((e) => e.action.startsWith('document.'));
  }

  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return list;

  return list.filter((e) => {
    const actionLabel = formatAction(e.action).toLowerCase();
    const actor = `${e.actor_name || ''} ${e.actor_email || ''} ${e.actor_id || ''}`.toLowerCase();
    const obj = formatAuditObject(e);
    const objText = `${obj.kind} ${obj.label}`.toLowerCase();
    const detailsText = formatEventDetails(e).map((d) => `${d.label || ''} ${d.value}`).join(' ').toLowerCase();
    return actionLabel.includes(q) || actor.includes(q) || objText.includes(q) || detailsText.includes(q);
  });
});

onMounted(load);
</script>

<template>
  <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 sm:pb-4 mb-5">
    <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">Audit Logs</h1>
    <button class="secondary text-xs font-semibold py-1.5 px-3 rounded-xl inline-flex items-center gap-1.5 justify-center flex-shrink-0 cursor-pointer" :disabled="busy" @click="load">
      <RefreshCw class="w-3.5 h-3.5 inline mr-1" />
      <span>Refresh</span>
    </button>
  </div>

  <TaskNotice :busy="busy" :error="error" :notice="notice" />

  <!-- AUDIT TRAIL CARD -->
  <section class="card">
    <div class="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
      <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0">System & Administrator Audit Events</h2>
      <div class="badge font-bold">
        {{ filteredEvents.length }} {{ filteredEvents.length === 1 ? 'event' : 'events' }}
      </div>
    </div>

    <!-- Filter & Search Toolbar -->
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 mb-4">
      <!-- Category Filter Pills -->
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          class="text-xs px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl transition-all font-semibold cursor-pointer"
          :class="auditCategory === 'all' ? 'bg-sky-600 text-white font-bold shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200/80'"
          @click="auditCategory = 'all'"
        >
          All Events ({{ categoryCounts.all }})
        </button>
        <button
          class="text-xs px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl transition-all font-semibold cursor-pointer"
          :class="auditCategory === 'accounts' ? 'bg-sky-600 text-white font-bold shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200/80'"
          @click="auditCategory = 'accounts'"
        >
          Accounts & Security ({{ categoryCounts.accounts }})
        </button>
        <button
          class="text-xs px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl transition-all font-semibold cursor-pointer"
          :class="auditCategory === 'payments' ? 'bg-sky-600 text-white font-bold shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200/80'"
          @click="auditCategory = 'payments'"
        >
          Payments & Memberships ({{ categoryCounts.payments }})
        </button>
        <button
          class="text-xs px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl transition-all font-semibold cursor-pointer"
          :class="auditCategory === 'trade' ? 'bg-sky-600 text-white font-bold shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200/80'"
          @click="auditCategory = 'trade'"
        >
          Trade Imports & Data ({{ categoryCounts.trade }})
        </button>
        <button
          class="text-xs px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-xl transition-all font-semibold cursor-pointer"
          :class="auditCategory === 'documents' ? 'bg-sky-600 text-white font-bold shadow-xs' : 'bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200/80'"
          @click="auditCategory = 'documents'"
        >
          Documents ({{ categoryCounts.documents }})
        </button>
      </div>

      <!-- Quick Search Bar -->
      <div class="search-field w-full lg:w-64 max-w-xs lg:ml-auto">
        <Search class="search-icon w-3.5 h-3.5" />
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Filter audit logs..."
          class="text-xs"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="search-clear-btn"
          title="Clear search"
          @click="searchQuery = ''"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Audit Events Table -->
    <div class="table-scroll">
      <table class="w-full text-xs min-w-[820px]">
        <thead>
          <tr class="bg-slate-50/80 border-b border-slate-200 text-slate-700">
            <th class="py-3 px-4 text-left font-bold" style="width: 170px;">Timestamp</th>
            <th class="py-3 px-4 text-left font-bold" style="min-width: 190px;">Actor</th>
            <th class="py-3 px-4 text-left font-bold" style="min-width: 170px;">Action</th>
            <th class="py-3 px-4 text-left font-bold" style="min-width: 220px;">Object</th>
            <th class="py-3 px-4 text-left font-bold">Recorded Details</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="event in filteredEvents" :key="event.id" class="hover:bg-slate-50/70 transition-colors">
            <!-- Timestamp -->
            <td class="py-3 px-4 whitespace-nowrap">
              <div class="font-bold text-slate-900 text-xs">{{ dateTime(event.created_at).split(',')[0] }}</div>
              <div class="text-slate-500 text-[11px] mono mt-0.5">{{ dateTime(event.created_at).split(',')[1] || '' }}</div>
            </td>

            <!-- Actor -->
            <td class="py-3 px-4 whitespace-nowrap">
              <div v-if="event.actor_name || event.actor_email">
                <div class="font-bold text-slate-900 text-xs">{{ event.actor_name || 'Administrator' }}</div>
                <div class="text-slate-500 text-xs mono mt-0.5">{{ event.actor_email }}</div>
              </div>
              <div v-else-if="event.actor_id">
                <div class="font-semibold text-xs text-slate-700 mb-0.5">Account</div>
                <span class="mono text-[11px] text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200" :title="event.actor_id">
                  {{ formatShortId(event.actor_id) }}
                </span>
              </div>
              <div v-else>
                <span class="badge text-xs font-semibold text-slate-600">System Automated</span>
              </div>
            </td>

            <!-- Action -->
            <td class="py-3 px-4 whitespace-nowrap">
              <span class="status-pill text-[11px] font-bold" :class="getActionBadgeClass(event.action)">
                {{ formatAction(event.action) }}
              </span>
            </td>

            <!-- Object -->
            <td class="py-3 px-4" :title="event.entity_id ? `ID: ${event.entity_id}` : undefined">
              <div class="inline-flex items-center mb-1">
                <span class="status-pill text-[10px] py-0.5 px-2 font-bold" :class="formatAuditObject(event).badgeClass">
                  {{ formatAuditObject(event).kind.toUpperCase() }}
                </span>
              </div>
              <div class="font-bold text-xs text-slate-900 leading-snug break-words">
                {{ formatAuditObject(event).label }}
              </div>
            </td>

            <!-- Recorded Details -->
            <td class="py-3 px-4">
              <div v-if="formatEventDetails(event).length" class="flex flex-wrap gap-1.5">
                <span
                  v-for="(item, idx) in formatEventDetails(event)"
                  :key="idx"
                  class="bg-slate-50/90 text-slate-800 px-2.5 py-1 rounded-lg text-xs border border-slate-200/90 inline-flex items-center shadow-2xs"
                  :class="item.badgeClass"
                >
                  <span v-if="item.label" class="font-medium text-slate-500 mr-1.5">{{ item.label }}:</span>
                  <span class="font-semibold text-slate-900 font-mono">{{ item.value }}</span>
                </span>
              </div>
              <span v-else class="text-slate-300 font-mono text-xs select-none">—</span>
            </td>
          </tr>
          <tr v-if="!filteredEvents.length">
            <td colspan="5" class="text-center py-8 text-slate-500 text-xs">
              <div v-if="searchQuery">No audit events match "<span class="font-semibold text-slate-700">{{ searchQuery }}</span>".</div>
              <div v-else class="italic text-slate-400">No audit trail events match the selected category.</div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
