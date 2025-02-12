import {GenomeMeta} from "../../../interfaces/Genome";

class AssemblyCache {
    private static instance: AssemblyCache;
    private cache: Map<string, any>; // Caches assembly data by assembly name

    private constructor() {
        this.cache = new Map();
    }

    // Singleton instance
    static getInstance(): AssemblyCache {
        if (!AssemblyCache.instance) {
            AssemblyCache.instance = new AssemblyCache();
        }
        return AssemblyCache.instance;
    }

    // Get data from cache
    get(assemblyName: string) {
        return this.cache.get(assemblyName);
    }

    // Set data in cache
    set(assemblyName: string, data: any) {
        this.cache.set(assemblyName, data);
    }

    // Clear the cache
    clear() {
        this.cache.clear();
    }
}

const getAssembly = (genomeMeta: GenomeMeta, fastaBaseUrl: string) => {
    const cache = AssemblyCache.getInstance();
    const assemblyName = genomeMeta.assembly_name;

    // Check if the assembly data is cached
    if (cache.get(assemblyName)) {
        console.log(`Cache hit for assembly: ${assemblyName}`);
        return cache.get(assemblyName);
    }

    console.log(`Cache miss for assembly: ${assemblyName}. Building assembly data.`);

    // Build assembly data
    const assemblyData = {
        name: assemblyName,
        sequence: {
            type: 'ReferenceSequenceTrack',
            trackId: 'reference',
            adapter: {
                type: 'BgzipFastaAdapter',
                sequences: genomeMeta.contigs.map(contig => ({
                    name: contig.seq_id,
                    length: contig.length,
                })),
                fastaLocation: {
                    uri: `${fastaBaseUrl}/${assemblyName}/${genomeMeta.fasta_file}.gz`,
                },
                faiLocation: {
                    uri: `${fastaBaseUrl}/${assemblyName}/${genomeMeta.fasta_file}.gz.fai`,
                },
                gziLocation: {
                    uri: `${fastaBaseUrl}/${assemblyName}/${genomeMeta.fasta_file}.gz.gzi`,
                },
            },
        },
    };

    // Cache the assembly data
    cache.set(assemblyName, assemblyData);

    return assemblyData;
};

export default getAssembly;
