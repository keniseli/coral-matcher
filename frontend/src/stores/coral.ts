// stores/coral.ts

import { MonitoringSession } from "../types/monitoringSession";
import { defineStore } from "pinia";

export interface CoralData {
    selectedMonitoringSession: MonitoringSession
}

export const useCoralDataStore =
    defineStore("coralData", {
        state: () => ({
            selectedMonitoringSession : {} as MonitoringSession,
        }),

        actions: {
            selectMonitoringSession(newSelected: MonitoringSession) {
                this.selectedMonitoringSession = newSelected;
            },
            getSelectedMonitoringSessionId(): string {
                return this.selectedMonitoringSession.id;
            },
        },
    });