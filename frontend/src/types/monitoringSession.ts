import { DiveSite } from "./diveSite";

export type MonitoringSession = {
    id: string;
    name: string | null;
    diveSite: DiveSite;
    timestamp: string;
    observationCount: number;
};