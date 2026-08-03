<template>

    <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-coral-bg overflow-auto">

        <ObservationSummaryRow :observations="observations" />

        <MetricGraph :metric-series="metricsSeries" :metric-definitions="metricDefinitions" />

        <MetricGrid :observationComparisons :metric-definitions="metricDefinitions"
            v-model:selectedMetricIds="selectedMetricIds" />

        <div class="min-h-0 shrink-0 overflow-auto p-6">
            <h2 class="mb-4 text-lg font-semibold">
                Visualizations
            </h2>
            Visualization placeholder
        </div>

    </section>

</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import ObservationSummaryRow from './ObservationSummaryRow.vue';
import MetricGrid from './MetricGrid.vue';

import { ObservationSummary } from '@/types/observationSummary';
import { produceComparisonMocks } from '@/types/observationComparison.js';
import { metricDefinitions, Metric } from '@/types/monitoring';
import MetricGraph from './MetricGraph.vue';

const props = defineProps<{
    observations: ObservationSummary[];
}>();

const selectedMetricIds = ref<string[]>([]);

const observationComparisons = computed(() =>
    produceComparisonMocks(props.observations)
);

const metricsSeries = computed(() => {
    const series: Map<string, Metric[]> = new Map();
    observationComparisons.value.forEach(comparison => {
        comparison.metrics
            .filter(metric => selectedMetricIds.value.includes(metric.id))
            .forEach(metric => {
                if (!series.get(metric.id)) {
                    series.set(metric.id, []);
                }
                series.get(metric.id)?.push(metric);
            });
    });
    return series;
});

</script>