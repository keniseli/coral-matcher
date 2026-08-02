<template>
    <div class="flex">

        <div v-for="observation in observations" class="flex w-60 shrink-0 flex-col
        rounded-xs border border-coral-surface-border bg-coral-surface p-3">

            <img src="https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031"
                class="mb-3 rounded object-cover" />

            <div class="font-semibold text-xs">
                {{ observation.coralName }}
            </div>

            <div class="text-xs text-coral-secondary-text">
                {{ observation.monitoringSessionSummary }}
            </div>

        </div>
    </div>
</template>

<script setup lang="ts">
import { ObservationSummary } from '../../types/observationSummary';

const props = defineProps<{
    observations: ObservationSummary[];
}>();


</script>