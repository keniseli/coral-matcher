<template>

    <div
        class="flex h-full flex-col items-center justify-center text-xs text-coral-secondary-text">
        <i class="h-5 w-5 rounded-full border-2 border-teal-300 border-t-transparent animate-spin"></i>

        <p class="mt-3">
            {{ text }}
        </p>
    </div>

</template>

<script setup lang="ts">

const props = defineProps<{
    text: string;
}>();

</script>