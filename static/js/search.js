import {fetchSearchResults, updateResultsTable} from './utils.js';

document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.getElementById('search-form');
    const searchBox = document.getElementById('search-box');
    const hiddenIsolateName = document.getElementById('hidden-isolate-name');
    const resultsBody = document.querySelector('.vf-table__body');

    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            event.preventDefault(); // Prevent the default form submission

            let query = searchBox.value.trim();
            let isolateName = hiddenIsolateName.value.trim();

            if (query && !isolateName) {
                isolateName = query; // If no isolate name selected, use the typed query
            }

            if (isolateName) {
                const queryString = new URLSearchParams({'isolate-name': isolateName}).toString();
                const url = `${searchForm.action}?${queryString}`;

                // console.log('Submitting search with URL:', url);

                fetchSearchResults(url, updateResultsTable, resultsBody)
                    .catch(error => console.error('Search fetch failed:', error));
            } else {
                console.log('No isolate name or query provided, search not submitted.');
            }
        });
    } else {
        console.log('Search form not found in the document.');
    }

    if (!resultsBody) {
        console.log('resultsBody element not found in the document.');
    }
});
