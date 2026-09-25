/**
 * Build JBrowse FASTA/GFF index directories from one configurable root.
 *
 * `VITE_JBROWSE_INDEXES_PATH` is the shared prefix, e.g.
 *   https://ftp.ebi.ac.uk/pub/databases/metagenomics/jbrowse_files/mett
 *
 * Code appends /{release}/{species}/fasta/{assembly} or /gff3/{isolate}.
 * Optional placeholders in the root: {release} {species}
 *
 * Examples (release v1, species BU, isolate BU_61, assembly BU_61_NT5381.1):
 *   fasta → …/mett/v1/BU/fasta/BU_61_NT5381.1
 *   gff3  → …/mett/v1/BU/gff3/BU_61
 */

export const JBROWSE_PATH_PLACEHOLDERS = [
    'release',
    'species',
    'isolate',
    'assembly',
] as const;

export type JbrowsePathPlaceholder = (typeof JBROWSE_PATH_PLACEHOLDERS)[number];

export type JbrowseIndexKind = 'fasta' | 'gff3';

export interface JbrowseReleaseCatalog {
    current_version?: string | null;
    releases?: Array<{version: string; is_current: boolean}>;
}

export interface JbrowsePathVars {
    release: string;
    species: string;
    isolate: string;
    assembly: string;
}

const PLACEHOLDER_RE = /\{(release|species|isolate|assembly)\}/g;
const HAS_PLACEHOLDER_RE = /\{(release|species|isolate|assembly)\}/;

export function fastaAssemblyFolder(fastaFile?: string, assemblyName?: string): string {
    if (fastaFile) {
        return fastaFile.replace(/\.(fa|fna|fasta)(\.gz)?$/i, '');
    }
    return assemblyName || '';
}

export function resolveJbrowseReleaseFolder(
    selected: string | undefined,
    catalog?: JbrowseReleaseCatalog | null
): string {
    const token = (selected || '').trim();
    if (token && token !== 'current') {
        return token.replace(/^\/+/, '');
    }
    const fromCatalog =
        catalog?.current_version || catalog?.releases?.find((r) => r.is_current)?.version;
    return (fromCatalog || 'v1').replace(/^\/+/, '');
}

export function joinUrlSegments(...parts: string[]): string {
    const cleaned = parts
        .filter((p) => p != null && String(p).length > 0)
        .map((p, i) => {
            const s = String(p).replace(/\\/g, '/');
            if (i === 0) {
                return s.replace(/\/+$/, '');
            }
            return s.replace(/^\/+|\/+$/g, '');
        })
        .filter((s) => s.length > 0);
    return cleaned.join('/');
}

export function interpolateJbrowsePath(template: string, vars: JbrowsePathVars): string {
    return template.replace(PLACEHOLDER_RE, (_, key: JbrowsePathPlaceholder) => vars[key] || '');
}

export function buildJbrowseIndexDir(
    basePath: string,
    kind: JbrowseIndexKind,
    vars: JbrowsePathVars
): string {
    const trimmed = (basePath || '').trim();
    if (!trimmed) {
        return '';
    }
    if (HAS_PLACEHOLDER_RE.test(trimmed)) {
        const interpolated = interpolateJbrowsePath(trimmed, vars).replace(/\/+$/, '');
        if (kind === 'fasta') {
            return joinUrlSegments(interpolated, 'fasta', vars.assembly);
        }
        return joinUrlSegments(interpolated, 'gff3', vars.isolate);
    }
    if (kind === 'fasta') {
        return joinUrlSegments(trimmed, vars.release, vars.species, 'fasta', vars.assembly);
    }
    return joinUrlSegments(trimmed, vars.release, vars.species, 'gff3', vars.isolate);
}

export function buildJbrowseIndexDirs(options: {
    basePath: string;
    selectedRelease?: string;
    catalog?: JbrowseReleaseCatalog | null;
    isolateName: string;
    speciesAcronym?: string;
    fastaFile?: string;
    assemblyName?: string;
}): {fastaDir: string; gffDir: string} {
    const vars: JbrowsePathVars = {
        release: resolveJbrowseReleaseFolder(options.selectedRelease, options.catalog),
        species: (options.speciesAcronym || '').toUpperCase(),
        isolate: options.isolateName,
        assembly: fastaAssemblyFolder(options.fastaFile, options.assemblyName),
    };
    return {
        fastaDir: buildJbrowseIndexDir(options.basePath, 'fasta', vars),
        gffDir: buildJbrowseIndexDir(options.basePath, 'gff3', vars),
    };
}

export function joinIndexFile(dir: string, filename: string): string {
    return joinUrlSegments(dir, filename);
}
