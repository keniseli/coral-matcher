<template>
    <aside
        class="flex flex-col 
        h-[65dvh] xl:h-auto xl:shrink-0 xl:w-[30vw]
            border-b xl:border-b-0 xl:border-r 
            border-coral-surface-border bg-coral-surface
            gap-3 p-4 overflow-hidden">

        <section>
            <h2 class="mb-2 text-xs tracking-wide text-coral-secondary-text">
                Filters
            </h2>

            <input
                type="text"
                placeholder="Search by coral name..."
                class="w-full mb-2 p-2 bg-coral-input text-coral-primary-text text-xs
                rounded border border-coral-surface-border"
            />
                <select class="w-full mb-2 rounded border border-coral-surface-border bg-coral-bg p-2 text-xs">
                    <option>All Dive Sites</option>
                </select>

                <select class="w-full mb-2 rounded border border-coral-surface-border bg-coral-bg p-2 text-xs">
                    <option>All Monitoring Sessions</option>
                </select>

        </section>

        <section class="flex-1 min-h-0 overflow-auto">

            <h2 class="mb-2 text-xs tracking-wide text-coral-secondary-text">
                Observations
            </h2>

            <div class="overflow-y-auto rounded border border-coral-surface-border">

                <label
                    v-for="i in 12" :key="i"
                    class="flex items-center gap-3 border-b border-coral-surface-border p-2 hover:bg-coral-bg">
                    
                    <input type="checkbox">
                    <div>
                        <div class="semibold text-sm">
                            Coral c00{{ i  }}
                        </div>

                        <div class="text-xs text-coral-secondary-text">
                            2026-07-18
                        </div>
                    </div>
                </label>

            </div>
        </section>
    </aside>
</template>

<script setup lang="ts">
</script>