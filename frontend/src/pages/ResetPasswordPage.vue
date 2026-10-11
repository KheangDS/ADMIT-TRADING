<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-14rem)] py-8 w-full">
    <div class="w-full max-w-md mx-auto bg-white rounded-3xl shadow-2xl border border-slate-200/90 p-6 sm:p-10 space-y-6">
      
      <!-- Brand & Header -->
      <div class="text-center space-y-2">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-indigo-600 text-white font-black text-xl shadow-md mx-auto mb-1">
          <LockIcon class="w-6 h-6 text-white" />
        </div>
        <h1 class="text-2xl font-black text-slate-900 tracking-tight">Reset Your Password</h1>
        <p class="text-xs text-slate-500">
          Enter a new secure password for your ADMIT TRADING account.
        </p>
      </div>

      <!-- Notice / Error / Success Messages (No emojis) -->
      <div v-if="successMessage" class="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold leading-relaxed">
        {{ successMessage }}
      </div>

      <div v-if="errorMessage" class="notice text-xs" role="alert">
        {{ errorMessage }}
      </div>

      <!-- Reset Form -->
      <form v-if="!successMessage && isValidToken" class="space-y-4" @submit.prevent="handleReset">
        
        <!-- New Password Input -->
        <div class="space-y-1.5 text-left">
          <label class="field-label text-xs">New Password</label>
          <div class="relative flex items-center">
            <span class="absolute left-3.5 text-slate-400 pointer-events-none flex items-center justify-center">
              <LockIcon class="w-4 h-4" />
            </span>
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="At least 8 characters"
              required
              autocomplete="new-password"
              class="block w-full rounded-xl border border-slate-300 bg-slate-50 pl-11 pr-11 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition-all"
            />
            <button
              type="button"
              class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-700 focus:outline-none transition-colors cursor-pointer rounded-lg hover:bg-slate-200/60"
              @click="showPassword = !showPassword"
            >
              <EyeOffIcon v-if="showPassword" class="w-4 h-4" />
              <EyeIcon v-else class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Confirm New Password Input -->
        <div class="space-y-1.5 text-left">
          <label class="field-label text-xs">Confirm New Password</label>
          <div class="relative flex items-center">
            <span class="absolute left-3.5 text-slate-400 pointer-events-none flex items-center justify-center">
              <LockIcon class="w-4 h-4" />
            </span>
            <input
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Re-enter password"
              required
              autocomplete="new-password"
              class="block w-full rounded-xl border border-slate-300 bg-slate-50 pl-11 pr-3.5 py-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white transition-all"
            />
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
            <span>Resetting password…</span>
          </span>
          <span v-else>
            Save New Password &amp; Continue
          </span>
        </button>

      </form>

      <!-- Invalid Token Fallback CTA -->
      <div v-if="!isValidToken && !successMessage" class="text-center pt-2">
        <router-link to="/login" class="primary-button py-2.5 text-xs font-bold justify-center w-full shadow-md">
          Return to Sign In
        </router-link>
      </div>

      <!-- Back to Login Link -->
      <div class="text-center pt-3 border-t border-slate-100">
        <router-link to="/login" class="text-xs font-bold text-sky-700 hover:text-sky-800 hover:underline inline-flex items-center gap-1">
          <ArrowLeftIcon class="w-3.5 h-3.5" />
          <span>Back to Sign In</span>
        </router-link>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Lock as LockIcon, Eye as EyeIcon, EyeOff as EyeOffIcon, ArrowLeft as ArrowLeftIcon } from 'lucide-vue-next';
import { apiError } from '../services/api';
import { useAuthStore } from '../stores/authStore';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const token = ref('');
const password = ref('');
const confirmPassword = ref('');
const showPassword = ref(false);
const busy = ref(false);
const isValidToken = ref(true);
const errorMessage = ref('');
const successMessage = ref('');

onMounted(() => {
  const queryToken = route.query.token;
  if (!queryToken || typeof queryToken !== 'string' || queryToken.trim().length < 10) {
    isValidToken.value = false;
    errorMessage.value = 'Invalid or missing password reset link. Please request a new link from the sign in page.';
  } else {
    token.value = queryToken.trim();
  }
});

async function handleReset() {
  errorMessage.value = '';
  if (password.value.length < 8) {
    errorMessage.value = 'Password must be at least 8 characters long.';
    return;
  }
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match. Please verify and try again.';
    return;
  }

  busy.value = true;
  try {
    const res = await auth.resetPassword(token.value, password.value);
    successMessage.value = res.message || 'Your password has been successfully reset. Redirecting to sign in...';
    setTimeout(() => {
      router.push('/login');
    }, 2500);
  } catch (err) {
    errorMessage.value = apiError(err, 'Failed to reset password. The link may be expired or already used.');
  } finally {
    busy.value = false;
  }
}
</script>

