<template>
    <div class="h-screen bg-coral-bg flex flex-col overflow-hidden text-coral-primary-text">
        <Navigation />
        <main class="flex-1 min-h-0 overflow-auto xl:overflow-hidden"">
            <RouterView />
        </main>
    </div>
</template>
<script setup lang="ts">

import Navigation from "./components/Navigation.vue";



</script>
