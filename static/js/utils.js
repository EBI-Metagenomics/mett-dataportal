export function extractIsolateName(suggestion) {
    const parts = suggestion.split(' - ');
    if (parts.length > 1) {
        return parts[1].split(' (')[0].trim(); // Extract and trim isolate name
    }
    return suggestion;
}

export function showResultsTable() {
    const resultsTable = document.getElementById('results-table');
    if (resultsTable) {
        resultsTable.style.display = 'block';
    }
}

// Update the HTML table with search results
export function updateResultsTable(results, resultsBody) {
    if (!resultsBody) {
        console.error('resultsBody is null when attempting to update results table');
        return;
    }

    resultsBody.innerHTML = ''; // Clear existing rows

    if (results.length === 0) {
        resultsBody.innerHTML = '<tr><td colspan="5">No results found</td></tr>';
    } else {
        results.forEach(result => {
            const row = `
                <tr class="vf-table__row">
                    <td class="vf-table__cell">${result.species}</td>
                    <td class="vf-table__cell">${result.isolate_name}</td>
                    <td class="vf-table__cell"><a href="${result.fasta_file}" target="_blank">${result.assembly_name}</a></td>
                    <td class="vf-table__cell"><a href="${result.gff_file}" target="_blank">GFF</a></td>
                    <td class="vf-table__cell"><a href="${result.gff_file}" target="_blank">Browse</a></td>
                </tr>
            `;
            resultsBody.innerHTML += row;
        });
    }

    showResultsTable(); // Show the results table
}

// Fetch search results from the server
export async function fetchSearchResults(url, updateResultsTable, resultsBody) {
    // console.log('Fetching search results from URL:', url);
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    updateResultsTable(data.results, resultsBody);
    return data;
}


