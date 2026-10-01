import {BaseGenome} from '../../../../../interfaces/Genome';

/** Combine selected genomes with type-strain isolate names for API isolate filters. */
export function genomesForQuery(
    selectedGenomes: BaseGenome[],
    extraIsolates: string[] = []
): BaseGenome[] | undefined {
    const names = new Set(selectedGenomes.map((genome) => genome.isolate_name));
    const combined = [
        ...selectedGenomes,
        ...extraIsolates
            .filter((isolateName) => isolateName && !names.has(isolateName))
            .map((isolate_name) => ({isolate_name, type_strain: true})),
    ];
    return combined.length ? combined : undefined;
}

/** Locus tags look like BU_ATCC8492_00001 / PV_CCUG68662_01886 — not free-text queries. */
export function looksLikeLocusTag(value: string): boolean {
    return /^[A-Za-z]{1,10}_.+_\d+$/.test(value.trim());
}

/** Homepage rail helper: genomes selected for gene search from genomes + type-strain chips. */
export function geneQueryGenomes(
    genomes: {isolate_name: string; type_strain: boolean}[],
    typeStrains: string[]
): {isolate_name: string; type_strain: boolean}[] {
    const names = new Set(genomes.map((genome) => genome.isolate_name));
    return [
        ...genomes,
        ...typeStrains
            .filter((isolateName) => !names.has(isolateName))
            .map((isolate_name) => ({isolate_name, type_strain: true})),
    ];
}
