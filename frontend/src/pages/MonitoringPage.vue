<template>
    <div class="flex flex-col xl:flex-row h-auto xl:h-full min-h-0 
        overflow-auto xl:overflow-hidden">

        <MonitoringSidebar
            :observations="observations"
            v-model:selectedObservationIds="selectedObservationIds"/>

        <MonitoringWorkspace 
            :observations="selectedObservations"/>

    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { compareAsc } from "date-fns";

import MonitoringSidebar from "../components/monitoring/Sidebar.vue";
import MonitoringWorkspace from "../components/monitoring/Workspace.vue";
import observationService, { mockObservations } from "../services/observationService";
import { ObservationSummary } from "@/types/observationSummary"
import { useNotificationStore } from "@/stores/notification";


const selectedObservationIds = ref<string[]>([]);

const observations = ref<ObservationSummary[]>([]);

const notificationStore = useNotificationStore();

const loadObservationSummaries = async () => {
    try {
        observations.value = await observationService.getObservationSummaries()
    } catch(e) {
        notificationStore.error("An error occurred while loading data: " + e)
    }
};

const selectedObservations = computed(() =>
    observations.value
        .filter((o: ObservationSummary) => selectedObservationIds.value.includes(o.id))
        .sort((a, b) => compareAsc(a.observedAt, b.observedAt))
);

onMounted(async () => {
    await loadObservationSummaries();
});

</script>