import { useEffect, useRef } from 'react';
import { getExternalLinks } from '../utils/featurePanelEnhancer';
import { EXTERNAL_DB_URLS, generateExternalDbLink } from '../utils/appConstants';

export const useFeaturePanelEnhancer = () => {
    const observerRef = useRef<MutationObserver | null>(null);

    // Function to enhance feature panel with external links
    const enhanceFeaturePanel = () => {
        console.log('🔍 Looking for feature panels to enhance...');
        
        // Look for JBrowse feature panel elements - try multiple selectors
        const selectors = [
            '[data-testid="feature-details"]',
            '.feature-details',
            '[class*="feature"]',
            '[class*="Feature"]',
            '.jbrowse-feature-details',
            '.feature-panel',
            '.feature-panel-content',
            '[class*="BaseFeatureWidget"]',
            '[class*="FeatureWidget"]',
            // JBrowse Material-UI specific selectors
            '.MuiPaper-root[class*="Accordion"]',
            '.MuiAccordion-root',
            '.MuiPaper-root[class*="elevation"]',
            '[class*="MuiPaper-root"]',
            '[class*="MuiAccordion"]',
            // More specific JBrowse selectors
            '[data-testid="widget-drawer-selects"]',
            '[class*="drawer"]',
            '[class*="widget"]',
            // Additional JBrowse panel selectors
            '.MuiDrawer-paper',
            '.MuiAccordionDetails-root',
            '.MuiCollapse-root',
            '[class*="MuiDrawer"]',
            '[class*="MuiCollapse"]'
        ];
        
        let featurePanels: any = null;
        
        for (const selector of selectors) {
            featurePanels = document.querySelectorAll(selector);
            if (featurePanels.length > 0) {
                console.log(`🔍 Found ${featurePanels.length} feature panels with selector: ${selector}`);
                break;
            }
        }
        
        if (!featurePanels || featurePanels.length === 0) {
            console.log('🔍 No feature panels found');
            return;
        }
        
        featurePanels.forEach((panel: any, index: number) => {
            console.log(`🔍 Processing panel ${index + 1}:`, panel);
            
            // Check if we've already enhanced this panel
            const isEnhanced = panel.getAttribute('data-enhanced') === 'true';
            if (isEnhanced) {
                console.log(`🔍 Panel ${index + 1} already enhanced, skipping`);
                return; // Skip already enhanced panels to avoid re-processing
            }

            // Look for feature data in the panel - try multiple approaches
            let featureData = null;
            
            // Method 1: Look for data attributes
            const dataElements = panel.querySelectorAll('[data-feature], [data-feature-data]');
            if (dataElements.length > 0) {
                console.log(`🔍 Found ${dataElements.length} data elements`);
                for (const element of dataElements) {
                    const data = element.getAttribute('data-feature') || element.getAttribute('data-feature-data');
                    if (data) {
                        try {
                            featureData = JSON.parse(data);
                            console.log('🔍 Found feature data in data attribute:', featureData);
                            break;
                        } catch (e) {
                            console.warn('Failed to parse data attribute:', e);
                        }
                    }
                }
            }
            
            // Method 2: Look for text content that might contain feature data
            if (!featureData) {
                const textContent = panel.textContent || '';
                console.log(`🔍 Panel text content (first 200 chars):`, textContent.substring(0, 200));
                
                // Look for patterns that suggest feature data
                const cogMatch = textContent.match(/COG:\s*([A-Z]|\d+)/);
                const keggMatch = textContent.match(/KEGG:\s*(ko:)?(K\d+)/);
                const goMatch = textContent.match(/GO:\d+/g);
                const pfamMatch = textContent.match(/PF\d+/g);
                const interproMatch = textContent.match(/IPR\d+/g);
                
                if (cogMatch || keggMatch || goMatch || pfamMatch || interproMatch) {
                    console.log('🔍 Found database patterns in text:', { cogMatch, keggMatch, goMatch, pfamMatch, interproMatch });
                    
                    // Create a mock feature object from the text content
                    featureData = {
                        cog: cogMatch ? cogMatch[1] : undefined,
                        kegg: keggMatch ? (keggMatch[1] ? keggMatch[1] + keggMatch[2] : keggMatch[2]) : undefined,
                        Ontology_term: goMatch ? goMatch.slice(0, 10).join(',') : undefined, // Limit GO terms
                        pfam: pfamMatch ? pfamMatch.slice(0, 5) : undefined, // Limit Pfam terms
                        interpro: interproMatch ? interproMatch.slice(0, 5) : undefined // Limit InterPro terms
                    };
                    
                    console.log('🔍 Created feature data from text:', featureData);
                } else if (isEnhanced) {
                    // If panel is already enhanced but no feature data found, skip it
                    console.log(`🔍 Panel ${index + 1} already enhanced and no feature data found, skipping`);
                    return;
                }
            }
            
            if (featureData) {
                console.log(`🔍 Enhancing existing key-value pairs with external links`);
                
                // Function to create a link element
                const createLink = (url: string, text: string) => {
                    const link = document.createElement('a');
                    link.href = url;
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.textContent = text;
                    link.style.cssText = `
                        color: #007bff;
                        text-decoration: underline;
                        margin-right: 4px;
                    `;
                    
                    link.addEventListener('mouseenter', () => {
                        link.style.color = '#0056b3';
                    });
                    
                    link.addEventListener('mouseleave', () => {
                        link.style.color = '#007bff';
                    });
                    
                    return link;
                };
                
                // Function to enhance a key-value pair
                const enhanceKeyValuePair = (key: string, value: string) => {
                    console.log(`🔍 Looking for key: ${key} with value: ${value}`);
                    
                    // First, try to find the key in the DOM
                    const keyElements = Array.from(panel.querySelectorAll('*')).filter((el: any) => {
                        const text = el.textContent || '';
                        return text.trim() === key;
                    });
                    
                    console.log(`🔍 Found ${keyElements.length} elements with key "${key}"`);
                    
                    keyElements.forEach((keyElement: any) => {
                        // Look for the value in the next sibling or parent
                        let valueElement = keyElement.nextElementSibling;
                        if (!valueElement) {
                            // Try parent's next sibling
                            valueElement = keyElement.parentElement?.nextElementSibling;
                        }
                        
                        if (valueElement) {
                            const valueText = valueElement.textContent || '';
                            console.log(`🔍 Found value element for ${key}: "${valueText}"`);
                            
                            // Check if this value contains the expected database IDs
                            let hasValidIds = false;
                            if (key.toLowerCase() === 'pfam') {
                                hasValidIds = /PF\d+/.test(valueText);
                            } else if (key.toLowerCase() === 'interpro') {
                                hasValidIds = /IPR\d+/.test(valueText);
                            } else if (key.toLowerCase() === 'cog') {
                                hasValidIds = /COG\d+/.test(valueText) || /^[A-Z]$/.test(valueText);
                            }
                            
                            if (hasValidIds) {
                                console.log(`🔍 Enhancing ${key} value: ${valueText}`);
                                
                                // Split the value by commas
                                const values = valueText.split(',').map((v: string) => v.trim());
                                
                                // Create a container for the enhanced content
                                const container = document.createElement('span');
                                
                                // Process each value
                                values.forEach((val: string, index: number) => {
                                    let url = '';
                                    let linkText = val;
                                    
                                    // Determine URL based on the key and value using environment variables
                                    if (key.toLowerCase() === 'cog') {
                                        if (/^[A-Z]$/.test(val)) {
                                            url = generateExternalDbLink('COG_CATEGORY', val);
                                            linkText = `COG Category: ${val}`;
                                        } else if (/^COG\d+$/.test(val)) {
                                            url = generateExternalDbLink('COG', val);
                                            linkText = val;
                                        }
                                    } else if (key.toLowerCase() === 'pfam') {
                                        if (/^PF\d+$/.test(val)) {
                                            url = generateExternalDbLink('PFAM', val);
                                            linkText = val;
                                        }
                                    } else if (key.toLowerCase() === 'interpro') {
                                        if (/^IPR\d+$/.test(val)) {
                                            url = generateExternalDbLink('INTERPRO', val);
                                            linkText = val;
                                        }
                                    }
                                    
                                    // Create link or plain text
                                    if (url) {
                                        container.appendChild(createLink(url, linkText));
                                    } else {
                                        const textSpan = document.createElement('span');
                                        textSpan.textContent = val;
                                        container.appendChild(textSpan);
                                    }
                                    
                                    // Add comma separator (except for last item)
                                    if (index < values.length - 1) {
                                        const comma = document.createElement('span');
                                        comma.textContent = ', ';
                                        container.appendChild(comma);
                                    }
                                });
                                
                                // Replace the value element with the enhanced content
                                valueElement.parentNode?.replaceChild(container, valueElement);
                                console.log(`✅ Enhanced ${key} with external links`);
                            }
                        }
                    });
                };
                
                // Enhance specific key-value pairs (focusing on COG, Pfam, InterPro)
                if (featureData.cog) enhanceKeyValuePair('cog', featureData.cog);
                if (featureData.pfam) enhanceKeyValuePair('pfam', featureData.pfam);
                if (featureData.interpro) enhanceKeyValuePair('interpro', featureData.interpro);
                
                console.log(`✅ Enhanced key-value pairs in panel ${index + 1}`);
            }
            
            // Mark this panel as enhanced
            panel.setAttribute('data-enhanced', 'true');
        });
    };

    useEffect(() => {
        // Set up mutation observer to watch for new feature panels
        observerRef.current = new MutationObserver((mutations) => {
            let shouldEnhance = false;
            
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const element = node as Element;
                            
                            // Check if this element or its children contain feature-related content
                            // But be more specific to avoid hover tooltips
                            const hasFeatureContent = element.textContent && (
                                element.textContent.includes('COG:') ||
                                element.textContent.includes('KEGG:') ||
                                element.textContent.includes('GO:') ||
                                element.textContent.includes('Gene:') ||
                                element.textContent.includes('Locus Tag:') ||
                                element.textContent.includes('Product:') ||
                                element.textContent.includes('Pfam:') ||
                                element.textContent.includes('InterPro:')
                            );
                            
                            // Also check if it's a feature panel element
                            const isFeaturePanel = element.querySelector && (
                                element.querySelector('[data-testid="feature-details"]') ||
                                element.querySelector('.feature-details') ||
                                element.querySelector('[class*="BaseFeatureWidget"]') ||
                                element.querySelector('[class*="FeatureWidget"]') ||
                                element.querySelector('.MuiPaper-root[class*="Accordion"]') ||
                                element.querySelector('.MuiAccordion-root')
                            );
                            
                            // Check if this is a JBrowse drawer or panel container
                            const isJBrowsePanel = element.classList && (
                                element.classList.contains('MuiPaper-root') ||
                                element.classList.contains('MuiDrawer-paper') ||
                                element.classList.contains('MuiAccordion-root') ||
                                element.classList.contains('MuiAccordionDetails-root')
                            );
                            
                            // Only enhance if it has feature content AND looks like a panel (not a tooltip)
                            if (hasFeatureContent && (isFeaturePanel || isJBrowsePanel)) {
                                console.log('🔍 Detected feature panel with content:', element);
                                shouldEnhance = true;
                            }
                        }
                    });
                }
            });
            
            // Only trigger enhancement once per batch of mutations
            if (shouldEnhance) {
                console.log('🔧 Triggering enhancement for new feature panel');
                setTimeout(enhanceFeaturePanel, 300);
            }
        });

        // Start observing with more comprehensive options
        observerRef.current.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'data-enhanced']
        });

        // Initial enhancement attempts (but fewer and with better timing)
        setTimeout(enhanceFeaturePanel, 1000);
        setTimeout(enhanceFeaturePanel, 2000);

        // Set up periodic enhancement check for dynamically loaded content
        const periodicCheck = setInterval(() => {
            console.log('🔍 Periodic check for feature panels...');
            enhanceFeaturePanel();
        }, 5000); // Check every 5 seconds

        // Cleanup
        return () => {
            if (observerRef.current) {
                observerRef.current.disconnect();
            }
            clearInterval(periodicCheck);
        };
    }, []);

    return { 
        enhanceFeaturePanel: () => {
            console.log('🔧 Manual enhancement triggered');
            enhanceFeaturePanel();
        },
        
        // Function to manually trigger enhancement after clicking a feature
        triggerOnFeatureClick: () => {
            console.log('🔧 Setting up click listener for features');
            
            // Add click listener to the document to detect when features are clicked
            const handleClick = (event: MouseEvent) => {
                const target = event.target as Element;
                
                // Check if the click is specifically on a feature (not just anywhere in the track)
                const isFeatureClick = target.closest('[class*="feature"], [class*="Feature"]');
                
                if (isFeatureClick) {
                    console.log('🔍 Feature click detected, will enhance when panel opens');
                    // Don't trigger enhancement immediately - let the mutation observer handle it
                    // when the feature panel actually opens
                }
            };
            
            document.addEventListener('click', handleClick);
            
            // Return cleanup function
            return () => {
                document.removeEventListener('click', handleClick);
            };
        }
    };
};
