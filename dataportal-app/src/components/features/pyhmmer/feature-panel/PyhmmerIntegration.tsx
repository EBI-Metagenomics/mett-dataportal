import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import { PyhmmerFeaturePanel } from './PyhmmerFeaturePanel';

export const PyhmmerIntegration: React.FC = () => {
    // Global event listener for PyHMMER search links
    useEffect(() => {
        const handlePyhmmerSearchClick = (event: Event) => {
            const target = event.target as HTMLElement;
            if (target.classList.contains('pyhmmer-search-link')) {
                event.preventDefault();
                event.stopPropagation();
                
                const proteinSequence = target.getAttribute('data-pyhmmer-search');
                if (proteinSequence) {
                    console.log('PyHMMER search link clicked for sequence:', proteinSequence);
                    
                    // Inject the search component directly into JBrowse
                    injectPyhmmerSearchIntoFeaturePanel(proteinSequence);
                }
            }
        };

        // Add event listener to the document
        document.addEventListener('click', handlePyhmmerSearchClick, true);

        return () => {
            document.removeEventListener('click', handlePyhmmerSearchClick, true);
        };
    }, []);

    // Function to inject PyHMMER search directly into JBrowse feature panel
    const injectPyhmmerSearchIntoFeaturePanel = (proteinSequence: string) => {
        console.log('Looking for JBrowse feature panel...');
        
        // Try multiple selectors to find the JBrowse feature panel
        let featurePanel = null;
        
        // Common JBrowse selectors
        const selectors = [
            '[data-testid="feature-details"]',
            '.feature-details',
            '[data-testid="jbrowse-feature-details"]',
            '.jbrowse-feature-details',
            '[data-testid="feature-panel"]',
            '.feature-panel',
            '[data-testid="jbrowse-panel"]',
            '.jbrowse-panel',
            // Look for panels containing feature information
            'div[class*="feature"]',
            'div[class*="panel"]',
            'div[class*="details"]',
            // Look for JBrowse-specific elements
            'div[class*="jbrowse"]',
            'div[class*="jbrowse-feature"]',
            // Look for panels that might contain gene information
            'div:has([class*="gene"]), div:has([class*="protein"])',
            'div:has([class*="sequence"]), div:has([class*="annotation"])',
            // More specific JBrowse selectors
            'div[class*="MuiPaper"]', // Material-UI panels
            'div[class*="css-"]', // CSS modules
            'div[class*="drawer"]', // JBrowse drawer panels
            'div[class*="sidebar"]', // JBrowse sidebar
            'div[class*="right"]', // Right-side panels
            'div[class*="east"]' // East-facing panels in JBrowse
        ];
        
        for (const selector of selectors) {
            try {
                const element = document.querySelector(selector);
                if (element) {
                    console.log(`Found potential panel with selector: ${selector}`, element);
                    // Check if this element contains feature-related content
                    const textContent = element.textContent || '';
                    if (textContent.includes('protein') || textContent.includes('sequence') || 
                        textContent.includes('gene') || textContent.includes('annotation') ||
                        textContent.includes('Name') || textContent.includes('ID')) {
                        featurePanel = element;
                        console.log('This looks like a feature panel!');
                        break;
                    }
                }
            } catch (e) {
                console.log(`Selector ${selector} failed:`, e);
            }
        }
        
        // If still not found, try to find any panel that might contain our search link
        if (!featurePanel) {
            console.log('Trying to find panel containing the search link...');
            const searchLinks = document.querySelectorAll('.pyhmmer-search-link');
            for (const link of searchLinks) {
                console.log('Found search link:', link);
                
                // Look for the actual JBrowse feature panel that contains this link
                let currentElement = link.parentElement;
                let depth = 0;
                const maxDepth = 10; // Prevent infinite loops
                
                while (currentElement && depth < maxDepth) {
                    console.log(`Checking parent at depth ${depth}:`, currentElement);
                    
                    // Check if this element looks like a JBrowse feature panel
                    const classes = currentElement.className || '';
                    const textContent = currentElement.textContent || '';
                    
                    if (classes.includes('jbrowse') || 
                        classes.includes('feature') || 
                        classes.includes('panel') ||
                        classes.includes('details') ||
                        textContent.includes('protein') ||
                        textContent.includes('sequence') ||
                        textContent.includes('gene') ||
                        textContent.includes('Name') ||
                        textContent.includes('ID')) {
                        
                        featurePanel = currentElement;
                        console.log('✅ Found JBrowse feature panel containing search link:', currentElement);
                        console.log('Panel classes:', classes);
                        console.log('Panel content preview:', textContent.substring(0, 200));
                        break;
                    }
                    
                    currentElement = currentElement.parentElement;
                    depth++;
                }
                
                if (featurePanel) break;
            }
        }
        
        if (featurePanel) {
            console.log('Found JBrowse feature panel, injecting PyHMMER search');
            
            // Create a container for our search component
            const searchContainer = document.createElement('div');
            searchContainer.id = 'pyhmmer-search-container';
            
            // Remove any existing search container
            const existingContainer = document.getElementById('pyhmmer-search-container');
            if (existingContainer) {
                existingContainer.remove();
            }
            
            // Find the best location to inject the search component within the feature panel
            const searchLinkInPanel = featurePanel.querySelector('.pyhmmer-search-link');
            if (searchLinkInPanel) {
                console.log('✅ Found search link in panel, injecting after it');
                // Insert after the search link
                searchLinkInPanel.parentNode?.insertBefore(searchContainer, searchLinkInPanel.nextSibling);
            } else {
                console.log('⚠️ Search link not found in panel, appending to end');
                // Fallback: append to the end of the feature panel
                featurePanel.appendChild(searchContainer);
            }
            
            console.log('✅ Search container added to feature panel');
            
            // Make sure the search container is visible
            searchContainer.style.display = 'block';
            
            // Render the React component into the container
            ReactDOM.render(<PyhmmerFeaturePanel proteinSequence={proteinSequence} />, searchContainer);
            
        } else {
            console.log('JBrowse feature panel not found, trying fallback approach...');
            
            // Fallback: Find the search link and inject the search component right after it
            const searchLinks = document.querySelectorAll('.pyhmmer-search-link');
            if (searchLinks.length > 0) {
                const searchLink = searchLinks[0] as HTMLElement;
                const parentElement = searchLink.parentElement;
                
                if (parentElement) {
                    console.log('Using fallback: injecting after search link');
                    
                    // Create a container for our search component
                    const searchContainer = document.createElement('div');
                    searchContainer.id = 'pyhmmer-search-container';
                    
                    // Remove any existing search container
                    const existingContainer = document.getElementById('pyhmmer-search-container');
                    if (existingContainer) {
                        existingContainer.remove();
                    }
                    
                    // Insert the search container after the search link
                    searchLink.parentNode?.insertBefore(searchContainer, searchLink.nextSibling);
                    
                    // Render the React component into the container
                    ReactDOM.render(<PyhmmerFeaturePanel proteinSequence={proteinSequence} />, searchContainer);
                } else {
                    console.error('Could not find parent element for search link');
                }
            } else {
                console.error('No search links found for fallback');
            }
        }
    };

    // This component doesn't render anything visible
    // It just sets up the event listeners and provides the injection logic
    return null;
};
