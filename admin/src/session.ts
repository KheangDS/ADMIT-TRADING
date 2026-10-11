import { reactive } from 'vue';
import type { AuthResponse } from './types';
export const session = reactive<AuthResponse & { ready: boolean; error: string; denied: boolean }>({
  user: null,
  membership: null,
  csrf_token: null,
  ready: false,
  error: '',
  denied: false,
});
export function clearSession() {
  session.user = null;
  session.membership = null;
  session.csrf_token = null;
}
