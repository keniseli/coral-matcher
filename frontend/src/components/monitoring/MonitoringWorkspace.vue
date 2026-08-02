<template>

    <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-coral-bg overflow-auto">

            <ObservationSummaryRow :observations="observations" />

            <div class="h-auto shrink-0 border-b border-coral-surface-border p-6">

                <h2 class="mb-4 text-lg font-semibold">
                    Metric Trend
                </h2>

                <div class="flex h-auto items-center justify-center 
                rounded border border-dashed border-coral-surface-border ">
                    Graph placeholder
                </div>

            </div>

            <div class="flex-1 min-h-0 overflow-auto border-b border-coral-surface-border p-6 ">
                <h2 class="mb-4 text-lg font-semibold">
                    Metrics
                </h2>
                Metric grid placeholder
                {{ observations }}
            </div>

            <div class="min-h-0 shrink-0 overflow-auto p-6">
                <h2 class="mb-4 text-lg font-semibold">
                    Visualizations
                </h2>
                Visualization placeholder
            </div>

    </section>

</template>

<script setup lang="ts">
import { ObservationSummary } from '@/types/observationSummary';
import ObservationSummaryRow from './ObservationSummaryRow.vue';


const props = defineProps<{
    observations: ObservationSummary[];
}>();

</script>