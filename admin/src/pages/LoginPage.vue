<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Eye, EyeOff, ShieldCheck } from 'lucide-vue-next';
import { loginWithPassword, errorText } from '../api';
import { session } from '../session';

const router = useRouter();
const route = useRoute();
const email = ref('');
const password = ref('');
const showPassword = ref(false);
const busy = ref(false);
const localError = ref('');

const returnTo = computed(() => {
  const target = route.query.return_to;
  if (typeof target === 'string' && target.startsWith('/') && !target.startsWith('//') && target !== '/login') {
    return target;
  }
  return '/imports';
});

async function handlePasswordLogin() {
  if (!email.value.trim() || !password.value) {
    localError.value = 'Please enter both email and password.';
    return;
  }
  busy.value = true;
  localError.value = '';
  try {
    const res = await loginWithPassword(email.value.trim(), password.value);
    if (res.user?.role === 'admin' || res.user?.role === 'superadmin') {
      router.push(returnTo.value);
    } else {
      localError.value = 'Access denied. This account does not have administrator privileges.';
    }
  } catch (err) {
    localError.value = errorText(err);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="min-h-[70vh] flex items-center justify-center p-2 sm:p-4">
    <section class="card login w-full max-w-md p-6 sm:p-8 rounded-2xl shadow-xl border border-slate-200/90 my-0">
      <div class="text-center mb-5">
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-sky-100 text-sky-700 mb-3 shadow-2xs">
          <ShieldCheck class="w-6 h-6" />
        </div>
        <h1 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight m-0">Administrator Sign In</h1>
      </div>

      <div
        v-if="localError || session.denied || (session.user && session.user.role !== 'admin' && session.user.role !== 'superadmin')"
        class="notice error"
        role="alert"
      >
        <strong>Access denied.</strong> {{ localError || 'This account is not authorized. Contact the operator to review privileges.' }}
      </div>

      <template v-if="(session.user?.role === 'admin' || session.user?.role === 'superadmin') && !session.denied">
        <RouterLink class="button w-full text-center" to="/imports">Open portal</RouterLink>
      </template>
      
      <template v-else>
        <form class="space-y-4 my-4" @submit.prevent="handlePasswordLogin">
          <label>
            Admin Email
            <input v-model="email" type="text" placeholder="admin@agritrade" required autocomplete="username" />
          </label>
          <label>
            Password
            <div class="password-field">
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                required
                autocomplete="current-password"
              />
              <button
                type="button"
                class="password-toggle-btn"
                :aria-label="showPassword ? 'Hide password' : 'Show password'"
                @click="showPassword = !showPassword"
              >
                <EyeOff v-if="showPassword" class="w-4 h-4" />
                <Eye v-else class="w-4 h-4" />
              </button>
            </div>
          </label>
          <button type="submit" class="button w-full" :disabled="busy">
            {{ busy ? 'Signing in...' : 'Sign in as Administrator' }}
          </button>
        </form>
      </template>
    </section>
  </div>
</template>
