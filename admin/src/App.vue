<script setup lang="ts">
import { computed, watch, ref } from 'vue';
import { useRoute } from 'vue-router';
import { router } from './router';
import { api, bootstrap } from './api';
import { clearSession, session } from './session';
import { useTask } from './composables/useTask';
import TaskNotice from './components/TaskNotice.vue';
import {
  UploadCloud,
  BookOpen,
  FileText,
  Layers,
  CreditCard,
  Users,
  ShieldAlert,
  LogOut,
  Menu,
  X,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-vue-next';

const route = useRoute();
const { busy, error, run } = useTask();
const epoch = ref(0);
const isDrawerOpen = ref(false);
const isSidebarCollapsed = ref(false);

interface NavLinkItem {
  path: string;
  label: string;
  icon: any;
}

const links = computed<NavLinkItem[]>(() => {
  const list: NavLinkItem[] = [
    { path: '/imports', label: 'Data imports', icon: UploadCloud },
    { path: '/dictionary', label: 'Dictionary', icon: BookOpen },
    { path: '/documents', label: 'Documents', icon: FileText },
    { path: '/plans', label: 'Plans', icon: Layers },
    { path: '/payments', label: 'Payments', icon: CreditCard },
    { path: '/users', label: 'Users', icon: Users },
  ];
  if (session.user?.role === 'superadmin') {
    list.push({ path: '/operations', label: 'Audit Logs', icon: ShieldAlert });
  }
  return list;
});

function toggleSidebar() {
  isSidebarCollapsed.value = !isSidebarCollapsed.value;
}

// Close mobile drawer on route change
watch(
  () => route.path,
  () => {
    isDrawerOpen.value = false;
  },
);

watch(
  () => [session.user?.id, session.denied, session.user?.role, session.ready],
  () => {
    epoch.value++;
    if (!session.ready) return;
    if (route.meta.admin && ((session.user?.role !== 'admin' && session.user?.role !== 'superadmin') || session.denied))
      void router.replace({ path: '/login', query: { return_to: route.path } });
  },
);

async function logout() {
  await run(async () => {
    await api.post('/auth/logout');
    clearSession();
    isDrawerOpen.value = false;
    await router.replace('/login');
  });
}
</script>

<template>
  <a class="skip" href="#main">Skip to content</a>

  <div class="min-h-screen bg-slate-100/70 flex flex-col md:flex-row">
    <!-- Desktop Left Sidebar (With Hide/Show Collapse Support) -->
    <aside
      v-if="(session.user?.role === 'admin' || session.user?.role === 'superadmin') && !session.denied"
      class="hidden md:flex bg-white text-slate-700 flex-col justify-between border-r border-slate-200/90 flex-shrink-0 sticky top-0 h-screen select-none z-20 shadow-xs transition-all duration-300 ease-in-out"
      :class="isSidebarCollapsed ? 'w-20 p-3 items-center' : 'w-64 lg:w-72 p-5'"
    >
      <div class="space-y-6 w-full">
        <!-- Brand Header with Original Logo & Collapse Button -->
        <div v-if="!isSidebarCollapsed" class="flex items-center justify-between px-1 pt-1">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <img src="/admit-trading.png" alt="ADMIT Trading" class="h-7 w-auto object-contain" />
            </div>
            <div class="flex items-center gap-1.5 mt-2">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Admin Portal</span>
            </div>
          </div>
          <button
            type="button"
            class="p-1.5 rounded-xl text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition cursor-pointer border border-transparent hover:border-slate-200"
            title="Hide sidebar"
            aria-label="Hide sidebar"
            @click="toggleSidebar"
          >
            <PanelLeftClose class="w-4 h-4" />
          </button>
        </div>

        <!-- Collapsed Brand Header / Expand Button -->
        <div v-else class="flex flex-col items-center gap-3 pt-2">
          <button
            type="button"
            class="p-2 rounded-xl text-slate-500 hover:text-sky-700 hover:bg-sky-50 transition cursor-pointer border border-slate-200 bg-slate-50 shadow-2xs"
            title="Show sidebar"
            aria-label="Show sidebar"
            @click="toggleSidebar"
          >
            <PanelLeftOpen class="w-5 h-5 text-sky-600" />
          </button>
        </div>

        <!-- Navigation Links -->
        <nav class="space-y-1.5 w-full" aria-label="Administration">
          <div v-if="!isSidebarCollapsed" class="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider px-3 mb-2">
            Navigation
          </div>
          <div v-else class="w-full border-t border-slate-100 my-2"></div>

          <RouterLink
            v-for="item in links"
            :key="item.path"
            :to="item.path"
            class="flex items-center rounded-xl text-xs font-semibold transition-colors group"
            :class="[
              isSidebarCollapsed 
                ? 'justify-center p-3 text-slate-500 hover:text-slate-900 hover:bg-slate-100' 
                : 'gap-3 px-3.5 py-2.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100/80',
            ]"
            :title="isSidebarCollapsed ? item.label : ''"
            active-class="!bg-sky-50 !text-sky-800 !font-bold !border !border-sky-200/90 shadow-2xs"
          >
            <component
              :is="item.icon"
              class="w-4 h-4 flex-shrink-0"
              :class="route.path === item.path ? 'text-sky-600' : 'text-slate-400 group-hover:text-slate-700'"
            />
            <span v-if="!isSidebarCollapsed">{{ item.label }}</span>
          </RouterLink>
        </nav>
      </div>

      <!-- User Profile Card -->
      <div class="pt-4 border-t border-slate-100 w-full">
        <!-- Expanded User Profile -->
        <div v-if="!isSidebarCollapsed" class="p-3 rounded-2xl bg-slate-50/90 border border-slate-200/80 flex items-start justify-between gap-2.5 shadow-2xs">
          <div class="flex items-start gap-2.5 min-w-0 flex-1">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-sky-500 to-sky-600 text-white font-black text-xs flex items-center justify-center flex-shrink-0 shadow-2xs uppercase mt-0.5">
              {{ session.user?.name ? session.user.name.charAt(0) : 'A' }}
            </div>
            <div class="min-w-0 flex-1 space-y-0.5">
              <p class="text-xs font-bold text-slate-900 m-0 leading-snug break-words" :title="session.user?.name">
                {{ session.user?.name }}
              </p>
              <p v-if="session.user?.email" class="text-[11px] text-slate-500 font-mono m-0 leading-snug break-all" :title="session.user?.email">
                {{ session.user?.email }}
              </p>
              <div class="pt-0.5">
                <span class="text-[9px] font-extrabold text-sky-700 bg-sky-100/70 border border-sky-200/80 px-1.5 py-0.5 rounded-md uppercase tracking-wide inline-block">
                  {{ session.user?.role }}
                </span>
              </div>
            </div>
          </div>
          <button
            class="text-slate-400 hover:text-rose-600 hover:bg-rose-50 p-1.5 rounded-xl transition-colors cursor-pointer flex-shrink-0"
            :disabled="busy"
            title="Sign out"
            aria-label="Sign out"
            @click="logout"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>

        <!-- Collapsed User Profile (Icon only) -->
        <div v-else class="flex flex-col items-center gap-2">
          <div 
            class="w-8 h-8 rounded-xl bg-gradient-to-br from-sky-500 to-sky-600 text-white font-black text-xs flex items-center justify-center shadow-2xs uppercase"
            :title="`${session.user?.name || ''} (${session.user?.email || ''}) - ${session.user?.role || ''}`"
          >
            {{ session.user?.name ? session.user.name.charAt(0) : 'A' }}
          </div>
          <button
            class="text-slate-400 hover:text-rose-600 hover:bg-rose-50 p-2 rounded-xl transition-colors cursor-pointer"
            :disabled="busy"
            title="Sign out"
            aria-label="Sign out"
            @click="logout"
          >
            <LogOut class="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>

    <!-- Mobile Top Header Bar (With Logo) -->
    <header
      v-if="(session.user?.role === 'admin' || session.user?.role === 'superadmin') && !session.denied"
      class="md:hidden h-11 px-3 bg-white text-slate-900 flex items-center justify-between sticky top-0 z-30 border-b border-slate-200 shadow-2xs flex-shrink-0"
    >
      <div class="flex items-center gap-1.5">
        <img src="/admit-trading.png" alt="ADMIT Trading" class="h-5 w-auto object-contain" />
        <span class="px-1.5 py-0.5 text-[9px] font-extrabold rounded bg-sky-50 text-sky-700 border border-sky-200 uppercase tracking-wider">
          Admin
        </span>
      </div>
      <button
        type="button"
        class="p-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 transition cursor-pointer"
        aria-label="Open menu"
        @click="isDrawerOpen = true"
      >
        <Menu class="w-4 h-4" />
      </button>
    </header>

    <!-- Mobile Slide-In Drawer Backdrop -->
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isDrawerOpen"
        class="fixed inset-0 bg-slate-950/40 backdrop-blur-xs z-40 md:hidden"
        @click="isDrawerOpen = false"
      ></div>
    </Transition>

    <!-- Mobile Slide-In Drawer Content -->
    <Transition
      enter-active-class="transition-transform duration-200 ease-out"
      enter-from-class="-translate-x-full"
      enter-to-class="translate-x-0"
      leave-active-class="transition-transform duration-150 ease-in"
      leave-from-class="translate-x-0"
      leave-to-class="-translate-x-full"
    >
      <aside
        v-if="isDrawerOpen"
        class="fixed inset-y-0 left-0 w-72 max-w-[85vw] bg-white text-slate-800 p-4 z-50 flex flex-col justify-between shadow-2xl md:hidden select-none border-r border-slate-200"
      >
        <div class="space-y-5">
          <!-- Drawer Header -->
          <div class="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <img src="/admit-trading.png" alt="ADMIT Trading" class="h-6 w-auto object-contain" />
              <p class="text-[10px] text-slate-500 font-medium m-0 mt-1">Admin Portal</p>
            </div>
            <button
              type="button"
              class="p-1.5 text-slate-400 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition cursor-pointer"
              aria-label="Close menu"
              @click="isDrawerOpen = false"
            >
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Drawer Navigation -->
          <nav class="space-y-1" aria-label="Administration Mobile">
            <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 mb-1.5">Navigation</div>
            <RouterLink
              v-for="item in links"
              :key="item.path"
              :to="item.path"
              class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              active-class="!bg-sky-50 !text-sky-700 !font-bold !border !border-sky-200/80 shadow-2xs"
              @click="isDrawerOpen = false"
            >
              <component
                :is="item.icon"
                class="w-4 h-4 flex-shrink-0"
                :class="route.path === item.path ? 'text-sky-600' : 'text-slate-400'"
              />
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>
        </div>

        <!-- Drawer Footer -->
        <div class="pt-3 border-t border-slate-100 space-y-3">
          <div class="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs font-bold text-slate-900 break-words">{{ session.user?.name }}</span>
              <span class="text-[9px] font-extrabold bg-sky-50 text-sky-700 border border-sky-200 px-2 py-0.5 rounded-md uppercase tracking-wider shrink-0">{{ session.user?.role }}</span>
            </div>
            <p v-if="session.user?.email" class="text-[11px] text-slate-500 font-mono break-all m-0">
              {{ session.user?.email }}
            </p>
          </div>
          <button
            type="button"
            class="w-full py-2.5 px-3 bg-rose-50 text-rose-700 hover:bg-rose-100 text-xs font-bold rounded-xl border border-rose-200 flex items-center justify-center gap-2 transition cursor-pointer"
            :disabled="busy"
            @click="logout"
          >
            <LogOut class="w-3.5 h-3.5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>
    </Transition>

    <!-- Main Workspace Container -->
    <div class="flex-1 flex flex-col min-w-0 bg-slate-100/60 min-h-screen overflow-x-hidden">
      <main id="main" class="flex-1 p-3.5 sm:p-6 lg:p-8 xl:p-10 w-full max-w-[1560px] mx-auto" tabindex="-1">
        <TaskNotice :busy="busy" :error="error" />
        <div v-if="session.error" class="notice error" role="alert">
          {{ session.error }} <button class="secondary" @click="bootstrap">Retry session</button>
        </div>
        <RouterView
          v-if="!route.meta.admin || ((session.user?.role === 'admin' || session.user?.role === 'superadmin') && !session.denied)"
          :key="epoch"
        />
      </main>
    </div>
  </div>
</template>
