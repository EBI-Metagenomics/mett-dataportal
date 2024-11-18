import React, {useEffect, useRef, useState} from 'react';
import styles from "@components/organisms/GeneSearch/GeneSearchInput.module.scss";
import {Autocomplete, TextField} from "@mui/material";

interface GeneSearchInputProps {
    query: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    suggestions: { gene_id: number; strain_name: string; gene_name: string }[];
    onSuggestionClick: (suggestion: { gene_id: number; strain_name: string; gene_name: string }) => void;
    onSuggestionsClear: () => void;
}

const GeneSearchInput: React.FC<GeneSearchInputProps> = ({
                                                             query,
                                                             onInputChange,
                                                             suggestions,
                                                             onSuggestionClick,
                                                             onSuggestionsClear
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
                options={suggestions}
                getOptionLabel={(option) =>
                    typeof option === 'string' ? option : `${option.strain_name} - (${option.gene_name})`
                }
                inputValue={query}
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
                        onSuggestionClick(value);
                    }
                }}
                isOptionEqualToValue={(option, value) =>
                    typeof option !== 'string' &&
                    typeof value !== 'string' &&
                    option.gene_id === value.gene_id
                }
                renderInput={(params) => (
                    <TextField
                        {...params}
                        // label="Search Gene"
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
