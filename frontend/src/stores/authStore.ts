import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import type { User, Membership } from '../types/membership';
import { apiError, forgotPasswordApi, getAuth, loginWithPassword, logout as endSession, registerWithPassword, resetPasswordApi, setCsrfToken } from '../services/api';
import { clearPrivateState, onPrivateReset, privateEpoch } from '../services/privateState';

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const membership = ref<Membership | null>(null);
  const bootstrapped = ref(false);
  const error = ref('');
  const canAccessMembers = computed(() => !!user.value && (user.value.role === 'admin' || user.value.role === 'superadmin' || !!membership.value?.active));
  let inFlight: Promise<void> | null = null;
  onPrivateReset(reason => {
    bootstrapped.value = false;
    if (reason !== 403) { user.value = null; membership.value = null; setCsrfToken(null); }
    else if (membership.value) membership.value = { ...membership.value, active: false };
  });
  async function bootstrap(force = false): Promise<void> {
    if (inFlight) return inFlight;
    if (bootstrapped.value && !force) return;
    const epoch = privateEpoch;
    inFlight = (async () => {
      error.value = '';
      try {
        const metadata = await getAuth();
        if (epoch !== privateEpoch) return;
        if (user.value && user.value.id !== metadata.user?.id) clearPrivateState('logout');
        else if (canAccessMembers.value && metadata.user?.role !== 'admin' && metadata.user?.role !== 'superadmin' && !metadata.membership?.active) clearPrivateState(403);
        user.value = metadata.user;
        membership.value = metadata.membership;
        setCsrfToken(metadata.csrf_token);
        if (!metadata.user) clearPrivateState('logout');
      } catch (err) {
        clearPrivateState('logout');
        error.value = apiError(err, 'Unable to check your session. Please retry.');
      } finally { bootstrapped.value = true; inFlight = null; }
    })();
    return inFlight;
  }
  async function login(email: string, password: string) {
    error.value = '';
    const metadata = await loginWithPassword(email, password);
    user.value = metadata.user;
    membership.value = metadata.membership;
    setCsrfToken(metadata.csrf_token);
    bootstrapped.value = true;
    return metadata;
  }
  async function register(name: string, email: string, password: string) {
    error.value = '';
    const metadata = await registerWithPassword(name, email, password);
    user.value = metadata.user;
    membership.value = metadata.membership;
    setCsrfToken(metadata.csrf_token);
    bootstrapped.value = true;
    return metadata;
  }
  async function forgotPassword(email: string) {
    error.value = '';
    return await forgotPasswordApi(email);
  }
  async function resetPassword(token: string, password: string) {
    error.value = '';
    return await resetPasswordApi(token, password);
  }
  async function logout() {
    try { await endSession(); clearPrivateState('logout'); }
    catch (err) { clearPrivateState(403); throw err; }
  }
  return { user, membership, bootstrapped, error, canAccessMembers, bootstrap, login, register, forgotPassword, resetPassword, logout };
});
