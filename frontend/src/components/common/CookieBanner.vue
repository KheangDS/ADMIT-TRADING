<template>
  <Transition name="cookie-slide">
    <div
      v-if="isOpen"
      class="fixed bottom-4 sm:bottom-6 right-4 sm:right-6 left-4 sm:left-auto sm:max-w-md z-50 bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-2xl rounded-2xl p-4 sm:p-5 text-slate-800"
      role="region"
      aria-label="Cookie consent banner"
    >
      <div class="flex items-start gap-3">
        <div class="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200/70 flex items-center justify-center flex-shrink-0 text-amber-600 mt-0.5">
          <CookieIcon class="w-5 h-5" />
        </div>
        <div class="flex-1 space-y-2">
          <div class="flex items-center justify-between gap-2">
            <h4 class="text-sm font-bold text-slate-900 m-0">Cookie & Privacy Notice</h4>
            <button
              class="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors"
              title="Close banner"
              aria-label="Close"
              @click="acceptChoice('essential')"
            >
              <XIcon class="w-4 h-4" />
            </button>
          </div>
          <p class="text-xs text-slate-600 leading-relaxed m-0 text-justify">
            ADMIT Trading uses essential HTTP cookies for secure session authentication and CSRF protection. We do not use third-party advertising or cross-site tracking cookies.
          </p>
          <div class="flex items-center gap-1.5 text-[11px] text-slate-500 pt-0.5">
            <ShieldCheckIcon class="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
            <span>Strictly necessary for login and security.</span>
            <router-link to="/privacy" class="text-sky-600 font-semibold hover:underline ml-auto" @click="isOpen = false">
              Learn more
            </router-link>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2.5 mt-4 pt-3 border-t border-slate-100">
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
          @click="acceptChoice('essential')"
        >
          Essential Only
        </button>
        <button
          type="button"
          class="px-4 py-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 rounded-lg shadow-xs transition-colors flex items-center gap-1.5"
          @click="acceptChoice('accepted')"
        >
          <CheckIcon class="w-3.5 h-3.5" />
          <span>Accept All</span>
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { CookieIcon, ShieldCheckIcon, CheckIcon, XIcon } from 'lucide-vue-next';

const STORAGE_KEY = 'admit_cookie_consent';
const isOpen = ref(false);

function checkConsent() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) {
    isOpen.value = true;
  }
}

function acceptChoice(choice: 'accepted' | 'essential') {
  try {
    const payload = {
      status: choice,
      timestamp: new Date().toISOString(),
      version: '1.0'
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Fallback if local storage is restricted
  }
  isOpen.value = false;
}

function openBanner() {
  isOpen.value = true;
}

onMounted(() => {
  // Check after slight delay for smooth entrance
  setTimeout(checkConsent, 600);
  window.addEventListener('admit:open-cookie-banner', openBanner);
});

onUnmounted(() => {
  window.removeEventListener('admit:open-cookie-banner', openBanner);
});
</script>

<style scoped>
.cookie-slide-enter-active,
.cookie-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.cookie-slide-enter-from,
.cookie-slide-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.97);
}
</style>

