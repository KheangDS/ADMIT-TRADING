<script setup lang="ts">
defineProps<{ busy?: boolean; error?: string; notice?: string }>();
</script>
<template>
  <p v-if="busy" class="notice" role="status">Working… Please wait.</p>
  <p v-if="error" class="notice error" role="alert">{{ error }}</p>
  <p v-if="notice" class="notice success" role="status">{{ notice }}</p>
</template>
