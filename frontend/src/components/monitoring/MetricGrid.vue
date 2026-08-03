<template>
    <table class="w-max border-collapse text-xs">

        <thead class="border-b border-coral-surface-border bg-coral-surface">
            <tr>

                <th class="w-monitoring-metric-label-column px-4 py-3 text-left font-medium text-coral-secondary-text">
                    Metric
                </th>

                <th v-for="observationComparison in observationComparisons"
                    class="w-monitoring-metric-value-column px-4 py-3 text-left font-medium text-coral-secondary-text">
                    {{ observationComparison.observation.observedAt }}
                    {{ observationComparison.observation.coralName }}
                </th>

            </tr>
        </thead>

        <tbody>
            
            <tr v-for="metricDefinition in metricDefinitions"
                :key="metricDefinition.id"
                @click="toggleMetric(metricDefinition.id)"
                :class="[
                    'cursor-pointer border-b border-coral-surface-border transition-colors',
                    isSelected(metricDefinition.id)
                        ? 'bg-coral-primary-bg'
                        : 'hover:bg-coral-primary-bg'
                ]">
                <td class="w-monitoring-metric-label-column px-4 py-2 font-medium text-coral-primary-text">
                    {{ metricDefinition.label }}
                </td>

                <td v-for="observationComparison in observationComparisons" 
                    class="w-monitoring-metric-value-column px-4 py-2 text-right font-mono">

                    {{ (metric = observationComparison.metrics.find((metric) => metric.id == metricDefinition.id), null) }}
                    <span class="text-coral-primary-text">
                        {{ metric?.value.toFixed(3) }}
                    </span>
                    <span v-if="observationComparison.baselineObservation" :class="metric && Math.abs(metric.changePercentage) >= 20
                        ? 'text-coral-attention'
                        : 'text-coral-secondary-text'">
                        ({{ metric?.changePercentage.toFixed(3) }}%)
                    </span>

                </td>

            </tr>

        </tbody>
    </table>
</template>

<script setup lang="ts">
import { Metric, MetricDefinition } from '@/types/monitoring';
import { ObservationComparison } from '@/types/observationComparison';

// this is solely for use in the template
var metric: Metric | undefined

const props = defineProps<{
    observationComparisons: ObservationComparison[];
    metricDefinitions: MetricDefinition[];
    selectedMetricIds: string[];
}>();

const emit = defineEmits<{
    (e: "update:selectedMetricIds", value: string[]): void;
}>();

function toggleMetric(metricId: string) {
    const selected = [...props.selectedMetricIds];

    const index = selected.indexOf(metricId);
    
    console.log(selected);

    if (index >= 0) {
        selected.splice(index, 1);
    } else {
        selected.push(metricId);
    }

    emit("update:selectedMetricIds", selected);
}

function isSelected(metricId: string) {
    return props.selectedMetricIds.includes(metricId);
}

</script>