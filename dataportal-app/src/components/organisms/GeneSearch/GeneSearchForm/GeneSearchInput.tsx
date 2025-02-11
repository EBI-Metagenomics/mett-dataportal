import React, {useEffect, useRef, useState} from 'react';
import styles from "@components/organisms/GeneSearch/GeneSearchForm/GeneSearchInput.module.scss";
import {Autocomplete, TextField} from "@mui/material";
import {GeneSuggestion} from "../../../../interfaces/Gene";

interface GeneSearchInputProps {
    query: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    suggestions: GeneSuggestion[];
    onSuggestionClick: (suggestion: GeneSuggestion) => void;
    onSuggestionsClear: () => void;
}

const GeneSearchInput: React.FC<GeneSearchInputProps> = ({
                                                             query,
                                                             onInputChange,
                                                             suggestions,
                                                             onSuggestionClick,
                                                             onSuggestionsClear,
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

                    return `${strainName}${geneNamePart} - (${product} - ${locusTag})`;
                }}
                inputValue={query || ''}
                onInputChange={(event, newValue, reason) => {
                    if (!isSelecting) {
                        onInputChange({
                            target: {value: newValue || ''},
                        } as React.ChangeEvent<HTMLInputElement>);
                    }
                    if (reason === 'reset') {
                        setIsSelecting(false);
                    }
                }}
                onChange={(event, value) => {
                    if (value && typeof value !== 'string') {
                        setIsSelecting(true);
                        const strainName = value.isolate_name || 'Unknown strain';
                        const geneNamePart = value.gene_name || value.locus_tag || 'Unknown locus tag';
                        const displayValue = `${geneNamePart} (${strainName})`;

                        onInputChange({
                            target: {value: displayValue},
                        } as React.ChangeEvent<HTMLInputElement>);
                        onSuggestionClick(value);
                    }
                }}
                isOptionEqualToValue={(option, value) =>
                    option &&
                    value &&
                    typeof option !== 'string' &&
                    typeof value !== 'string' &&
                    option.gene_id === value.gene_id
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
                type="submit"
                className="vf-button vf-button--primary vf-button--sm"
                onClick={onSuggestionsClear}
            >
                <span className="vf-button__text">Search</span>
            </button>
        </div>
    );
};

export default GeneSearchInput;
