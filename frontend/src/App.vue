<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    <Navbar />
    <main class="flex-1 max-w-7xl w-full mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
      <div v-if="!auth.bootstrapped" class="py-24 text-center text-slate-600" role="status">Checking your session…</div>
      <template v-else>
        <div v-if="auth.error" class="notice mb-4" role="alert">{{ auth.error }} <button class="underline" @click="auth.bootstrap(true)">Retry session check</button></div>
        <div v-if="$route.meta.analytics && auth.canAccessMembers && store.publicationNotice" class="mb-4">
          <div class="notice" role="status">{{ store.publicationNotice }}</div>
        </div>
        <ValidationBanner v-if="$route.meta.analytics" :message="store.validationError" />
        <div v-if="$route.meta.analytics && store.isLoading && !store.hasLoaded" class="flex flex-col items-center justify-center py-24 space-y-4" role="status">
          <div class="w-12 h-12 border-4 border-sky-600 border-t-transparent rounded-full animate-spin"></div>
          <p class="text-sm font-semibold text-slate-700">Loading published trade analytics…</p>
        </div>
        <router-view v-else :key="$route.path" />
      </template>
    </main>
    <Footer />
    <CookieBanner />
    <ChatbotDrawer v-if="$route.meta.analytics && auth.canAccessMembers && store.dashboardData.is_valid_trade_data" />
  </div>
</template>
<script setup lang="ts">
import { watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from './stores/authStore';
import { useDatasetStore } from './stores/datasetStore';
import { onPrivateReset } from './services/privateState';
import Navbar from './components/common/Navbar.vue';
import Footer from './components/common/Footer.vue';
import CookieBanner from './components/common/CookieBanner.vue';
import ValidationBanner from './components/common/ValidationBanner.vue';
import ChatbotDrawer from './components/chat/ChatbotDrawer.vue';

const store = useDatasetStore();
const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

function loadAnalyticsIfNeeded() {
  if (route.meta.analytics && auth.canAccessMembers && auth.bootstrapped) {
    void store.fetchMasterData(false);
  }
}

watch(() => [route.meta.analytics, auth.canAccessMembers, auth.bootstrapped], loadAnalyticsIfNeeded, { immediate: true });

const stopPrivateReset = onPrivateReset(reason => {
  if (route.meta.member || (reason !== 403 && route.meta.authenticated)) {
    void router.replace(reason === 403 ? '/account' : { path: '/login', query: { return_to: route.fullPath } });
  }
});

onUnmounted(() => {
  stopPrivateReset();
});
</script>
