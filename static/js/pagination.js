document.addEventListener('DOMContentLoaded', function () {
    // console.log('pagination.js loaded');

    const resultsBody = document.querySelector('.vf-table__body');
    const searchForm = document.getElementById('search-form');
    const searchBox = document.getElementById('search-box');
    const hiddenIsolateName = document.getElementById('hidden-isolate-name');

    let currentSortField = '';
    let currentSortOrder = '';

    async function fetchSearchResults(page = 1, sortField = currentSortField, sortOrder = currentSortOrder) {
        console.log('fetchSearchResults called');
        const query = searchBox.value.trim();
        let isolateName = hiddenIsolateName.value.trim();

        if (!isolateName) {
            isolateName = query; // Use the typed query if no isolate name
        }

        if (isolateName) {
            const queryString = new URLSearchParams({
                'isolate_name': isolateName,
                'page': page,
                'sortField': sortField,
                'sortOrder': sortOrder
            }).toString();
            const url = `/api/search/results/?${queryString}`;
            // console.log('Full URL:', url);

            try {
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
                console.log('Fetched data:', data);

                // Extract the `results` array from the response and pass it to `updateResultsTable`
                if (data && Array.isArray(data.results)) {
                    updateResultsTable(data.results); // Pass just the array of results
                    updatePagination(data); // Pass the entire data object to handle pagination
                } else {
                    console.error('Fetched data does not contain a valid results array:', data);
                    updateResultsTable([]); // Pass an empty array to clear the table
                }

            } catch (error) {
                console.error('Error fetching data:', error);
                updateResultsTable([]); // Clear the table in case of an error
            }
        } else {
            console.log('No isolate name provided.');
        }
    }

    window.fetchSearchResults = fetchSearchResults;


    function updateResultsTable(results) {
        console.log('Updating results table with results:', results);
        if (!resultsBody) {
            console.error('resultsBody element not found.');
            return;
        }

        resultsBody.innerHTML = ''; // Clear existing results

        if (!Array.isArray(results)) {
            console.error('Results should be an array but got:', typeof results);
            return;
        }

        results.forEach(result => {
            console.log("result.id:::: " + result);
            const row = `
            <tr class="vf-table__row">
                <td class="vf-table__cell">${result.species || 'Unknown Species'}</td>
                <td class="vf-table__cell">${result.isolate_name || 'Unknown Isolate'}</td>
                <td class="vf-table__cell"><a href="${result.fasta_file || '#'}">${result.assembly_name || 'Unknown Assembly'}</a></td>
                <td class="vf-table__cell"><a href="${result.gff_file || '#'}">GFF</a></td>
                <td class="vf-table__cell"><a href="/jbrowse/${result.id}/">Browse</a></td>
            </tr>
        `;
            resultsBody.innerHTML += row;
        });
        showResultsTable(); // Show the results table
        console.log('Results table updated.');
    }
    window.updateResultsTable = updateResultsTable;

    function showResultsTable() {
        const resultsTable = document.getElementById('results-table');
        if (resultsTable) {
            resultsTable.style.display = 'block';
        }
    }


    function updatePagination(data) {
        console.log('Updating pagination with data:', data);
        const pagination = document.querySelector('.vf-pagination__list');
        if (!pagination) {
            console.error('Pagination container not found');
            return;
        }

        pagination.innerHTML = ''; // Clear existing pagination

        if (data.num_pages > 1) {
            if (data.has_previous) {
                pagination.innerHTML += `
                <li class="vf-pagination__item"><a href="#" data-page="1" class="vf-pagination__link">First<span class="vf-u-sr-only"> page</span></a></li>
                <li class="vf-pagination__item vf-pagination__item--previous-page"><a href="#" data-page="${data.page_number - 1}" class="vf-pagination__link">Previous<span class="vf-u-sr-only"> page</span></a></li>`;
            }

            pagination.innerHTML += `<li class="vf-pagination__item"><span>Page ${data.page_number} of ${data.num_pages}</span></li>`;

            if (data.has_next) {
                pagination.innerHTML += `
                <li class="vf-pagination__item vf-pagination__item--next-page"><a href="#" data-page="${data.page_number + 1}" class="vf-pagination__link">Next<span class="vf-u-sr-only"> page</span></a></li>
                <li class="vf-pagination__item"><a href="#" data-page="${data.num_pages}" class="vf-pagination__link">Last<span class="vf-u-sr-only"> page</span></a></li>`;
            }

            console.log('Pagination HTML:', pagination.innerHTML);

            // Attach event listeners to the pagination links
            document.querySelectorAll('.vf-pagination__link').forEach(link => {
                link.addEventListener('click', function (event) {
                    event.preventDefault();
                    const page = this.dataset.page;
                    fetchSearchResults(page);
                });
            });

        } else {
            console.log('Only one page of results, no pagination needed.');
        }
    }


    // Initial call to fetch results if needed
    fetchSearchResults();

    // Set up form submission handler
    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            event.preventDefault();
            fetchSearchResults();
        });
    }

    // Ensure pagination links are correctly initialized
    document.querySelectorAll('.vf-pagination__link').forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            const page = this.dataset.page;
            fetchSearchResults(page);
        });
    });

    // Add event listeners for sorting
    document.querySelectorAll('.vf-table__button--sortable').forEach(button => {
        button.addEventListener('click', function () {
            const sortField = this.dataset.sortField;

            // Toggle the sort order for the next click
            if (currentSortField === sortField) {
                currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortOrder = 'asc';
            }

            currentSortField = sortField;

            fetchSearchResults(1, currentSortField, currentSortOrder);
        });
    });
});

