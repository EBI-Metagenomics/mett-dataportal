import React, {useEffect, useRef, useState} from 'react';
import styles from "@components/features/gene-viewer/GeneSearchForm/GeneSearchInput.module.scss";
import {Autocomplete, TextField} from "@mui/material";
import {GeneSuggestion} from "../../../../interfaces/Gene";

interface GeneSearchInputProps {
    query: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    suggestions: GeneSuggestion[];
    onSuggestionClick: (suggestion: GeneSuggestion) => void;
    onSuggestionsClear: () => void;
    onSearch: () => void;
    onClear?: () => void;
}

const isAutocompletePopupTarget = (target: EventTarget | null): boolean => {
    if (!(target instanceof Element)) {
        return false;
    }
    return Boolean(
        target.closest(
            '.MuiAutocomplete-popper, .MuiAutocomplete-listbox, .MuiAutocomplete-option, [role="listbox"], [role="option"]'
        )
    );
};

const GeneSearchInput: React.FC<GeneSearchInputProps> = ({
                                                             query,
                                                             onInputChange,
                                                             suggestions,
                                                             onSuggestionClick,
                                                             onSuggestionsClear,
                                                             onSearch,
                                                             onClear,
                                                         }) => {
    const wrapperRef = useRef<HTMLDivElement | null>(null);
    const selectingRef = useRef(false);
    const [isSelecting, setIsSelecting] = useState(false);

    useEffect(() => {
        // Use click (not mousedown): clearing suggestions on mousedown unmounts the
        // option before Autocomplete can commit the selection.
        const handleClickOutside = (event: MouseEvent) => {
            if (selectingRef.current || isAutocompletePopupTarget(event.target)) {
                return;
            }
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                onSuggestionsClear();
            }
        };

        document.addEventListener('click', handleClickOutside);
        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [onSuggestionsClear]);

    const handleInputChange = (_event: any, newValue: string, reason: string) => {
        // MUI Autocomplete emits `reset` when options reload / a value is chosen.
        // Never let that wipe the controlled input while a suggestion is being applied.
        if (reason === 'reset') {
            return;
        }
        if (selectingRef.current || isSelecting || (reason !== 'input' && reason !== 'clear')) {
            return;
        }

        const syntheticEvent = {
            target: {value: newValue || ''},
        } as React.ChangeEvent<HTMLInputElement>;
        onInputChange(syntheticEvent);
    };

    const hasQuery = Boolean(query?.trim());

    return (
        <div ref={wrapperRef} className={`vf-form__item ${styles.vfFormItem}`}>
            <div className={styles.inputWithClear}>
                <Autocomplete
                    disablePortal
                    freeSolo
                    options={suggestions || []}
                    style={{zIndex: 1000, flex: 1}}
                    getOptionLabel={(option) => {
                        if (typeof option === 'string') return option;
                        const strainName = option.isolate_name || 'Unknown strain';
                        const product = option.product || 'Unknown product';
                        const locusTag = option.locus_tag || 'Unknown locus tag';
                        const geneNamePart = option.gene_name ? ` - ${option.gene_name}` : '';
                        const uniprot_id = option.uniprot_id ? ` - ${option.uniprot_id}` : '';
                        const alias =
                            Array.isArray(option.alias) && option.alias.some(a => a.trim())
                                ? ` - ${option.alias.filter(a => a.trim()).join(', ')}`
                                : '';

                        return `${strainName}${geneNamePart}${alias} (${product} - ${locusTag}${uniprot_id})`;
                    }}
                    inputValue={query || ''}
                    onInputChange={handleInputChange}
                    onChange={(_event, value) => {
                        if (value && typeof value !== 'string') {
                            selectingRef.current = true;
                            setIsSelecting(true);
                            onSuggestionClick(value);
                            // Keep the lock until after MUI's follow-up reset events settle.
                            window.setTimeout(() => {
                                selectingRef.current = false;
                                setIsSelecting(false);
                            }, 0);
                        }
                    }}
                    isOptionEqualToValue={(option, value) =>
                        option &&
                        value &&
                        typeof option !== 'string' &&
                        typeof value !== 'string' &&
                        option.locus_tag === value.locus_tag
                    }
                    renderInput={(params) => (
                        <TextField
                            {...params}
                            placeholder="Try Vitamin B12 transporter or a gene locus as dnaA ..."
                            variant="outlined"
                            sx={{
                                '& .MuiInputBase-root': {
                                    height: '41px',
                                    paddingRight: hasQuery ? '40px' : undefined,
                                },
                            }}
                        />
                    )}
                />
                {hasQuery && onClear && (
                    <button
                        type="button"
                        className={styles.clearInputButton}
                        onClick={onClear}
                        aria-label="Clear search"
                        title="Clear search and show all genes"
                    >
                        ×
                    </button>
                )}
            </div>

            <button
                type="button"
                className="vf-button vf-button--primary vf-button--sm"
                onClick={onSearch}
            >
                <span className="vf-button__text">Search</span>
            </button>
        </div>
    );
};

export default GeneSearchInput;
