import React, {useEffect, useRef} from 'react';
import styles from "./GenomeSearchInput.module.scss";
import {Autocomplete, TextField} from "@mui/material";
import {AutocompleteResponse} from "../../../../interfaces/Genome";

interface GenomeSearchInputProps {
    query: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    suggestions: AutocompleteResponse[];
    onSuggestionClick: (suggestion: AutocompleteResponse) => void;
    onSuggestionsClear: () => void;
}

const GenomeSearchInput: React.FC<GenomeSearchInputProps> = ({
                                                                 query,
                                                                 onInputChange,
                                                                 suggestions,
                                                                 onSuggestionClick,
                                                                 onSuggestionsClear
                                                             }) => {
    const wrapperRef = useRef<HTMLDivElement | null>(null);

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
                inputValue={query}
                onInputChange={(event, newValue) => {
                    onInputChange({
                        target: {value: newValue || ''}
                    } as React.ChangeEvent<HTMLInputElement>);
                }}

                onChange={(event, value) => {
                    if (value && typeof value !== 'string') {
                        onInputChange({
                            target: {value: value.isolate_name}
                        } as React.ChangeEvent<HTMLInputElement>);

                        onSuggestionClick(value);
                    }
                }}
                getOptionLabel={(option) =>
                    typeof option === 'string'
                        ? option
                        : option.isolate_name
                }
                sx={{
                    width: '100%',
                    '& .MuiInputBase-root': {
                        height: '41px',
                    },
                    '& .MuiAutocomplete-listbox': {
                        maxHeight: 300,
                        overflowY: 'auto',
                    },
                    '& .MuiAutocomplete-input': {
                        fontSize: '14px',
                    },
                    '& .MuiAutocomplete-option': {
                        fontSize: '12px',
                    },
                }}
                renderInput={(params) => (
                    <TextField
                        {...params}
                        placeholder="Try BU_909 or PV_ET47 ..."
                        variant="outlined"
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

export default GenomeSearchInput;
