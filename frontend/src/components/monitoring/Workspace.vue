<template>

    <section class="flex-1 min-w-0 min-h-0 flex flex-col bg-coral-bg overflow-auto">

        <div v-if="!comparisonLoading && observations.length > 0">

            <ObservationSummaryRow :observations="observations" />

            <MetricGraph :metrics-series="metricsSeries" :metric-definitions="metricDefinitions" />

            <MetricGrid :observationComparisons :metric-definitions="metricDefinitions"
                v-model:selectedMetricIds="selectedMetricIds" />

            <ObservationVisualizations :observations="observations" />
        </div>

        <Spinner v-else-if="comparisonLoading && observations.length > 0" text="Metrics calculation & comparison in progress..." />

        <div v-else-if="!observations || observations.length == 0"
            class="flex h-full flex-col items-center justify-center text-xs text-coral-secondary-text">
            <p class="mt-3">
                Select Observations to start
            </p>
        </div>

    </section>

</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { computedAsync } from '@vueuse/core'
import ObservationSummaryRow from './ObservationSummaryRow.vue';
import MetricGrid from './MetricGrid.vue';

import { ObservationSummary } from '@/types/observationSummary';
import observationComparisonService from '@/services/observationMonitoringService';
import { metricDefinitions, Metric, MetricSeries } from '@/types/monitoring';
import MetricGraph from './MetricGraph.vue';
import Spinner from '../utils/Spinner.vue';
import ObservationVisualizations from './ObservationVisualizations.vue';

const props = defineProps<{
    observations: ObservationSummary[];
}>();

const selectedMetricIds = ref<string[]>([]);
const comparisonLoading = ref<boolean>(false);

const observationComparisons = computedAsync(
    async () => {
        if (!props.observations.length) return [];
        comparisonLoading.value = true;
        const comparisons = await observationComparisonService.compareObservations(props.observations);
        comparisonLoading.value = false;
        return comparisons;
    }, []
);

const metricsSeries = computed(() => {
    const metricsSeries: MetricSeries[] = [];
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
    })

    series.forEach((metrics, metricId) => {
        metricsSeries.push({
            "observations": observationComparisons.value,
            "metricId": metricId,
            "metrics": metrics,
        });
    });
    return metricsSeries;
});

</script>