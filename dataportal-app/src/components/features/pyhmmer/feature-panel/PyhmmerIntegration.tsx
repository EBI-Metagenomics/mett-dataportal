import React, {useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import {PyhmmerFeaturePanel} from '@components/features';
import {PYHMMER_CONSTANTS} from '../../../../utils/pyhmmer';
import styles from './PyhmmerIntegration.module.scss';

export const PyhmmerIntegration: React.FC = () => {
    console.log('PyhmmerIntegration: Component loaded');

    useEffect(() => {
        console.log('PyhmmerIntegration: Starting integration');
        
        // Clean up any existing styled elements
        const existingButtons = document.querySelectorAll('.pyhmmer-button-styled');
        existingButtons.forEach(button => {
            button.classList.remove('pyhmmer-button-styled', styles.pyhmmerButton, styles.buttonHover);
        });

        // Function to style the search button
        const styleSearchButton = () => {
            // Hide unwanted attributes first
            const hideUnwantedAttributes = () => {
                const allElements = document.querySelectorAll('*');
                allElements.forEach(element => {
                    const text = element.textContent || '';
                    if (text.includes('pyhmmerSearch.proteinSequence') ||
                        text.includes('pyhmmerSearch.proteinLength') ||
                        text.includes('pyhmmerSearch.pyhmmerSearchLink')) {
                        // Only hide the field name elements, not the value elements
                        if (element.classList.contains('css-ify9vk-fieldName')) {
                            console.log('PyhmmerIntegration: Hiding unwanted attribute name:', text);
                            (element as HTMLElement).style.display = 'none';
                        }
                    }
                });
            };

            hideUnwantedAttributes();

            // Find and style the search button
            const allElements = document.querySelectorAll('*');
            let foundButton = false;

            allElements.forEach(element => {
                const text = element.textContent || '';
                if (text.includes('Search Protein Domains') && !element.classList.contains('pyhmmer-button-styled')) {
                    // Check if this is a suitable element to style
                    if (element.classList.contains('css-1m8nxnb-field') ||
                        element.classList.contains('css-xb19vs-fieldValue') ||
                        (element.tagName === 'SPAN' && element.textContent?.trim() === text.trim()) ||
                        (element.tagName === 'DIV' && element.children.length === 0)) {

                        if (!foundButton) {
                            console.log('PyhmmerIntegration: Found Search Protein Domains element, styling it as button');
                            
                            // Style the element
                            element.classList.add('pyhmmer-button-styled');
                            element.classList.add(styles.pyhmmerButton);

                            // Remove any existing href or link behavior
                            if (element.tagName === 'A') {
                                (element as HTMLAnchorElement).href = 'javascript:void(0);';
                                (element as HTMLAnchorElement).target = '';
                                (element as HTMLAnchorElement).rel = '';
                            }

                            // Add click handler
                            const clickHandler = (e: Event) => {
                                console.log('PyhmmerIntegration: Button clicked!');
                                e.preventDefault();
                                e.stopPropagation();
                                e.stopImmediatePropagation();

                                // Extract protein sequence
                                let sequence = '';
                                const panel = element.closest('.MuiAccordionDetails-root, [role="region"]');
                                
                                if (panel) {
                                    const panelText = panel.textContent || '';
                                    
                                    // Try multiple sequence patterns
                                    const seqMatch = panelText.match(/pyhmmerSearch\._proteinSequence([A-Z*]+)/);
                                    if (seqMatch) {
                                        sequence = seqMatch[1];
                                    } else {
                                        const seqMatch2 = panelText.match(/pyhmmerSearch\.proteinSequence([A-Z*]+)/);
                                        if (seqMatch2) {
                                            sequence = seqMatch2[1];
                                        } else {
                                            const seqMatch3 = panelText.match(/([A-Z]{20,})/);
                                            if (seqMatch3) {
                                                sequence = seqMatch3[1];
                                            }
                                        }
                                    }

                                    if (sequence) {
                                        console.log('PyhmmerIntegration: Sequence found, injecting search panel');
                                        injectPyhmmerSearchIntoFeaturePanel(sequence);
                                    } else {
                                        console.log('PyhmmerIntegration: Could not find sequence');
                                    }
                                }

                                return false;
                            };

                            // Remove existing handlers and add new one
                            element.removeEventListener('click', clickHandler);
                            element.addEventListener('click', clickHandler, true);

                            // Add hover effects
                            element.addEventListener('mouseenter', () => {
                                element.classList.add(styles.buttonHover);
                            });

                            element.addEventListener('mouseleave', () => {
                                element.classList.remove(styles.buttonHover);
                            });

                            foundButton = true;
                            console.log('PyhmmerIntegration: Successfully styled Search Protein Domains as button');
                        }
                    }
                }
            });

            return foundButton;
        };

        // Set up MutationObserver to watch for DOM changes
        const observer = new MutationObserver((mutations) => {
            let shouldStyle = false;
            
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const element = node as Element;
                            if (element.textContent?.includes('Search Protein Domains')) {
                                shouldStyle = true;
                            }
                        }
                    });
                }
            });

            if (shouldStyle) {
                console.log('PyhmmerIntegration: DOM change detected, re-styling button');
                setTimeout(styleSearchButton, 100); // Small delay to ensure DOM is ready
            }
        });

        // Start observing
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Initial styling
        styleSearchButton();

        // Cleanup function
        return () => {
            observer.disconnect();
            
            // Clean up styled elements
            const buttons = document.querySelectorAll('.pyhmmer-button-styled');
            buttons.forEach(button => {
                button.classList.remove('pyhmmer-button-styled', styles.pyhmmerButton, styles.buttonHover);
            });
            
            // Cleanup complete
        };
    }, []);

    // Function to inject the PyHMMER search panel
    const injectPyhmmerSearchIntoFeaturePanel = (proteinSequence: string) => {
        console.log('PyhmmerIntegration: injectPyhmmerSearchIntoFeaturePanel called with sequence length:', proteinSequence.length);

        // Find or create container
        let container = document.getElementById('pyhmmer-search-react');
        if (!container) {
            container = document.createElement('div');
            container.id = 'pyhmmer-search-react';
        }

        // Clear existing content
        container.innerHTML = '';

        // Make the container collapsible
        container.className = styles.searchPanelContainer;

        // Create collapsible header
        const header = document.createElement('div');
        header.className = styles.searchPanelHeader;
        header.innerHTML = `
            <span class="${styles.searchPanelTitle}">🧬 PyHMMER Protein Search</span>
            <span class="${styles.searchPanelToggle}">−</span>
        `;

        // Create content container
        const content = document.createElement('div');
        content.id = 'pyhmmer-search-content';
        content.className = styles.searchPanelContent;

        // Toggle functionality
        let isCollapsed = false;
        header.addEventListener('click', () => {
            isCollapsed = !isCollapsed;
            if (isCollapsed) {
                content.style.display = 'none';
                header.querySelector('span:last-child')!.textContent = '+';
            } else {
                content.style.display = 'block';
                header.querySelector('span:last-child')!.textContent = '−';
            }
        });

        // Add structure to container
        container.appendChild(header);
        container.appendChild(content);

        // Position the container
        const button = document.querySelector('.pyhmmer-button-styled');
        if (button && button.parentNode) {
            const jbrowsePanel = button.closest('.MuiAccordionDetails-root, [role="region"]');
            if (jbrowsePanel) {
                try {
                    const buttonParent = button.parentNode;
                    if (buttonParent && buttonParent.parentNode) {
                        buttonParent.parentNode.insertBefore(container, buttonParent.nextSibling);
                    } else {
                        jbrowsePanel.appendChild(container);
                    }
                } catch (error) {
                    jbrowsePanel.appendChild(container);
                }
            } else {
                button.parentNode.appendChild(container);
            }
        } else {
            // Fallback positioning
            const panel = document.querySelector('.MuiAccordionDetails-root, [role="region"]');
            if (panel) {
                panel.appendChild(container);
            } else {
                document.body.appendChild(container);
            }
        }

        // Mount React component
        try {
            const root = createRoot(content);
            root.render(<PyhmmerFeaturePanel proteinSequence={proteinSequence}/>);
            console.log('PyhmmerIntegration: PyhmmerFeaturePanel rendered successfully');
        } catch (error) {
            console.error('PyhmmerIntegration: Error rendering PyhmmerFeaturePanel:', error);
        }

        // Make container visible
        container.style.display = 'block';
        container.style.visibility = 'visible';
    };

    // Return null since this is a utility component
    return null;
};
