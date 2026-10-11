import { onMounted, onUnmounted } from 'vue';
export function usePolling(refresh: () => Promise<void>, milliseconds = 60000) {
  let timer: ReturnType<typeof setInterval> | undefined;
  onMounted(() => {
    timer = setInterval(() => {
      if (document.visibilityState === 'visible') void refresh();
    }, milliseconds);
  });
  onUnmounted(() => {
    if (timer) clearInterval(timer);
  });
}
