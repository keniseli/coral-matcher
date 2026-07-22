<template>
    <div class="fixed right-4 top-4 z-50 space-y-2">
        <div v-for="notification in notificationStore.notifications" :key="notification.id">

            <div v-if="notification.type == 'error'"
                class="relative mb-3 rounded border border-red-400 bg-red-600 px-4 py-3 pr-10 text-sm text-red-100">
                <span>
                    {{ notification.message }}
                </span>

                <button class="absolute right-3 top-3 text-red-200 transition hover:text-white" aria-label="Dismiss"
                    @click="notificationStore.remove(notification.id)">
                    ✕
                </button>
            </div>

            <div v-if="notification.type == 'info'"
                class="relative mb-3 rounded border border-white-400 bg-coral-overlay px-4 py-3 pr-10 text-sm text-red-100">
                <span>
                    {{ notification.message }}
                </span>

                <button class="absolute right-3 top-3 text-white-200 transition hover:text-white" aria-label="Dismiss"
                    @click="notificationStore.remove(notification.id)">
                    ✕
                </button>
            </div>

            <div v-if="notification.type == 'success'"
                class="relative mb-3 rounded border border-coral-primary bg-[#15665B] px-4 py-3 pr-10 text-sm text-red-100">
                <span>
                    {{ notification.message }}
                </span>

                <button class="absolute right-3 top-3 text-green-200 transition hover:text-white" aria-label="Dismiss"
                    @click="notificationStore.remove(notification.id)">
                    ✕
                </button>
            </div>
        </div>
    </div>
</template>
<script setup lang="ts">
import { useNotificationStore } from "../stores/notification";

const notificationStore = useNotificationStore();
</script>