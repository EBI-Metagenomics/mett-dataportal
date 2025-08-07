import { useEffect, useRef } from 'react';
import { getExternalLinks } from '../utils/featurePanelEnhancer';
import { EXTERNAL_DB_URLS, generateExternalDbLink } from '../utils/appConstants';

export const useFeaturePanelEnhancer = () => {
    const observerRef = useRef<MutationObserver | null>(null);

            // Function to enhance feature panel with external links
        const enhanceFeaturePanel = () => {
            console.log('🔍 Looking for feature panels to enhance...');
            
            // Quick check - if we already have enhanced panels, don't clear them immediately
            const existingEnhanced = document.querySelectorAll('[data-enhanced="true"]');
            if (existingEnhanced.length > 0) {
                console.log('🔍 Found existing enhanced panels, skipping flag clearing for speed');
            } else {
                // Clear any existing enhanced flags to allow re-enhancement
                document.querySelectorAll('[data-enhanced="true"]').forEach((el: any) => {
                    if (el.textContent && (
                        el.textContent.includes('Gene:') ||
                        el.textContent.includes('Locus Tag:') ||
                        el.textContent.includes('Product:')
                    )) {
                        // Only clear flags for actual feature panels, not UI elements
                        el.removeAttribute('data-enhanced');
                    }
                });
                
                // Also clear flags from any accordion elements that might be feature panels
                document.querySelectorAll('.MuiAccordion-root[data-enhanced="true"]').forEach((el: any) => {
                    if (el.textContent && (
                        el.textContent.includes('Gene:') ||
                        el.textContent.includes('Locus Tag:') ||
                        el.textContent.includes('Product:') ||
                        el.textContent.includes('COG:') ||
                        el.textContent.includes('KEGG:') ||
                        el.textContent.includes('Dbxref:')
                    )) {
                        el.removeAttribute('data-enhanced');
                    }
                });
            }
        
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
                // JBrowse Material-UI specific selectors - more specific to avoid UI elements
                '.MuiPaper-root[class*="Accordion"]:not([class*="AppBar"]):not([class*="trackLabel"])',
                '.MuiAccordion-root',
                // More specific JBrowse selectors
                '[data-testid="widget-drawer-selects"]',
                '[class*="drawer"]',
                '[class*="widget"]',
                // Additional JBrowse panel selectors
                '.MuiDrawer-paper',
                '.MuiAccordionDetails-root',
                '.MuiCollapse-root',
                '[class*="MuiDrawer"]',
                '[class*="MuiCollapse"]',
                // Even more aggressive selectors for faster detection
                '.MuiPaper-root',
                '[class*="MuiPaper"]',
                '[class*="MuiAccordion"]'
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
            
            // Check if this panel actually contains feature data (not just UI elements)
            let hasFeatureContent = panel.textContent && (
                panel.textContent.includes('Gene:') ||
                panel.textContent.includes('Locus Tag:') ||
                panel.textContent.includes('Product:') ||
                panel.textContent.includes('COG:') ||
                panel.textContent.includes('KEGG:') ||
                panel.textContent.includes('Dbxref:') ||
                panel.textContent.includes('ko:')
            );
            
            // If not found in textContent, check deeper in the DOM structure
            if (!hasFeatureContent) {
                const allTextNodes = panel.querySelectorAll('*');
                for (const element of allTextNodes) {
                    const text = element.textContent || '';
                    if (text.includes('Gene:') || text.includes('Locus Tag:') || text.includes('Product:')) {
                        hasFeatureContent = true;
                        console.log(`🔍 Found feature content in child element:`, element);
                        break;
                    }
                }
            }
            
            if (!hasFeatureContent) {
                console.log(`🔍 Panel ${index + 1} has no feature content, but trying anyway...`);
                console.log(`🔍 Panel text content (first 500 chars):`, panel.textContent?.substring(0, 500));
                console.log(`🔍 Panel innerHTML (first 500 chars):`, panel.innerHTML?.substring(0, 500));
                
                // Even if we can't detect feature content, try to enhance anyway
                // This handles cases where the content is loaded asynchronously
                console.log(`🔍 Attempting enhancement anyway for panel ${index + 1}`);
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
            
            // Method 1.5: Look for any text content that might contain feature data
            if (!featureData) {
                const allTextContent = panel.textContent || '';
                console.log(`🔍 All text content in panel (first 1000 chars):`, allTextContent.substring(0, 1000));
                
                // Look for any patterns that suggest this is a feature panel
                const hasAnyFeaturePattern = allTextContent.includes('gene') || 
                                           allTextContent.includes('locus') || 
                                           allTextContent.includes('product') ||
                                           allTextContent.includes('COG') ||
                                           allTextContent.includes('KEGG') ||
                                           allTextContent.includes('Dbxref') ||
                                           allTextContent.includes('PF') ||
                                           allTextContent.includes('IPR') ||
                                           allTextContent.includes('GO:');
                
                if (hasAnyFeaturePattern) {
                    console.log('🔍 Found feature patterns in text content, creating mock feature data');
                    featureData = { hasContent: true }; // Mark that we have content to process
                }
            }
            
            // Method 2: Look for text content that might contain feature data
            if (!featureData) {
                const textContent = panel.textContent || '';
                console.log(`🔍 Panel text content (first 200 chars):`, textContent.substring(0, 200));
                
                // Look for patterns that suggest feature data
                const cogMatch = textContent.match(/COG:\s*([A-Z]|\d+)/);
                const keggMatch = textContent.match(/kegg:\s*(ko:)?(K\d+)/i);
                const goMatch = textContent.match(/GO:\d+/g);
                const pfamMatch = textContent.match(/PF\d+/g);
                const interproMatch = textContent.match(/IPR\d+/g);
                const dbxrefMatch = textContent.match(/Dbxref\s*([^,\n]+(?:,[^,\n]+)*?)(?=\w+:|$)/);
                
                // Also look for standalone patterns
                const standaloneKeggMatch = textContent.match(/ko:K\d+/g);
                const standaloneDbxrefMatch = textContent.match(/COG:COG\d+|UniProt:[A-Z0-9]+/g);
                
                if (cogMatch || keggMatch || goMatch || pfamMatch || interproMatch || dbxrefMatch || standaloneKeggMatch || standaloneDbxrefMatch) {
                    console.log('🔍 Found database patterns in text:', { 
                        cogMatch, 
                        keggMatch, 
                        goMatch, 
                        pfamMatch, 
                        interproMatch, 
                        dbxrefMatch,
                        standaloneKeggMatch,
                        standaloneDbxrefMatch
                    });
                    
                    // Create a mock feature object from the text content
                    featureData = {
                        cog: cogMatch ? cogMatch[1] : undefined,
                        kegg: keggMatch ? (keggMatch[1] ? keggMatch[1] + keggMatch[2] : keggMatch[2]) : 
                              (standaloneKeggMatch ? standaloneKeggMatch[0] : undefined),
                        Ontology_term: goMatch ? goMatch.slice(0, 10).join(',') : undefined, // Limit GO terms
                        pfam: pfamMatch ? pfamMatch.slice(0, 5) : undefined, // Limit Pfam terms
                        interpro: interproMatch ? interproMatch.slice(0, 5) : undefined, // Limit InterPro terms
                        dbxref: dbxrefMatch ? dbxrefMatch[1].trim() : 
                               (standaloneDbxrefMatch ? standaloneDbxrefMatch.join(',') : undefined)
                    };
                    
                    console.log('🔍 Created feature data from text:', featureData);
                
                // Debug: Log what we found for KEGG and Dbxref specifically
                if (featureData.kegg) {
                    console.log('🔍 Found KEGG data:', featureData.kegg);
                }
                if (featureData.dbxref) {
                    console.log('🔍 Found Dbxref data:', featureData.dbxref);
                    console.log('🔍 Dbxref length:', featureData.dbxref.length);
                    console.log('🔍 Dbxref first 100 chars:', featureData.dbxref.substring(0, 100));
                }
                } else if (isEnhanced) {
                    // If panel is already enhanced but no feature data found, skip it
                    console.log(`🔍 Panel ${index + 1} already enhanced and no feature data found, skipping`);
                    return;
                }
            }
            
            if (featureData) {
                console.log(`🔍 Enhancing existing key-value pairs with external links`);
                
                // If we have a mock feature data object, try to parse the text content
                if (featureData.hasContent && !featureData.cog && !featureData.kegg && !featureData.dbxref) {
                    console.log('🔍 Parsing text content for feature data...');
                    const textContent = panel.textContent || '';
                    
                    // Try to extract feature data from text content
                    const cogMatch = textContent.match(/COG:\s*([A-Z]|\d+)/);
                    const keggMatch = textContent.match(/kegg:\s*(ko:)?(K\d+)/i);
                    const goMatch = textContent.match(/GO:\d+/g);
                    const pfamMatch = textContent.match(/PF\d+/g);
                    const interproMatch = textContent.match(/IPR\d+/g);
                    const dbxrefMatch = textContent.match(/Dbxref\s*([^,\n]+(?:,[^,\n]+)*?)(?=\w+:|$)/);
                    const standaloneKeggMatch = textContent.match(/ko:K\d+/g);
                    const standaloneDbxrefMatch = textContent.match(/COG:COG\d+|UniProt:[A-Z0-9]+/g);
                    
                    if (cogMatch || keggMatch || goMatch || pfamMatch || interproMatch || dbxrefMatch || standaloneKeggMatch || standaloneDbxrefMatch) {
                        console.log('🔍 Found database patterns in text:', { cogMatch, keggMatch, goMatch, pfamMatch, interproMatch, dbxrefMatch, standaloneKeggMatch, standaloneDbxrefMatch });
                        
                        featureData = {
                            cog: cogMatch ? cogMatch[1] : undefined,
                            kegg: keggMatch ? (keggMatch[1] ? keggMatch[1] + keggMatch[2] : keggMatch[2]) : 
                                  (standaloneKeggMatch ? standaloneKeggMatch[0] : undefined),
                            Ontology_term: goMatch ? goMatch.slice(0, 10).join(',') : undefined,
                            pfam: pfamMatch ? pfamMatch.slice(0, 5) : undefined,
                            interpro: interproMatch ? interproMatch.slice(0, 5) : undefined,
                            dbxref: dbxrefMatch ? dbxrefMatch[1].trim() : 
                                   (standaloneDbxrefMatch ? standaloneDbxrefMatch.join(',') : undefined)
                        };
                        
                        console.log('🔍 Created feature data from text:', featureData);
                    }
                }
                
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
                    
                    // First, try to find the key in the DOM (case-insensitive)
                    const keyElements = Array.from(panel.querySelectorAll('*')).filter((el: any) => {
                        const text = el.textContent || '';
                        return text.trim().toLowerCase() === key.toLowerCase();
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
                            } else if (key.toLowerCase() === 'kegg') {
                                hasValidIds = /ko:K\d+/.test(valueText);
                            } else if (key.toLowerCase() === 'dbxref') {
                                hasValidIds = /(COG:COG\d+|UniProt:[A-Z0-9]+)/.test(valueText);
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
                                    } else if (key.toLowerCase() === 'kegg') {
                                        if (/^ko:K\d+$/.test(val)) {
                                            const keggId = val.replace('ko:', '');
                                            url = generateExternalDbLink('KEGG', keggId);
                                            linkText = val;
                                        }
                                    } else if (key.toLowerCase() === 'dbxref') {
                                        // Handle comma-separated Dbxref values
                                        if (/^COG:COG\d+$/.test(val)) {
                                            const cogId = val.replace('COG:', '');
                                            url = generateExternalDbLink('COG', cogId);
                                            linkText = val;
                                        } else if (/^UniProt:[A-Z0-9]+$/.test(val)) {
                                            const uniprotId = val.replace('UniProt:', '');
                                            url = generateExternalDbLink('UNIPROT', uniprotId);
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
                
                // Enhance specific key-value pairs (focusing on COG, Pfam, InterPro, KEGG, Dbxref)
                if (featureData.cog) enhanceKeyValuePair('cog', featureData.cog);
                if (featureData.pfam) enhanceKeyValuePair('pfam', featureData.pfam);
                if (featureData.interpro) enhanceKeyValuePair('interpro', featureData.interpro);
                if (featureData.kegg) enhanceKeyValuePair('kegg', featureData.kegg);
                if (featureData.dbxref) {
                    // Clean up Dbxref value if it's too long (might include other attributes)
                    let cleanDbxref = featureData.dbxref;
                    if (cleanDbxref.length > 200) {
                        // Try to find the end of the Dbxref value
                        const endIndex = cleanDbxref.indexOf('gene') || cleanDbxref.indexOf('locus_tag') || cleanDbxref.indexOf('product');
                        if (endIndex > 0) {
                            cleanDbxref = cleanDbxref.substring(0, endIndex).trim();
                        }
                    }
                    console.log('🔍 Cleaned Dbxref value:', cleanDbxref);
                    
                    enhanceKeyValuePair('dbxref', cleanDbxref);
                    enhanceKeyValuePair('Dbxref', cleanDbxref); // Try both cases
                }
                
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
            let hasNewFeaturePanel = false;
            
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            const element = node as Element;
                            
                            // Check if this element or its children contain feature-related content
                            const hasFeatureContent = element.textContent && (
                                element.textContent.includes('COG:') ||
                                element.textContent.includes('KEGG:') ||
                                element.textContent.includes('GO:') ||
                                element.textContent.includes('Gene:') ||
                                element.textContent.includes('Locus Tag:') ||
                                element.textContent.includes('Product:') ||
                                element.textContent.includes('Pfam:') ||
                                element.textContent.includes('InterPro:') ||
                                element.textContent.includes('Dbxref:') ||
                                element.textContent.includes('ko:')
                            );
                            
                            // Check if it's a feature panel element
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
                            
                            // Check for attribute changes that might indicate new content
                            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                                const target = mutation.target as Element;
                                if (target.classList.contains('MuiAccordion-root') && 
                                    target.classList.contains('Mui-expanded')) {
                                    hasNewFeaturePanel = true;
                                }
                            }
                            
                            // Only enhance if it has feature content AND looks like a panel (not a tooltip)
                            if (hasFeatureContent && (isFeaturePanel || isJBrowsePanel)) {
                                console.log('🔍 Detected feature panel with content:', element);
                                shouldEnhance = true;
                            }
                        }
                    });
                } else if (mutation.type === 'attributes') {
                    // Watch for attribute changes that might indicate new feature panels
                    if (mutation.attributeName === 'class') {
                        const target = mutation.target as Element;
                        if (target.classList.contains('MuiAccordion-root') && 
                            target.classList.contains('Mui-expanded')) {
                            hasNewFeaturePanel = true;
                        }
                    }
                }
            });
            
            // Trigger enhancement if we detected new feature content or panel expansion
            if (shouldEnhance || hasNewFeaturePanel) {
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
        
        // Also listen for JBrowse-specific events that might indicate new feature panels
        const handleJBrowseEvents = () => {
            console.log('🔧 JBrowse event detected, checking for new panels');
            setTimeout(enhanceFeaturePanel, 200);
        };
        
        // Listen for various events that might indicate new content
        document.addEventListener('scroll', handleJBrowseEvents, { passive: true });
        document.addEventListener('resize', handleJBrowseEvents, { passive: true });
        
        // Watch for URL changes (if using hash-based navigation)
        let lastUrl = location.href;
        new MutationObserver(() => {
            const url = location.href;
            if (url !== lastUrl) {
                lastUrl = url;
                console.log('🔧 URL changed, checking for new panels');
                setTimeout(enhanceFeaturePanel, 300);
            }
        }).observe(document, { subtree: true, childList: true });
        
        // Watch for changes in the feature panel content specifically (simplified)
        let lastFeatureContent = '';
        const featureContentObserver = new MutationObserver(() => {
            const featurePanels = document.querySelectorAll('.MuiAccordion-root');
            featurePanels.forEach(panel => {
                const content = panel.textContent || '';
                if (content !== lastFeatureContent && content.includes('Gene:')) {
                    lastFeatureContent = content;
                    console.log('🔧 Feature panel content changed, triggering enhancement');
                    setTimeout(enhanceFeaturePanel, 100);
                }
            });
        });
        
        featureContentObserver.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Initial enhancement attempts (but fewer and with better timing)
        setTimeout(enhanceFeaturePanel, 1000);
        setTimeout(enhanceFeaturePanel, 2000);

        // Set up periodic enhancement check for dynamically loaded content (less frequent since we have click-based)
        const periodicCheck = setInterval(() => {
            console.log('🔍 Periodic check for feature panels...');
            enhanceFeaturePanel();
        }, 10000); // Check every 10 seconds as backup

        // Cleanup
        return () => {
            if (observerRef.current) {
                observerRef.current.disconnect();
            }
            clearInterval(periodicCheck);
            
            // Remove event listeners (use the same function reference)
            document.removeEventListener('scroll', handleJBrowseEvents);
            document.removeEventListener('resize', handleJBrowseEvents);
            
            // Disconnect content observer
            if (featureContentObserver) {
                featureContentObserver.disconnect();
            }
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
            
            // Track if we're currently processing a feature click
            let isProcessingClick = false;
            let clickTimeout: any = null;
            
            // Add click listener to the document to detect when features are clicked
            const handleClick = (event: MouseEvent) => {
                const target = event.target as Element;
                
                // Check if the click is specifically on a feature (not just anywhere in the track)
                const isFeatureClick = target.closest('[class*="feature"], [class*="Feature"], [class*="svg"], [class*="rect"]');
                
                if (isFeatureClick && !isProcessingClick) {
                    console.log('🔍 Feature click detected, starting enhancement sequence');
                    isProcessingClick = true;
                    
                    // Clear any existing timeout
                    if (clickTimeout) {
                        clearTimeout(clickTimeout);
                    }
                    
                    // Immediate enhancement attempt (no delay)
                    console.log('🔧 Immediate enhancement attempt (0ms)');
                    enhanceFeaturePanel();
                    
                    // Start a sequence of enhancement attempts with faster initial attempts
                    const attemptEnhancement = (attempt: number, delay: number) => {
                        clickTimeout = setTimeout(() => {
                            console.log(`🔧 Post-click enhancement attempt ${attempt} (${delay}ms)`);
                            enhanceFeaturePanel();
                            
                            // Check if we found and enhanced a panel
                            const enhancedPanels = document.querySelectorAll('[data-enhanced="true"]');
                            if (enhancedPanels.length > 0) {
                                console.log('✅ Enhancement successful, stopping sequence');
                                isProcessingClick = false;
                                return;
                            }
                            
                            // Continue with next attempt if we haven't found a panel yet
                            if (attempt < 8) { // Reduced max attempts
                                let nextDelay;
                                if (attempt < 3) {
                                    // First 3 attempts are very fast
                                    nextDelay = attempt === 1 ? 50 : 100;
                                } else {
                                    // Then gradually increase but cap lower
                                    nextDelay = Math.min(delay * 1.2, 2000); // Cap at 2 seconds
                                }
                                attemptEnhancement(attempt + 1, nextDelay);
                            } else {
                                console.log('❌ Max attempts reached, stopping sequence');
                                isProcessingClick = false;
                            }
                        }, delay);
                    };
                    
                    // Start the sequence with faster initial timing
                    attemptEnhancement(1, 50);
                }
            };
            
            document.addEventListener('click', handleClick);
            
            // Also watch for when the feature panel actually becomes visible
            const panelObserver = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const target = mutation.target as Element;
                        if (target.classList.contains('MuiAccordion-root') && 
                            target.classList.contains('Mui-expanded')) {
                            console.log('🔍 Feature panel expanded, triggering enhancement');
                            setTimeout(enhanceFeaturePanel, 100);
                            setTimeout(enhanceFeaturePanel, 500);
                        }
                    }
                });
            });
            
            // Watch for accordion elements
            const accordions = document.querySelectorAll('.MuiAccordion-root');
            accordions.forEach(accordion => {
                panelObserver.observe(accordion, { attributes: true });
            });
            
            // Return cleanup function
            return () => {
                document.removeEventListener('click', handleClick);
                panelObserver.disconnect();
                if (clickTimeout) {
                    clearTimeout(clickTimeout);
                }
            };
        }
    };
};
