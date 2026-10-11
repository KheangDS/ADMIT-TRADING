<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { Eye, EyeOff, Shield, Users as UsersIcon, UserPlus, Edit3, Trash2, X } from 'lucide-vue-next';
import { api } from '../api';
import { dateTime } from '../format';
import { session } from '../session';
import type { AdminUser } from '../types';
import { useTask } from '../composables/useTask';
import TaskNotice from '../components/TaskNotice.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';

const users = ref<AdminUser[]>([]);

// Current user privilege check
const isSuperadmin = computed(() => session.user?.role === 'superadmin');

// Add Admin Modal State
const showAddAdminModal = ref(false);
const showAdminPassword = ref(false);
const addAdminForm = reactive({
  name: '',
  email: '',
  password: '',
});

// Edit Admin Modal State
const showEditAdminModal = ref(false);
const showEditPassword = ref(false);
const editingAdmin = ref<AdminUser | null>(null);
const editAdminForm = reactive({
  name: '',
  email: '',
  password: '',
  disabled: false,
});

// Delete Admin Confirmation State
const showDeleteConfirm = ref(false);
const deletingAdmin = ref<AdminUser | null>(null);

const { busy, error, notice, run } = useTask();

const admins = computed(() =>
  users.value.filter((u) => u.role === 'admin' || u.role === 'superadmin'),
);

const members = computed(() =>
  users.value.filter((u) => u.role === 'member'),
);

async function fetchUsers() {
  users.value = (await api.get<AdminUser[]>('/admin/users')).data;
}

async function load() {
  await run(fetchUsers);
}

// Open Add Admin Modal
function openAddAdmin() {
  addAdminForm.name = '';
  addAdminForm.email = '';
  addAdminForm.password = '';
  showAdminPassword.value = false;
  showAddAdminModal.value = true;
}

// Handle Add Admin Submit
async function handleCreateAdmin() {
  await run(async () => {
    if (!addAdminForm.name.trim() || !addAdminForm.email.trim() || !addAdminForm.password) {
      throw new Error('Please fill out all required fields.');
    }
    if (addAdminForm.password.length < 8) {
      throw new Error('Password must be at least 8 characters long.');
    }
    await api.post('/admin/users/create-admin', {
      name: addAdminForm.name.trim(),
      email: addAdminForm.email.trim(),
      password: addAdminForm.password,
    });
    showAddAdminModal.value = false;
    await fetchUsers();
    notice.value = `Administrator account created successfully for ${addAdminForm.email.trim()}.`;
  });
}

// Open Edit Admin Modal
function openEditAdmin(admin: AdminUser) {
  editingAdmin.value = admin;
  editAdminForm.name = admin.name;
  editAdminForm.email = admin.email;
  editAdminForm.password = '';
  editAdminForm.disabled = admin.disabled;
  showEditPassword.value = false;
  showEditAdminModal.value = true;
}

// Handle Edit Admin Submit
async function handleUpdateAdmin() {
  const admin = editingAdmin.value;
  if (!admin) return;
  await run(async () => {
    if (!editAdminForm.name.trim() || !editAdminForm.email.trim()) {
      throw new Error('Name and email cannot be empty.');
    }
    if (editAdminForm.password && editAdminForm.password.length < 8) {
      throw new Error('New password must be at least 8 characters long.');
    }

    const payload: Record<string, unknown> = {
      name: editAdminForm.name.trim(),
      email: editAdminForm.email.trim(),
      disabled: editAdminForm.disabled,
    };
    if (editAdminForm.password) {
      payload.password = editAdminForm.password;
    }

    await api.patch(`/admin/users/${encodeURIComponent(admin.id)}`, payload);
    showEditAdminModal.value = false;
    editingAdmin.value = null;
    await fetchUsers();
    notice.value = `Administrator account updated successfully.`;
  });
}

// Open Delete Confirmation
function openDeleteAdmin(admin: AdminUser) {
  deletingAdmin.value = admin;
  showDeleteConfirm.value = true;
}

// Handle Delete Admin Submit
async function handleDeleteAdmin() {
  const admin = deletingAdmin.value;
  if (!admin) return;
  await run(async () => {
    await api.delete(`/admin/users/${encodeURIComponent(admin.id)}`);
    showDeleteConfirm.value = false;
    const deletedEmail = admin.email;
    deletingAdmin.value = null;
    await fetchUsers();
    notice.value = `Administrator account for ${deletedEmail} was permanently removed.`;
  });
}

onMounted(load);
</script>

<template>
  <div class="flex items-center justify-between gap-3 border-b border-slate-200 pb-3 sm:pb-4 mb-5">
    <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">User & Admin Management</h1>
  </div>

  <TaskNotice :busy="busy" :error="error" :notice="notice" />

  <!-- SECTION 1: ADMINISTRATORS -->
  <section class="card mb-6">
    <div class="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
      <div class="flex items-center gap-2">
        <Shield class="w-4 h-4 text-indigo-600 flex-shrink-0" />
        <h2 class="text-base sm:text-lg font-bold text-slate-900 !m-0 !p-0 leading-none">Administrators</h2>
        <span class="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-xs font-bold rounded-full bg-sky-50 text-sky-700 border border-sky-200 leading-none">
          {{ admins.length }}
        </span>
      </div>
      <div v-if="isSuperadmin" class="actions m-0">
        <button class="secondary text-xs font-semibold py-1 px-2.5 rounded-lg flex-shrink-0 cursor-pointer" :disabled="busy" @click="openAddAdmin">+ Add Administrator</button>
      </div>
    </div>

    <!-- Mobile Cards View (md:hidden) -->
    <div class="space-y-3 md:hidden">
      <div
        v-for="admin in admins"
        :key="admin.id"
        class="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/60 space-y-2.5"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <div class="font-bold text-slate-900 text-sm leading-snug break-words">{{ admin.name }}</div>
            <div class="text-xs font-mono text-slate-500 mt-0.5 break-all select-all">{{ admin.email }}</div>
          </div>
          <span class="status-pill flex-shrink-0" :class="admin.role">
            {{ admin.role.toUpperCase() }}
          </span>
        </div>

        <div class="flex items-center justify-between pt-2 border-t border-slate-200/60 text-xs">
          <div class="flex items-center gap-1.5">
            <span
              class="w-1.5 h-1.5 rounded-full"
              :class="admin.disabled ? 'bg-rose-500' : 'bg-emerald-500'"
            ></span>
            <span :style="{ color: admin.disabled ? '#dc2626' : '#16a34a', fontWeight: 'bold' }">
              {{ admin.disabled ? 'Disabled' : 'Active' }}
            </span>
            <span v-if="admin.created_at" class="text-slate-400 font-mono text-[11px] ml-1">
              • {{ dateTime(admin.created_at) }}
            </span>
          </div>
          <div v-if="isSuperadmin" class="flex items-center gap-1.5">
            <button
              class="secondary text-xs py-0.5 px-2"
              :disabled="busy || (admin.role === 'superadmin' && admin.id !== session.user?.id)"
              @click="openEditAdmin(admin)"
            >
              Edit
            </button>
            <button
              class="danger text-xs py-0.5 px-2"
              :disabled="busy || admin.role === 'superadmin' || admin.id === session.user?.id"
              :title="admin.role === 'superadmin' ? 'Superadmin cannot be deleted' : admin.id === session.user?.id ? 'Cannot delete own account' : 'Delete administrator'"
              @click="openDeleteAdmin(admin)"
            >
              Delete
            </button>
          </div>
          <span v-else class="muted text-xs">Read only</span>
        </div>
      </div>
      <div v-if="!admins.length" class="text-center py-4 muted text-xs">
        No administrator accounts found.
      </div>
    </div>

    <!-- Desktop Table View (hidden md:block) -->
    <div class="hidden md:block table-scroll">
      <table class="w-full">
        <thead>
          <tr>
            <th class="whitespace-nowrap min-w-[200px]">Administrator</th>
            <th class="whitespace-nowrap">Role</th>
            <th class="whitespace-nowrap">Account Status</th>
            <th class="whitespace-nowrap">Created Date</th>
            <th class="whitespace-nowrap">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="admin in admins" :key="admin.id">
            <td>
              <div class="font-bold text-slate-900">{{ admin.name }}</div>
              <div class="muted mono text-xs">{{ admin.email }}</div>
            </td>
            <td class="whitespace-nowrap">
              <span class="status-pill" :class="admin.role">
                {{ admin.role.toUpperCase() }}
              </span>
            </td>
            <td class="whitespace-nowrap">
              <span :style="{ color: admin.disabled ? '#dc2626' : '#16a34a', fontWeight: 'bold' }">
                {{ admin.disabled ? 'Disabled' : 'Active' }}
              </span>
            </td>
            <td class="whitespace-nowrap">
              <span v-if="admin.created_at" class="mono text-xs">{{ dateTime(admin.created_at) }}</span>
              <span v-else class="muted text-xs">—</span>
            </td>
            <td class="whitespace-nowrap">
              <template v-if="isSuperadmin">
                <div class="flex items-center gap-2">
                  <button
                    class="secondary text-xs"
                    :disabled="busy || (admin.role === 'superadmin' && admin.id !== session.user?.id)"
                    @click="openEditAdmin(admin)"
                  >
                    Edit
                  </button>
                  <button
                    class="danger text-xs"
                    :disabled="busy || admin.role === 'superadmin' || admin.id === session.user?.id"
                    :title="admin.role === 'superadmin' ? 'Superadmin cannot be deleted' : admin.id === session.user?.id ? 'Cannot delete own account' : 'Delete administrator'"
                    @click="openDeleteAdmin(admin)"
                  >
                    Delete
                  </button>
                </div>
              </template>
              <template v-else>
                <span class="muted text-xs">Read only</span>
              </template>
            </td>
          </tr>
          <tr v-if="!admins.length">
            <td colspan="5" class="text-center py-4 muted">No administrator accounts found.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- SECTION 2: PLATFORM MEMBERS -->
  <section class="card">
    <div class="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-4">
      <div class="flex items-center gap-2">
        <UsersIcon class="w-4 h-4 text-slate-600 flex-shrink-0" />
        <h2 class="text-base sm:text-lg font-bold text-slate-900 !m-0 !p-0 leading-none">Platform Members</h2>
        <span class="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-xs font-bold rounded-full bg-sky-50 text-sky-700 border border-sky-200 leading-none">
          {{ members.length }}
        </span>
      </div>
    </div>

    <!-- Mobile Cards View (md:hidden) -->
    <div class="space-y-3 md:hidden">
      <div
        v-for="member in members"
        :key="member.id"
        class="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/60 space-y-2.5"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <div class="font-bold text-slate-900 text-sm leading-snug break-words">{{ member.name }}</div>
            <div class="text-xs font-mono text-slate-500 mt-0.5 break-all select-all">{{ member.email }}</div>
          </div>
          <span class="status-pill pending flex-shrink-0">
            MEMBER
          </span>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200/60 text-xs">
          <div class="flex items-center gap-1.5">
            <span
              class="w-1.5 h-1.5 rounded-full"
              :class="member.disabled ? 'bg-rose-500' : 'bg-emerald-500'"
            ></span>
            <span :style="{ color: member.disabled ? '#dc2626' : '#16a34a', fontWeight: 'bold' }">
              {{ member.disabled ? 'Disabled' : 'Active' }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="status-pill" :class="member.membership?.active ? 'active' : 'locked'">
              {{ member.membership?.active ? 'Active Member' : 'No Active Membership' }}
            </span>
          </div>
        </div>

        <div v-if="member.membership?.expires_at || member.membership?.source" class="text-[11px] text-slate-500 font-mono bg-white p-2 rounded-lg border border-slate-200/60 flex items-center justify-between">
          <span>Expires: {{ member.membership?.expires_at ? dateTime(member.membership.expires_at) : '—' }}</span>
          <span v-if="member.membership?.source" class="text-slate-400">({{ member.membership.source }})</span>
        </div>
      </div>
      <div v-if="!members.length" class="text-center py-4 muted text-xs">
        No member accounts found.
      </div>
    </div>

    <!-- Desktop Table View (hidden md:block) -->
    <div class="hidden md:block table-scroll">
      <table class="w-full">
        <thead>
          <tr>
            <th class="whitespace-nowrap min-w-[200px]">Member Account</th>
            <th class="whitespace-nowrap">Role</th>
            <th class="whitespace-nowrap">Account Status</th>
            <th class="whitespace-nowrap">Membership Access</th>
            <th class="whitespace-nowrap">Expiry / Source</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="member in members" :key="member.id">
            <td>
              <div class="font-bold text-slate-900">{{ member.name }}</div>
              <div class="muted mono text-xs">{{ member.email }}</div>
            </td>
            <td>
              <span class="status-pill pending">
                MEMBER
              </span>
            </td>
            <td>
              <span :style="{ color: member.disabled ? '#dc2626' : '#16a34a', fontWeight: 'bold' }">
                {{ member.disabled ? 'Disabled' : 'Active' }}
              </span>
            </td>
            <td>
              <span class="status-pill" :class="member.membership?.active ? 'active' : 'locked'">
                {{ member.membership?.active ? 'Active Member' : 'No Active Membership' }}
              </span>
            </td>
            <td>
              <span v-if="member.membership?.expires_at" class="mono text-xs">{{ dateTime(member.membership.expires_at) }}</span>
              <span v-else class="muted text-xs">—</span>
              <div v-if="member.membership?.source" class="muted text-xs">Source: {{ member.membership.source }}</div>
            </td>
          </tr>
          <tr v-if="!members.length">
            <td colspan="5" class="text-center py-4 muted">No member accounts found.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <!-- ADD ADMINISTRATOR MODAL -->
  <div
    v-if="showAddAdminModal"
    class="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs"
    @click="showAddAdminModal = false"
  ></div>
  <dialog
    v-if="showAddAdminModal"
    open
    class="card"
    style="display: block; position: fixed; z-index: 50; top: 50%; left: 50%; transform: translate(-50%, -50%); margin: 0; max-width: 480px; width: 92%; box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25); border-radius: 1.25rem; border: 1px solid #e2e8f0; background: white; padding: 1.75rem;"
  >
    <div class="flex items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-100">
      <div class="min-w-0 flex-1">
        <h2 class="text-base font-bold text-slate-900 m-0">Create Administrator Account</h2>
      </div>
      <button type="button" class="btn-icon-close flex-shrink-0" aria-label="Close" @click="showAddAdminModal = false">
        <X class="w-4 h-4" />
      </button>
    </div>
    <form class="space-y-3 mt-3" @submit.prevent="handleCreateAdmin">
      <label>
        Admin Full Name
        <input v-model="addAdminForm.name" placeholder="e.g. Sok Dara" required />
      </label>
      <label>
        Admin Email
        <input v-model="addAdminForm.email" type="email" placeholder="admin@agritrade.gov.kh" required autocomplete="username" />
      </label>
      <label>
        Password (min 8 characters)
        <div class="password-field">
          <input
            v-model="addAdminForm.password"
            :type="showAdminPassword ? 'text' : 'password'"
            placeholder="••••••••"
            required
            autocomplete="new-password"
          />
          <button
            type="button"
            class="password-toggle-btn"
            :aria-label="showAdminPassword ? 'Hide password' : 'Show password'"
            @click="showAdminPassword = !showAdminPassword"
          >
            <EyeOff v-if="showAdminPassword" class="w-4 h-4" />
            <Eye v-else class="w-4 h-4" />
          </button>
        </div>
      </label>
      <div class="actions mt-5 pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
        <button type="button" class="secondary" :disabled="busy" @click="showAddAdminModal = false">Cancel</button>
        <button type="submit" :disabled="busy">Create Administrator</button>
      </div>
    </form>
  </dialog>

  <!-- EDIT ADMINISTRATOR MODAL -->
  <div
    v-if="showEditAdminModal && editingAdmin"
    class="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs"
    @click="showEditAdminModal = false"
  ></div>
  <dialog
    v-if="showEditAdminModal && editingAdmin"
    open
    class="card"
    style="display: block; position: fixed; z-index: 50; top: 50%; left: 50%; transform: translate(-50%, -50%); margin: 0; max-width: 480px; width: 92%; box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.25); border-radius: 1.25rem; border: 1px solid #e2e8f0; background: white; padding: 1.75rem;"
  >
    <div class="flex items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-100">
      <div class="min-w-0 flex-1">
        <h2 class="text-base font-bold text-slate-900 m-0 truncate" :title="`Edit Administrator: ${editingAdmin.name}`">
          Edit Administrator
        </h2>
        <p class="text-xs text-slate-500 m-0 mt-0.5 truncate">{{ editingAdmin.name }} ({{ editingAdmin.email }})</p>
      </div>
      <button type="button" class="btn-icon-close flex-shrink-0" aria-label="Close" @click="showEditAdminModal = false">
        <X class="w-4 h-4" />
      </button>
    </div>
    <form class="space-y-3 mt-3" @submit.prevent="handleUpdateAdmin">
      <label>
        Full Name
        <input v-model="editAdminForm.name" required />
      </label>
      <label>
        Email Address
        <input v-model="editAdminForm.email" type="email" required autocomplete="username" />
      </label>
      <label>
        Reset Password (optional)
        <div class="password-field">
          <input
            v-model="editAdminForm.password"
            :type="showEditPassword ? 'text' : 'password'"
            placeholder="Leave blank to keep current password"
            autocomplete="new-password"
          />
          <button
            type="button"
            class="password-toggle-btn"
            :aria-label="showEditPassword ? 'Hide password' : 'Show password'"
            @click="showEditPassword = !showEditPassword"
          >
            <EyeOff v-if="showEditPassword" class="w-4 h-4" />
            <Eye v-else class="w-4 h-4" />
          </button>
        </div>
      </label>
      <label class="check mt-2" v-if="editingAdmin.id !== session.user?.id">
        <input v-model="editAdminForm.disabled" type="checkbox" />
        Disable administrator account (prevents login)
      </label>
      <div class="actions mt-5 pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
        <button type="button" class="secondary" :disabled="busy" @click="showEditAdminModal = false">Cancel</button>
        <button type="submit" :disabled="busy">Save Changes</button>
      </div>
    </form>
  </dialog>

  <!-- DELETE CONFIRMATION DIALOG -->
  <ConfirmDialog
    :open="showDeleteConfirm"
    :busy="busy"
    :error="error"
    title="Delete Administrator Account?"
    :message="`Are you sure you want to permanently delete administrator account ${deletingAdmin?.name} (${deletingAdmin?.email})? This action cannot be undone.`"
    @cancel="showDeleteConfirm = false"
    @confirm="handleDeleteAdmin"
  />
</template>
