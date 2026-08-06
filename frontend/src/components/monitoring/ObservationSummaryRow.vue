<template>
    <div class="flex">
        <div class="flex-col shrink-0 w-monitoring-metric-label-column">
            &nbsp;
        </div>
        <div v-for="observation in observations" class="flex w-monitoring-metric-value-column 
            shrink-0 flex-col p-3">

            <img :src="observation.imagePath"
                class="mb-3 rounded object-cover" />

            <div class="font-semibold text-xs text-center">
                <Date :timestamp="observation.observedAt" />
            </div>
            
            <div class="text-xs text-coral-secondary-text text-center">
                {{ observation.coralName }}
            </div>

        </div>
    </div>
</template>

<script setup lang="ts">
import { ObservationSummary } from '../../types/observationSummary';
import Date from '../utils/Date.vue';

const props = defineProps<{
    observations: ObservationSummary[];
}>();


</script>