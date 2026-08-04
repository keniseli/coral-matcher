<template>
    <table v-if="observationComparisons.length > 0" class="w-max border-collapse text-xs">

        <thead class="border-b border-coral-surface-border bg-coral-surface">
            <tr>

                <th class="w-monitoring-metric-label-column px-4 py-3 text-left font-medium text-coral-secondary-text">
                    Metric
                </th>

                <th v-for="observationComparison in observationComparisons"
                    class="w-monitoring-metric-value-column px-4 py-3 text-center font-medium text-coral-secondary-text">
                    {{ observationComparison.observation.observedAt }}
                    {{ observationComparison.observation.coralName }}
                </th>

            </tr>
        </thead>

        <tbody v-for="[group, metricDefinitions] in groupedMetricDefinitions" :key="group">

            <tr @click="toggleGroup(group)"
                class="cursor-pointer bg-coral-surface hover:bg-coral-overlay border-t border-coral-surface-border">

                <td :colspan="observationComparisons.length + 1" class="px-4 py-2 font-medium">
                    <span :class="[
                        'mr-2 inline-block transition-transform',
                        isGroupCollapsed(group)
                            ? '-rotate-90'
                            : 'rotate-0'
                    ]">
                        ▼
                    </span>
                    {{ group }}
                </td>
            </tr>

            <template v-if="!collapsedGroups.has(group)">
                <tr v-for="metricDefinition in metricDefinitions" :key="metricDefinition.id"
                    @click="toggleMetric(metricDefinition.id)" :class="[
                        'cursor-pointer border-b border-coral-surface-border transition-colors',
                        isSelected(metricDefinition.id)
                            ? 'bg-coral-primary-bg hover:bg-coral-overlay'
                            : 'hover:bg-coral-primary-bg'
                    ]">
                    <td class="w-monitoring-metric-label-column px-6 py-3 text-coral-primary-text">
                        {{ metricDefinition.label }}
                        <span class="text-coral-secondary-text">{{ metricDefinition.unit }}</span>
                    </td>

                    <td v-for="observationComparison in observationComparisons"
                        class="w-monitoring-metric-value-column px-4 py-2 text-center font-mono">

                        {{(metric = observationComparison.metrics.find((metric) => metric.id == metricDefinition.id),
                            null)}}
                        <span class="text-coral-primary-text">
                            {{ metric?.value.toFixed(3) }}
                        </span>
                        <span v-if="observationComparison.baselineObservation" :class="metric && Math.abs(metric.changePercentage) >= 20
                            ? 'text-coral-attention'
                            : 'text-coral-secondary-text'">
                            (<span v-if="metric?.changePercentage && (Math.sign(metric?.changePercentage | 0) > 0)">+</span>{{
                                metric?.changePercentage.toFixed(3) }}%)
                        </span>

                    </td>

                </tr>
            </template>

        </tbody>
    </table>

</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

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

const groupedMetricDefinitions = computed(() => {
    const groups = new Map<string, MetricDefinition[]>();

    for (const definition of props.metricDefinitions) {
        if (!groups.has(definition.group)) {
            groups.set(definition.group, []);
        }

        groups.get(definition.group)!.push(definition);
    }

    return [...groups.entries()];
});

const collapsedGroups = ref(new Set<string>());

function toggleMetric(metricId: string) {
    const selected = [...props.selectedMetricIds];
    const index = selected.indexOf(metricId);
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

function toggleGroup(group: string) {
    const next = new Set(collapsedGroups.value);

    if (next.has(group))
        next.delete(group);
    else
        next.add(group);

    collapsedGroups.value = next;
}

function isGroupCollapsed(group: string): boolean {
    return collapsedGroups.value.has(group);
}

</script>