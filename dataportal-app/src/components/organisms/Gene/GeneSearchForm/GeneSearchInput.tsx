import React, {useEffect, useRef, useState} from 'react';
import styles from "@components/organisms/Gene/GeneSearchForm/GeneSearchInput.module.scss";
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
        <div ref={wrapperRef} className={`vf-form__item ${styles.vfFormItem}`} style={{width: '100%'}}>
            <Autocomplete
                disablePortal
                freeSolo
                options={suggestions || []}
                style={{zIndex: 1000, flex: 1}}
                getOptionLabel={(option) => {
                    if (typeof option === 'string') return option;
                    const product = option.product || 'Unknown product';
                    const locusTag = option.locus_tag || 'Unknown locus tag';
                    const geneNamePart = option.gene_name ? ` - ${option.gene_name}` : '';
                    return `${geneNamePart} (${product} - ${locusTag})`;
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
                        const geneNamePart = value.gene_name || value.locus_tag || 'Unknown locus tag';
                        onInputChange({
                            target: {value: geneNamePart},
                        } as React.ChangeEvent<HTMLInputElement>);
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
                                width: '100%',
                                minWidth: 0,
                            },
                        }}
                        fullWidth
                    />
                )}
            />
            <button
                type="submit"
                className="vf-button vf-button--primary vf-button--sm"
                onClick={onSuggestionsClear}
                style={{height: '41px'}}
            >
                <span className="vf-button__text">Search</span>
            </button>
        </div>
    );
};

export default GeneSearchInput;
