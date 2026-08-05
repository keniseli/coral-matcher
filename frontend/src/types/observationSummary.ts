import { DiveSite } from "./diveSite"

export interface ObservationSummary {

    id: string;

    coralName: string;

    monitoringSessionSummary: string;
    monitoringSessionId: string;

    diveSite: string;

    observedAt: string;

    imagePath: string;

}