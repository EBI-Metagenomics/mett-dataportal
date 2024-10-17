import React from 'react';

interface DropdownProps {
    options: { value: string, label: string }[];
    selectedValue: string;
    onChange: (value: string) => void;
    className?: string;
    style?: React.CSSProperties;
}

const Dropdown: React.FC<DropdownProps> = ({options, selectedValue, onChange, className, style}) => {
    return (
        <select
            className={`vf-dropdown ${className || ''}`}
            style={style}
            value={selectedValue}
            onChange={e => onChange(e.target.value)}
        >
            <option value="">--- Select Species ---</option>
            {/* Placeholder option */}
            {options.map(option => (
                <option key={option.value} value={option.value}>
                    {option.label}
                </option>
            ))}
        </select>
    );
};

export default Dropdown;
