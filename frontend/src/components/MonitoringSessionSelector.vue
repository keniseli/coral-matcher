<template>
    <div ref="container" class="relative">
        
        <!-- Selector button -->
        <button type="button"
            class="mt-1 flex w-full items-center justify-between rounded border border-slate-700 bg-[#091419] p-2 text-left hover:border-slate-600 disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="loading" @click="toggleDropdown">
            <div>
                <p v-if="selectedSession" class="text-sm text-slate-200">
                    {{ sessionLabel(selectedSession) }}
                </p>

                <p v-if="selectedSession" class="mt-0.5 text-xs text-slate-500">
                    {{ selectedSession.diveSite.name }}
                    ·
                    {{ selectedSession.observationCount }}
                    observation{{
                        selectedSession.observationCount === 1
                            ? ""
                            : "s"
                    }}
                </p>


                <p v-else class="text-sm text-slate-500">
                    {{
                        loading
                            ? "Loading monitoring sessions..."
                            : "Select a monitoring session"
                    }}
                </p>
            </div>

            <span class="ml-3 text-slate-500 transition-transform" :class="open ? 'rotate-180' : ''">
                ▼
            </span>
        </button>

        <!-- Error -->
        <p v-if="error" class="mt-1 text-xs text-red-400">
            {{ error }}
        </p>

        <!-- Dropdown -->
        <div v-if="open"
            class="absolute z-40 mt-1 w-full overflow-hidden rounded border border-slate-700 bg-[#0d1b21] shadow-xl">
            <!-- Loading -->
            <div v-if="loading" class="px-3 py-4 text-center text-sm text-slate-500">
                Loading sessions...
            </div>

            <!-- Existing sessions -->
            <div v-else-if="sessions.length" class="max-h-72 overflow-y-auto">
                <button v-for="session in sessions" :key="session.id" type="button"
                    class="w-full border-b border-slate-800 px-3 py-2 text-left transition hover:bg-slate-800" :class="session.id === selectedSession?.id
                        ? 'bg-teal-400/10'
                        : ''
                        " @click="selectSession(session)">
                    <div class="flex items-center justify-between">
                        <p class="text-sm text-slate-200">
                            <span class="text-sm text-slate-300">
                                Monitoring Session:
                            </span>
                            {{ sessionLabel(session) }}
                        </p>

                        <span v-if="
                            session.id === selectedSession?.id
                        " class="text-xs text-teal-300">
                            Active
                        </span>
                    </div>

                    <p class="mt-0.5 text-xs text-slate-500">
                        {{ session.diveSite.name }}
                        ·
                        {{ session.observationCount }}
                        observation{{
                            session.observationCount === 1
                                ? ""
                                : "s"
                        }}
                    </p>
                </button>
            </div>

            <!-- Empty state -->
            <p v-else class="px-3 py-4 text-center text-sm text-slate-500">
                No monitoring sessions yet.
            </p>

            <!-- Create new session -->
            <button type="button"
                class="w-full border-t border-slate-700 px-3 py-3 text-left text-sm font-medium text-teal-300 transition hover:bg-teal-400/10"
                @click="openCreateDialog">
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

const toggleDropdown = () => {
    if (loading.value) {
        return;
    }
    open.value = !open.value;
};

const selectSession = (session: MonitoringSession) => {
    emit(
        "update:modelValue",
        session,
    );
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
        sessions.value =
            await monitoringSessionService.getAll();
    } catch (e) {
        error.value =
            e instanceof Error
                ? e.message
                : "Could not load monitoring sessions.";
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
        return `${formatDate(session.timestamp)} · ${session.diveSite.name} · ${session.name}`;
    }

    return `${formatDate(session.timestamp)} · ${session.diveSite.name}`;
};

const formatDate = (timestamp: string) => {
    return new Intl.DateTimeFormat(
        undefined,
        {
            dateStyle: "medium",
            timeStyle: "short",
        },
    ).format(
        new Date(timestamp),
    );
};

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