import { DiveSite } from "./diveSite"

export interface ObservationSummary {

    id: string;

    coralName: string;

    monitoringSessionSummary: string;

    diveSite: DiveSite;

    observedAt: string;

}