<template>
    <div class="right-4 z-50 space-y-2">
        <div v-for="notification in notificationStore.notifications" :key="notification.id">

            <div v-if="notification.type == 'error'"
                class="bg-red-600 rounded text-red-100 p-2 text-sm">
                <span>
                    {{ notification.message }}
                </span>

                <button class="ml-2 text-red-200 transition hover:text-white" aria-label="Dismiss"
                    @click="notificationStore.remove(notification.id)">
                    ✕
                </button>
            </div>

            <div v-if="notification.type == 'info'"
                class="bg-coral-overlay rounded text-coral-primary-text p-2 text-sm">
                <span>
                    {{ notification.message }}
                </span>

                <button class="ml-2 text-coral-primary-text transition hover:text-white" aria-label="Dismiss"
                    @click="notificationStore.remove(notification.id)">
                    ✕
                </button>
            </div>

            <div v-if="notification.type == 'success'"
                class="bg-coral-primary-bg rounded text-coral-primary p-2 text-sm">
                <span>
                    {{ notification.message }}
                </span>

                <button class="ml-3 text-green-200 transition hover:text-white" aria-label="Dismiss"
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