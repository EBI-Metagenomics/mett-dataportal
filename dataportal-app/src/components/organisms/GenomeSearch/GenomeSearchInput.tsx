import React, {useEffect, useRef} from 'react';
import styles from "./GenomeSearchInput.module.scss";
import {Autocomplete, TextField} from "@mui/material";

interface GenomeSearchInputProps {
    query: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    suggestions: { strain_id: number; isolate_name: string; assembly_name: string }[];
    onSuggestionClick: (suggestion: { strain_id: number; isolate_name: string; assembly_name: string }) => void;
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
                options={suggestions}
                getOptionLabel={(option) => `${option.isolate_name} - (${option.assembly_name})`}
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
                        // label="Search Genome"
                        placeholder="Try BU_909 or PV_ET47 ..."
                        value={query}
                        onChange={onInputChange}
                        variant="outlined"
                    />
                )}
                onChange={(event, value) => {
                    if (value) {
                        onSuggestionClick(value);
                    }
                }}
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
