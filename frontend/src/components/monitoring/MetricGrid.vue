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
                class="border-b border-coral-surface-border transition-colors hover:bg-coral-primary-bg">

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


const props = defineProps<{
    observationComparisons: ObservationComparison[];
    metricDefinitions: MetricDefinition[];
}>();

// this is for temporary use in the template
var metric: Metric | undefined

</script>