<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-14rem)] py-4 sm:py-8 w-full">
    <!-- Single Banner Hero Auth Workspace -->
    <div class="w-full max-w-md lg:max-w-6xl mx-auto bg-white rounded-3xl shadow-2xl border border-slate-200/90 overflow-hidden grid lg:grid-cols-12 min-h-0 lg:min-h-[640px]">
      
      <!-- Left Column: Intelligent Trade Showcase Banner (Desktop Only) -->
      <div class="hidden lg:flex lg:col-span-6 xl:col-span-7 bg-gradient-to-br from-slate-950 via-slate-900 to-sky-950 text-white p-6 sm:p-10 lg:p-12 relative flex-col justify-between overflow-hidden">
        <!-- Ambient Glow Effects -->
        <div class="absolute -top-16 -left-16 w-80 h-80 bg-sky-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-16 -right-16 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>

        <!-- Top Header & Brand Pitch -->
        <div class="relative z-10">
          <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/10 text-sky-300 border border-white/15 text-xs font-bold tracking-wide backdrop-blur-md">
            <SparklesIcon class="w-3.5 h-3.5 text-sky-400 animate-pulse" />
            <span>Cambodian Agricultural Trade Intelligence</span>
          </div>
        </div>

        <!-- High-Resolution Vector Dashboard Animation Showcase -->
        <div class="my-3 relative z-10 flex flex-col items-center justify-center p-3 sm:p-4 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 shadow-xl overflow-hidden">
          <div class="absolute inset-0 bg-gradient-to-tr from-sky-500/10 via-transparent to-indigo-500/10 pointer-events-none"></div>
          
          <!-- Top Mini Badge inside animation frame -->
          <div class="w-full flex items-center justify-between border-b border-white/10 pb-2 mb-1">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span class="text-[11px] font-bold text-slate-200">Live Trade Intelligence</span>
            </div>
            <span class="text-[10px] font-mono text-sky-300 bg-sky-950/80 px-2 py-0.5 rounded-md border border-sky-500/30">
              MEF Sync Active
            </span>
          </div>

          <!-- Ultra-Crisp Vector SVG Animated Dashboard -->
          <div class="w-full flex items-center justify-center py-1">
            <DashboardAnimation />
          </div>

          <!-- Live Feature Badges Row -->
          <div class="w-full grid grid-cols-3 gap-2 pt-2.5 mt-1 border-t border-white/10 text-[10px] text-slate-300 text-center font-medium">
            <div class="p-1.5 rounded-lg bg-white/5 border border-white/5">
              <span class="text-sky-300 font-bold block">HS4/HS8</span>
              <span class="text-slate-400 text-[9px]">Granularity</span>
            </div>
            <div class="p-1.5 rounded-lg bg-white/5 border border-white/5">
              <span class="text-emerald-300 font-bold block">AI Agent</span>
              <span class="text-slate-400 text-[9px]">Grounded</span>
            </div>
            <div class="p-1.5 rounded-lg bg-white/5 border border-white/5">
              <span class="text-indigo-300 font-bold block">PDF Hub</span>
              <span class="text-slate-400 text-[9px]">Reports</span>
            </div>
          </div>
        </div>

        <!-- Trust Badges Footer -->
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-slate-400 font-medium relative z-10 pt-2 border-t border-white/10">
          <span class="inline-flex items-center gap-1">
            <CheckCircle2Icon class="w-3.5 h-3.5 text-emerald-400" />
            Transparent USD Pricing
          </span>
          <span class="inline-flex items-center gap-1">
            <CheckCircle2Icon class="w-3.5 h-3.5 text-emerald-400" />
            Live MEF Rates
          </span>
          <span class="inline-flex items-center gap-1">
            <CheckCircle2Icon class="w-3.5 h-3.5 text-emerald-400" />
            Verified ABA QR
          </span>
        </div>
      </div>

      <!-- Right Column: Authentication Form Workspace -->
      <div class="lg:col-span-6 xl:col-span-5 p-6 sm:p-10 lg:p-12 flex flex-col justify-center bg-white w-full">
        
        <!-- Authenticated State View -->
        <template v-if="auth.user">
          <div class="space-y-6 my-auto text-center py-6">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white flex items-center justify-center font-black text-2xl mx-auto shadow-lg">
              {{ (auth.user.name || auth.user.email || 'U').charAt(0).toUpperCase() }}
            </div>

            <div class="space-y-2">
              <span 
                class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold"
                :class="auth.canAccessMembers 
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                  : 'bg-slate-100 text-slate-700 border border-slate-200'"
              >
                <span class="w-2 h-2 rounded-full" :class="auth.canAccessMembers ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                {{ auth.user.role === 'admin' ? 'Administrator' : auth.membership?.active ? 'Active Member' : 'Free Account' }}
              </span>
              <h2 class="text-xl font-bold text-slate-900">Welcome back, {{ auth.user.name || 'Member' }}!</h2>
              <p class="text-xs text-slate-500 font-mono">{{ auth.user.email }}</p>
            </div>

            <div class="space-y-3 pt-2 max-w-xs mx-auto">
              <router-link 
                v-if="auth.canAccessMembers" 
                to="/dashboard"
                class="w-full primary-button py-2.5 text-xs font-bold justify-center shadow-md cursor-pointer inline-flex items-center gap-2"
              >
                <LayoutDashboardIcon class="w-4 h-4" />
                <span>Open Member Dashboard</span>
              </router-link>

              <router-link 
                to="/account"
                class="w-full secondary-button py-2.5 text-xs font-bold justify-center border border-slate-300 text-slate-700 hover:bg-slate-50 cursor-pointer inline-flex items-center gap-2"
              >
                <UserIcon class="w-4 h-4 text-slate-500" />
                <span>Account Profile & History</span>
              </router-link>

              <router-link 
                to="/plans"
                class="w-full secondary-button py-2.5 text-xs font-bold justify-center border border-slate-300 text-slate-700 hover:bg-slate-50 cursor-pointer inline-flex items-center gap-2"
              >
                <LayersIcon class="w-4 h-4 text-slate-500" />
                <span>Upgrade / Membership Plans</span>
              </router-link>

              <button
                @click="handleSignOut"
                :disabled="signingOut"
                class="w-full py-2.5 text-xs font-bold text-red-600 hover:bg-red-50 rounded-xl transition-colors cursor-pointer inline-flex items-center justify-center gap-2 border border-red-200"
              >
                <LogOutIcon class="w-4 h-4 text-red-500" />
                <span>{{ signingOut ? 'Signing out…' : 'Sign Out' }}</span>
              </button>
            </div>
          </div>
        </template>

        <!-- Unauthenticated Form View -->
        <template v-else>
          <div class="space-y-6">
            
            <!-- Form Header -->
            <div class="space-y-1 text-center sm:text-left">
              <h2 class="text-2xl font-black text-slate-900 tracking-tight">
                {{ mode === 'login' ? 'Sign in to your account' : 'Create member account' }}
              </h2>
            </div>

            <!-- Success & Info Banner (No emojis) -->
            <div v-if="forgotSuccessMessage" class="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold leading-relaxed">
              {{ forgotSuccessMessage }}
            </div>

            <!-- Error Banner -->
            <div v-if="$route.query.error || auth.error || localError" class="notice text-xs" role="alert">
              {{ localError || auth.error || oauthErrorMessage }}
            </div>

            <!-- Single Banner Mode Switcher Pill -->
            <div class="flex p-1 bg-slate-100/90 rounded-2xl border border-slate-200/80">
              <button
                type="button"
                :class="['flex-1 py-2 text-xs font-bold rounded-xl text-center transition-all cursor-pointer', mode === 'login' ? 'bg-white text-sky-700 shadow-xs border border-slate-200/80' : 'text-slate-500 hover:text-slate-900']"
                @click="switchMode('login')"
              >
                Sign In
              </button>
              <button
                type="button"
                :class="['flex-1 py-2 text-xs font-bold rounded-xl text-center transition-all cursor-pointer', mode === 'register' ? 'bg-white text-sky-700 shadow-xs border border-slate-200/80' : 'text-slate-500 hover:text-slate-900']"
                @click="switchMode('register')"
              >
                Create Account
              </button>
            </div>

            <!-- Credentials Form -->
            <form class="space-y-3.5 pt-1" @submit.prevent="handleSubmit">
              <!-- Name Input (Register Mode) -->
              <div v-if="mode === 'register'" class="space-y-1.5 text-left">
                <label class="field-label text-xs">Full Name</label>
                <div class="relative flex items-center">
                  <span class="absolute left-3.5 text-slate-400 pointer-events-none flex items-center justify-center">
                    <UserIcon class="w-4 h-4" />
                  </span>
                  <input
                    v-model="name"
                    type="text"
                    placeholder="e.g. Sok Dara"
                    required
                    class="block w-full rounded-xl border border-slate-300 bg-slate-50 pl-11 pr-3.5 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition-all"
                  />
                </div>
              </div>

              <!-- Email Input -->
              <div class="space-y-1.5 text-left">
                <label class="field-label text-xs">Email Address</label>
                <div class="relative flex items-center">
                  <span class="absolute left-3.5 text-slate-400 pointer-events-none flex items-center justify-center">
                    <MailIcon class="w-4 h-4" />
                  </span>
                  <input
                    v-model="email"
                    type="email"
                    placeholder="user@example.com"
                    required
                    autocomplete="email"
                    class="block w-full rounded-xl border border-slate-300 bg-slate-50 pl-11 pr-3.5 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition-all"
                  />
                </div>
              </div>

              <!-- Password Input -->
              <div class="space-y-1.5 text-left">
                <div class="flex items-center justify-between">
                  <label class="field-label text-xs">Password</label>
                  <button
                    v-if="mode === 'login'"
                    type="button"
                    class="text-[11px] font-semibold text-sky-600 hover:text-sky-700 hover:underline cursor-pointer focus:outline-none"
                    :disabled="forgotBusy"
                    @click="handleForgotPassword"
                  >
                    {{ forgotBusy ? 'Sending link…' : 'Forgot password?' }}
                  </button>
                </div>
                <div class="relative flex items-center">
                  <span class="absolute left-3.5 text-slate-400 pointer-events-none flex items-center justify-center">
                    <LockIcon class="w-4 h-4" />
                  </span>
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="At least 8 characters"
                    required
                    autocomplete="current-password"
                    class="block w-full rounded-xl border border-slate-300 bg-slate-50 pl-11 pr-11 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition-all"
                  />
                  <button
                    type="button"
                    class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-700 focus:outline-none transition-colors cursor-pointer rounded-lg hover:bg-slate-200/60"
                    :aria-label="showPassword ? 'Hide password' : 'Show password'"
                    @click="showPassword = !showPassword"
                  >
                    <EyeOffIcon v-if="showPassword" class="w-4 h-4" />
                    <EyeIcon v-else class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <!-- Submit Button -->
              <button
                type="submit"
                class="w-full primary-button py-2.5 text-xs font-bold shadow-md hover:shadow transition-all cursor-pointer justify-center"
                :disabled="busy"
              >
                <span v-if="busy" class="inline-flex items-center gap-2">
                  <span class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Processing…</span>
                </span>
                <span v-else>
                  {{ mode === 'login' ? 'Sign In to Workspace' : 'Create Member Account' }}
                </span>
              </button>
            </form>

            <!-- Social Auth Divider -->
            <div class="relative flex py-1 items-center">
              <div class="flex-grow border-t border-slate-200"></div>
              <span class="flex-shrink mx-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Or continue with</span>
              <div class="flex-grow border-t border-slate-200"></div>
            </div>

            <!-- Google OAuth Sign In -->
            <a 
              class="w-full secondary-button justify-center py-2.5 border border-slate-200 hover:border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-bold shadow-2xs transition-all flex items-center" 
              :href="signInUrl"
            >
              <svg class="w-4 h-4 mr-2" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
              </svg>
              <span>Sign in with Google</span>
            </a>
          </div>
        </template>

        <!-- Footer Plans Link -->
        <div class="text-center pt-4 border-t border-slate-100 mt-6">
          <router-link class="text-xs font-bold text-sky-700 hover:text-sky-800 hover:underline inline-flex items-center gap-1" to="/plans">
            <span>Explore membership plans & pricing</span>
            <ArrowRightIcon class="w-3.5 h-3.5" />
          </router-link>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { 
  Sparkles as SparklesIcon, 
  Eye as EyeIcon, 
  EyeOff as EyeOffIcon,
  User as UserIcon,
  Mail as MailIcon,
  Lock as LockIcon,
  ArrowRight as ArrowRightIcon,
  CheckCircle2 as CheckCircle2Icon,
  Layers as LayersIcon,
  LayoutDashboard as LayoutDashboardIcon,
  LogOut as LogOutIcon
} from 'lucide-vue-next';
import { apiError, googleSignInUrl } from '../services/api';
import { useAuthStore } from '../stores/authStore';
import DashboardAnimation from '../components/dashboard/DashboardAnimation.vue';

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const mode = ref<'login' | 'register'>('login');
const name = ref('');
const email = ref('');
const password = ref('');
const showPassword = ref(false);
const busy = ref(false);
const forgotBusy = ref(false);
const signingOut = ref(false);
const localError = ref('');
const forgotSuccessMessage = ref('');

const targetPath = computed(() => (typeof route.query.return_to === 'string' ? route.query.return_to : '/account'));
const signInUrl = computed(() => googleSignInUrl(targetPath.value));

const oauthErrorMessage = computed(() => {
  const err = route.query.error;
  if (err === 'access_denied') {
    return 'Google sign-in was cancelled or access was denied. If your Google Cloud project is in Testing mode, ensure your email is added under Test Users in Google Cloud Console.';
  }
  if (err) {
    return `Google sign-in could not be completed (${err}). Please try again.`;
  }
  return 'Google sign-in could not be completed. Please try again.';
});

function switchMode(newMode: 'login' | 'register') {
  mode.value = newMode;
  localError.value = '';
  forgotSuccessMessage.value = '';
}

async function handleForgotPassword() {
  localError.value = '';
  forgotSuccessMessage.value = '';
  const targetEmail = email.value.trim();
  if (!targetEmail) {
    localError.value = 'Please enter your email address in the field above to receive the password reset link.';
    return;
  }
  forgotBusy.value = true;
  try {
    const res = await auth.forgotPassword(targetEmail);
    forgotSuccessMessage.value = res.message || 'A password reset link has been sent to your email address. Please check your inbox and spam folder.';
  } catch (err) {
    localError.value = apiError(err, 'Unable to process password reset request. Please try again.');
  } finally {
    forgotBusy.value = false;
  }
}

async function handleSignOut() {
  signingOut.value = true;
  localError.value = '';
  try {
    await auth.logout();
    await router.replace('/');
  } catch (err) {
    localError.value = apiError(err, 'Failed to sign out. Please retry.');
  } finally {
    signingOut.value = false;
  }
}

async function handleSubmit() {
  localError.value = '';
  busy.value = true;
  try {
    if (mode.value === 'register') {
      if (!name.value.trim()) {
        localError.value = 'Please enter your name';
        return;
      }
      if (password.value.length < 8) {
        localError.value = 'Password must be at least 8 characters';
        return;
      }
      await auth.register(name.value.trim(), email.value.trim(), password.value);
    } else {
      await auth.login(email.value.trim(), password.value);
    }
    router.push(targetPath.value);
  } catch (err) {
    localError.value = apiError(err, 'Authentication failed. Please check your credentials.');
  } finally {
    busy.value = false;
  }
}
</script>
