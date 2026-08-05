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

export function produceComparisonMocks(observations: ObservationSummary[]) {
    const mocks: ObservationComparison[] = [];
    var baselineObservation: ObservationSummary | undefined = undefined;
    observations.forEach(observation => {
        mocks.push({
            "observation": observation,
            "baselineObservation": baselineObservation,
            "metrics": createMetrics()
        });
        baselineObservation = observation;
    });
    return mocks;
}

export const observationComparisonMocks = [{
    "observation": mockObservations[0],
    "baselineObservation": undefined,
    "metrics": createMetrics()
}, {
    "observation": mockObservations[1],
    "baselineObservation": mockObservations[0],
    "metrics": createMetrics()
}, {
    "observation": mockObservations[3],
    "baselineObservation": mockObservations[1],
    "metrics": createMetrics()
}, {
    "observation": mockObservations[5],
    "baselineObservation": mockObservations[3],
    "metrics": createMetrics()
}];

function createMetrics() {
    return [
        {
            "id": "MEAN_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "MEDIAN_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200
        }, {
            "id": "STD_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P5_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P10_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P15_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P25_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P75_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P85_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P90_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "P95_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "DYNAMIC_RANGE_L",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "MEAN_A",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "MEAN_B",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "STD_A",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "STD_B",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "SOBEL_MEAN",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "SOBEL_STD",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "SOBEL_MEDIAN",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "SOBEL_P95",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }, {
            "id": "LAPLACIAN_VARIANCE",
            "value": Math.random() * 100,
            "changePercentage": 100 - Math.random() * 200,
        }
    ];
}

export default { compareObservations }