<template>

    <table v-if="metricSeries.size > 0" class="w-max border-collapse text-xs">
        <tr v-for="[key, metrics] in metricSeries" :key="key">
            <td class="w-monitoring-metric-label-column">
                {{ getLabel(key) }}
            </td>
            <td class="w-monitoring-metric-value-column" v-for="metric in metrics">
                {{ metric.changePercentage }}
            </td>
        </tr>
    </table>
    <span v-else>
        Select metrics
    </span>
</template>

<script setup lang="ts">
import { Metric, MetricDefinition, metricDefinitions } from '@/types/monitoring';

const props = defineProps<{
    metricSeries: Map<string, Metric[]>;
    metricDefinitions: MetricDefinition[];
}>();

function getLabel(metricId: string) {
    return metricDefinitions.find(definition => definition.id == metricId)?.label;
}

</script>