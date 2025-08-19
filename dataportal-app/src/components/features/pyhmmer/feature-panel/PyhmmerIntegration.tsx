import React, {useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import {PyhmmerFeaturePanel} from '@components/features';
import {PYHMMER_CONSTANTS} from '../../../../utils/pyhmmer';
import styles from './PyhmmerIntegration.module.scss';

export const PyhmmerIntegration: React.FC = () => {
    console.log('PyhmmerIntegration: Component loaded');

    useEffect(() => {
        console.log('PyhmmerIntegration: useEffect running');

        // Simple approach: style the existing pyhmmerSearch.pyhmmerSearchLink to look like a button
        const styleLink = () => {
            // First, hide the unwanted attributes
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
                        // Don't hide css-1m8nxnb-field elements as they contain the actual values
                    }
                });
            };

            // Hide unwanted attributes first
            hideUnwantedAttributes();

            // Find elements containing the pyhmmerSearch.pyhmmerSearchLink text
            const allElements = document.querySelectorAll('*');
            let foundFieldElement = false;

            allElements.forEach(element => {
                const text = element.textContent || '';
                // Look for the actual button text instead of the hidden attribute name
                if (text.includes('Search Protein Domains')) {
                    // Check if we already styled this element
                    if (element.classList.contains('pyhmmer-button-styled')) {
                        return;
                    }

                    // Be VERY specific about which elements we can style
                    // Only style elements that are likely to be button values, not entire containers
                    if (element.classList.contains('css-1m8nxnb-field') ||
                        element.classList.contains('css-xb19vs-fieldValue') ||
                        (element.tagName === 'SPAN' && element.textContent?.trim() === text.trim()) ||
                        (element.tagName === 'DIV' && element.children.length === 0)) {

                        // Only style if we haven't found a field element yet (avoid duplicates)
                        if (!foundFieldElement) {
                            console.log('PyhmmerIntegration: Found Search Protein Domains element, styling it as button');
                            console.log('PyhmmerIntegration: Element details:', {
                                tagName: element.tagName,
                                className: element.className,
                                textContent: element.textContent?.substring(0, 50)
                            });

                            // Style this element directly as the button
                            console.log('PyhmmerIntegration: Styling element as button');

                            // Add button styling to the element - be very specific to avoid affecting other elements
                            element.classList.add('pyhmmer-button-styled');
                            element.classList.add(styles.pyhmmerButton);

                            // Remove any existing href or link behavior
                            if (element.tagName === 'A') {
                                (element as HTMLAnchorElement).href = 'javascript:void(0);';
                                (element as HTMLAnchorElement).target = '';
                                (element as HTMLAnchorElement).rel = '';
                            }

                            // Add click handler with stronger event prevention
                            const clickHandler = (e: Event) => {
                                console.log('PyhmmerIntegration: Button clicked!');
                                e.preventDefault();
                                e.stopPropagation();
                                e.stopImmediatePropagation();

                                // Try to find the sequence in multiple ways
                                let sequence = '';

                                // Method 1: Look in the closest panel
                                const panel = element.closest('.MuiAccordionDetails-root, [role="region"]');
                                if (panel) {
                                    console.log('PyhmmerIntegration: Found panel, extracting sequence...');
                                    const panelText = panel.textContent || '';
                                    console.log('PyhmmerIntegration: Full panel text length:', panelText.length);

                                    // Try multiple sequence patterns
                                    const seqMatch = panelText.match(/pyhmmerSearch\._proteinSequence([A-Z*]+)/);
                                    if (seqMatch) {
                                        sequence = seqMatch[1];
                                        console.log('PyhmmerIntegration: Found sequence with pattern 1:', sequence.length);
                                    } else {
                                        const altMatch = panelText.match(/_proteinSequence([A-Z*]+)/);
                                        if (altMatch) {
                                            sequence = altMatch[1];
                                            console.log('PyhmmerIntegration: Found sequence with pattern 2:', sequence.length);
                                        } else {
                                            console.log('PyhmmerIntegration: No sequence found in panel');
                                        }
                                    }
                                }

                                // Method 2: If no sequence found, search the entire document
                                if (!sequence) {
                                    console.log('PyhmmerIntegration: Searching entire document for sequence...');
                                    const allElements = document.querySelectorAll('*');
                                    for (const elem of allElements) {
                                        const text = elem.textContent || '';
                                        if (text.includes('pyhmmerSearch._proteinSequence')) {
                                            const seqMatch = text.match(/pyhmmerSearch\._proteinSequence([A-Z*]+)/);
                                            if (seqMatch) {
                                                sequence = seqMatch[1];
                                                console.log('PyhmmerIntegration: Found sequence in document search:', sequence.length);
                                                break;
                                            }
                                        }
                                    }
                                }

                                // Method 3: Look for any protein sequence
                                if (!sequence) {
                                    console.log('PyhmmerIntegration: Looking for any protein sequence...');
                                    const allElements = document.querySelectorAll('*');
                                    for (const elem of allElements) {
                                        const text = elem.textContent || '';
                                        if (text.includes('protein_sequence') && text.length > 100) {
                                            const seqMatch = text.match(/protein_sequence([A-Z*]+)/);
                                            if (seqMatch) {
                                                sequence = seqMatch[1];
                                                console.log('PyhmmerIntegration: Found protein sequence:', sequence.length);
                                                break;
                                            }
                                        }
                                    }
                                }

                                if (sequence) {
                                    console.log('PyhmmerIntegration: Button clicked, sequence length:', sequence.length);
                                    injectPyhmmerSearchIntoFeaturePanel(sequence);
                                } else {
                                    console.log('PyhmmerIntegration: Could not find any sequence, showing available content...');
                                    // Show what's actually available in the panel
                                    if (panel) {
                                        const panelText = panel.textContent || '';
                                        const lines = panelText.split('\n').filter(line => line.trim().length > 0);
                                        console.log('PyhmmerIntegration: Available panel content lines:', lines.slice(0, 10));
                                    }
                                }

                                return false;
                            };

                            // Remove any existing click handlers and add our own
                            element.removeEventListener('click', clickHandler);
                            element.addEventListener('click', clickHandler, true);

                            // Add hover effect - darker blue on hover
                            element.addEventListener('mouseenter', () => {
                                element.classList.add(styles.buttonHover);
                            });

                            element.addEventListener('mouseleave', () => {
                                element.classList.remove(styles.buttonHover);
                            });

                            console.log('PyhmmerIntegration: Successfully styled Search Protein Domains as button');
                            foundFieldElement = true;
                        }
                    }
                }
            });

            if (!foundFieldElement) {
                console.log('PyhmmerIntegration: No suitable field element found for styling');
            }

            // Return whether we found and styled an element
            return foundFieldElement;
        };

        // Run immediately and set up interval to catch late-rendered elements
        let interval: any;
        let startTime = Date.now();

        const runStyling = () => {
            const success = styleLink();
            if (success) {
                // If we successfully styled the button, clear the interval
                console.log('PyhmmerIntegration: Button styled successfully, stopping interval');
                clearInterval(interval);
            } else {
                // If we've been trying for more than the configured timeout, stop to avoid infinite logs
                if (Date.now() - startTime > PYHMMER_CONSTANTS.TIMING.BUTTON_STYLING_TIMEOUT) {
                    console.log('PyhmmerIntegration: No button found after timeout, stopping interval');
                    clearInterval(interval);
                }
            }
        };

        runStyling();
        interval = setInterval(runStyling, PYHMMER_CONSTANTS.TIMING.STYLING_CHECK_INTERVAL);

        return () => {
            if (interval) {
                clearInterval(interval);
            }
        };
    }, []);

    // Render the React component when the button is clicked
    const injectPyhmmerSearchIntoFeaturePanel = (proteinSequence: string) => {
        console.log('PyhmmerIntegration: injectPyhmmerSearchIntoFeaturePanel called with sequence length:', proteinSequence.length);

        // Find or create container
        let container = document.getElementById('pyhmmer-search-react');
        if (!container) {
            console.log('PyhmmerIntegration: Creating new container');
            container = document.createElement('div');
            container.id = 'pyhmmer-search-react';

            // Try to find the button to position the panel next to it
            const button = document.querySelector('.pyhmmer-button-styled');
            console.log('PyhmmerIntegration: Found button:', button);

            if (button && button.parentNode) {
                console.log('PyhmmerIntegration: Positioning container after button');
                // Find the actual JBrowse feature panel that contains the button
                const jbrowsePanel = button.closest('.MuiAccordionDetails-root, [role="region"], .MuiAccordion-region');
                console.log('PyhmmerIntegration: JBrowse panel found:', jbrowsePanel);

                if (jbrowsePanel) {
                    // Always insert into the JBrowse feature panel, but try to position it after the button
                    try {
                        // Find the button's immediate parent container
                        const buttonParent = button.parentNode;
                        if (buttonParent && buttonParent.parentNode) {
                            // Insert after the button's parent container
                            buttonParent.parentNode.insertBefore(container, buttonParent.nextSibling);
                            console.log('PyhmmerIntegration: Container inserted after button parent');
                        } else {
                            // Fallback: append to the end of the JBrowse panel
                            jbrowsePanel.appendChild(container);
                            console.log('PyhmmerIntegration: Container appended to JBrowse panel');
                        }
                    } catch (error) {
                        console.log('PyhmmerIntegration: Error with positioning, falling back to panel append');
                        // Fallback: append to the end of the JBrowse panel
                        jbrowsePanel.appendChild(container);
                    }
                } else {
                    // Fallback: try to find the button's immediate parent row
                    const buttonRow = button.closest('div[style*="display: flex"]') || button.parentNode;
                    console.log('PyhmmerIntegration: Button row:', buttonRow);
                    if (buttonRow && buttonRow.parentNode) {
                        buttonRow.parentNode.insertBefore(container, buttonRow.nextSibling);
                        console.log('PyhmmerIntegration: Container inserted after button row');
                    } else {
                        // Last resort: append to the button's parent
                        button.parentNode.appendChild(container);
                        console.log('PyhmmerIntegration: Container appended to button parent');
                    }
                }
            } else {
                console.log('PyhmmerIntegration: Using fallback positioning');
                // Fallback: find the panel and append to it
                const panel = document.querySelector('.MuiAccordionDetails-root, [role="region"]');
                if (panel) {
                    console.log('PyhmmerIntegration: Appending to panel');
                    panel.appendChild(container);
                } else {
                    console.log('PyhmmerIntegration: Appending to body');
                    document.body.appendChild(container);
                }
            }
        } else {
            console.log('PyhmmerIntegration: Using existing container');
        }

        console.log('PyhmmerIntegration: Container element:', container);
        console.log('PyhmmerIntegration: Container parent:', container.parentNode);

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

        // Clear existing content and add new structure
        container.innerHTML = '';
        container.appendChild(header);
        container.appendChild(content);

        console.log('PyhmmerIntegration: Container structure created, header and content added');
        console.log('PyhmmerIntegration: Container children count:', container.children.length);

        // Mount with React 18 root
        try {
            const root = (content as any).__root || createRoot(content);
            (content as any).__root = root;
            console.log('PyhmmerIntegration: React root created, rendering PyhmmerFeaturePanel');
            root.render(<PyhmmerFeaturePanel proteinSequence={proteinSequence}/>);
            console.log('PyhmmerIntegration: PyhmmerFeaturePanel rendered successfully');
        } catch (error) {
            console.error('PyhmmerIntegration: Error rendering PyhmmerFeaturePanel:', error);
        }

        // Make sure container is visible
        container.style.display = 'block';
        container.style.visibility = 'visible';
        console.log('PyhmmerIntegration: Container made visible, final container:', container);
    };

    return null;
};
