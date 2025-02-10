
export const copyToClipboard = (text: string) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        // Modern API
        navigator.clipboard.writeText(text)
            .then(() => {
                alert('Copied to clipboard!');
            })
            .catch((err) => {
                console.error('Failed to copy text to clipboard:', err);
                alert('Failed to copy to clipboard.');
            });
    } else {
        // Fallback for unsupported browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();

        try {
            const successful = document.execCommand('copy');
            if (successful) {
                alert('Copied to clipboard!');
            } else {
                alert('Failed to copy to clipboard.');
            }
        } catch (err) {
            console.error('Fallback: Oops, unable to copy', err);
        }

        document.body.removeChild(textArea);
    }
};

export const generateCurlRequest = (apiRequestDetails: {
    url: string;
    method: string;
    headers: any;
    params?: any
} | null) => {
    if (!apiRequestDetails) return '';

    const {url, method, headers, params} = apiRequestDetails;

    // Convert params object to query string
    const queryString = params && Object.keys(params).length > 0
        ? '?' + new URLSearchParams(params).toString()
        : '';

    let curlCommand = `curl -X ${method} '${url}${queryString}'`;

    // Append headers
    Object.entries(headers).forEach(([key, value]) => {
        curlCommand += ` -H '${key}: ${value}'`;
    });

    return curlCommand;
};

export const generateHttpRequest = (apiRequestDetails: { url: string; method: string; params?: any } | null) => {
    if (!apiRequestDetails) return '';

    const {url, method, params} = apiRequestDetails;

    // Convert params object to query string
    const queryString = params && Object.keys(params).length > 0
        ? '?' + new URLSearchParams(params).toString()
        : '';

    return `${url}${queryString}`;
};


export const downloadTableData = (data: any[], format: 'csv' | 'json', filename = 'table_data') => {
    if (!data || data.length === 0) {
        alert('No data available for download.');
        return;
    }

    if (format === 'json') {
        const jsonData = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonData], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.json`;
        a.click();
        URL.revokeObjectURL(url);
    } else if (format === 'csv') {
        const headers = Object.keys(data[0]).join(',') + '\n';
        const csvContent = data.map(row => Object.values(row).join(',')).join('\n');
        const csv = headers + csvContent;
        const blob = new Blob([csv], {type: 'text/csv'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${filename}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }
};
