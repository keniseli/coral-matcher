const diveSites: string[] = ["Isla Larga", "Olohuita"];

async function getAll(): Promise<string[]> {
    return diveSites;
}

export default { getAll }
