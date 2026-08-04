import { DiveSite } from "./diveSite";

export type MonitoringSession = {
    id: string;
    name: string | null;
    diveSite: string;
    timestamp: string;
    observationCount: number;
};