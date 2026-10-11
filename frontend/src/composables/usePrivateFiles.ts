import { onUnmounted, ref } from 'vue';
import { privateBlob, apiError } from '../services/api';
import { onPrivateReset, privateEpoch } from '../services/privateState';
export function usePrivateFiles() {
  const error = ref('');
  const busy = ref(false);
  const previewUrl = ref('');
  const urls = new Set<string>();
  let disposed = false;
  function clear() { for (const url of urls) URL.revokeObjectURL(url); urls.clear(); previewUrl.value = ''; error.value = ''; }
  const off = onPrivateReset(clear);
  onUnmounted(() => { disposed = true; clear(); off(); });
  async function open(path: string, filename?: string) {
    if (busy.value) return;
    const epoch = privateEpoch;
    busy.value = true; error.value = '';
    try {
      const blob = await privateBlob(path);
      if (disposed || epoch !== privateEpoch) return;
      const url = URL.createObjectURL(blob);
      if (filename) {
        urls.add(url);
        const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
        setTimeout(() => { URL.revokeObjectURL(url); urls.delete(url); }, 60000);
      } else { clear(); urls.add(url); previewUrl.value = url; }
    } catch (err) { if (!disposed && epoch === privateEpoch) error.value = apiError(err, 'The file is not ready or is unavailable. Refresh its status and try again.'); }
    finally { busy.value = false; }
  }
  return { error, busy, previewUrl, open, clear };
}
