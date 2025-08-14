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
}

const GeneSearchInput: React.FC<GeneSearchInputProps> = ({
                                                             query,
                                                             onInputChange,
                                                             suggestions,
                                                             onSuggestionClick,
                                                             onSuggestionsClear,
                                                             onSearch,
                                                         }) => {
    const wrapperRef = useRef<HTMLDivElement | null>(null);
    const [isSelecting, setIsSelecting] = useState(false);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                onSuggestionsClear();
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [onSuggestionsClear]);

    const handleInputChange = (event: any, newValue: string, reason: string) => {
        console.log('GeneSearchInput handleInputChange:', {newValue, reason, isSelecting});

        // Don't call onInputChange when selecting a suggestion or when resetting
        if (!isSelecting && reason !== 'reset') {
            // Create a proper synthetic event for the parent component
            const syntheticEvent = {
                target: {value: newValue || ''}
            } as React.ChangeEvent<HTMLInputElement>;

            onInputChange(syntheticEvent);
        }

        if (reason === 'reset') {
            setIsSelecting(false);
        }
    };

    return (
        <div ref={wrapperRef} className={`vf-form__item ${styles.vfFormItem}`}>
            <Autocomplete
                disablePortal
                freeSolo
                options={suggestions || []}
                style={{zIndex: 1000}}
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
                onChange={(event, value) => {
                    if (value && typeof value !== 'string') {
                        console.log('GeneSearchInput onChange - suggestion selected:', value);
                        setIsSelecting(true);
                        // Don't call onInputChange here - let onSuggestionClick handle it
                        onSuggestionClick(value);
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
                            },
                        }}
                    />
                )}
            />

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
