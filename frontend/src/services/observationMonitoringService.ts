import { ObservationComparison, ObservationVisualization } from "../types/monitoring";
import { ObservationSummary } from "../types/observationSummary";

const apiBase = import.meta.env.VITE_API_BASE as string

async function compareObservations(observations: ObservationSummary[]): Promise<ObservationComparison[]> {
    const url = apiBase ? `${apiBase}/api/observations/comparisons` : '/api/observations/comparisons'
    const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            "observationIds": observations.map(observation => observation.id)
        }),
        headers: {
            "Content-Type": "application/json",
        }
    });
    if (!response.ok) throw new Error('Observations comparison request failed: ' + response.status + ' ' + response.statusText);
    return await response.json();
}

async function loadVisualizations(observationId: string): Promise<ObservationVisualization> {
    const url = apiBase ? `${apiBase}/api/observations/${observationId}/metrics/visualizations` : `/api/observations/${observationId}/metrics/visualizations`
    const response = await fetch(url, { method: 'GET' });
    if (!response.ok) throw new Error('Observation metrics visualizations request failed: ' + response.status + ' ' + response.statusText);
    const data = await response.json();

    const visualization: ObservationVisualization = {
        observation: data.observation,
        sobelGradient: data.sobelGradient,
        laplaceResponse: data.laplaceResponse,
    };

    return visualization;
}


export default { compareObservations, loadVisualizations }