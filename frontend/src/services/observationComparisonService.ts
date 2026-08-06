import { mockObservations } from "@/services/observationService";
import { ObservationComparison } from "../types/monitoring";
import { ObservationSummary } from "../types/observationSummary";

const apiBase = import.meta.env.VITE_API_BASE as string

async function compareObservations(observations: ObservationSummary[]): Promise<ObservationComparison[]> {
    const comparisons: ObservationComparison[] = [];
    const url = apiBase ? `${apiBase}/api/observations/comparisons` : '/api/observations/comparisons'
    const res = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            "observationIds": observations.map(observation => observation.id)
        }),
        headers: {
            "Content-Type": "application/json",
        }
    });
    if (!res.ok) throw new Error('Observations comparison request failed: ' + res.status + ' ' + res.statusText);
    return await res.json();
}


export default { compareObservations }