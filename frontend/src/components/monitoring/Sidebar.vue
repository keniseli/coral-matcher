<template>
    <aside class="flex flex-col 
        h-[65dvh] xl:h-auto xl:shrink-0 xl:w-[30vw]
            border-b xl:border-b-0 xl:border-r 
            border-coral-surface-border bg-coral-surface
            gap-3 p-4 overflow-hidden">

        <section>
            <h2 class="mb-2 text-xs tracking-wide text-coral-secondary-text">
                Filters
            </h2>

            <input type="text" placeholder="Search by coral name..." class="w-full mb-2 p-2 bg-coral-input text-coral-primary-text text-xs
                rounded border border-coral-surface-border" />
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

                <label v-for="observationSummary in observations" :key="observationSummary.id"
                    @click.prevent="toggleObservation(observationSummary.id)" :class="[
                        'flex cursor-pointer items-center gap-3 border-b border-coral-surface-border p-2 transition-colors',
                        props.selectedObservationIds.includes(observationSummary.id)
                            ? 'bg-coral-primary-bg hover:bg-coral-overlay'
                            : 'hover:bg-coral-primary-bg'
                    ]">

                    <input type="checkbox" :checked="props.selectedObservationIds.includes(observationSummary.id)"
                        @change="toggleObservation(observationSummary.id)" 
                        class="h-4 w-4 accent-coral-primary focus:ring-0" />

                    <div>
                        <div :class="[
                            'truncate text-xs font-medium',
                            props.selectedObservationIds.includes(observationSummary.id)
                                ? 'text-coral-primary'
                                : 'text-coral-primary-text'
                        ]">
                            {{ observationSummary.coralName }}
                        </div>

                        <div class="text-xs text-coral-secondary-text">
                            {{ observationSummary.observedAt }}
                        </div>
                    </div>
                </label>

            </div>
        </section>
    </aside>
</template>

<script setup lang="ts">
import { ObservationSummary } from '../../types/observationSummary';


const props = defineProps<{
    selectedObservationIds: string[];
    observations: ObservationSummary[];
}>();

const emit = defineEmits<{
    (e: "update:selectedObservationIds", value: string[]): void;
}>();

function toggleObservation(id: string) {
    const selected = props.selectedObservationIds;
    const index = selected.indexOf(id);

    if (index >= 0) {
        selected.splice(index, 1);
    } else {
        selected.push(id);
    }

    emit("update:selectedObservationIds", selected);
}


</script>