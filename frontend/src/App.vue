<template>
  <div class="min-h-screen bg-slate-50 flex flex-col font-sans">
    
    <!-- Top Navigation Header -->
    <Navbar />

    <!-- Main Content Area -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
      
      <!-- Validation Error Banner -->
      <ValidationBanner :message="store.validationError" />

      <!-- Loading Spinner Overlay -->
      <div v-if="store.isLoading" class="flex flex-col items-center justify-center py-24 space-y-4">
        <div class="w-12 h-12 border-4 border-sky-600 border-t-transparent rounded-full animate-spin"></div>
        <p class="text-sm font-semibold text-slate-700 animate-pulse">Running 5-Stage Trade Data ETL & AI Analytics...</p>
      </div>

      <!-- Routed Page Views (Home, Category Detail, Commodity Detail, Compare) -->
      <router-view v-else />

    </main>

    <!-- Floating RAG Chatbot Drawer Component -->
    <ChatbotDrawer />

  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useDatasetStore } from './stores/datasetStore';
import Navbar from './components/common/Navbar.vue';
import ValidationBanner from './components/common/ValidationBanner.vue';
import ChatbotDrawer from './components/chat/ChatbotDrawer.vue';

const store = useDatasetStore();

onMounted(() => {
  store.fetchMasterData();
});
</script>
