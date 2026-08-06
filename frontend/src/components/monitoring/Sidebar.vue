<template>
    <aside class="flex flex-col 
        h-[65dvh] xl:h-auto xl:shrink-0 xl:w-[30vw]
            border-b xl:border-b-0 xl:border-r 
            border-coral-surface-border bg-coral-surface
            gap-3 p-4 overflow-hidden">

        <section>
            <div v-if="!loadingSessions && !loadingDiveSites">
                <h2 class="mb-2 text-xs tracking-wide text-coral-secondary-text">
                    Filters
                </h2>

                <input type="text" v-model="coralNameSearchTerm" placeholder="Search by coral name..."
                    class="w-full mb-2 p-2 bg-coral-input text-coral-primary-text text-xs rounded border border-coral-surface-border" />
                <select v-model="selectedDiveSite"
                    class="w-full mb-2 rounded border border-coral-surface-border bg-coral-bg p-2 text-xs">
                    <option value="All Dive Sites">All Dive Sites</option>
                    <option v-for="diveSite in diveSites" :value="diveSite">{{ diveSite }}</option>
                </select>

                <select v-model="selectedSessionId"
                    class="w-full mb-2 rounded border border-coral-surface-border bg-coral-bg p-2 text-xs accent-coral-primary">
                    <option value="All Monitoring Sessions">All Monitoring Sessions</option>
                    <option v-for="session in monitoringSessions" :value="session.id">
                        <Date :timestamp="session.timestamp" /> · {{ session.diveSite }}
                    </option>
                </select>
            </div>
            <Spinner v-else text="Loading Filters..." />
        </section>

        <section class="flex-1 min-h-0 overflow-auto">

            <h2 class="mb-2 text-xs tracking-wide text-coral-secondary-text">
                Observations
            </h2>

            <div v-if="!loadingObservations" class="overflow-y-auto rounded border border-coral-surface-border">

                <label v-for="observationSummary in filteredObservations" :key="observationSummary.id"
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
                            <Date :timestamp="observationSummary.observedAt" />
                            · {{ observationSummary.diveSite }}
                        </div>
                    </div>
                </label>

            </div>
            <div v-else>
                <Spinner text="Loading Observations..." />
            </div>
        </section>
    </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { ObservationSummary } from '../../types/observationSummary';
import { MonitoringSession } from "@/types/monitoringSession";
import monitoringSessionService from "@/services/monitoringSessionService.js";
import { useNotificationStore } from '@/stores/notification';
import diveSiteService from '@/services/diveSiteService';
import { compareDesc, format } from 'date-fns';
import Spinner from '../utils/Spinner.vue';
import Date from '../utils/Date.vue';
import ObservationSummaryRow from './ObservationSummaryRow.vue';


const props = defineProps<{
    selectedObservationIds: string[];
    observations: ObservationSummary[];
    loadingObservations: boolean;
}>();

const emit = defineEmits<{
    (e: "update:selectedObservationIds", value: string[]): void;
}>();

const notificationStore = useNotificationStore();

const coralNameSearchTerm = ref<string>();

const diveSites = ref<string[]>([]);
const loadingDiveSites = ref<boolean>(false);
const selectedDiveSite = ref<string>("All Dive Sites");

const monitoringSessions = ref<MonitoringSession[]>([]);
const loadingSessions = ref<boolean>(false);
const selectedSessionId = ref<string>("All Monitoring Sessions");

const filteredObservations = computed<ObservationSummary[]>(() => {
    return props.observations
        .filter(summary =>
            summary.diveSite.toLowerCase() == selectedDiveSite.value?.toLowerCase()
            || selectedDiveSite.value == "All Dive Sites"
        ).filter(summary =>
            summary.monitoringSessionId == selectedSessionId.value
            || selectedSessionId.value == "All Monitoring Sessions"
        ).filter(summary =>
            summary.coralName.toLocaleLowerCase().includes(coralNameSearchTerm.value ? coralNameSearchTerm.value.toLowerCase() : "")
        ).sort((a, b) => {
            const nameCompare = a.coralName.toLowerCase().localeCompare(b.coralName.toLocaleLowerCase());
            if (nameCompare == 0) {
                return compareDesc(a.observedAt, b.observedAt);
            }
            return nameCompare;
        });
});

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

const loadDiveSites = async () => {
    loadingDiveSites.value = true;
    try {
        diveSites.value = await diveSiteService.getAll();
    } catch (e) {
        notificationStore.error("An error occurred while loading dive sites: " + e);
    }
    loadingDiveSites.value = false;
};

const loadMonitoringSessions = async () => {
    loadingSessions.value = true;
    try {
        monitoringSessions.value = await monitoringSessionService.getAll();
    } catch (e) {
        notificationStore.error("An error occurred while loading monitoring sessions: " + e);
    }
    loadingSessions.value = false;
};

onMounted(async () => {
    await loadMonitoringSessions();
    await loadDiveSites();
});

</script>