import { computed, onMounted, onUnmounted, ref } from 'vue';
import { useMemberStore } from '../stores/memberStore';
import { useAuthStore } from '../stores/authStore';
import { apiError } from '../services/api';
export function usePaymentPolling() {
  const member = useMemberStore();
  const auth = useAuthStore();
  const loading = ref(true);
  const error = ref('');
  const now = ref(Date.now());
  let timer: ReturnType<typeof setTimeout> | undefined;
  let disposed = false;
  let busy = false;
  const shouldPoll = computed(() => member.payments.some(p => p.status === 'created' || p.status === 'submitted') || member.receipts.some(r => r.pdf_status === 'pending' || r.email_status === 'pending'));
  async function refresh() {
    if (busy || disposed || !auth.user) return;
    busy = true;
    error.value = '';
    try { await member.loadPayments(); if (!disposed) await auth.bootstrap(true); }
    catch (err) { if (!disposed) error.value = apiError(err); }
    finally { busy = false; if (!disposed) { loading.value = false; now.value = Date.now(); } }
  }
  async function tick() {
    if (disposed) return;
    now.value = Date.now();
    if (!document.hidden && shouldPoll.value) await refresh();
    if (!disposed && auth.user) timer = setTimeout(tick, 30000);
  }
  onMounted(async () => { await refresh(); if (!disposed) timer = setTimeout(tick, 30000); });
  onUnmounted(() => { disposed = true; clearTimeout(timer); });
  return { member, loading, error, now, refresh };
}
