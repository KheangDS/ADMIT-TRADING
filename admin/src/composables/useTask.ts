import { ref } from 'vue';
import { blobError } from '../api';
export function useTask() {
  const busy = ref(false);
  const error = ref('');
  const notice = ref('');
  async function run(task: () => Promise<void>, success = '') {
    if (busy.value) return;
    busy.value = true;
    error.value = '';
    notice.value = '';
    try {
      await task();
      if (success && !error.value) notice.value = success;
    } catch (failure) {
      error.value = await blobError(failure);
    } finally {
      busy.value = false;
    }
  }
  return { busy, error, notice, run };
}
