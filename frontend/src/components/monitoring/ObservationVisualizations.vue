<template>
    <div class="flex">
        <div class="flex-col shrink-0 w-monitoring-metric-label-column">
            &nbsp;
        </div>
        <div v-for="visualization in visualizations" class="flex w-monitoring-metric-value-column 
            shrink-0 flex-col p-3">

            <img :src="visualization.sobelGradient" class="mb-3 rounded object-cover" />

            <div class="text-xs text-coral-secondary-text text-center">
                {{ visualization.observation.coralName }}
                <p><Date :timestamp="visualization.observation.observedAt"/></p>
            </div>

        </div>
    </div>
</template>

<script setup lang="ts">
import { useImageCache } from '@/composables/useImageCache';
import { ObservationSummary } from '../../types/observationSummary';
import Date from '../utils/Date.vue';
import { computed } from 'vue';
import observationService from '@/services/observationService';
import { computedAsync } from '@vueuse/core';

const props = defineProps<{
    observations: ObservationSummary[];
}>();

const imageCache = useImageCache();

const visualizations = computedAsync(async () => {
    const visualizations = [];
    for(const observation of props.observations) {
        visualizations.push(await imageCache.getOrFetchVisualizations(observation.id))
    }
    return visualizations;
});


</script>