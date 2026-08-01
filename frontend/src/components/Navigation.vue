<template>

    <nav class="shrink-0 px-5 pt-2 bg-coral-surface border-b border-coral-surface-border ">
        <div class="mx-auto flex h-full max-w-[1800px] min-h-0 flex-col">
            <header class="flex items-end justify-between">
                <div class="flex flex-col mb-2">
                    <h1 class="text-3xl font-bold">
                        Coral Companion
                    </h1>
                </div>

                <div class="flex absolute left-1/2 -translate-x-1/2 flex h-full items-end text-lg">
                    <RouterLink to="/observe" v-slot="{ isActive }">
                        <span :class="[
                            'block border-b-2 px-3 py-2 -mb-px font-medium transition-colors',
                            isActive
                                ? 'border-coral-primary text-coral-primary'
                                : 'border-transparent text-coral-secondary-text hover:text-coral-primary-hover'
                        ]">
                            Observe
                        </span>
                    </RouterLink>
                    <RouterLink to="/monitor" v-slot="{ isActive }">
                        <span :class="[
                            'block border-b-2 px-3 py-2 -mb-px font-medium transition-colors',
                            isActive
                                ? 'border-coral-primary text-coral-primary'
                                : 'border-transparent text-coral-secondary-text hover:text-coral-primary-hover'
                        ]">
                            Monitor
                        </span>
                    </RouterLink>
                    
                </div>
                
                <div class="ml-auto mb-2 flex items-center">
                    <NotificationContainer />
                </div>
            </header>
        </div>
    </nav>

</template>
<script setup lang="ts">
import NotificationContainer from "./NotificationContainer.vue";

</script>