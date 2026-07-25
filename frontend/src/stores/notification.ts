// stores/notification.ts

import { defineStore } from "pinia";

export type NotificationType =
    | "success"
    | "error"
    | "info"

export interface Notification {
    id: number;
    message: string;
    type: NotificationType;
}

export const useNotificationStore =
    defineStore("notification", {
        state: () => ({
            notifications: [] as Notification[],
        }),

        actions: {
            show(message: string, type: NotificationType = "info") {
                const id = Date.now();
                this.notifications.pop();
                this.notifications.push({ id, message, type });
            },

            success(message: string) {
                this.show(message, "success");
            },

            error(message: string) {
                this.show(message, "error");
            },

            info(message: string) {
                this.show(message, "info");
            },

            remove(id: number) {
                this.notifications =
                    this.notifications.filter((notification) => notification.id !== id);
            },
        },
    });