import { extractIsolateName } from './utils.js';

document.addEventListener('DOMContentLoaded', function () {
    const searchBox = document.getElementById('search-box');
    const suggestionsContainer = document.getElementById('suggestions');
    const hiddenIsolateName = document.getElementById('hidden-isolate-name');

    function displaySuggestions(suggestions) {
        suggestionsContainer.innerHTML = ''; // Clear previous suggestions
        suggestions.forEach(suggestion => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.textContent = suggestion;

            suggestionItem.addEventListener('click', function () {
                searchBox.value = suggestion; // Show full suggestion in search box
                hiddenIsolateName.value = extractIsolateName(suggestion); // Store isolate name in hidden field
                suggestionsContainer.innerHTML = ''; // Clear suggestions
            });

            suggestionsContainer.appendChild(suggestionItem);
        });
    }

    async function fetchSuggestions() {
        const query = searchBox.value;
        if (query.length >= 2) {
            try {
                const response = await fetch(`/autocomplete/?query=${encodeURIComponent(query)}`);
                if (response.ok) {
                    const data = await response.json();
                    displaySuggestions(data.suggestions);
                } else {
                    console.error('Error fetching suggestions:', response.statusText);
                }
            } catch (error) {
                console.error('Network error:', error);
            }
        } else {
            suggestionsContainer.innerHTML = ''; // Clear suggestions if input is less than 2 characters
        }
    }

    function debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    }

    const debouncedFetchSuggestions = debounce(fetchSuggestions, 300); // todo - externalise

    // Hide suggestions when clicking outside
    document.addEventListener('click', function(event) {
        if (!suggestionsContainer.contains(event.target) && event.target !== searchBox) {
            suggestionsContainer.innerHTML = ''; // Clear suggestions
        }
    });

    searchBox.addEventListener('input', function() {
        hiddenIsolateName.value = ''; // Clear hidden field when user types
        debouncedFetchSuggestions();
    });
});
