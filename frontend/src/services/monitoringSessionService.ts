import type { MonitoringSession } from '../types/monitoringSession'

const monitoringSessions: MonitoringSession[] = [
    {
        "id": "abcd",
        "name": "",
        "diveSite": { "id": "islalarga", name: "Isla Larga" },
        "timestamp": `${new Date("Jul 01 2026 08:00 GMT-0600")}`,
        "observationCount": 27
    },
    {
        "id": "1234",
        "name": "Additional Name",
        "diveSite": { "id": "olohuita", name: "Olohuita" },
        "timestamp": `${new Date("Jul 07 2026 10:00 GMT-0600")}`,
        "observationCount": 42
    }
];

async function getAll(): Promise<MonitoringSession[]> {
    const apiBase = import.meta.env.VITE_API_BASE as string
    const url = apiBase ? `${apiBase}/api/monitoring-sessions` : '/api/monitoring-sessions'
    const res = await fetch(url, { method: 'GET' })
    if (!res.ok) throw new Error('Segmentation request failed.')
    return await res.json();
}

async function create(monitoringSession: MonitoringSession): Promise<MonitoringSession> {
    console.log("creating monitoring session");
    console.log(monitoringSession);
    const apiBase = import.meta.env.VITE_API_BASE as string
    const url = apiBase ? `${apiBase}/api/monitoring-sessions` : '/api/monitoring-sessions'
    const res = await fetch(url, {
        method: 'POST',
        body: JSON.stringify({
            "name": monitoringSession.name,
            "timestamp": monitoringSession.timestamp,
            "diveSite": monitoringSession.diveSite.name
        }),
        headers: {
            "Content-Type": "application/json",
        }
    })
    if (!res.ok) throw new Error('Session creation request failed.')
    await res.json().then(response => { monitoringSession.id = response.sessionId });
    return monitoringSession;
}

export default { getAll, create }
