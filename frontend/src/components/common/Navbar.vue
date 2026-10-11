<template>
  <header class="bg-white/95 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-40 shadow-xs transition-all">
    <div class="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-3">
      
      <!-- Left: Brand Logo & Intelligence Badge -->
      <div class="flex items-center gap-3 flex-shrink-0">
        <router-link to="/" class="flex items-center gap-2.5 group hover:opacity-95 transition-opacity">
          <img 
            src="/admit-trading.png" 
            alt="ADMIT TRADING" 
            class="h-8 sm:h-9 md:h-10 w-auto object-contain max-w-[140px] sm:max-w-[190px] flex-shrink-0" 
          />
          <div class="hidden 2xl:flex items-center h-7 pl-3 border-l border-slate-200 gap-2">
            <span class="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200/80 whitespace-nowrap">
              <SparklesIcon class="w-3 h-3 text-sky-600" />
              Intelligence
            </span>
            <span class="text-[11px] text-slate-500 font-medium whitespace-nowrap">Agricultural Analytics</span>
          </div>
        </router-link>
      </div>

      <!-- Center: Member Workspace Navigation Links (When Logged In) -->
      <nav v-if="auth.canAccessMembers" class="hidden md:flex items-center gap-1.5 flex-shrink-0" aria-label="Main Navigation">
        <!-- Member Segmented Tabs -->
        <div class="inline-flex items-center p-0.5 bg-slate-100/90 rounded-xl border border-slate-200/80 gap-1 flex-shrink-0">
          <router-link
            to="/dashboard"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap flex-shrink-0 transition-all"
            :class="$route.path === '/dashboard'
              ? 'bg-white text-sky-700 shadow-xs border border-slate-200/80'
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'"
          >
            <LayoutDashboardIcon class="w-3.5 h-3.5 flex-shrink-0" :class="$route.path === '/dashboard' ? 'text-sky-600' : 'text-slate-400'" />
            <span class="whitespace-nowrap">Overview</span>
          </router-link>
          
          <router-link
            to="/compare"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap flex-shrink-0 transition-all"
            :class="$route.path === '/compare' 
              ? 'bg-white text-sky-700 shadow-xs border border-slate-200/80' 
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'"
          >
            <ArrowLeftRightIcon class="w-3.5 h-3.5 flex-shrink-0" :class="$route.path === '/compare' ? 'text-sky-600' : 'text-slate-400'" />
            <span class="whitespace-nowrap">Compare</span>
          </router-link>

          <router-link
            to="/documents"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap flex-shrink-0 transition-all"
            :class="$route.path === '/documents' 
              ? 'bg-white text-sky-700 shadow-xs border border-slate-200/80' 
              : 'text-slate-600 hover:text-slate-900 hover:bg-white/50'"
          >
            <FileTextIcon class="w-3.5 h-3.5 flex-shrink-0" :class="$route.path === '/documents' ? 'text-sky-600' : 'text-slate-400'" />
            <span class="whitespace-nowrap">Documents</span>
          </router-link>
        </div>
      </nav>

      <!-- Right: Period, Exchange Rate, User Menu / Auth CTAs -->
      <div class="flex items-center gap-2 sm:gap-3 flex-shrink-0">
        
        <!-- Live Reporting Period Indicator (Desktop & In Analytics) -->
        <div 
          v-if="auth.canAccessMembers && $route.meta.analytics && liveDisplayPeriod" 
          class="hidden lg:inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-700 shadow-2xs whitespace-nowrap"
        >
          <CalendarIcon class="w-3.5 h-3.5 text-sky-600 flex-shrink-0" />
          <span class="font-bold text-slate-800 text-xs font-mono">{{ liveDisplayPeriod }}</span>
        </div>

        <!-- Exchange Rate Capsule Badge with Live Date & Status Feedback -->
        <div 
          v-if="auth.canAccessMembers && $route.meta.analytics"
          class="hidden sm:inline-flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-xl border shadow-2xs whitespace-nowrap transition-all"
          :class="isLiveRateOnline 
            ? 'bg-slate-50/95 border-slate-200 hover:border-emerald-300' 
            : 'bg-amber-50/80 border-amber-200 hover:border-amber-300'"
        >
          <div class="inline-flex items-center gap-1 text-xs font-bold text-slate-800">
            <CoinsIcon class="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
            <span class="text-slate-500 text-[11px] font-medium">$1 =</span>
            <span class="text-sky-700 font-extrabold font-mono text-xs">
              {{ (store.dashboardData?.exchange_rate || store.exchangeRate).toLocaleString() }}
            </span>
            <span class="text-slate-400 text-[11px] font-medium">៛</span>
          </div>

          <span 
            v-if="isLiveRateOnline" 
            class="inline-flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80"
            :title="`Official exchange rate from Ministry of Economy and Finance (MEF)\nDate: ${formattedRateDate}\nRate: $1 USD = ${(store.dashboardData?.exchange_rate || store.exchangeRate).toLocaleString()} KHR`"
          >
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse flex-shrink-0"></span>
            <span>MEF Live · {{ formattedRateDate }}</span>
          </span>
          <span 
            v-else 
            class="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300"
            :title="rateErrorMessage"
          >
            <span>Fallback</span>
          </span>
        </div>

        <!-- Authenticated User Profile Dropdown / Pill -->
        <div v-if="auth.user" class="relative">
          <button 
            @click="isUserMenuOpen = !isUserMenuOpen"
            type="button"
            class="inline-flex items-center gap-2 pl-2 pr-2.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
            :aria-expanded="isUserMenuOpen"
          >
            <div class="w-6 h-6 rounded-lg bg-gradient-to-tr from-sky-600 to-indigo-600 text-white flex items-center justify-center font-bold text-[11px]">
              {{ (auth.user.name || auth.user.email || 'U').charAt(0).toUpperCase() }}
            </div>
            <span class="hidden sm:inline font-medium text-slate-800 max-w-[110px] truncate">{{ auth.user.name || auth.user.email }}</span>
            <span 
              v-if="auth.canAccessMembers" 
              class="hidden lg:inline-block px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200/80"
            >
              PRO
            </span>
            <ChevronDownIcon class="w-3.5 h-3.5 text-slate-400 transition-transform" :class="isUserMenuOpen ? 'rotate-180' : ''" />
          </button>

          <!-- Dropdown Flyout Menu -->
          <div v-if="isUserMenuOpen" class="fixed inset-0 z-40" @click="isUserMenuOpen = false"></div>
          <div 
            v-if="isUserMenuOpen" 
            class="absolute right-0 mt-2 w-64 rounded-2xl bg-white border border-slate-200/90 shadow-xl py-2 z-50 animate-in fade-in slide-in-from-top-2"
          >
            <!-- User Header Info -->
            <div class="px-4 py-2.5 border-b border-slate-100">
              <p class="font-bold text-slate-900 text-xs truncate">{{ auth.user.name }}</p>
              <p class="text-[11px] text-slate-500 truncate mt-0.5">{{ auth.user.email }}</p>
              <div class="mt-2 flex items-center gap-1.5">
                <span 
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold"
                  :class="auth.canAccessMembers 
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                    : 'bg-slate-100 text-slate-600 border border-slate-200'"
                >
                  <span class="w-1.5 h-1.5 rounded-full" :class="auth.canAccessMembers ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                  {{ auth.user.role === 'admin' ? 'Administrator' : auth.membership?.active ? 'Active Member' : 'Free Account' }}
                </span>
              </div>
            </div>

            <!-- Menu Links -->
            <div class="py-1">
              <router-link 
                to="/account" 
                @click="isUserMenuOpen = false"
                class="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 hover:text-sky-700 font-medium"
              >
                <UserIcon class="w-4 h-4 text-slate-400" />
                <span>Account Profile</span>
              </router-link>
              
              <router-link 
                to="/payments" 
                @click="isUserMenuOpen = false"
                class="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 hover:text-sky-700 font-medium"
              >
                <CreditCardIcon class="w-4 h-4 text-slate-400" />
                <span>Payment History & Receipts</span>
              </router-link>

              <router-link 
                to="/plans" 
                @click="isUserMenuOpen = false"
                class="flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 hover:text-sky-700 font-medium"
              >
                <LayersIcon class="w-4 h-4 text-slate-400" />
                <span>Upgrade / Membership Plans</span>
              </router-link>
            </div>

            <!-- Sign Out Row -->
            <div class="border-t border-slate-100 pt-1">
              <button 
                @click="signOut" 
                :disabled="signingOut"
                class="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-red-600 hover:bg-red-50 font-medium transition-colors cursor-pointer disabled:opacity-50"
              >
                <LogOutIcon class="w-4 h-4 text-red-500" />
                <span>{{ signingOut ? 'Signing out…' : 'Sign Out' }}</span>
              </button>
            </div>
            
            <p v-if="signOutError" class="px-4 py-1 text-[11px] text-red-600" role="alert">{{ signOutError }}</p>
          </div>
        </div>

        <!-- Unauthenticated Public CTAs: Plans & Pricing + Sign In -->
        <template v-else>
          <div class="hidden sm:flex items-center gap-2">
            <router-link
              to="/plans"
              class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all"
              :class="$route.path === '/plans' 
                ? 'bg-sky-50 text-sky-700 border border-sky-200/90 shadow-2xs' 
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 border border-slate-200/80'"
            >
              <LayersIcon class="w-3.5 h-3.5" :class="$route.path === '/plans' ? 'text-sky-600' : 'text-slate-400'" />
              <span>Plans & Pricing</span>
            </router-link>

            <router-link 
              to="/login"
              class="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-sky-700 hover:bg-sky-800 shadow-xs hover:shadow transition-all cursor-pointer whitespace-nowrap"
              :class="$route.path === '/login' ? 'ring-2 ring-sky-600 ring-offset-2' : ''"
            >
              <UserIcon class="w-3.5 h-3.5" />
              <span>Sign In</span>
            </router-link>
          </div>
        </template>

        <!-- Mobile Hamburger Menu Button -->
        <button
          @click="isMobileMenuOpen = !isMobileMenuOpen"
          type="button"
          class="md:hidden cursor-pointer p-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 transition-colors shadow-2xs"
          :aria-expanded="isMobileMenuOpen"
          aria-label="Toggle Navigation Menu"
        >
          <MenuIcon v-if="!isMobileMenuOpen" class="w-5 h-5 text-slate-700" />
          <XIcon v-else class="w-5 h-5 text-slate-700" />
        </button>

      </div>
    </div>

    <!-- Mobile Dropdown Navigation Menu -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform -translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0 opacity-100"
      leave-to-class="transform -translate-y-2 opacity-0"
    >
      <div 
        v-if="isMobileMenuOpen" 
        class="md:hidden border-t border-slate-200 bg-white/98 backdrop-blur-xl px-4 py-4 shadow-lg space-y-3"
      >
        <!-- Nav Links Grid -->
        <div class="grid grid-cols-2 gap-2">
          <router-link
            to="/plans"
            @click="isMobileMenuOpen = false"
            class="flex items-center gap-2 p-2.5 rounded-xl text-xs font-bold transition-all border"
            :class="$route.path === '/plans'
              ? 'bg-sky-50 text-sky-700 border-sky-200'
              : 'bg-slate-50 text-slate-700 border-slate-200/80 hover:bg-slate-100'"
          >
            <LayersIcon class="w-4 h-4 text-sky-600 flex-shrink-0" />
            <span class="truncate">Plans & Pricing</span>
          </router-link>

          <template v-if="auth.canAccessMembers">
            <router-link
              to="/dashboard"
              @click="isMobileMenuOpen = false"
              class="flex items-center gap-2 p-2.5 rounded-xl text-xs font-bold transition-all border"
              :class="$route.path === '/dashboard'
                ? 'bg-sky-50 text-sky-700 border-sky-200'
                : 'bg-slate-50 text-slate-700 border-slate-200/80 hover:bg-slate-100'"
            >
              <LayoutDashboardIcon class="w-4 h-4 text-sky-600" />
              <span>Overview</span>
            </router-link>

            <router-link
              to="/compare"
              @click="isMobileMenuOpen = false"
              class="flex items-center gap-2 p-2.5 rounded-xl text-xs font-bold transition-all border"
              :class="$route.path === '/compare' 
                ? 'bg-sky-50 text-sky-700 border-sky-200' 
                : 'bg-slate-50 text-slate-700 border-slate-200/80 hover:bg-slate-100'"
            >
              <ArrowLeftRightIcon class="w-4 h-4 text-sky-600" />
              <span>Compare</span>
            </router-link>

            <router-link
              to="/documents"
              @click="isMobileMenuOpen = false"
              class="flex items-center gap-2 p-2.5 rounded-xl text-xs font-bold transition-all border"
              :class="$route.path === '/documents' 
                ? 'bg-sky-50 text-sky-700 border-sky-200' 
                : 'bg-slate-50 text-slate-700 border-slate-200/80 hover:bg-slate-100'"
            >
              <FileTextIcon class="w-4 h-4 text-sky-600" />
              <span>Documents</span>
            </router-link>
          </template>
        </div>

        <!-- Authenticated Links -->
        <div v-if="auth.user" class="border-t border-slate-100 pt-3 space-y-1">
          <router-link
            to="/account"
            @click="isMobileMenuOpen = false"
            class="flex items-center justify-between p-2 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <span class="flex items-center gap-2">
              <UserIcon class="w-4 h-4 text-slate-400" />
              Account ({{ auth.user.name || auth.user.email }})
            </span>
            <span class="text-[10px] px-2 py-0.5 rounded-full font-bold" :class="auth.canAccessMembers ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'">
              {{ auth.canAccessMembers ? 'Active' : 'Free' }}
            </span>
          </router-link>

          <router-link
            to="/payments"
            @click="isMobileMenuOpen = false"
            class="flex items-center gap-2 p-2 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <CreditCardIcon class="w-4 h-4 text-slate-400" />
            Payment Status & Receipts
          </router-link>

          <button
            @click="signOut"
            :disabled="signingOut"
            class="w-full flex items-center gap-2 p-2 rounded-lg text-xs font-semibold text-red-600 hover:bg-red-50 text-left"
          >
            <LogOutIcon class="w-4 h-4 text-red-500" />
            {{ signingOut ? 'Signing out…' : 'Sign out' }}
          </button>
        </div>

        <!-- Mobile Sign In Button if not logged in -->
        <div v-else class="border-t border-slate-100 pt-3">
          <router-link
            to="/login"
            @click="isMobileMenuOpen = false"
            class="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-xs font-bold text-white bg-sky-700 hover:bg-sky-800"
          >
            <UserIcon class="w-4 h-4" />
            <span>Sign In / Create Account</span>
          </router-link>
        </div>

        <!-- Period & Exchange Rate Details for Mobile -->
        <div v-if="auth.canAccessMembers && $route.meta.analytics" class="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
          <div class="flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full" :class="isLiveRateOnline ? 'bg-emerald-500' : 'bg-amber-500'"></span>
            <span>MEF {{ isLiveRateOnline ? `Live (${formattedRateDate})` : 'Offline' }}</span>
          </div>
          <div v-if="liveDisplayPeriod" class="font-mono text-slate-600 font-semibold">
            {{ liveDisplayPeriod }}
          </div>
        </div>
      </div>
    </transition>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  LayoutDashboard as LayoutDashboardIcon,
  ArrowLeftRight as ArrowLeftRightIcon,
  FileText as FileTextIcon,
  Layers as LayersIcon,
  Calendar as CalendarIcon,
  Coins as CoinsIcon,
  Sparkles as SparklesIcon,
  Menu as MenuIcon,
  X as XIcon,
  User as UserIcon,
  LogOut as LogOutIcon,
  CreditCard as CreditCardIcon,
  ChevronDown as ChevronDownIcon
} from 'lucide-vue-next';
import { useDatasetStore } from '../../stores/datasetStore';
import { useAuthStore } from '../../stores/authStore';
import { useRouter } from 'vue-router';
import { apiError } from '../../services/api';

const auth = useAuthStore();
const router = useRouter();
const store = useDatasetStore();

const isMobileMenuOpen = ref(false);
const isUserMenuOpen = ref(false);
const signingOut = ref(false);
const signOutError = ref('');

async function signOut() {
  signingOut.value = true;
  signOutError.value = '';
  isUserMenuOpen.value = false;
  isMobileMenuOpen.value = false;
  try { 
    await auth.logout(); 
    await router.replace('/'); 
  }
  catch (err) { 
    signOutError.value = apiError(err, 'Session could not be revoked on the server. Retry signing out.'); 
  }
  finally { 
    signingOut.value = false; 
  }
}

function formatDisplayMonth(ym: string | undefined | null): string {
  if (!ym) return '';
  const clean = ym.trim();
  if (/^\d{4}-\d{2}$/.test(clean)) {
    const [y, m] = clean.split('-').map(Number);
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const monthName = monthNames[m - 1];
    if (monthName) return `${monthName} ${y}`;
  }
  return clean;
}

const liveDisplayPeriod = computed(() => {
  const pub = store.dashboardData?.publication;
  if (pub?.start_month && pub?.end_month) {
    return `${formatDisplayMonth(pub.start_month)} – ${formatDisplayMonth(pub.end_month)}`;
  }
  const begin = store.dashboardData?.begin_date;
  const end = store.dashboardData?.end_date;
  if (begin && end) {
    return `${formatDisplayMonth(begin)} – ${formatDisplayMonth(end)}`;
  }
  return '';
});

const isLiveRateOnline = computed(() => {
  return !!store.dashboardData?.exchange_rate_info?.is_realtime;
});

const formattedRateDate = computed(() => {
  const info = store.dashboardData?.exchange_rate_info;
  const rawDate = info?.valid_date;
  if (rawDate && typeof rawDate === 'string') {
    const parts = rawDate.split('T')[0].split('-');
    if (parts.length === 3) {
      const [y, m, d] = parts.map(Number);
      if (!isNaN(y) && !isNaN(m) && !isNaN(d)) {
        const dt = new Date(y, m - 1, d);
        return dt.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
      }
    }
  }
  return new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
});

const rateErrorMessage = computed(() => {
  const msg = store.dashboardData?.exchange_rate_info?.error_message;
  return msg 
    ? `MEF Live API Notice: ${msg}\nUsing default standard rate: $1 USD = 4,000 KHR.`
    : 'Could not reach MEF Live Exchange Rate API. Using standard fallback rate: $1 USD = 4,000 KHR.';
});
</script>
