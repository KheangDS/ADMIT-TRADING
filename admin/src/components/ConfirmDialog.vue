<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { Check, AlertTriangle, X } from 'lucide-vue-next';

const props = withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    message?: string;
    busy?: boolean;
    error?: string;
    confirmClass?: string;
    confirmText?: string;
    cancelText?: string;
  }>(),
  {
    message: '',
    confirmClass: 'danger',
    confirmText: 'Confirm',
    cancelText: 'Cancel',
  },
);

const emit = defineEmits<{ confirm: []; cancel: [] }>();
const dialog = ref<HTMLDialogElement>();

watch(
  () => props.open,
  async (open) => {
    await nextTick();
    if (open && !dialog.value?.open) dialog.value?.showModal();
    else if (!open && dialog.value?.open) dialog.value?.close();
  },
);
</script>

<template>
  <dialog
    ref="dialog"
    aria-labelledby="confirmation-title"
    class="rounded-2xl border border-slate-200/90 shadow-2xl p-6 sm:p-7 max-w-lg w-full bg-white backdrop:bg-slate-900/60 backdrop:backdrop-blur-xs"
    @cancel.prevent="!busy && emit('cancel')"
  >
    <!-- Header with Visual Badge & Dismiss Close Button -->
    <div class="flex items-start justify-between gap-3 mb-4">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
          :class="
            confirmClass === 'success' || confirmClass === 'btn-success'
              ? 'bg-emerald-50 text-emerald-600 border border-emerald-200/80'
              : confirmClass === 'primary' || confirmClass === 'btn-primary'
                ? 'bg-sky-50 text-sky-600 border border-sky-200/80'
                : 'bg-red-50 text-red-600 border border-red-200/80'
          "
        >
          <Check v-if="confirmClass === 'success' || confirmClass === 'btn-success'" class="w-5 h-5 stroke-[2.5]" />
          <AlertTriangle v-else class="w-5 h-5 stroke-[2.5]" />
        </div>
        <h2 id="confirmation-title" class="text-base sm:text-lg font-bold text-slate-900 m-0 leading-tight">
          {{ title }}
        </h2>
      </div>
      <button
        type="button"
        class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer -mr-1"
        :disabled="busy"
        aria-label="Close dialog"
        @click="emit('cancel')"
      >
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- Body Content / Slot -->
    <div class="my-3">
      <slot>
        <p v-if="message" class="preserve text-slate-600 text-xs sm:text-sm leading-relaxed m-0 text-justify">
          {{ message }}
        </p>
      </slot>
    </div>

    <!-- Error Banner if Action Failed -->
    <div v-if="error" class="notice error my-3 text-xs leading-relaxed" role="alert">
      {{ error }}
    </div>

    <!-- Action Buttons Toolbar -->
    <div class="actions flex flex-col-reverse sm:flex-row sm:justify-end gap-2.5 mt-5 pt-3 border-t border-slate-100">
      <button
        type="button"
        class="secondary text-xs font-semibold py-2.5 px-4 rounded-xl w-full sm:w-auto transition-colors cursor-pointer"
        :disabled="busy"
        @click="emit('cancel')"
      >
        {{ cancelText }}
      </button>
      <button
        type="button"
        :class="confirmClass"
        class="inline-flex items-center justify-center gap-1.5 text-xs font-bold py-2.5 px-5 rounded-xl w-full sm:w-auto shadow-sm transition-all cursor-pointer disabled:opacity-50"
        :disabled="busy"
        @click="emit('confirm')"
      >
        <span v-if="busy" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
        <Check v-else-if="confirmClass === 'success' || confirmClass === 'btn-success'" class="w-4 h-4 stroke-[2.5]" />
        <span>{{ busy ? 'Processing…' : confirmText }}</span>
      </button>
    </div>
  </dialog>
</template>
