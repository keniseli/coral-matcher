<template>
    <div class="flex flex-col xl:flex-row h-auto xl:h-full min-h-0 
        overflow-auto xl:overflow-hidden">

        <MonitoringSidebar
            :observations="mockObservations"
            v-model:selectedObservationIds="selectedObservationIds"/>

        <MonitoringWorkspace 
            :observations="selectedObservations"/>

    </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";

import MonitoringSidebar from "../components/monitoring/Sidebar.vue";
import MonitoringWorkspace from "../components/monitoring/Workspace.vue";
import { mockObservations } from "../services/observationService.js";
import { compareAsc } from "date-fns";

const selectedObservationIds = ref<string[]>([]);

const selectedObservations = computed(() =>
    mockObservations.filter(o =>
        selectedObservationIds.value.includes(o.id)
    ).sort((a, b) => compareAsc(a.observedAt, b.observedAt))
);

</script>