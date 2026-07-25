<template>
    <div ref="container" class="relative">

        <!-- Selector button -->
        <button type="button" class="flex w-full items-center justify-between rounded 
            border border-coral-surface-border bg-coral-input p-2 text-left 
            hover:border-slate-600 disabled:cursor-not-allowed disabled:opacity-50" :disabled="loading"
            @click="toggleDropdown">
            <div class="grid grid-cols-[3fr_1fr] w-full text-xs text-coral-primary-text font-semibold m-1">
                <span v-if="selectedSession">
                    <span class="text-coral-secondary-text font-normal">Monitoring Session</span>
                    {{ formatDate(selectedSession.timestamp) }} · {{ selectedSession.diveSite.name }}
                    <span v-if="selectedSession.name"> · {{ selectedSession.name }}</span>
                </span>

                <span v-if="selectedSession" class="ml-auto text-coral-secondary-text font-normal">
                    {{ selectedSession.observationCount }}
                    observation{{
                        selectedSession.observationCount === 1
                            ? ""
                            : "s"
                    }}
                </span>


                <p v-else class="text-xs text-coral-secondary-text">
                    {{
                        loading
                            ? "Loading monitoring sessions..."
                            : "Select a monitoring session"
                    }}
                </p>
            </div>

            <span class="ml-3 text-coral-secondary-text transition-transform" :class="open ? 'rotate-180' : ''">
                ▼
            </span>
        </button>

        <!-- Error -->
        <p v-if="error" class="mt-1 text-xs text-red-400">
            {{ error }}
        </p>

        <!-- Dropdown -->
        <div v-if="open"
            class="absolute z-40 mt-1 w-full overflow-hidden rounded border border-coral-surface-border bg-coral-surface shadow-xl">
            <!-- Loading -->
            <div v-if="loading" class="px-3 py-4 text-center text-xs text-coral-secondary-text bg-coral-raised">
                Loading sessions...
            </div>

            <!-- Existing sessions -->
            <div v-else-if="sessions.length" class="max-h-72 overflow-y-auto">
                <button v-for="session in sessions" :key="session.id" type="button" class="w-full border-b border-coral-raised-border
                    px-3 py-2 text-left transition 
                    hover:bg-coral-primary-bg" :class="session.id === selectedSession?.id
                        ? 'bg-coral-primary-bg'
                        : 'bg-coral-raised'
                        " @click="selectSession(session)">
                    <div class="grid grid-cols-[3fr_1fr] w-full text-xs text-coral-primary-text font-semibold m-1">
                        <span v-if="selectedSession">
                            <span class="text-coral-secondary-text font-normal">Monitoring Session</span>
                            {{ formatDate(session.timestamp) }} · {{ session.diveSite.name }}
                            <span v-if="session.name"> · {{ session.name }}</span>
                        </span>

                        <span v-if="session" class="ml-auto text-coral-secondary-text font-normal">
                            {{ session.observationCount }}
                            observation{{
                                session.observationCount === 1
                                    ? ""
                                    : "s"
                            }}
                        </span>
                    </div>
                </button>
            </div>

            <!-- Empty state -->
            <p v-else class="px-3 py-4 text-center text-xs text-coral-secondary-text">
                No monitoring sessions yet.
            </p>

            <!-- Create new session -->
            <button type="button" class="w-full border-coral-raised-border px-3 py-3 text-left text-xs font-medium text-teal-300 transition
                bg-coral-raised hover:bg-coral-primary-bg" @click="openCreateDialog">
                ＋ Create new monitoring session
            </button>
        </div>

        <!-- Create dialog -->
        <CreateMonitoringSessionDialog v-if="showCreateDialog" :dive-sites="diveSites" :initial-dive-site-id="selectedSession?.diveSite.id
            " @cancel="showCreateDialog = false" @create="createSession" />
    </div>
</template>

<script setup lang="ts">
import {
    computed,
    onBeforeUnmount,
    onMounted,
    ref,
} from "vue";


import monitoringSessionService from "../services/monitoringSessionService";
import { MonitoringSession } from "../types/monitoringSession"
import CreateMonitoringSessionDialog from "./CreateMonitoringSessionDialog.vue";
import diveSiteService from "../services/diveSiteService"
import { DiveSite } from "../types/diveSite"
import { useNotificationStore } from "../stores/notification";
import { useCoralDataStore } from "../stores/coral";
import { format } from "date-fns";

type Props = {
    modelValue: MonitoringSession | null;
};

const props = defineProps<Props>();

const emit = defineEmits<{
    "update:modelValue": [
        session: MonitoringSession | null,
    ];
}>();

const container =
    ref<HTMLElement | null>(null);

const open = ref(false);
const loading = ref(false);
const error = ref("");
const showCreateDialog = ref(false);
const sessions = ref<MonitoringSession[]>([]);
const diveSites = ref<DiveSite[]>([]);
const selectedSession = computed(() => props.modelValue);
const notificationStore = useNotificationStore();
const coralDataStore = useCoralDataStore();

const toggleDropdown = () => {
    if (loading.value) {
        return;
    }
    open.value = !open.value;
};

const selectSession = (session: MonitoringSession) => {
    emit("update:modelValue", session);
    coralDataStore.selectMonitoringSession(session);
    open.value = false;
};

const openCreateDialog = () => {
    open.value = false;
    showCreateDialog.value = true;
};

const loadSessions = async () => {
    loading.value = true;
    error.value = "";

    try {
        sessions.value = await monitoringSessionService.getAll();
        if (sessions.value.length > 0) {
            selectSession(sessions.value[0]);
        }
    } catch (e) {
        if (e instanceof Error) {
            notificationStore.error(e.message);
        } else {
            notificationStore.error("Could not load monitoring sessions.");
        }
    } finally {
        loading.value = false;
    }
};

const loadDiveSites = async () => {
    loading.value = true;
    error.value = "";

    try {
        diveSites.value =
            await diveSiteService.getAll();
    } catch (e) {
        error.value =
            e instanceof Error
                ? e.message
                : "Could not load dive sites.";
    } finally {
        loading.value = false;
    }
};

const createSession = async (payload: MonitoringSession) => {
    loading.value = true;
    error.value = "";

    try {
        const created = await monitoringSessionService.create(payload);
        showCreateDialog.value = false;

        // Automatically select the newly-created session.
        emit("update:modelValue", created);
        coralDataStore.selectMonitoringSession(created);
    } catch (e) {
        error.value =
            e instanceof Error
                ? e.message
                : "Could not create monitoring session.";
    } finally {
        loading.value = false;
    }
};

const sessionLabel = (session: MonitoringSession) => {
    if (session.name) {
        return `${formatDate(session.timestamp)} · ${session.name} · ${session.diveSite.name}`;
    }

    return `${formatDate(session.timestamp)} · ${session.diveSite.name}`;
};

const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return format(date, "dd. MMM yyyy 'at' p");
}

const handleClickOutside = (event: MouseEvent) => {
    if (container.value &&
        !container.value.contains(event.target as Node)) {
        open.value = false;
    }
};

onMounted(async () => {
    document.addEventListener(
        "click",
        handleClickOutside,
    );

    await loadSessions();
    await loadDiveSites();
});

onBeforeUnmount(() => {
    document.removeEventListener(
        "click",
        handleClickOutside,
    );
});
</script>