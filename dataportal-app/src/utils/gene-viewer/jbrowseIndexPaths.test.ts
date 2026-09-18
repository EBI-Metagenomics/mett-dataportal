import {
    buildJbrowseIndexDir,
    buildJbrowseIndexDirs,
    fastaAssemblyFolder,
    joinIndexFile,
    resolveJbrowseReleaseFolder,
} from './jbrowseIndexPaths';

const ROOT = 'https://ftp.ebi.ac.uk/pub/databases/metagenomics/jbrowse_files/mett';

describe('jbrowseIndexPaths', () => {
    const vars = {
        release: 'v1',
        species: 'BU',
        isolate: 'BU_61',
        assembly: 'BU_61_NT5381.1',
    };

    it('strips .fa from fasta_file for the assembly folder', () => {
        expect(fastaAssemblyFolder('BU_61_NT5381.1.fa', 'ignored')).toBe('BU_61_NT5381.1');
    });

    it('resolves current to the catalog current_version', () => {
        expect(resolveJbrowseReleaseFolder('current', {current_version: 'v1'})).toBe('v1');
        expect(resolveJbrowseReleaseFolder('v2', {current_version: 'v1'})).toBe('v2');
    });

    it('falls back to v1 when current has no catalog', () => {
        expect(resolveJbrowseReleaseFolder('current', null)).toBe('v1');
    });

    it('appends the versioned layout to a root URL', () => {
        expect(buildJbrowseIndexDir(ROOT, 'fasta', vars)).toBe(
            `${ROOT}/v1/BU/fasta/BU_61_NT5381.1`
        );
        expect(buildJbrowseIndexDir(ROOT, 'gff3', vars)).toBe(`${ROOT}/v1/BU/gff3/BU_61`);
    });

    it('interpolates {release} and {species} in a shared root template', () => {
        const tpl = `${ROOT}/{release}/{species}`;
        expect(buildJbrowseIndexDir(tpl, 'fasta', vars)).toBe(
            `${ROOT}/v1/BU/fasta/BU_61_NT5381.1`
        );
        expect(buildJbrowseIndexDir(tpl, 'gff3', vars)).toBe(`${ROOT}/v1/BU/gff3/BU_61`);
    });

    it('builds both dirs from genome metadata matching the EBI layout', () => {
        const dirs = buildJbrowseIndexDirs({
            basePath: ROOT,
            selectedRelease: 'current',
            catalog: {current_version: 'v1'},
            isolateName: 'BU_61',
            speciesAcronym: 'bu',
            fastaFile: 'BU_61_NT5381.1.fa',
        });
        expect(dirs.fastaDir).toBe(`${ROOT}/v1/BU/fasta/BU_61_NT5381.1`);
        expect(dirs.gffDir).toBe(`${ROOT}/v1/BU/gff3/BU_61`);
        expect(joinIndexFile(dirs.fastaDir, 'BU_61_NT5381.1.fa.gz')).toBe(
            `${ROOT}/v1/BU/fasta/BU_61_NT5381.1/BU_61_NT5381.1.fa.gz`
        );
        expect(joinIndexFile(dirs.gffDir, 'BU_61_annotations.gff.gz')).toBe(
            `${ROOT}/v1/BU/gff3/BU_61/BU_61_annotations.gff.gz`
        );
    });

    it('returns empty when the template is unset', () => {
        expect(buildJbrowseIndexDir('', 'fasta', vars)).toBe('');
    });
});
