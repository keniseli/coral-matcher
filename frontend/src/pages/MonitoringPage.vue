<template>
    <div class="flex flex-col xl:flex-row h-auto xl:h-full min-h-0 
        overflow-auto xl:overflow-hidden">

        <MonitoringSidebar
            :observations="mockObservations"
            v-model:selectedObservationIds="selectedObservationIds"/>

        <MonitoringWorkspace 
            :selectedObservations="selectedObservations"/>

    </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";

import MonitoringSidebar from "../components/monitoring/MonitoringSidebar.vue";
import MonitoringWorkspace from "../components/monitoring/MonitoringWorkspace.vue";
import { mockObservations } from "../services/observationService.js";
const selectedObservationIds = ref<string[]>([]);

const selectedObservations = computed(() =>
    mockObservations.filter(o =>
        selectedObservationIds.value.includes(o.id)
    )
);

</script>