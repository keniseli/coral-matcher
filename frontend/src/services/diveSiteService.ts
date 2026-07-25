import type { DiveSite } from '@/types/diveSite';

const diveSites: DiveSite[] = [
    { id: "islalarga", name: "Isla Larga" },
    { id: "olohuita", name: "Olohuita" }
];

async function getAll(): Promise<DiveSite[]> {
    return diveSites;
}

export default { getAll }
