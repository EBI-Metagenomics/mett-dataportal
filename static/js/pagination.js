document.addEventListener('DOMContentLoaded', function () {
    console.log('pagination.js loaded');

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
            console.log('Fetching data...');
            const queryString = new URLSearchParams({
                'isolate-name': isolateName,
                'page': page,
                'sortField': sortField,
                'sortOrder': sortOrder
            }).toString();
            const url = `/search/?${queryString}`;
            console.log('Full URL:', url);

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
                updateResultsTable(data.results);
                updatePagination(data);
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        } else {
            console.log('No isolate name provided.');
        }
    }

    function updateResultsTable(results) {
        console.log('Updating results table with results:', results);
        if (!resultsBody) {
            console.error('resultsBody element not found.');
            return;
        }
        resultsBody.innerHTML = ''; // Clear existing results
        results.forEach(result => {
            const row = `
                <tr class="vf-table__row">
                    <td class="vf-table__cell">${result.species}</td>
                    <td class="vf-table__cell">${result.isolate_name}</td>
                    <td class="vf-table__cell"><a href="${result.fasta_file}">${result.assembly_name}</a></td>
                    <td class="vf-table__cell"><a href="${result.gff_file}">GFF</a></td>
                    <td class="vf-table__cell"><a href="${result.gff_file}">Browse</a></td>
                </tr>
            `;
            resultsBody.innerHTML += row;
        });
        console.log('Results table updated.');
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
            pagination.innerHTML += '';

            if (data.has_previous) {
                pagination.innerHTML += `<li class="vf-pagination__item"><a href="#" data-page="1" class="vf-pagination__link">First<span class="vf-u-sr-only"> page</span></a></li>`;
                pagination.innerHTML += `<li class="vf-pagination__item vf-pagination__item--previous-page"><a href="#" data-page="${data.page_number - 1}" class="vf-pagination__link">Previous<span class="vf-u-sr-only"> page</span></a></li>`;
            }

            pagination.innerHTML += `<li class="vf-pagination__item"><span>Page ${data.page_number} of ${data.num_pages}</span></li>`;

            if (data.has_next) {
                pagination.innerHTML += `<li class="vf-pagination__item vf-pagination__item--next-page"><a href="#" data-page="${data.page_number + 1}" class="vf-pagination__link">Next<span class="vf-u-sr-only"> page</span></a></li>`;
                pagination.innerHTML += `<li class="vf-pagination__item"><a href="#" data-page="${data.num_pages}" class="vf-pagination__link">Last<span class="vf-u-sr-only"> page</span></a></li>`;
            }

            console.log('Pagination HTML:', pagination.innerHTML);
            document.querySelectorAll('.vf-pagination__link').forEach(link => {
                link.addEventListener('click', function (event) {
                    event.preventDefault();
                    const page = this.dataset.page;
                    fetchSearchResults(page);
                });
            });

        } else {
            console.log('Pagination not required.');
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
