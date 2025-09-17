import React, {useEffect, useRef} from 'react';
import {createRoot} from 'react-dom/client';
import {PyhmmerFeaturePanel} from '@components/features';
import {PYHMMER_CONSTANTS} from '../../../../utils/pyhmmer';
import {saveJBrowseSearchToHistory} from '../../../../services/pyhmmer/pyhmmerHistoryService';
import styles from './PyhmmerIntegration.module.scss';

export const PyhmmerIntegration: React.FC = () => {
    console.log('PyhmmerIntegration: Component loaded');
    
    // Track current gene context to detect changes
    const currentGeneContextRef = useRef<string | null>(null);

    // Function to hide PyHMMER panel
    const hidePyhmmerPanel = () => {
        const container = document.getElementById('pyhmmer-search-react');
        if (container) {
            container.remove();
            console.log('PyhmmerIntegration: PyHMMER panel hidden');
        }
    };

    // Function to extract gene information from JBrowse feature panel
    const extractGeneContext = (panel: Element): {
        source: 'jbrowse';
        geneId?: string;
        locusTag?: string;
        product?: string;
        geneName?: string;
        featureType?: string;
        genome?: string;
        coordinates?: {
            start?: number;
            end?: number;
            strand?: string;
            contig?: string;
        };
    } => {
        const context: any = {
            source: 'jbrowse' as const
        };

        try {
                    // Extract locus tag from the panel text
        let locusTag = '';
        const panelText = panel.textContent || '';
        
        // Look for "locus_tag" followed by the actual locus tag value
        const locusTagMatch = panelText.match(/locus_tag\s*\n?([A-Z0-9_]+)/i);
        if (locusTagMatch) {
            // Clean the locus tag - remove any appended product information
            let rawLocusTag = locusTagMatch[1];
            
            // If the locus tag contains product info (like "BU_ATCC8492_00001productChromosomal"),
            // extract just the locus tag part
            const cleanLocusTagMatch = rawLocusTag.match(/^([A-Z]{2}_[A-Z0-9]+_[0-9]+)/);
            if (cleanLocusTagMatch) {
                locusTag = cleanLocusTagMatch[1];
                console.log('PyhmmerIntegration: Cleaned locus tag from:', rawLocusTag, 'to:', locusTag);
                
                // Extract product information from the remaining part
                const productMatch = rawLocusTag.match(/^[A-Z]{2}_[A-Z0-9]+_[0-9]+(.+)/);
                if (productMatch && productMatch[1]) {
                    context.product = productMatch[1];
                    console.log('PyhmmerIntegration: Extracted product info:', context.product);
                }
            } else {
                locusTag = rawLocusTag;
                console.log('PyhmmerIntegration: Found locus tag from locus_tag attribute:', locusTag);
            }
        }
            
            if (locusTag) {
                context.geneId = locusTag;
                context.locusTag = locusTag;
            }

            // Try to find gene name (different from locus tag)
            const geneNameElement = panel.querySelector('.gene-name, .feature-name, [data-gene-name]');
            if (geneNameElement) {
                const geneName = geneNameElement.textContent?.trim() || geneNameElement.getAttribute('data-gene-name');
                if (geneName && geneName !== locusTag) {
                    context.geneName = geneName;
                }
            }

            // Try to find feature type
            const featureTypeElement = panel.querySelector('.feature-type, [data-feature-type]');
            if (featureTypeElement) {
                context.featureType = featureTypeElement.textContent?.trim() || featureTypeElement.getAttribute('data-feature-type');
            }

            // Try to find genome information
            const genomeElement = panel.querySelector('.genome, [data-genome]');
            if (genomeElement) {
                context.genome = genomeElement.textContent?.trim() || genomeElement.getAttribute('data-genome');
            }

            // Try to find coordinates from the panel text
            const coordMatch = panelText.match(/coordinates?[:\s]+(\d+)\s*-\s*(\d+)/i);
            if (coordMatch) {
                context.coordinates = {
                    start: parseInt(coordMatch[1]),
                    end: parseInt(coordMatch[2])
                };
            }

            // Try to find strand information
            const strandMatch = panelText.match(/strand[:\s]+([+-])/i);
            if (strandMatch) {
                if (context.coordinates) {
                    context.coordinates.strand = strandMatch[1];
                } else {
                    context.coordinates = { strand: strandMatch[1] };
                }
            }

            // Try to find contig information
            const contigMatch = panelText.match(/contig[:\s]+([^\s\n]+)/i);
            if (contigMatch) {
                if (context.coordinates) {
                    context.coordinates.contig = contigMatch[1];
                } else {
                    context.coordinates = { contig: contigMatch[1] };
                }
            }

            console.log('PyhmmerIntegration: Extracted gene context:', context);
        } catch (error) {
            console.warn('PyhmmerIntegration: Error extracting gene context:', error);
        }

        return context;
    };

    useEffect(() => {
        console.log('PyhmmerIntegration: Starting integration');
        
        // Clean up any existing styled elements
        const existingButtons = document.querySelectorAll('.pyhmmer-button-styled');
        existingButtons.forEach(button => {
            button.classList.remove('pyhmmer-button-styled', styles.pyhmmerButton, styles.buttonHover);
        });

        // Hide PyHMMER panel when gene context changes
        const checkForGeneContextChange = () => {
            const panels = document.querySelectorAll('.MuiAccordionDetails-root, [role="region"]');
            panels.forEach(panel => {
                const geneContext = extractGeneContext(panel);
                const newGeneContext = geneContext.locusTag || geneContext.geneId || 'unknown';
                
                if (currentGeneContextRef.current && currentGeneContextRef.current !== newGeneContext) {
                    console.log('PyhmmerIntegration: Gene context changed, hiding PyHMMER panel');
                    hidePyhmmerPanel();
                }
                currentGeneContextRef.current = newGeneContext;
            });
        };

        // Check for gene context changes periodically
        const geneContextInterval = setInterval(checkForGeneContextChange, 1000);

        // Function to style the search button
        const styleSearchButton = () => {
            // Hide unwanted attributes first - SAFE VERSION
            const hideUnwantedAttributes = () => {
                try {
                    console.log('PyhmmerIntegration: Starting to hide unwanted attributes...');
                    
                    // Only look for elements within the current feature panel, not the entire document
                    const featurePanel = document.querySelector('.MuiAccordionDetails-root, [role="region"]');
                    if (!featurePanel) {
                        console.log('PyhmmerIntegration: No feature panel found, skipping attribute hiding');
                        return;
                    }
                    
                    // Look for specific PyHMMER attribute elements within the panel only
                    const pyhmmerElements = featurePanel.querySelectorAll('*');
                    console.log('PyhmmerIntegration: Checking', pyhmmerElements.length, 'elements in feature panel');
                    
                    let hiddenCount = 0;
                    pyhmmerElements.forEach((element) => {
                        try {
                            const text = element.textContent || '';
                            
                            // Only hide elements that are clearly PyHMMER attributes
                            if (text.includes('pyhmmerSearch.proteinSequence') ||
                                text.includes('pyhmmerSearch.proteinLength') ||
                                text.includes('pyhmmerSearch.pyhmmerSearchLink')) {
                                
                                // Make sure we don't hide the element we're about to style
                                if (!text.includes('Search Protein Domains')) {
                                    console.log('PyhmmerIntegration: Hiding PyHMMER attribute:', text.substring(0, 50) + '...');
                                    (element as HTMLElement).style.display = 'none';
                                    hiddenCount++;
                                }
                            }
                        } catch (elementError) {
                            console.warn('PyhmmerIntegration: Error processing element:', elementError);
                        }
                    });
                    
                    console.log('PyhmmerIntegration: Hidden', hiddenCount, 'PyHMMER attribute elements');
                    
                } catch (error) {
                    console.error('PyhmmerIntegration: Error in hideUnwantedAttributes:', error);
                }
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

                                // Extract protein sequence and gene context
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
                                    
                                    // Clean and deduplicate the sequence if found
                                    if (sequence) {
                                        // Remove any non-amino acid characters
                                        sequence = sequence.replace(/[^A-Z*]/g, '');
                                        
                                        // Check if sequence is duplicated within itself
                                        if (sequence.length > 200) {
                                            const halfLength = Math.floor(sequence.length / 2);
                                            const firstHalf = sequence.substring(0, halfLength);
                                            const secondHalf = sequence.substring(halfLength);
                                            
                                            if (firstHalf === secondHalf) {
                                                console.log('PyhmmerIntegration: Detected duplicated sequence, using first half only');
                                                sequence = firstHalf;
                                            }
                                        }
                                    }

                                    if (sequence) {
                                        console.log('PyhmmerIntegration: Sequence found, injecting search panel');
                                        
                                        // Extract gene context and save to history
                                        const geneContext = extractGeneContext(panel);
                                        
                                        // Debug: Log what we're extracting
                                        console.log('PyhmmerIntegration: Extracted gene context:', geneContext);
                                        console.log('PyhmmerIntegration: Locus tag:', geneContext.locusTag);
                                        console.log('PyhmmerIntegration: Gene ID:', geneContext.geneId);
                                        
                                        // Save to history with context
                                        const searchRequest = {
                                            database: PYHMMER_CONSTANTS.DATABASES.DEFAULT,
                                            threshold: 'evalue',
                                            threshold_value: PYHMMER_CONSTANTS.THRESHOLDS.DEFAULT_EVALUE.toString(),
                                            input: `>${geneContext.locusTag || geneContext.geneId || 'jbrowse_gene'}${geneContext.product ? ' ' + geneContext.product : ''}\n${sequence}`
                                        };
                                        
                                        console.log('PyhmmerIntegration: Search request input:', searchRequest.input);
                                        
                                        // Save JBrowse search to history and get the temporary job ID
                                        const tempJobId = saveJBrowseSearchToHistory(searchRequest, geneContext);
                                        console.log('PyhmmerIntegration: JBrowse search saved to history with temp ID:', tempJobId);
                                        
                                        // Extract isolate name from locus tag for isolate-specific search
                                        const isolateName = geneContext.locusTag || geneContext.geneId;
                                        
                                        // Inject the search panel with the temporary job ID for tracking
                                        injectPyhmmerSearchIntoFeaturePanel(sequence, tempJobId, isolateName);
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
            clearInterval(geneContextInterval);
            
            // Clean up styled elements
            const buttons = document.querySelectorAll('.pyhmmer-button-styled');
            buttons.forEach(button => {
                button.classList.remove('pyhmmer-button-styled', styles.pyhmmerButton, styles.buttonHover);
            });
            
            // Cleanup complete
        };
    }, []);

    // Function to inject the PyHMMER search panel
    const injectPyhmmerSearchIntoFeaturePanel = (proteinSequence: string, tempJobId?: string, isolateName?: string) => {
        console.log('PyhmmerIntegration: injectPyhmmerSearchIntoFeaturePanel called with sequence length:', proteinSequence.length);

        // Remove existing container if it exists
        const existingContainer = document.getElementById('pyhmmer-search-react');
        if (existingContainer) {
            existingContainer.remove();
        }

        // Create fresh container
        const container = document.createElement('div');
        container.id = 'pyhmmer-search-react';

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
                    root.render(
                        <PyhmmerFeaturePanel 
                            proteinSequence={proteinSequence} 
                            tempJobId={tempJobId} 
                            isolateName={isolateName}
                        />
                    );
                    console.log('PyhmmerIntegration: PyhmmerFeaturePanel rendered successfully with temp job ID:', tempJobId);
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
