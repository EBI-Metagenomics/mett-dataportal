import {GenomeMeta} from "../../../../interfaces/Genome";
import {joinIndexFile} from "../../../../utils/gene-viewer/jbrowseIndexPaths";

const getAssembly = (genomeMeta: GenomeMeta, fastaDir: string) => ({
    name: genomeMeta.assembly_name,
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
                uri: joinIndexFile(fastaDir, `${genomeMeta.fasta_file}.gz`),
            },
            faiLocation: {
                uri: joinIndexFile(fastaDir, `${genomeMeta.fasta_file}.gz.fai`),
            },
            gziLocation: {
                uri: joinIndexFile(fastaDir, `${genomeMeta.fasta_file}.gz.gzi`),
            },
        }
    },
});

export default getAssembly;
