export function getAnnotationRunIdFromSearch(search: string = window.location.search): string | null {
    const value = new URLSearchParams(search).get('annotation_run_id');
    return value && value.trim() ? value : null;
}

export function withAnnotationRunParam(
    path: string,
    annotationRunId?: string | number | null,
): string {
    if (annotationRunId === undefined || annotationRunId === null || annotationRunId === '') {
        return path;
    }
    const separator = path.includes('?') ? '&' : '?';
    return `${path}${separator}annotation_run_id=${encodeURIComponent(String(annotationRunId))}`;
}

export function currentGenomePath(isolateName: string, locusTag?: string | null): string {
    const base = `/genome/${isolateName}`;
    return locusTag ? `${base}?locus_tag=${encodeURIComponent(locusTag)}` : base;
}
