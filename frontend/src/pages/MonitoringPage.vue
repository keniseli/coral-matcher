<template>
    <div class="flex flex-col xl:flex-row h-auto xl:h-full min-h-0 
        overflow-auto xl:overflow-hidden">

        <MonitoringSidebar />

        <MonitoringWorkspace />

    </div>
</template>

<script setup lang="ts">
import MonitoringSidebar from "../components/monitoring/MonitoringSidebar.vue";
import MonitoringWorkspace from "../components/monitoring/MonitoringWorkspace.vue";
</script>