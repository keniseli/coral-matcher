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

            <MetricGrid :observationComparisons :metric-definitions="metricDefinitions" />

            <div class="min-h-0 shrink-0 overflow-auto p-6">
                <h2 class="mb-4 text-lg font-semibold">
                    Visualizations
                </h2>
                Visualization placeholder
            </div>

    </section>

</template>

<script setup lang="ts">
import { computed } from 'vue';

import ObservationSummaryRow from './ObservationSummaryRow.vue';
import MetricGrid from './MetricGrid.vue';

import { ObservationSummary } from '@/types/observationSummary';
import { produceComparisonMocks } from '@/types/observationComparison.js';
import { metricDefinitions } from '@/types/monitoring.js';


const props = defineProps<{
    observations: ObservationSummary[];
}>();

const observationComparisons = computed(() =>
    produceComparisonMocks(props.observations)
);

</script>