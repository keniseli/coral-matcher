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
    return monitoringSessions;
}

async function create(monitoringSession: MonitoringSession): Promise<MonitoringSession> {
    console.log("creating monitoring session");
    console.log(monitoringSession);
    monitoringSessions.push(monitoringSession);
    return monitoringSession;
}

export default { getAll, create }
