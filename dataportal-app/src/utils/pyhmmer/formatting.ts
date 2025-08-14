export const formatRelativeDate = (dateString: string): string => {
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffInMs = now.getTime() - date.getTime();
        const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
        const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
        const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

        let result: string;
        if (diffInMinutes < 1) result = 'Just now';
        else if (diffInMinutes < 60) result = `${diffInMinutes} min ago`;
        else if (diffInHours < 24) result = `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
        else if (diffInDays < 7) result = `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`;
        else if (diffInDays < 14) result = `${Math.floor(diffInDays / 7)} week ago`;
        else result = date.toLocaleDateString();

        console.log(`formatRelativeDate: "${dateString}" -> "${result}" (${diffInMinutes} min ago)`);
        return result;
    } catch (error) {
        console.error('Error formatting date:', error, 'for date string:', dateString);
        return 'Unknown date';
    }
};

/**
 * Format E-value for display
 */
export const formatEValue = (value: number): string => {
    if (value === 0) return '0';
    if (value < 0.001) return value.toExponential(2);
    return value.toFixed(3);
};

/**
 * Format Bit Score for display
 */
export const formatBitScore = (value: number): string => {
    return value.toFixed(2);
};

/**
 * Format sequence for display (truncate if too long)
 */
export const formatSequence = (sequence: string, maxLength: number = 50): string => {
    if (!sequence) return '';

    const cleanSequence = sequence.replace(/\n/g, '').trim();

    if (cleanSequence.length <= maxLength) {
        return cleanSequence;
    }

    return `${cleanSequence.substring(0, maxLength)}...`;
};

/**
 * Clean FASTA sequence (remove header and newlines)
 */
export const cleanFastaSequence = (sequence: string): string => {
    if (!sequence) return '';

    // Remove FASTA header if present
    const withoutHeader = sequence.replace(/^>.*\n/, '');

    // Remove all newlines and whitespace
    return withoutHeader.replace(/\s/g, '').trim();
};

/**
 * Format database name for display
 */
export const formatDatabaseName = (databaseId: string): string => {
    // Convert database ID to readable name
    const databaseNames: Record<string, string> = {
        'bu_all': 'BU All Strains',
        'bu_pv_all': 'BU + PV All Strains',
        'bu_atcc': 'BU ATCC Strains',
        'pv_all': 'PV All Strains'
    };

    return databaseNames[databaseId] || databaseId;
};

/**
 * Format threshold type for display
 */
export const formatThresholdType = (threshold: 'evalue' | 'bitscore'): string => {
    return threshold === 'evalue' ? 'E-value' : 'Bit Score';
};

/**
 * Format search parameters for display
 */
export const formatSearchParameters = (params: {
    database: string;
    threshold: 'evalue' | 'bitscore';
    threshold_value: string;
    input: string;
}): string => {
    const dbName = formatDatabaseName(params.database);
    const thresholdType = formatThresholdType(params.threshold);
    const sequence = formatSequence(params.input, 30);

    return `${dbName} • ${thresholdType}: ${params.threshold_value} • ${sequence}`;
};

/**
 * Format validation errors for display
 */
export const formatValidationErrors = (errors: Array<{ field: string; message: string }>): string => {
    if (errors.length === 0) return '';

    return errors.map(error => `${error.field}: ${error.message}`).join(', ');
};
